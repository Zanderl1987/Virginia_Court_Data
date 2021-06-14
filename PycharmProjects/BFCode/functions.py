import numpy as np
from scipy.stats import variation
import datetime
from scipy.linalg import expm
from numpy.linalg import inv
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import os
import base64
import pandas as pd
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from flask_login import current_user 
from decimal import *
from functions_basalIQ import *
from functions_controlIQ import *

#########################################################################################################################
#########################################################################################################################
# General function to compute all glucose metrics based on collected cgm records (array version)
def compute_metrics_array(cgmValueArray,cgmTimeArray,cgmToffArray, d1, d2):

    totalDays = int(np.around((d2-d1)/60/60/24))
    cvV = [0]*totalDays
    lbgiV = [0]*totalDays
    hbgiV = [0]*totalDays
    percentR1V = [0]*totalDays
    percentR2V = [0]*totalDays
    percentR3V = [0]*totalDays
    percentR4V = [0]*totalDays
       
    cgmArray = np.array(cgmValueArray)
    if len(cgmTimeArray) > 0:
        timeArray = np.array(cgmTimeArray)
        tOffArray = np.array(cgmToffArray)
        for i in range(0,totalDays):
            sdCGM = np.array(cgmArray[(timeArray+tOffArray>=d1+i*60*60*24) & (timeArray+tOffArray<d1+(i+1)*60*60*24)])  
            cv = compute_cv(sdCGM) # Computes coefficient of variation
            risk = compute_risk(sdCGM) # Computes hypo and hyper risks
            tir = compute_tir(sdCGM) # Computes time in range    
           
            cvV[i] = cv
            lbgiV[i] = risk[0]
            hbgiV[i] = risk[1]
            percentR1V[i] = tir[0]
            percentR2V[i] = tir[1]
            percentR3V[i] = tir[2]
            percentR4V[i] = tir[3]
            
    metrics = {
        'cv': cvV,
        'lbgi': lbgiV,
        'hbgi': hbgiV,
        'percentR1': percentR1V, # % <70
        'percentR2': percentR2V, # % 70-180
        'percentR3': percentR3V, # % 180-250
        'percentR4': percentR4V  # % > 250
    }

    return metrics

#########################################################################################################################
# Function to compute the time in range
def compute_tir(cgmArray):

    tir = np.array([None, None, None, None])

    if cgmArray.size>0:
        tb70 = (cgmArray < 70.0).sum()

        t70180 = ((cgmArray >= 70.0) & (cgmArray < 180.0)).sum()
        t180250 = ((cgmArray >= 180.0) & (cgmArray < 250.0)).sum()
        ta250 = (cgmArray >= 250.0).sum()

        total = cgmArray.size
        percentR1 = np.around(tb70*100/total, decimals=1)
        percentR4 = np.around(ta250*100/total, decimals=1)
        percentR3 = np.around(t180250*100/total, decimals=1)
        percentR2 = max(np.around(100.0-(percentR1+percentR3+percentR4),decimals=1),0)
        
        tir = np.array([percentR1, percentR2, percentR3, percentR4])
    
    return tir

#########################################################################################################################
# Function to compute the coefficient of variation
def compute_cv(cgmArray):

    cv_transf = None

    if cgmArray.size>0:
        cv = variation(cgmArray)
        cv_transf = (500/3)*cv

        if cv_transf < 0:
            cv_transf = 0.0
        elif cv_transf > 100:
            cv_transf = 100.0

        cv_transf = np.around(cv_transf)

    return cv_transf

#########################################################################################################################
# Function to compute the risks
def compute_risk(cgmArray):

    risk = np.array([None,None])

    if cgmArray.size>0:
        rhArray = np.zeros((cgmArray.size, 1), dtype='float64')
        rlArray = np.zeros((cgmArray.size, 1), dtype='float64')
        i = 0

        for cgm in np.nditer(cgmArray):
            fbg = 1.509*(np.log(cgm)**1.084-5.381)
            rbg = 10*fbg**2
            if fbg < 0:
                rlArray[i] = rbg
                rhArray[i] = 0
            else:
                rhArray[i] = rbg
                rlArray[i] = 0
            i += 1

        LBGI = np.mean(rlArray)
        HBGI = np.mean(rhArray)
        
        LBGI_transf = 10*LBGI
        if LBGI_transf < 0:
            LBGI_transf = 0.0
        elif LBGI_transf > 100:
            LBGI_transf = 100.0
        LBGI_transf = np.around(LBGI_transf)

        HBGI_transf = (50/9)*HBGI
        if HBGI_transf < 0:
            HBGI_transf = 0.0
        elif HBGI_transf > 100:
            HBGI_transf = 100.0
        HBGI_transf = np.around(HBGI_transf)

        risk = np.array([LBGI_transf, HBGI_transf])
        
    return risk

#########################################################################################################################
# Function to compute the amount of available data (array version)
def compute_dataQuality_array(modelPars, d1_utc, d2_utc):
    
    totalDays = int(np.around((d2_utc-d1_utc)/60/60/24))
    playableV = [0]*totalDays
    nonPlayableV = [100]*totalDays

    if len(modelPars) > 0:
        js = 0
        for i in range(0,totalDays):
            piv_ts = d1_utc+i*60*60*24
            if (piv_ts<=modelPars[len(modelPars)-1][0]) and (piv_ts>=modelPars[0][0]):
                for j in range(js,len(modelPars)):
                    if modelPars[j][0]==piv_ts:
                        playableV[i] = 100
                        nonPlayableV[i] = 0
                        js = j+1
                        break
        
    quality = {
        'playable': playableV,
        'nonplayable': nonPlayableV
    }
    
    return quality

#########################################################################################################################
# Function to define the (glucose) area chart data (full glucose data)
def compute_glucSeries_full(cgmTimeArray, cgmValueArray, cgmToffArray, d1, d2):

    totalDays = int(np.around((d2-d1)/60/60/24))
    glucosePack = []
    glucMatrix = np.nan*np.zeros((totalDays, 288)) # Missing data is represented by NaN's
                                                   # 1 sample every 5 minutes: 288 samples per day - 288 columns
                                                   # As many rows as days
    
    if len(cgmValueArray) > 0:
        cgmArray = np.around(np.array(cgmValueArray),decimals=1)
        timeArray = np.array(cgmTimeArray)
        toffArray = np.array(cgmToffArray)

        for i in range(0,totalDays):
            if len(cgmArray[(np.where((timeArray+toffArray>=d1+i*60*60*24) & (timeArray+toffArray<d1+(i+1)*60*60*24)))])>1:
                toff = toffArray[(np.where((timeArray+toffArray>=d1+i*60*60*24) & (timeArray+toffArray<d1+(i+1)*60*60*24)))][0]
                day = datetime.datetime.fromtimestamp(d1+i*60*60*24,tz=datetime.timezone.utc).strftime('%d %b %Y')
                glucMatrix[i,:] = cgmArray[(np.where((timeArray+toffArray>=d1+i*60*60*24) & (timeArray+toffArray<d1+(i+1)*60*60*24)))]
                glucosePack.append([day,glucMatrix[i,:].tolist()])

    return glucosePack    

#########################################################################################################################
# Function to generate parameter array
def generate_parArray(tmtiV,elements,flagTOff):
    
    parV = [[0 for x in range(len(tmtiV)+1)] for y in range(len(elements))]
    j = 0
    tOffV = []
    for element in elements: 
        parV[j][0] = getattr(element,'timeini')+getattr(element,'utcOffset')
        tOffV.append(getattr(element,'utcOffset'))
        for i in range(0,len(tmtiV)):
            value = getattr(element,tmtiV[i])
            parV[j][i+1] = float(value)
        j+=1
    
    if flagTOff:
        return parV,tOffV
    else:
        return parV

#########################################################################################################################
# Function to generate parameter array
def generate_xhparArray(tmtiV,element,xh):

    parV = [0]*xh*12
    j = 0
    for i in range(48-2*xh,len(tmtiV)):
        value = getattr(element,tmtiV[i])
        parV[j*6:j*6+6] = [float(value)]*6
        j+=1
        
    return parV

#########################################################################################################################
# Function to extract profiles
def extractProfiles(parameterArray):
    
    pProfiles = []
        
    if len(parameterArray)>=1:
        jj = 0
        ii = 1
        pProfiles.append(parameterArray[0])
        while ii < len(parameterArray):
            if (parameterArray[jj][1:]==parameterArray[ii][1:])==False:
                jj=ii
                pProfiles.append(parameterArray[jj])
            ii+=1   
     
    return pProfiles

#########################################################################################################################
# Function to extract block profiles
def extract_blockProfiles(profile_full,d1_full,d1,d2):
    
    indAux1 = []
    indAux2 = []

    for y in range(0,len(profile_full)):
        if (profile_full[y][0]>=d1) and (profile_full[y][0]<d2):
            indAux1.append(y)
        if len(indAux1)==0:
            if (profile_full[y][0]>=d1_full) and (profile_full[y][0]<d2):
                indAux2.append(y)

    indAux = indAux1+indAux2[-1:]
    indAux.sort()
    indFinal = list(set(indAux))
    
    profile_block = []

    for y in range(0,len(indFinal)):
        profile_block.append(profile_full[indFinal[y]])
    
    return profile_block

#########################################################################################################################
# Function to generate meal arrays (version 2: 5 min sampling time)
def generate_mArrays_5min(elements):
    
    mealV = []
    hypoV = []

    sdArrayM = [0]*288
    sdArrayH = [0]*288

    if len(elements)>0:
        time = getattr(elements[0],'time')
        toff = getattr(elements[0],'utcOffset')
        dayp = datetime.datetime.fromtimestamp(time+toff,tz=datetime.timezone.utc).strftime('%d %b %Y')
        for element in elements: 
                
            rFlag = getattr(element,'is_rescue')
            time = getattr(element,'time')
            toff = getattr(element,'utcOffset')
            auxTime = datetime.datetime.fromtimestamp(time+toff,tz=datetime.timezone.utc)
            day = auxTime.strftime('%d %b %Y')
            tod = round(60*auxTime.hour+auxTime.minute+auxTime.second/60)
            if tod<0:
                tod+=1440
            ind = round(tod/5)
            carbs = float(getattr(element,'carbs'))/1000.0
            if day==dayp:               
                if rFlag==1:
                    sdArrayH[ind] = carbs         
                else:
                    sdArrayM[ind] = carbs
            else:
                mealV.append([dayp,sdArrayM])        
                hypoV.append([dayp,sdArrayH])
                sdArrayM = [0]*288
                sdArrayH = [0]*288
                if rFlag==1:
                    sdArrayH[ind] = carbs         
                else:
                    sdArrayM[ind] = carbs
            dayp = day

        mealV.append([day,sdArrayM])        
        hypoV.append([day,sdArrayH])

    return mealV,hypoV

#########################################################################################################################
# Function to extract block of meal arrays
def extract_blockMeals(array_full,d1,d2):
    
    d1_datetime = datetime.datetime.utcfromtimestamp(d1)
    d2_datetime = datetime.datetime.utcfromtimestamp(d2)

    profile_block = []

    for y in range(0,len(array_full)):
        dArray = datetime.datetime.strptime(array_full[y][0],'%d %b %Y')
        if (dArray>=d1_datetime) and (dArray<d2_datetime):
            profile_block.append(array_full[y])
    
    return profile_block

#########################################################################################################################
# Function to compute the number of ht per day
def compute_nHT(moH,d1_utc,d2_utc):

    totalDays = int(np.around((d2_utc-d1_utc)/60/60/24))
    nHT_total = [None]*totalDays
    dayArray = [datetime.datetime.fromtimestamp(d1_utc,tz=datetime.timezone.utc).strftime('%d %b %Y')]

    for ii in range(1,totalDays):
        dayArray.append(datetime.datetime.fromtimestamp(d1_utc+ii*60*60*24,tz=datetime.timezone.utc).strftime('%d %b %Y'))
    for ii in range(0,len(moH)):
        indDay = dayArray.index(moH[ii][0])
        nHT_total[indDay] = np.count_nonzero(moH[ii][1:])

    return nHT_total

#########################################################################################################################
# Function to generate array of x hours of insulin records
def generate_xh_InsArray_5min(elements,xh):
    insulinV = []    

    if len(elements)>0:
        insulinV = [0]*xh*12
        j = 0
        for element in elements: 
            basal = float(getattr(element,'basal')) 
            corr = float(getattr(element,'corr'))
            meal = float(getattr(element,'meal'))
                            
            insulinV[j] = basal+corr+meal 
            j+=1        

    return insulinV

#########################################################################################################################
# Function to generate array of x hours from column of insulin table
def generate_xh_Ins_Attr_5min(elements,attr,xh):
    
    attrV = []

    if len(elements)>0:
        attrV = [0]*12*xh
        j = 0
        for element in elements: 
            attrV[j] = float(getattr(element,attr))
            j+=1 
        
    return attrV

#########################################################################################################################
# Function to generate insulin arrays
def generate_xh_InsArray_5min_nonStruct(elements,xh):

    insulinV = []    

    if len(elements)>0:
        for element in elements: 
            basal = float(getattr(element,'basal')) 
            corr = float(getattr(element,'corr'))
            meal = float(getattr(element,'meal'))
                            
            insulinV.append(basal+corr+meal)
                    
    return insulinV

#########################################################################################################################
# Function to generate insulin arrays
def generate_InsArray_5min_nonStruct_interval(elements,d1,d2):

    insulinV = []    

    if len(elements)>0:
        for element in elements: 
            time = getattr(element,'time')
            if (time < d2):
                if (time >= d1):
                    basal = float(getattr(element,'basal')) 
                    corr = float(getattr(element,'corr'))
                    meal = float(getattr(element,'meal'))
                
                    insulinV.append(basal+corr+meal)
            else:
                break
                           
    return insulinV

#########################################################################################################################
# Function to generate an array of the last xh hour meal records
def generate_xh_mealArray_5min(elements,xh):
    
    mealV = [0.0]*xh*12
    
    if len(elements)>0:
        for element in elements: 
            fResc = getattr(element,'is_rescue')
            if fResc==0:
                time = getattr(element,'time')
                toff = getattr(element,'utcOffset')
                auxTime = datetime.datetime.fromtimestamp(time+toff,tz=datetime.timezone.utc)
                tod = round(60*auxTime.hour+auxTime.minute+auxTime.second/60)
                if tod<0:
                    tod+=1440
                ind = round(tod/5)-(288-xh*12)
                carbs = float(getattr(element,'carbs'))/1000.0
                mealV[ind] = carbs

    return mealV

#########################################################################################################################
# Function to generate an array of the last xh hour meal records as informed
def generate_xh_mealArray_Ins_5min(elements,xh):
    
    mealV = [0.0]*xh*12
    
    if len(elements)>0:
        for element in elements: 
            carbs = float(getattr(element,'cho'))/1000.0
            if carbs>0:
                time = getattr(element,'time')
                toff = getattr(element,'utcOffset')
                auxTime = datetime.datetime.fromtimestamp(time+toff,tz=datetime.timezone.utc)
                tod = round(60*auxTime.hour+auxTime.minute+auxTime.second/60)
                if tod<0:
                    tod+=1440
                ind = round(tod/5)-(288-xh*12)
                mealV[ind] = carbs

    return mealV

#########################################################################################################################
# Function to generate glucose array
def generate_xh_glucoseArray_5min(elements,xh, BGinit):
    
    glucoseV = [BGinit]*xh

    if len(elements)>0:
        j = 0
        for element in elements: 
            
            value = float(getattr(element,'value'))       
            glucoseV[j] = value
            j+=1        

    return glucoseV

#########################################################################################################################
# Function to generate insulin parameter array
def generate_iArray_5min(elements,attr):
    
    attrV = []

    sdAttr = [0]*288
    
    if len(elements)>0:
        time = getattr(elements[0],'time')
        toff = getattr(elements[0],'utcOffset')
        dayp = datetime.datetime.fromtimestamp(time+toff,tz=datetime.timezone.utc).strftime('%d %b %Y')
         
        for element in elements: 
                
            time = getattr(element,'time')
            toff = getattr(element,'utcOffset')
            auxTime = datetime.datetime.fromtimestamp(time+toff,tz=datetime.timezone.utc)
            day = auxTime.strftime('%d %b %Y')
            tod = round(60*auxTime.hour+auxTime.minute+auxTime.second/60)
            if tod<0:
                tod+=1440
            ind = round(tod/5)
            attrValue = float(getattr(element,attr))
            if day==dayp:               
                sdAttr[ind] = attrValue
            else:   
                attrV.append([dayp,sdAttr])
                sdAttr = [0]*288
                sdAttr[ind] = attrValue
                
            dayp = day

        attrV.append([day,sdAttr])
        
    return attrV

#########################################################################################################################
# Function to compute the tdb 
def compute_td(basalV,corrV,mealV,d1_utc,d2_utc):

    totalDays = int(np.around((d2_utc-d1_utc)/60/60/24))
    tdb_total = [None]*totalDays
    tdi_total = [None]*totalDays
    dayArray = [datetime.datetime.fromtimestamp(d1_utc,tz=datetime.timezone.utc).strftime('%d %b %Y')]

    for ii in range(1,totalDays):
        dayArray.append(datetime.datetime.fromtimestamp(d1_utc+ii*60*60*24,tz=datetime.timezone.utc).strftime('%d %b %Y'))

    for ii in range(0,len(basalV)):
        indDay = dayArray.index(basalV[ii][0])
        tdb_total[indDay] = np.around(np.sum(basalV[ii][1:]),decimals=1)
        tdi_total[indDay] = np.around(tdb_total[indDay]+np.sum(corrV[ii][1:])+np.sum(mealV[ii][1:]),decimals=1)

    return tdb_total,tdi_total

#########################################################################################################################
# Function to run the replay simulation (step 1)
def replaySim_preProc_v2(modelPars,dataSim):

    # Get data from dataSim dictionary
    tOffV = dataSim['tOffV']
    bProfiles = dataSim['bProfiles']
    crProfiles = dataSim['crProfiles']
    cfProfiles = dataSim['cfProfiles']
    bBolusV = dataSim['bBolusV']
    cBolusV = dataSim['cBolusV']
    mBolusV = dataSim['mBolusV']
    choV = dataSim['choV']
    BT = dataSim['BT']
    lagB = dataSim['lagB']
    corrDecl = dataSim['corrDecl']
    target = dataSim['target']
    userOv = dataSim['userOv']
    tempR = dataSim['tempR']
    extB = dataSim['extB']
    extB_per = dataSim['extB_per']
    extB_dur = dataSim['extB_dur']
    moM = dataSim['moM']
    moH = dataSim['moH']
    INSdif_6 = dataSim['INSdif_6']
    bProfiles_6 = dataSim['bProfiles_6']
    insulinV_6 = dataSim['insulinV_6']
    modelPars_previousD = dataSim['modelPars_previousD']
    apSel = dataSim['apSel']
    adjIns = dataSim['adjIns']
    genIns = dataSim['genIns']
    adjHTs = dataSim['adjHTs']
    genHTs = dataSim['genHTs']
    BW = dataSim['BW']
    cgmValueArray = dataSim['cgmValueArray']
    apData = dataSim['apData']
    insDur = dataSim['insDur']

    # Sampling time & Fourier order
    h = 5
    fourierOrder = 12
    
    # One way to determine the number of simulation days
    nDays = len(modelPars)

    # Prepare lists 
    glucReplayPack = []
    htReplayPack = []
    basalReplayPack = []
    cBolusReplayPack = []
    mBolusReplayPack = []
    SumBolusMem = []
    mealV = np.zeros((nDays,288))
    htV = np.zeros((nDays,288))
    CRV = np.zeros((nDays,288))
    CFV = np.zeros((nDays,288))
    basalPV = np.zeros((nDays,288))

    # Simulation options
    options = {
        'apSel': apSel,
        'adjIns': adjIns,
        'genIns': genIns,
        'adjHTs': adjHTs,
        'genHTs': genHTs
    }

    # Get data from previous day
    if len(modelPars_previousD)>0:
        model_x0 = modelPars_previousD[0][11+2*fourierOrder+1:11+2*fourierOrder+1+16]
        pfCoeff = modelPars_previousD[0][11:10+1+2*fourierOrder+1] # Fourier coefficients
        pivcSig = buildNE(pfCoeff,h)
        pivc_x = pivcSig[0,pivcSig.size-288:pivcSig.size]
        dosekempt = modelPars_previousD[0][11+2*fourierOrder+1+17]
        lastMeal = modelPars_previousD[0][11+2*fourierOrder+1+18]
        HTimer = modelPars_previousD[0][11+2*fourierOrder+1+19]
        corrTimer = modelPars_previousD[0][11+2*fourierOrder+1+20]
    else:
        model_x0 = []
        pivc_x = np.array([0.0]*288)
        dosekempt = 0
        lastMeal = 0
        HTimer = 0
        corrTimer = 0    

    if nDays>0: # One indicator that there is data

        # Pattern manipulation
        BPattern  = profileProc(bProfiles,nDays)
        CRPattern = profileProc(crProfiles,nDays)
        CFPattern = profileProc(cfProfiles,nDays)

        jj = 0

        for ii in range(0,nDays):

            # Struttura
            struttura = strutturaGen(modelPars[ii][1:11],BW)

            # If no initial conditions, compute them
            if len(model_x0)==0:
                misc_x0,u2ss = compute_initialCond(struttura,cgmValueArray[0])
                ins_x0 = [u2ss/(struttura['kd']+struttura['ka1']), u2ss*struttura['kd']/(struttura['ka2']*(struttura['kd']+struttura['ka1']))]
                model_x0 = [0.0, 0.0, 0.0]
                model_x0.extend(ins_x0)
                model_x0.extend(misc_x0)

            # Insulin boluses
            bBolusVD = bBolusV[ii][1]
            mBolusVD = mBolusV[ii][1]
            cBolusVD = cBolusV[ii][1]
            BTD = BT[ii][1]
            lagBD = lagB[ii][1]
            targetD = target[ii][1]
            corrDeclD = corrDecl[ii][1]
            choVD = choV[ii][1]
            userOvD = userOv[ii][1]
            extBD = extB[ii][1]
            extB_durD = extB_dur[ii][1]
            extB_perD = extB_per[ii][1]

            # Meals+HTs
            mealV[ii,:] = moM[ii][1]
            htV[ii,:] = moH[ii][1]

            # Patterns
            for zz in range(0,48):
                CRV[ii,zz*6:zz*6+6] = CRPattern[ii,zz]
                CFV[ii,zz*6:zz*6+6] = CFPattern[ii,zz]
                basalPV[ii,zz*6:zz*6+6] = BPattern[ii,zz]

            # Basal profile+Temp Rate
            basalPV_mod = np.multiply(basalPV[ii,:],0.01*np.array(tempR[ii][1]))
            
            if ii>0:
                INSdif_6 = sim['INSdif_6']
            
            # Generate profile dictionary
            profile = {
                'dosekempt': dosekempt,
                'lastMeal': lastMeal,
                'HTimer': int(HTimer),
                'corrTimer': int(corrTimer),
                'meal': 1000*mealV[ii,:],
                'ht': 1000*htV[ii,:],
                'mealF': 1000*(mealV[ii,:]+htV[ii,:]),
                'basalP': basalPV[ii,:],
                'basalPM': basalPV_mod,
                'CR': CRV[ii,:],
                'CF': CFV[ii,:],
                'target': targetD,
                'userOv': userOvD,
                'bBolusV': bBolusVD,
                'mBolusV': mBolusVD,
                'cBolusV': cBolusVD,
                'BT': BTD,
                'lagB': lagBD,
                'corrDecl': corrDeclD,
                'choV': choVD,
                'extB': extBD,
                'extB_per': extB_perD,
                'extB_dur': extB_durD,
                'bProfiles_6': bProfiles_6,
                'insulinV_6': insulinV_6,
                'INSdif_6': INSdif_6,
                'pivc_x': pivc_x,
                'insDur': insDur
            }

            if ii>0:
                profile['insulinV_6'] = sim['insulinV_6']

            # Basal-IQ
            if options['apSel'] == '1':
                if ii==0:
                    ap = {
                        'flagInsSusp': apData['flagInsSusp'],
                        'tInsSusp': apData['tInsSusp'],
                        'gTPred' : apData['gTPred'],
                        'gVPred' : apData['gVPred']
                    }
                else:
                    ap['flagInsSusp'] = sim['flagInsSusp']
                    ap['tInsSusp'] = sim['tInsSusp']
                    ap['gVPred'] = sim['gVPred']
            # Control-IQ
            elif options['apSel'] == '2':
                
                EXD     = apData['EX'][ii]
                tgtD    = apData['tgt'][ii]
                sleepD  = apData['sleep'][ii]
                TDIpopD = apData['TDIpop'][ii]
                
                if ii==0:
                    TDIest_0,auxVar = controlIQ_TDI(apData['insulinV_24'],apData['SumBolusMem'],TDIpopD[0])
                    ap = {
                        'J24h': np.array(apData['insulinV_24']),
                        'J6': np.array(apData['insulinV_6']),
                        'G6': np.array(apData['glucoseV_6']),
                        'M6': np.array(apData['mealsV_6']),
                        'sbMem': np.array(apData['SumBolusMem']),
                        'TDIest': TDIest_0
                    }
                else:
                    ap.clear()
                    ap = {
                        'J24h': sim['J24h'],
                        'J6': sim['J6'],
                        'G6': sim['G6'],
                        'M6': sim['M6'],
                        'sbMem': sim['sbMem'],
                        'TDIest': sim['TDIest']
                    }

                ap['EX']     = EXD
                ap['tgt']    = tgtD
                ap['sleep']  = sleepD
                ap['TDIpop'] = TDIpopD
            # No-APS
            else:
                ap = []

            # NE signal
            neCoeff = modelPars[ii][11:10+1+2*fourierOrder+1]
            ivcSig = buildNE(neCoeff,h)

            # Run replay            
            sim = runReplay_v2(profile,options,struttura,ivcSig[0],h,model_x0,ap)
            
            # Pack output variables
            if ii<nDays-1:
                model_x0 = sim['model_xf']

            simGlucose = sim['simGlucose']
            dosekempt = sim['dosekempt']
            lastMeal = sim['lastMeal']
            HTimer = sim['HTimer']
            corrTimer = sim['corrTimer']
            htReplay = [i/1000.0 for i in sim['htReplay']]
            basalReplay = sim['bBReplay']
            basalReplay_f = sim['bBReplay_f']
            cBolusReplay = sim['cBReplay']
            cBolusReplay_f = sim['cBReplay_f']
            mBolusReplay = sim['mBReplay']
            mBolusReplay_f = sim['mBReplay_f']
            BTReplay_f = sim['BTReplay_f']
            SumBolusMem = sim['sbMem']
            model_xf = sim['model_xf']
            pivc_x = ivcSig[0]
            J24h = sim['J24h']

            day = datetime.datetime.fromtimestamp(modelPars[ii][0],tz=datetime.timezone.utc).strftime('%d %b %Y')
            glucReplayPack.append([day,simGlucose.tolist()])
            htReplayPack.append([day,htReplay])
            basalReplayPack.append([day,basalReplay])
            cBolusReplayPack.append([day,cBolusReplay])
            mBolusReplayPack.append([day,mBolusReplay])

    # Generate output
    resSim = {
        'glucReplayPack': glucReplayPack,
        'htReplayPack': htReplayPack,
        'basalReplayPack': basalReplayPack,
        'cBolusReplayPack': cBolusReplayPack,
        'mBolusReplayPack': mBolusReplayPack,
        'SumBolusMem': SumBolusMem,
        'J24h': J24h,
        'lastSimGlucose': simGlucose,
        'lastDosekempt': dosekempt,
        'lastLastMeal': lastMeal,
        'lastHTimer': HTimer,
        'lastCorrTimer': corrTimer,
        'lastModel_xf': model_xf,
        'lastBasalReplay': basalReplay,
        'lastBasalReplay_f': np.array(basalReplay_f),
        'lastCBolusReplay_f': np.array(cBolusReplay_f),
        'lastMBolusReplay_f': np.array(mBolusReplay_f),
        'lastCBolusReplay': cBolusReplay,
        'lastMBolusReplay': mBolusReplay,
        'lastBTReplay_f': np.array(BTReplay_f)
    }
    
    return resSim

#########################################################################################################################
# Function to compute steady-state conditions
def compute_initialCond(struttura,BGinit):

    risk = 0.0
    if BGinit<struttura['Gb']:
        fGp = np.power(np.log(BGinit),struttura['r1'])-struttura['r2']
        risk = 10.0*np.power(fGp,2)
    if BGinit*struttura['Vg']>struttura['ke2']:
        Et = struttura['ke1']*(BGinit*struttura['Vg']-struttura['ke2'])
    else:
        Et = 0.0

    Gpop = BGinit*struttura['Vg']
    GGta = -struttura['k2']-struttura['Vmx']*(1+struttura['r3']*risk)*struttura['k2']/struttura['kp3']
    GGtb = struttura['k1']*Gpop-struttura['k2']*struttura['Km0']-struttura['Vm0']+\
       struttura['Vmx']*(1+struttura['r3']*risk)*struttura['Ib']+\
        (struttura['Vmx']*(1+struttura['r3']*risk)*(struttura['k1']+struttura['kp2'])*Gpop-\
        struttura['Vmx']*(1+struttura['r3']*risk)*struttura['kp1']+\
        struttura['Vmx']*(1+struttura['r3']*risk)*(struttura['Fsnc']+Et))/struttura['kp3']
    GGtc = struttura['k1']*Gpop*struttura['Km0']
    Gtop = (-GGtb-np.sqrt(np.power(GGtb,2)-4.0*GGta*GGtc))/(2.0*GGta)
    Idop = max(0.0,(-(struttura['k1']+struttura['kp2'])*Gpop+struttura['k2']*Gtop+struttura['kp1']-(struttura['Fsnc']+Et))/struttura['kp3'])
    Ipop = Idop*struttura['Vi']
    Xop = Ipop/struttura['Vi']-struttura['Ib']

    ILop = struttura['m2']*Ipop/(struttura['m1']+struttura['m30'])
    u2ss = ((struttura['m2']+struttura['m4'])*Ipop-struttura['m1']*ILop)

    misc_x0 = [Gpop, Gtop, Ipop, Xop, Idop, Idop, ILop, Gpop, struttura['Gnb'], 0.0, (struttura['k01g']/struttura['Vgn'])*struttura['Gnb']]

    return misc_x0, u2ss

#########################################################################################################################
# Function to manipulate patterns
def profileProc(profile,nDays):

    profileMod = np.zeros((nDays,48))
    nProf = len(profile) 
    indD = [0]
    if nProf>1:
        for ii in range(0,nProf-1):
            indD.append(indD[ii]+round((profile[ii+1][0]-profile[ii][0])/60/60/24))
    
    for ii in range(0,len(indD)-1):
        profileMod[indD[ii]:indD[ii+1]+1,:] = profile[ii][1:]
    profileMod[indD[len(indD)-1]:nDays,:] = profile[nProf-1][1:]

    return profileMod

#########################################################################################################################
# Function to generate struttura
def strutturaGen(mPar,BW):

    struttura = {
        'Gb': mPar[0],
        'Ib': mPar[1],
        'EGPb': mPar[2],
        'Vmx': mPar[3],
        'Km0': mPar[4],
        'k1': mPar[5],
        'k2': mPar[6],
        'CL': mPar[7],
        'kp2': mPar[8],
        'kmax': mPar[9],
        'tau': 9.99,
        'kabs': 0.340687795521730,
        'kmin': 0.013132521425629,
        'b': 0.784750129681729,
        'd': 0.150842141635419,
        'Vg': 1.837721201777274,
        'Vi': 0.048724317178365,
        'Vgn': 59.306533986843630,
        'r1': 0.812448965378357,
        'r3': 1.440700425342160,
        'p2u': 0.051683639091094,
        'm1': 0.194408127073184,
        'ki': 0.010865364722281,
        'kp3': 0.009689890142566,
        'ksc': 0.110031820289151,
        'kd': 0.029532896480899,
        'ka1': 0.0003063024534025626,
        'ka2': 0.015611558668410,
        'Gnb': 53.873643118016690,
        'k01g': 7.828644720490854,
        'alfaG': 0.496195753873505,
        'kGSRs': 0.245714372755989,
        'kGSRd': 0.152680457204997,
        'kXGn': 0.096869088892215,
        'kcounter': 0.008267741538801,
        'dosekempt': 0.0,
        'rqsto': 0.0,
        'f': 0.9,
        'ke1': 0.0005,
        'ke2': 339,
        'Fsnc': 1.0,
        'HEb': 0.6,
        'kGSRs2': 0.0,
        'BW': BW
    }

    Gth = struttura['Gb']
    Gpb = struttura['Gb']*struttura['Vg']
    r2 = np.log(struttura['Gb'])**struttura['r1']

    struttura.update({'Gth':Gth, 'Gpb':Gpb, 'r2':r2})

    if struttura['Gpb']<=struttura['ke2']:
        Gtb = (struttura['Fsnc']-struttura['EGPb']+struttura['k1']*struttura['Gpb'])/struttura['k2']
        Vm0 = (struttura['EGPb']-struttura['Fsnc'])*(struttura['Km0']+Gtb)/Gtb
    else:
        Gtb = ((struttura['Fsnc']-struttura['EGPb']+struttura['ke1']*(struttura['Gpb']-struttura['ke2']))/struttura['Vg']+struttura['k1']*struttura['Gpb'])/struttura['k2']
        Vm0 = (struttura['EGPb']-struttura['Fsnc']-struttura['ke1']*(struttura['Gpb']-struttura['ke2']))*(struttura['Km0']+Gtb)/Gtb
 
    m2  = 3/5*struttura['CL']/struttura['HEb']/(struttura['Vi']*struttura['BW'])  
    m4  = 2/5*struttura['CL']/(struttura['Vi']*struttura['BW'])
    m30 = struttura['HEb']*struttura['m1']/(1-struttura['HEb'])

    struttura.update({'Gtb':Gtb, 'Vm0':Vm0, 'm2':m2, 'm4':m4, 'm30':m30})
    
    Ains = np.array([[-(struttura['ka1']+struttura['kd']),0,0,0], \
        [struttura['kd'],-struttura['ka2'],0,0],\
            [struttura['ka1'],struttura['ka2'],-(struttura['m2']+struttura['m4']),struttura['m1']],\
                [0,0,struttura['m2'],-(struttura['m1']+struttura['m30'])]]) 
    Bins = np.array([[1],[0],[0],[0]])
    Cins = np.array([0,0,1/struttura['Vi'],0])

    Ipb = struttura['Ib']*struttura['Vi']
    Ilb = struttura['Ib']*struttura['Vi']*struttura['m2']/(struttura['m1']+struttura['m30'])
    Ith = struttura['Ib']
    kp1 = struttura['EGPb']+struttura['kp2']*struttura['Gb']*struttura['Vg']+struttura['kp3']*struttura['Ib']

    struttura.update({'Ains': Ains, 'Bins': Bins, 'Cins': Cins, 'Ipb': Ipb, \
            'Ilb': Ilb, 'Ith': Ith, 'kp1': kp1})

    return struttura    

#########################################################################################################################
# Function to generate the IVC from Fourier coefficients
def buildNE(neCoeff,h):

    neSig = (neCoeff[0]*np.ones((1,288)))
    for xx in range(0,288):
        for pp in range(0,int(np.fix(len(neCoeff)/2))):            
            neSig[0,xx] = neSig[0,xx] + neCoeff[2*pp+1]*np.cos(h*xx*(pp+1)*2*np.pi/1440) + neCoeff[2*pp+2]*np.sin(h*xx*(pp+1)*2*np.pi/1440)
    
    return neSig

#########################################################################################################################
# Function to run the replay (Step 2)
def runReplay_v2(profile,options,struttura,ivcSig,h,model_x0,ap):
    
    n = int(np.round(struttura['tau'])/h)

    model_x = np.zeros((16, 289))
    model_x[:, 0] = model_x0
    tRK = 0

    rqsto = model_x0[0]+model_x0[1]
    dosekempt = profile['dosekempt']
    lastMeal = profile['lastMeal']
    indHTimer = profile['HTimer']
    indCorrTimer = profile['corrTimer']

    insDur = profile['insDur']

    Bmeal_c = np.array([[1], [0], [0]])
    Cmeal_c = np.array(
        [0, 0, (struttura['f']*struttura['kabs']/struttura['BW'])])

    Ains_c = struttura['Ains']
    Bins_c = struttura['Bins']
    Ains_d = expm(Ains_c*h)
    Bins_d = np.matmul(np.matmul(inv(Ains_c), Ains_d -
                                 np.identity(np.size(Ains_c, 0))), Bins_c)

    model_xIns = np.zeros((4, 289))
    model_xIns[:, 0] = np.take(model_x0, [3, 4, 7, 11])
    model_xMeal = np.zeros((3, 289))
    model_xMis = np.zeros((9, 289))
    model_xMis[:, 0] = np.take(model_x0, [5, 6, 8, 9, 10, 12, 13, 14, 15])

    Uaux = [0.0]*7
    Uaux[1] = lastMeal

    INSdif_6 = profile['INSdif_6']
    BP_6 = profile['bProfiles_6']
    insulinV_6 = profile['insulinV_6']

    A_delay_aux = np.identity(n-1)
    A_delay_aux1 = np.zeros((1, n))
    A_delay_aux2 = np.zeros((n-1, 1))
    A_delay = np.block([[A_delay_aux1], [A_delay_aux, A_delay_aux2]])
    B_delay = np.zeros((n, 1))
    B_delay[0][0] = 1
    C_delay = np.zeros((1, n))
    C_delay[0][n-1] = 1

    model_delay = np.zeros((n, 289))

    # model_delay[:, [0]] = 0.2*(6000.0/struttura['BW']) * \
    #     profile['bBolusV'][0]*np.ones((n, 1))
    model_delay[:, [0]] = 0.2*(6000.0/struttura['BW']) * \
        profile['insulinV_6'][-1]*np.ones((n, 1))

    x = len(profile['pivc_x'])
    if np.sum(profile['pivc_x'])==0:
        ivcSig_x = np.array([ivcSig[0]]*x)
    else:
        ivcSig_x = profile['pivc_x']    

    ivcSigp = [ivcSig_x[0], ivcSig_x[0]]
    ivcSig_Fp = [ivcSig_x[-1], ivcSig_x[-1]]

    fNum = [0.003916126660547, 0.007832253321095, 0.003916126660547]
    fDen = [1.000000000000000, -1.815341082704568, 0.831005589346757]

    for ii in range(0,x):
        ivcSigF = np.sum(np.multiply(fNum,np.hstack((ivcSig_x[ii],ivcSigp))))-np.sum(np.multiply(fDen[1:],ivcSig_Fp))
        ivcSigp = np.roll(ivcSigp,1)
        ivcSigp[0] = ivcSig_x[ii]
        ivcSig_Fp = np.roll(ivcSig_Fp,1)
        ivcSig_Fp[0] = ivcSigF

    htReplay = [0]*288
    bBReplay = [0]*288
    cBReplay = [0]*288
    mBReplay = [0]*288

    bBReplay_f = [0.0]*288
    cBReplay_f = [0.0]*288
    mBReplay_f = [0.0]*288
    BTReplay_f = [0]*288

    apDoseA = []

    if options['apSel'] == '1':
        flagInsSusp = ap['flagInsSusp']
        tInsSusp = ap['tInsSusp']
        gTPred = ap['gTPred']
        gVPred = ap['gVPred']
    elif options['apSel'] == '2':
        J24h = ap['J24h']
        J6 = ap['J6']
        M6 = ap['M6']
        G6 = ap['G6']
        sbMem = ap['sbMem']
        TDIest = ap['TDIest']

    delayB = 0
    indExtMBTimer = 0
    indExtCBTimer = 0
    rMDose = 0
    rCDose = 0
    rCDose_final = 0
    rMDose_final = 0
    flagInsSusp = 0

    apDose_acum =[]
    GP30_acum = []
    apBDose_acum = []
    apCDose_acum = []

    for ii in range(0, 288):
                
        ivcSigF = np.sum(np.multiply(fNum,np.hstack((ivcSig[ii],ivcSigp))))-np.sum(np.multiply(fDen[1:],ivcSig_Fp))
        ivcSigp = np.roll(ivcSigp,1)
        ivcSigp[0] = ivcSig[ii]
        ivcSig_Fp = np.roll(ivcSig_Fp,1)
        ivcSig_Fp[0] = ivcSigF
        Uaux[3] = ivcSigF

        Uaux[4] = profile['CR'][ii]
        Uaux[5] = profile['CF'][ii]
        Uaux[6] = profile['target'][ii]

        if options['apSel'] == '2':
            TDIpop = ap['TDIpop'][ii]
            tgt    = ap['tgt'][ii]
            sleep  = ap['sleep'][ii]
            ex     = ap['EX'][ii]

        # Hypo treatment
        if indHTimer >= 6:
            indHTimer = 0
        elif indHTimer >= 1:
            indHTimer = indHTimer+1

        # HT adjuster #
        if profile['ht'][ii] > 0.0:
            if options['adjHTs']:
                g = model_x[12, ii]/struttura['Vg']
                if (g > 70.0) or (indHTimer > 0):
                    mealF_aux = profile['mealF']
                    mealF_aux[ii] = profile['meal'][ii]
                    profile.update({'mealF': mealF_aux})
                else:
                    htReplay[ii] = profile['ht'][ii]
                    indHTimer = 1
            else:
                htReplay[ii] = profile['ht'][ii]
                indHTimer = 1

        # HT generator #
        flagHTG = 0
        if options['genHTs']:
            g = model_x[12, ii]/struttura['Vg']
            if (g <= 70.0) and (indHTimer == 0):
                mealF_aux = profile['mealF']
                mealF_aux[ii] = profile['mealF'][ii]+20e3
                profile.update({'mealF': mealF_aux})
                indHTimer = 1
                flagHTG = 1
                htReplay[ii] = 20e3

        # IOB estimation
        IOBest_BC = IOB_estimator(INSdif_6,int(options['apSel']),insDur)
        
        # Extended Meal bolus
        if indExtMBTimer >= 1 and flagInsSusp!=1: # flagInsSusp!=1 to suspend extended bolus if subj is on Basal-IQ and insulin is suspended
            indExtMBTimer = indExtMBTimer-1
            mBReplay[ii] = rMDose
            rMDose_final = rMDose
        else:
            indExtMBTimer = 0
            rMDose = 0.0
            rMDose_final = 0.0
        
        # Extended Corr bolus
        if indExtCBTimer >= 1 and flagInsSusp!=1: # flagInsSusp!=1 to suspend extended bolus if subj is on Basal-IQ and insulin is suspended
            indExtCBTimer = indExtCBTimer-1
            cBReplay[ii] = rCDose
            rCDose_final = rCDose
        else:
            indExtCBTimer = 0
            rCDose = 0.0
            rCDose_final = 0.0

        # Bolus calculator
        mBolus = 0
        cBolus = 0

        if profile['mBolusV'][ii] > 0.0:
            delayB = profile['lagB'][ii]
            indCorrTimer = 1
            g = model_x[12, ii]/struttura['Vg']
            cho = profile['choV'][ii]/1e3
            if profile['userOv'][ii] == 0.0:
                mBolus_f,mBolus,rMDose,indExtMBTimer = MB_calculator(
                    cho, g, Uaux[4], Uaux[5], Uaux[6], IOBest_BC,profile['corrDecl'][ii],profile['extB'][ii],profile['extB_per'][ii],profile['extB_dur'][ii])
            else:
                if options['adjIns']:
                    mBolus_f,mBolus,rMDose,indExtMBTimer = MB_calculator(
                        cho, g, Uaux[4], Uaux[5], Uaux[6], IOBest_BC,profile['corrDecl'][ii],profile['extB'][ii],profile['extB_per'][ii],profile['extB_dur'][ii])
                else:
                    mBolus_f,mBolus,rMDose,indExtMBTimer = FB_calculator(profile['mBolusV'][ii],profile['extB'][ii],profile['extB_per'][ii],profile['extB_dur'][ii])
            mBReplay[ii] = mBolus
            mBReplay_f[ii] = mBolus_f

        if (profile['cBolusV'][ii] > 0.0) and (profile['choV'][ii] == 0.0) and (profile['BT'][ii] == 0):
            delayB = profile['lagB'][ii]
            indCorrTimer = 1
            g = model_x[12, ii]/struttura['Vg']
            if profile['userOv'][ii] == 0.0:
                cBolus_f,cBolus,rCDose,indExtCBTimer = CB_calculator(g, Uaux[5], Uaux[6], IOBest_BC, profile['extB'][ii],profile['extB_per'][ii],profile['extB_dur'][ii])
            else:
                if options['adjIns']:
                    cBolus_f,cBolus,rCDose,indExtCBTimer = CB_calculator(g, Uaux[5], Uaux[6], IOBest_BC, profile['extB'][ii],profile['extB_per'][ii],profile['extB_dur'][ii])
                else:
                    cBolus_f,cBolus,rCDose,indExtCBTimer = FB_calculator(profile['cBolusV'][ii],profile['extB'][ii],profile['extB_per'][ii],profile['extB_dur'][ii])
            cBReplay[ii] = cBolus
            cBReplay_f[ii] = cBolus_f

        if options['apSel'] != '2':
            if options['genIns']:
                g = model_x[12, ii]/struttura['Vg']
                if (g > 250.0) and (indCorrTimer == 0):
                    cBolus_f,cBolus,rCDose,indExtCBTimer = CB_calculator(g, Uaux[5], Uaux[6], IOBest_BC, 0,0,0)
                    indCorrTimer = 1
                    cBReplay[ii] = cBolus

        basal = profile['basalPM'][ii]/12.0

        # IOB re-estimation taking into account async bolus
        INSdif_6_aux = np.copy(INSdif_6)
        INSdif_6_aux[len(INSdif_6)-1] = INSdif_6[len(INSdif_6) -
                                                 1] + mBolus + cBolus + rMDose_final+rCDose_final

        IOBest_BC = IOB_estimator(INSdif_6_aux,int(options['apSel']),insDur)

        if options['apSel'] == '2':
            J24h_aux = np.copy(J24h)
            if len(J24h)==288:
                J24h_aux[len(J24h)-1] = J24h[len(J24h)-1] + mBolus + cBolus + rMDose_final+rCDose_final
            else:
                J24h_aux = np.append(J24h_aux,[mBolus + cBolus + rMDose_final+rCDose_final])
            J6_aux = np.copy(J6)
            J6_aux[len(J6)-1] = J6[len(J6)-1] + mBolus + cBolus + rMDose_final+rCDose_final

            M6_aux = np.copy(M6)
            M6_aux[len(M6)-1] = M6[len(M6)-1]+profile['choV'][ii]/1e3

        # AP
        if options['apSel'] == '0':
            apDose = basal
            bBReplay[ii] = apDose
            bBReplay_f[ii] = apDose
        elif options['apSel'] == '1':
            # BasalIQ
            apDose,tInsSusp,flagInsSusp = basalIQ(gTPred,gVPred,tInsSusp,basal,flagInsSusp)
            bBReplay[ii] = apDose
            bBReplay_f[ii] = apDose
        else:
            # ControlIQ
            tod = ii*5.0/60.0
            TDIest, sbMem, apBDose, apCDose, indCorrTimer, GP30 = controlIQ(
                J24h_aux, J6_aux, G6, M6_aux, tod, np.array(BP_6), profile['basalPM'][ii], 
                Uaux[5], ex, indCorrTimer, sbMem, TDIpop, sleep, tgt, struttura['BW'], TDIest)
            apDose = apBDose+apCDose
            bBReplay[ii] = apBDose
            bBReplay_f[ii] = apBDose
            cBReplay[ii] = cBReplay[ii]+apCDose
            cBReplay_f[ii] = cBReplay_f[ii]+apCDose
            apBDose_acum.append(apBDose)
            apCDose_acum.append(apCDose)
            apDose_acum.append(apDose)
            GP30_acum.append(GP30)
            if apCDose>0.0:
                BTReplay_f[ii] = 1

        if indCorrTimer ==0:
            delayB = 0

        # Correction bolus
        if indCorrTimer >= 12+delayB:
            indCorrTimer = 0
        elif indCorrTimer >= 1:
            indCorrTimer = indCorrTimer+1

        apDoseA.append(apDose)

        # Final insulin dose
        Uaux[2] = 6000*(mBolus+cBolus+apDose+rMDose_final+rCDose_final)/5/struttura['BW']

        # Update 6h insulin vector
        INSdif_6 = np.roll(INSdif_6, -1)

        INSdif_6[len(INSdif_6)-1] = mBolus+cBolus+rMDose_final+rCDose_final + \
            apDose - profile['basalPM'][ii]/12.0
        BP_6 = np.roll(BP_6, -1)
        BP_6[len(BP_6)-1] = profile['basalPM'][ii]

        if options['apSel'] == '2':
            if len(J24h)==288:
                J24h = np.roll(J24h, -1)
                J24h[len(J24h)-1] = mBolus+cBolus+rMDose_final+rCDose_final+apDose
            else:
                J24h = np.append(J24h,[mBolus+cBolus+rMDose_final+rCDose_final+apDose])
            J6 = np.roll(J6, -1)
            J6[len(J6)-1] = mBolus+cBolus+rMDose_final+rCDose_final+apDose

            M6 = np.roll(M6, -1)
            M6[len(M6)-1] = profile['choV'][ii]/1e3

        insulinV_6 = np.roll(insulinV_6,-1)
        insulinV_6[len(insulinV_6)-1] = mBolus+cBolus+rMDose_final+rCDose_final+apDose

        # Meals
        Uaux[0] = profile['mealF'][ii]/h  # To rate

        if (profile['mealF'][ii] > 0.0) or (flagHTG == 1):
            rqsto = model_xMeal[0, ii]+model_xMeal[1, ii]

        if profile['mealF'][ii] > 0.0:
            lastMeal = profile['mealF'][ii]
            Uaux[1] = lastMeal
            dosekempt = Uaux[1]+rqsto

        struttura.update({'dosekempt': dosekempt, 'rqsto': rqsto})

        if struttura['dosekempt'] > 0.0:
            aa = 5/2/(1-struttura['b'])/struttura['dosekempt']
            cc = 5/2/struttura['d']/struttura['dosekempt']
            if struttura['dosekempt'] <= 16000:
                kgut = struttura['kmax']
            else:
                kgut = struttura['kmin']+(struttura['kmax']-struttura['kmin'])/2*(np.tanh(aa*(model_xMeal[0, ii]+model_xMeal[1, ii] -
                                                                                              struttura['b']*struttura['dosekempt']))-np.tanh(cc*(model_xMeal[0, ii]+model_xMeal[1, ii]-struttura['d']*struttura['dosekempt']))+2)
        else:
            kgut = struttura['kmax']

        struttura.update({'kgut': kgut})

        if lastMeal<=20000:
            mF = 5.0
            Ameal_c = np.array([[-mF*struttura['kmax'], 0, 0],
                                [mF*struttura['kmax'], -mF*struttura['kgut'], 0],
                                [0, mF*struttura['kgut'], -struttura['kabs']]])
        else:
            Ameal_c = np.array([[-struttura['kmax'], 0, 0],
                                [struttura['kmax'], -struttura['kgut'], 0],
                                [0, struttura['kgut'], -struttura['kabs']]])

        Ameal_d = expm(Ameal_c*h)
        Bmeal_d = np.matmul(
            np.matmul(inv(Ameal_c), Ameal_d-np.identity(np.size(Ameal_c, 0))), Bmeal_c)

        model_xMeal[:, [ii+1]
                    ] = np.matmul(Ameal_d, model_xMeal[:, [ii]])+Bmeal_d*Uaux[0]
        Rat = np.matmul(Cmeal_c, model_xMeal[:, ii])

        # Ins
        model_delay[:, [ii+1]
                    ] = np.matmul(A_delay, model_delay[:, [ii]])+B_delay*Uaux[2]

        model_xIns[:, [ii+1]] = np.matmul(Ains_d, model_xIns[:, [ii]])+np.matmul(
            Bins_d, np.matmul(C_delay, model_delay[:, [ii]]))

        It = model_xIns[2, ii]/struttura['Vi']
        In = It*Uaux[3]

        # Mis
        inputs_equations = np.array([It, In, Rat])
        k1 = model_equations(model_xMis[:, ii], struttura, inputs_equations)
        k2 = model_equations(
            model_xMis[:, ii]+h*k1/2, struttura, inputs_equations)
        k3 = model_equations(
            model_xMis[:, ii]+h*k2/2, struttura, inputs_equations)
        k4 = model_equations(
            model_xMis[:, ii]+h*k3, struttura, inputs_equations)

        model_xMis[:, ii+1] = model_xMis[:, ii]+h*(k1+2*k2+2*k3+k4)/6
        model_xMis[[0],ii+1] = max(model_xMis[[0],ii+1],0)
        model_xMis[[1],ii+1] = max(model_xMis[[1],ii+1],0)
        model_xMis[[3],ii+1] = max(model_xMis[[3],ii+1],0)
        model_xMis[[4],ii+1] = max(model_xMis[[4],ii+1],0)
        model_xMis[[5],ii+1] = max(model_xMis[[5],ii+1],0)
        model_x[[0, 1, 2], ii+1] = model_xMeal[:, ii+1]
        model_x[[3, 4, 7, 11], ii+1] = model_xIns[:, ii+1]
        model_x[[5, 6, 8, 9, 10, 12, 13, 14, 15], ii+1] = model_xMis[:, ii+1]

        if options['apSel'] == '1':
            gVPred = np.roll(gVPred, -1)
            gVPred[len(gVPred)-1] = model_x[12, ii+1]/struttura['Vg']

        if options['apSel'] == '2':
            G6 = np.roll(G6, -1)
            G6[len(G6)-1] = model_x[12, ii]/struttura['Vg']

        tRK = tRK + h

    simGlucose = np.clip(model_x[12, 0:np.size(
        model_x, 1)-1]/struttura['Vg'], 20.0, 400.0)

    model_xf = model_x[:, 287].tolist()

    sim = {
        'simGlucose': simGlucose,
        'model_xf': model_xf,
        'dosekempt': dosekempt,
        'lastMeal': lastMeal,
        'HTimer': indHTimer,
        'corrTimer': indCorrTimer,
        'bBReplay': bBReplay,
        'bBReplay_f': bBReplay_f,
        'cBReplay': cBReplay,
        'cBReplay_f': cBReplay_f,
        'mBReplay': mBReplay,
        'mBReplay_f': mBReplay_f,
        'htReplay': htReplay,
        'BTReplay_f': BTReplay_f,
        'INSdif_6': INSdif_6,
        'insulinV_6': insulinV_6
    }

    if options['apSel'] == '0':
        sim['sbMem'] = []
        sim['J24h'] = []
    elif options['apSel'] == '1':
        sim['sbMem'] = []
        sim['J24h'] = []
        sim['tInsSusp'] = tInsSusp
        sim['gVPred'] = gVPred
        sim['flagInsSusp'] = flagInsSusp
    elif options['apSel'] == '2':
        sim['J24h'] = J24h
        sim['J6'] = J6
        sim['G6'] = G6
        sim['M6'] = M6
        sim['sbMem'] = sbMem
        sim['TDIest'] = TDIest

    return sim

#########################################################################################################################
# Function that contains the model equations
def model_equations(x,struttura,U):

    It = U[0]
    In = U[1]
    Rat = U[2]
    dxdt = np.zeros(9)

    # Hepatic Glucose Production
    EGPt = struttura['kp1']-struttura['kp2']*max(x[0],0)-struttura['kp3']*max(x[4],0)+struttura['kcounter']*x[7]

    # Insulin Independent Glucose Utilization
    Uiit = struttura['Fsnc']
    
    # Renal excretion
    if x[0]>struttura['ke2']:
        Et = struttura['ke1']*(x[0]-struttura['ke2'])
    else:
        Et = 0.0

    # Glucose kinetics
    dxdt[0] = max(EGPt,0)+Rat-Uiit-Et-struttura['k1']*max(x[0],0)+struttura['k2']*max(x[1],0)
    
    # Utilization by insulin dependent tissues
    if x[0]/struttura['Vg']>=struttura['Gb']:
        fGp = 0
    else:
        threshold = 60
        if x[0]/struttura['Vg']>threshold:
            fGp = np.log(x[0]/struttura['Vg'])**struttura['r1']-struttura['r2']
        else:
            fGp = np.log(threshold)**struttura['r1']-struttura['r2']
    
    risk = 10*fGp**2

    Vmt = struttura['Vm0'] + struttura['Vmx']*x[2]*(1+struttura['r3']*risk)
    Kmt = struttura['Km0']
    Uidt = Vmt*x[1]/(Kmt+x[1])
    dxdt[1] = -max(Uidt,0)+struttura['k1']*max(x[0],0)-struttura['k2']*max(x[1],0)

    # Insulin action on glucose utilization
    dxdt[2] = -struttura['p2u']*x[2]+struttura['p2u']*(In-struttura['Ib'])
    
    # Insulin action on production
    dxdt[3] = -struttura['ki']*(x[3]-In)
    dxdt[4] = -struttura['ki']*(x[4]-x[3])

    # Subcutaneous glucose
    dxdt[5] = -struttura['ksc']*(x[5]-x[0])
    
    # Glucagon secretion & kinetics
    # Secretion
    Gp = x[0]/struttura['Vg']
    GSRb = struttura['k01g']/struttura['Vgn']*struttura['Gnb']

    if Gp-struttura['Gth']>0:
        GSRs = max(struttura['kGSRs2']*(struttura['Gth']-Gp)+GSRb,0)
    else:
        GSRs = max(struttura['kGSRs']*(struttura['Gth']-Gp)/(max(It-struttura['Ith'],0)+1)+GSRb,0)
    
    dxdt[8] = -struttura['alfaG']*(x[8]-GSRs)
    
    GSRd = max(-struttura['kGSRd']*dxdt[0]/struttura['Vg'],0)
    GSR = GSRd+max(x[8],0)
    
    # Kinetics
    dxdt[6] = -struttura['k01g']/struttura['Vgn']*x[6]+GSR
    
    # Glucagon action
    dxdt[7] = -struttura['kXGn']*x[7]+struttura['kXGn']*max(x[6]-struttura['Gnb'],0)

    return dxdt

#########################################################################################################################
# Function to estimate IOB
def IOB_estimator(INSdif,apSel,insDur):

    # IOB_curve_4h = np.transpose([[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    #     0,0,0,0,0,0,0.0013,0.0028,0.0045,0.0064,0.0085,
    #     0.0108,0.0135,0.0164,0.0196,0.0233,0.0273,0.0318,
    #     0.0369,0.0425,0.0487,0.0556,0.0633,0.0719,0.0813,
    #     0.0918,0.1034,0.1162,0.1304,0.1460,0.1632,0.1822,
    #     0.2029,0.2257,0.2506,0.2777,0.3072,0.3393,0.3739,
    #     0.4111,0.4510,0.4936,0.5387,0.5861,0.6355,0.6865,
    #     0.7383,0.7901,0.8407,0.8884,0.9312,0.9664,0.9908]])

    IOB_curve_6h = np.transpose([[0.0041,0.0046,0.0050,0.0055,0.0061,0.0067,0.0073,0.0081,0.0089,0.0098,0.0107,0.0118,
        0.0129,0.0142,0.0156,0.0171,0.0188,0.0206,0.0226,0.0248,0.0272,0.0298,0.0327,0.0358,
        0.0392,0.0429,0.0469,0.0513,0.0561,0.0613,0.0670,0.0732,0.0799,0.0872,0.0951,0.1036,
        0.1129,0.1230,0.1339,0.1456,0.1583,0.1720,0.1867,0.2025,0.2196,0.2378,0.2574,0.2784,
        0.3007,0.3246,0.3499,0.3768,0.4053,0.4353,0.4670,0.5001,0.5348,0.5708,0.6080,0.6463,
        0.6854,0.7250,0.7647,0.8040,0.8422,0.8787,0.9125,0.9426,0.9676,0.9860,0.9959,0.9953]])
    
    IOB_curve_2h_mud = np.transpose([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0.0018,0.0057,0.0106,0.0166,
        0.0240,0.0330,0.0437,0.0565,0.0716,0.0891,0.1095,0.1329,0.1597,0.1900,0.2242,0.2623,0.3046,
        0.3510,0.4015,0.4559,0.5139,0.5748,0.6380,0.7021,0.7658,0.8270,0.8834,0.9317,0.9682,0.9884,0.9866]])
    
    IOB_curve_3h_mud = np.transpose([[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.0007,0.0019,
        0.0034,0.0052,0.0073,0.0099,0.0129,0.0164,0.0205,0.0253,0.0308,0.0371,0.0444,0.0527,0.0621,0.0727,0.0846,
        0.0981,0.1131,0.1298,0.1484,0.1690,0.1917,0.2166,0.2438,0.2734,0.3055,0.3402,0.3773,0.4170,0.4592,0.5035,
        0.5500,0.5981,0.6475,0.6976,0.7477,0.7969,0.8441,0.8878,0.9266,0.9583,0.9808,0.9913,0.9866]])

    IOB_curve_4h_mud = np.transpose([[0.0000,0.0001,0.0001,0.0002,0.0003,0.0004,0.0005,0.0007,0.0009,0.0011,
        0.0013,0.0016,0.0020,0.0024,0.0029,0.0034,0.0040,0.0047,0.0056,0.0065,0.0076,0.0088,0.0102,0.0117,0.0135,
        0.0155,0.0178,0.0204,0.0233,0.0265,0.0302,0.0343,0.0388,0.0439,0.0496,0.0560,0.0630,0.0708,0.0795,0.0890,
        0.0996,0.1112,0.1240,0.1381,0.1535,0.1703,0.1887,0.2087,0.2304,0.2539,0.2793,0.3066,0.3360,0.3674,0.4008,
        0.4363,0.4738,0.5133,0.5544,0.5971,0.6411,0.6860,0.7312,0.7761,0.8201,0.8620,0.9008,0.9350,0.9629,0.9825,0.9913,0.9866]])
    
    IOB_curve_5h_mud = np.transpose([[0.0027,0.0030,0.0033,0.0037,0.0041,0.0045,0.0050,0.0055,0.0061,0.0068,0.0076,
        0.0084,0.0093,0.0103,0.0114,0.0126,0.0139,0.0154,0.0170,0.0188,0.0207,0.0229,0.0253,0.0279,0.0308,0.0340,0.0374,
        0.0413,0.0454,0.0500,0.0550,0.0605,0.0665,0.0731,0.0803,0.0881,0.0967,0.1060,0.1161,0.1271,0.1391,0.1521,0.1661,
        0.1814,0.1978,0.2156,0.2348,0.2554,0.2775,0.3012,0.3265,0.3536,0.3823,0.4129,0.4451,0.4791,0.5148,0.5520,0.5907,
        0.6306,0.6715,0.7130,0.7547,0.7960,0.8362,0.8745,0.9098,0.9408,0.9660,0.9836,0.9913,0.9866]])
    
    IOB_curve_6h_mud = np.transpose([[0.0082,0.0090,0.0098,0.0106,0.0116,0.0126,0.0137,0.0149,0.0162,0.0176,0.0191,0.0208,
        0.0226,0.0245,0.0267,0.0289,0.0314,0.0341,0.0370,0.0401,0.0435,0.0472,0.0511,0.0554,0.0600,0.0649,0.0703,0.0760,0.0822,
        0.0889,0.0961,0.1038,0.1120,0.1209,0.1304,0.1407,0.1516,0.1633,0.1758,0.1892,0.2034,0.2186,0.2348,0.2520,0.2703,0.2897,
        0.3102,0.3319,0.3548,0.3789,0.4043,0.4309,0.4587,0.4878,0.5180,0.5493,0.5816,0.6149,0.6489,0.6834,0.7184,0.7533,0.7880,
        0.8220,0.8549,0.8859,0.9145,0.9397,0.9608,0.9765,0.9856,0.9866]])

    IOB_curve_7h_mud = np.transpose([[0.0193,0.0208,0.0223,0.0240,0.0258,0.0277,0.0297,0.0319,0.0342,0.0367,0.0394,0.0423,0.0453,
        0.0486,0.0521,0.0558,0.0598,0.0641,0.0686,0.0734,0.0786,0.0841,0.0899,0.0962,0.1028,0.1099,0.1174,0.1253,0.1338,0.1428,0.1523,
        0.1624,0.1732,0.1845,0.1965,0.2092,0.2225,0.2367,0.2516,0.2673,0.2838,0.3011,0.3194,0.3385,0.3585,0.3794,0.4013,0.4240,0.4477,
        0.4723,0.4978,0.5242,0.5513,0.5793,0.6079,0.6371,0.6667,0.6968,0.7270,0.7572,0.7872,0.8167,0.8454,0.8729,0.8989,0.9228,0.9441,
        0.9622,0.9764,0.9858,0.9896,0.9866]])
    
    IOB_curve_8h_mud = np.transpose([[0.0343,0.0365,0.0389,0.0414,0.0441,0.0469,0.0499,0.0531,0.0564,0.0600,0.0638,0.0678,0.0720,0.0765,
        0.0813,0.0863,0.0916,0.0972,0.1032,0.1094,0.1161,0.1231,0.1304,0.1382,0.1464,0.1551,0.1642,0.1738,0.1838,0.1944,0.2056,0.2173,0.2295,
        0.2424,0.2558,0.2700,0.2847,0.3001,0.3162,0.3330,0.3505,0.3688,0.3877,0.4074,0.4278,0.4489,0.4708,0.4933,0.5165,0.5404,0.5649,0.5900,
        0.6156,0.6416,0.6680,0.6947,0.7215,0.7483,0.7751,0.8015,0.8274,0.8526,0.8769,0.8998,0.9211,0.9405,0.9574,0.9714,0.9819,0.9885,0.9903,
        0.9866]])

    if apSel==2:
        IOB_curve = np.copy(IOB_curve_6h)
    else:
        if insDur==2:
            IOB_curve = np.copy(IOB_curve_2h_mud)
        elif insDur==3:
            IOB_curve = np.copy(IOB_curve_3h_mud)
        elif insDur==4:
            IOB_curve = np.copy(IOB_curve_4h_mud)
        elif insDur==5:
            IOB_curve = np.copy(IOB_curve_5h_mud)
            IOB_curve = np.copy(IOB_curve_6h) # Almost the same
        elif insDur==6:
            IOB_curve = np.copy(IOB_curve_6h_mud)
        elif insDur==7:
            IOB_curve = np.copy(IOB_curve_7h_mud)
        elif insDur==8:
            IOB_curve = np.copy(IOB_curve_8h_mud)
        else:
            IOB_curve = np.copy(IOB_curve_5h_mud)

    IOBest = np.clip(np.matmul(INSdif,IOB_curve)[0],0,np.Inf)

    return IOBest

#########################################################################################################################
# Function to compute the meal bolus
def MB_calculator(cho,g,CR,CF,target,IOBest,corrDecl,extB,extB_per,extB_dur):

    # print('MB_calculator')
    # print(cho)
    # print(CR)
    # print(CF)
    # print(target)
    # print(IOBest)
    # print(corrDecl)
    # print(extB)
    # print(extB_dur)
    # print(extB_per)

    mDose = cho/CR
    cDose = (g-target)/CF
    
    tBolus = 0
    tBolus_f = 0
    indExtBTimer = 0
    rDose = 0

    if mDose>0:
        tBolus_f = mDose
        if extB>0:       
            indExtBTimer = int(np.fix(extB_dur/5))
            rDose = ((100.0-extB_per)*mDose/100.0)/indExtBTimer
            mDose = extB_per*mDose/100.0     
        if (corrDecl==1) and (g>70.0):
            tBolus = mDose
        else:
            if cDose>=0:
                if cDose-IOBest<0:
                    tBolus = mDose
                else:
                    tBolus = mDose+cDose-IOBest
                    tBolus_f = tBolus_f+cDose-IOBest
            else:
                if mDose+cDose-IOBest>0:
                    tBolus = mDose+cDose-IOBest
                    tBolus_f = tBolus_f+cDose-IOBest
                else:
                    tBolus = mDose
    
    return tBolus_f,tBolus,rDose,indExtBTimer

#########################################################################################################################
# Function to compute the correction bolus
def CB_calculator(g,CF,target,IOBest,extB,extB_per,extB_dur):

    # print('CB_calculator')
    # print(g)
    # print(CF)
    # print(target)
    # print(IOBest)
    # print(extB)
    # print(extB_dur)
    # print(extB_per)

    cDose = (g-target)/CF

    tBolus = 0.0
    indExtBTimer = 0
    rDose = 0.0
    tBolus_f = 0.0

    if cDose>=0:
        if cDose-IOBest<0:
            tBolus = 0.0
        else:
            cBolus = cDose-IOBest
            tBolus_f = cDose-IOBest
            if extB>0:       
                indExtBTimer = int(np.fix(extB_dur/5))
                rDose = ((100.0-extB_per)*cBolus/100.0)/indExtBTimer
                tBolus = extB_per*cBolus/100.0  
            else:
                tBolus = cBolus
    
    return tBolus_f,tBolus,rDose,indExtBTimer   

#########################################################################################################################
# Function to compute a fixed bolus
def FB_calculator(dose,extB,extB_per,extB_dur):

    tBolus = 0.0
    indExtBTimer = 0
    rDose = 0.0
    tBolus_f = 0.0

    if dose>=0:
        tBolus_f = dose
        if extB>0:       
            indExtBTimer = int(np.fix(extB_dur/5))
            rDose = ((100.0-extB_per)*dose/100.0)/indExtBTimer
            tBolus = extB_per*dose/100.0  
        else:
            tBolus = dose
    
    return tBolus_f,tBolus,rDose,indExtBTimer   

#########################################################################################################################
# Function to generate the TIR chart
def tirChart(vals):

    fig, ax = plt.subplots()
    size = 0.4
    outer_colors = [[61.0/255.0,173.0/255.0,217.0/255.0,0.75],\
        [109.0/255.0,237.0/255.0,139.0/255.0,0.75],\
            [248.0/255.0,248.0/255.0,87.0/255.0,0.75], \
                [243.0/255.0,50.0/255.0,16.0/255.0,0.75]]
    inner_colors = outer_colors
    ax.pie(vals[:,0], radius=1, colors=outer_colors,wedgeprops=dict(width=size-0.1, edgecolor='w'))
    ax.pie(vals[:,1], radius=1-size, colors=inner_colors,wedgeprops=dict(width=size-0.1, edgecolor='w'))
    ax.set(aspect="equal", title='outer circle: original; inner circle: replay')
    strFile = 'static/img/tir.png'
    if os.path.isfile(strFile):
        os.remove(strFile)   
    plt.savefig(strFile, bbox_inches = 'tight',pad_inches = 0)
    plt.close()

    with open(strFile, 'rb') as f:
        tir_string = base64.b64encode(f.read()).decode()

    return tir_string

#########################################################################################################################
# Function to generate the logo
def logoChart():

    strFile = 'static/img/logo_hor_v2.png'
    
    with open(strFile, 'rb') as f:
        logo_string = base64.b64encode(f.read()).decode()

    return logo_string

#########################################################################################################################
# Function to compute the glucose metrics for report
def meanMetrics(original,replay):

    tirs = np.array([[np.nanmean(np.array(original['metrics']['percentR1'],dtype=np.float)), np.nanmean(np.array(replay['metrics']['percentR1'],dtype=np.float))],\
        [np.nanmean(np.array(original['metrics']['percentR2'],dtype=np.float)), np.nanmean(np.array(replay['metrics']['percentR2'],dtype=np.float))], \
        [np.nanmean(np.array(original['metrics']['percentR3'],dtype=np.float)), np.nanmean(np.array(replay['metrics']['percentR3'],dtype=np.float))], \
        [np.nanmean(np.array(original['metrics']['percentR4'],dtype=np.float)), np.nanmean(np.array(replay['metrics']['percentR4'],dtype=np.float))]])
    
    cvs = np.array([np.nanmean(np.array(original['metrics']['cv'],dtype=np.float)),np.nanmean(np.array(replay['metrics']['cv'],dtype=np.float))])
    tdis = np.array([np.nanmean(np.array(original['tdi'],dtype=np.float)),np.nanmean(np.array(replay['tdi'],dtype=np.float))])
    tdbs = np.array([np.nanmean(np.array(original['tdb'],dtype=np.float)),np.nanmean(np.array(replay['tdb'],dtype=np.float))])
    hypors = np.array([np.nanmean(np.array(original['metrics']['lbgi'],dtype=np.float)),np.nanmean(np.array(replay['metrics']['lbgi'],dtype=np.float))])
    hypers = np.array([np.nanmean(np.array(original['metrics']['hbgi'],dtype=np.float)),np.nanmean(np.array(replay['metrics']['hbgi'],dtype=np.float))]) 
    hts = np.array([np.nanmean(np.array(original['nHT'],dtype=np.float)),np.nanmean(np.array(replay['nHT'],dtype=np.float))])

    return tirs,cvs,tdis,tdbs,hypors,hypers,hts

#########################################################################################################################
# Function to generate the glucose chart
def glucChart(original,replay):

    times = pd.date_range('2019-01-01', periods=288, freq='5min')

    glucOrig = []
    glucReplay = []
    for ii in range(0,len(original)):
        glucOrig.append(original[ii][1:][0])
        glucReplay.append(replay[ii][1:][0])

    glucOrig_median = np.nanmedian(glucOrig,axis=0)
    glucOrig_p25 = np.nanpercentile(glucOrig,25,axis=0)
    glucOrig_p75 = np.nanpercentile(glucOrig,75,axis=0)
    
    glucReplay_median = np.nanmedian(glucReplay,axis=0)
    glucReplay_p25 = np.nanpercentile(glucReplay,25,axis=0)
    glucReplay_p75 = np.nanpercentile(glucReplay,75,axis=0)

    gLimit1 = 70.0*np.ones(288)
    gLimit2 = 180.0*np.ones(288)
    fig, ax = plt.subplots(1)
    fig.autofmt_xdate()
    ax.fill_between(times,gLimit1,gLimit2,facecolor=[130.0/255.0,245.0/255.0,126.0/255.0,.15],alpha=0.15)
    ax.fill_between(times,glucOrig_p25,glucOrig_p75,facecolor=[61.0/255.0,173.0/255.0,217.0/255.0,.3],alpha=0.5)
    plt.plot(times, glucOrig_median,color=[61.0/255.0,173.0/255.0,217.0/255.0,1],linewidth=2,alpha=0.7)
    ax.fill_between(times,glucReplay_p25,glucReplay_p75,facecolor=[222.0/255.0,157.0/255.0,117.0/255.0,.3],alpha=0.5)
    plt.plot(times, glucReplay_median,color=[222.0/255.0,157.0/255.0,117.0/255.0,1],linewidth=2,alpha=0.7)
    plt.xticks(rotation=45)
    plt.ylabel('Glucose [mg/dl]', fontsize=11)
    xfmt = mdates.DateFormatter('%I %p')
    ax.xaxis.set_major_formatter(xfmt)
    ax.grid(linestyle=':', linewidth='0.5')
    strFile = 'static/img/gluc.png'
    if os.path.isfile(strFile):
        os.remove(strFile)   
    plt.savefig(strFile, bbox_inches = 'tight',pad_inches = 0)
    plt.close()

    with open(strFile, 'rb') as f:
        gluc_string = base64.b64encode(f.read()).decode()

    return gluc_string

#########################################################################################################################
# Function to generate the profile chart
def profileChart(original,replay,nf,d2,p,f):

    indP = []
    p_string = []
    p_dates = []

    p_orig_t = []
    p_orig_v = []
    p_replay_t = []
    p_replay_v = []

    p_diff = []

    for ii in range(0,len(original)):
        if original[ii]!=replay[ii]:
            indP.append(ii)
    times = pd.date_range('2019-01-01', periods=p, freq=f)
    for ii in range(0,len(indP)):
        fig, ax = plt.subplots(1)
        fig.autofmt_xdate()
        if nf=='meal':
            plt.step(times, np.array(original[indP[ii]][1:][0]),color=[61.0/255.0,173.0/255.0,217.0/255.0,1],linewidth=2,alpha=1,label='Original')
            plt.step(times, np.array(replay[indP[ii]][1:][0]),color=[222.0/255.0,157.0/255.0,117.0/255.0,1],linewidth=4,alpha=0.5,label='Replay')

            mOrig_ind = np.nonzero(np.array(original[indP[ii]][1:][0]))
            mOrig_time = []
            mOrig_size = []
            for qq in range(0,len(mOrig_ind[0])):
                mOrig_time.append(datetime.datetime.fromtimestamp(1593475200+mOrig_ind[0][qq]*300,tz=datetime.timezone.utc).strftime('%I:%M %p'))
                mOrig_size.append(original[indP[ii]][1:][0][mOrig_ind[0][qq]])

            mReplay_ind = np.nonzero(np.array(replay[indP[ii]][1:][0]))
            mReplay_time = []
            mReplay_size = []
            for qq in range(0,len(mReplay_ind[0])):
                mReplay_time.append(datetime.datetime.fromtimestamp(1593475200+mReplay_ind[0][qq]*300,tz=datetime.timezone.utc).strftime('%I:%M %p'))
                mReplay_size.append(replay[indP[ii]][1:][0][mReplay_ind[0][qq]])

            plt.ylabel('Carbs [g]', fontsize=11)
        else:
            plt.step(times, np.array(original[indP[ii]][1:]),color=[61.0/255.0,173.0/255.0,217.0/255.0,1],linewidth=2,alpha=1,label='Original')
            plt.step(times, np.array(replay[indP[ii]][1:]),color=[222.0/255.0,157.0/255.0,117.0/255.0,1],linewidth=4,alpha=0.5,label='Replay')
            if nf=='bp':
                plt.ylabel('Basal rate [U/h]', fontsize=11)
            elif nf=='crp':
                plt.ylabel('CR [g/U]', fontsize=11)
            else:
                plt.ylabel('CF [mg/dl/U]', fontsize=11)

            profOrig_time = []
            profOrig_size = []
            for qq in range(0,len(original[indP[ii]][1:])):
                profOrig_time.append(datetime.datetime.fromtimestamp(1593475200+qq*60*30,tz=datetime.timezone.utc).strftime('%I:%M %p')+' - '+datetime.datetime.fromtimestamp(1593475200+(qq+1)*60*30,tz=datetime.timezone.utc).strftime('%I:%M %p'))
                profOrig_size.append(original[indP[ii]][1:][qq])

            profReplay_time = []
            profReplay_size = []
            for qq in range(0,len(replay[indP[ii]][1:])):
                profReplay_time.append(datetime.datetime.fromtimestamp(1593475200+qq*60*30,tz=datetime.timezone.utc).strftime('%I:%M %p')+' - '+datetime.datetime.fromtimestamp(1593475200+(qq+1)*60*30,tz=datetime.timezone.utc).strftime('%I:%M %p'))
                profReplay_size.append(replay[indP[ii]][1:][qq])
            
            p_diff_aux = []
            for qq in range(0,len(original[indP[ii]][1:])):
                p_diff_aux.append(np.around(-100.0+100.0*replay[indP[ii]][1:][qq]/original[indP[ii]][1:][qq]))

        plt.xticks(rotation=45)
        xfmt = mdates.DateFormatter('%I %p')
        ax.xaxis.set_major_formatter(xfmt)
        legend = ax.legend(loc='upper right', shadow=True, fontsize='small')
        strFile = 'static/img/'+nf+str(ii)+'.png'
        ax.grid(linestyle=':', linewidth='0.5')
        if os.path.isfile(strFile):
            os.remove(strFile)   
        plt.savefig(strFile, bbox_inches = 'tight',pad_inches = 0)
        plt.close()

        with open(strFile, 'rb') as f:
            p_string.append(base64.b64encode(f.read()).decode())
            if nf!='meal':
                dayS = datetime.datetime.fromtimestamp(original[indP[ii]][0],tz=datetime.timezone.utc).strftime('%d %b %Y')
                if indP[ii]==len(original)-1:
                    dayE = datetime.datetime.fromtimestamp(d2).strftime('%d %b %Y')
                else:
                    dayE = datetime.datetime.fromtimestamp(original[indP[ii]+1][0]).strftime('%d %b %Y')
                dayR = dayS+' - '+dayE
                p_dates.append(dayR)
                p_orig_t.append(profOrig_time)
                p_orig_v.append(np.around(np.array(profOrig_size),decimals=2))
                p_replay_t.append(profReplay_time)
                p_replay_v.append(np.around(np.array(profReplay_size),decimals=2))
                p_diff.append(p_diff_aux)
            else:
                p_orig_t.append(mOrig_time)
                p_orig_v.append(np.trunc(np.array(mOrig_size)))
                p_replay_t.append(mReplay_time)
                p_replay_v.append(np.trunc(np.array(mReplay_size)))
                p_dates.append(original[indP[ii]][0])
            
    return p_string,p_dates,p_orig_t,p_orig_v,p_replay_t,p_replay_v,p_diff
