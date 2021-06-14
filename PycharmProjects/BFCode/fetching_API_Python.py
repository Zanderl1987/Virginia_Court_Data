import json
import numpy as np
import datetime
from scipy import interpolate
from scipy import signal

#####################################################################################################################
def read_jsonFile(jsonFile):

    with open(jsonFile,encoding="utf8") as f:
        data = json.load(f)

    return data

#####################################################################################################################
def determine_APSMode(data):

    flagCIQ = 0
    flagBIQ = 0

    ii = 0
    flagWhile = True
    while (flagWhile) and (ii<len(data)):
        if (data[ii]['name'][0:6]=="LID_AA"):
            flagWhile = False
            flagCIQ = 1 # Control-IQ
        ii+=1
    
    ii = 0
    flagWhile = True
    while (flagWhile) and (ii<len(data)):
        if data[ii]['id']==140: # Confirmed, but test data is mixed
            flagWhile = False
            flagBIQ = 1 # Basal-IQ
        ii+=1
         
    return flagBIQ,flagCIQ

#####################################################################################################################
def sort_filter_data(data,timeStampIni,timeStampEnd,utcOffset):
    
    dateEv_acum = []

    for ii in range(0,len(data)):
        dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
        dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
        dateEv_acum.append(dateEv)
    
    indSort = np.argsort(dateEv_acum,axis=0)
    sData = np.take_along_axis(np.array(data),indSort,axis=0)
    sdateEv_acum = np.take_along_axis(np.array(dateEv_acum),indSort,axis=0)

    indAcum = []
    flagWhile = True
    ii = 0
    while (ii<len(sdateEv_acum)) and (flagWhile):
        if (sdateEv_acum[ii]>=timeStampIni) and (sdateEv_acum[ii]<=timeStampEnd):
            indAcum.append(ii)
        elif (sdateEv_acum[ii]>timeStampEnd):
            flagWhile = False
        ii+=1

    sfData = np.take_along_axis(np.array(sData),np.array(indAcum),axis=0)

    return sfData

#####################################################################################################################
def extract_OLdata(data,utcOffset):

    glucoseData = extract_glucoseData(data,utcOffset)
    bpData,crData,cfData = extract_profData(data,utcOffset)
    mealData = extract_mealData(data,utcOffset)
    insData = extract_insData(data,utcOffset)

    return glucoseData,bpData,crData,cfData,mealData,insData

#####################################################################################################################
def extract_glucoseData(data,utcOffset):
       
    glucoseValues    = []
    glucoseStatus    = []
    glucoseTrend     = []
    glucoseTS        = []
    glucoseUTCOffset = []
    glucoseCal       = []
    glucoseCalTS     = []
    glucose_final    = []

    for ii in range(0,len(data)):
        if data[ii]['id']==256:
            glucoseValueStatus = data[ii]['dataFields']['glucoseValueStatus']['rawValue']
            glucoseStatus_aux = data[ii]['dataFields']['CGM Data Type']['rawValue']
            
            if (glucoseStatus_aux!=16) and (glucoseStatus_aux!=2):
                glucoseStatus.append(data[ii]['dataFields']['CGM Data Type']['rawValue'])
                glucoseTrend.append(data[ii]['dataFields']['Rate']['value'])
                if glucoseValueStatus==0:
                    glucoseValues.append(data[ii]['dataFields']['currentGlucoseDisplayValue']['value'])
                elif glucoseValueStatus==1:
                    glucoseValues.append(400.0)
                else:
                    glucoseValues.append(40.0)

                dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
                dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
                glucoseTS.append(dateEv)
                glucoseUTCOffset.append(utcOffset)

        if data[ii]['id']==210:
            dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
            dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
            glucoseCalTS.append(dateEv)
            
    glucoseTS_final,ind    = np.unique(glucoseTS,return_index=True)
    glucoseValues_final    = np.array(glucoseValues)[ind].tolist()
    glucoseTrend_final     = np.array(glucoseTrend)[ind].tolist()
    glucoseStatus_final    = np.array(glucoseStatus)[ind].tolist()
    glucoseUTCOffset_final = np.array(glucoseUTCOffset)[ind].tolist()
    glucoseCal_final       = [0]*len(glucoseTS_final)

    glucoseCalTS_final,ind = np.unique(glucoseCalTS,return_index=True)
    
    for ii in range(0,len(glucoseCalTS_final)):
        indMin = np.argmin(np.abs(glucoseCalTS_final[ii]-glucoseTS_final))
        if glucoseCalTS_final[ii]-glucoseTS_final[indMin]<=0:
            glucoseCal_final[indMin] = 1
        elif len(glucoseTS_final)>=indMin+2:
            if glucoseCalTS_final[ii]-glucoseTS_final[indMin+1]<=600:
                glucoseCal_final[indMin+1] = 1

    glucose_final.append(glucoseTS_final.tolist())
    glucose_final.append(glucoseValues_final)
    glucose_final.append(glucoseUTCOffset_final)
    glucose_final.append(glucoseCal_final)
    glucose_final.append(glucoseTrend_final)
    glucose_final.append(glucoseStatus_final)
    
    return glucose_final

#####################################################################################################################
def extract_profData(data,utcOffset):
    
    bpValues = []
    bpTS     = []
    bp_final = []

    for ii in range(0,len(data)):
        if data[ii]['id']==279:
            if data[ii]['dataFields']['Profile Basal Rate']['value']!=65535:
                bpValues.append(data[ii]['dataFields']['Profile Basal Rate']['value']/1000.0)
                dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
                dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
                bpTS.append(dateEv)

    bpTS_final,ind = np.unique(bpTS,return_index=True)
    bpValues_final = np.array(bpValues)[ind].tolist()

    bp_final.append(bpTS_final.tolist())
    bp_final.append(bpValues_final)

    ###########################################################

    crValues = []
    crTS     = []
    cr_final = []

    for ii in range(0,len(data)):
        if data[ii]['id']==64:
            if data[ii]['dataFields']['CarbRatio']['value']>0.0:
                crValues.append(data[ii]['dataFields']['CarbRatio']['value'])
                dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
                dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
                crTS.append(dateEv)

    crTS_final,ind = np.unique(crTS,return_index=True)
    crValues_final = np.array(crValues)[ind].tolist()

    cr_final.append(crTS_final.tolist())
    cr_final.append(crValues_final)

    ###########################################################

    cfValues = []
    cfTS     = []
    cf_final = []

    for ii in range(0,len(data)):
        if data[ii]['id']==65:
            if data[ii]['dataFields']['ISF']['value']>0.0:
                cfValues.append(data[ii]['dataFields']['ISF']['value'])
                dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
                dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
                cfTS.append(dateEv)

    cfTS_final,ind = np.unique(cfTS,return_index=True)
    cfValues_final = np.array(cfValues)[ind].tolist()

    cf_final.append(cfTS_final.tolist())
    cf_final.append(cfValues_final)

    return bp_final,cr_final,cf_final

#####################################################################################################################
def extract_mealData(data,utcOffset):
    
    mealValues    = []
    mealTS        = []
    meal_final    = []
    mealIsResc    = []
    mealUTCOffset = []

    for ii in range(0,len(data)):
        if (data[ii]['id']==64) and (data[ii]['dataFields']['BolusType']['rawValue']==1) and (data[ii]['dataFields']['CarbAmount']['value']>0):
            mealValues.append(data[ii]['dataFields']['CarbAmount']['value'])
            dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
            dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
            mealTS.append(dateEv)
            mealIsResc.append(0)
            mealUTCOffset.append(utcOffset)

    mealTS_final,ind    = np.unique(mealTS,return_index=True)
    mealValues_final    = np.array(mealValues)[ind].tolist()
    mealIsResc_final    = np.array(mealIsResc)[ind].tolist()
    mealUTCOffset_final = np.array(mealUTCOffset)[ind].tolist()

    meal_final.append(mealTS_final.tolist())
    meal_final.append(mealValues_final)
    meal_final.append(mealIsResc_final)
    meal_final.append(mealUTCOffset_final)

    return meal_final

#####################################################################################################################
def updateAbBol(mealData_ini,bolusData_ini,cgmF_time,cgmF_values):
    
    mealData = mealData_ini.copy()
    bolusData = bolusData_ini.copy()

    for ii in range(0,len(bolusData_ini[12])):
        if (bolusData_ini[12][ii]<0.01) and ((bolusData_ini[9][ii]==0) or ((bolusData_ini[9][ii]==1) and (bolusData_ini[10][ii]>0))): # Bolus was aborted
            bolusData[1][ii] = 0.0
            bolusData[2][ii] = 0.0
            bolusData[8][ii] = 1
            if bolusData[4][ii]>0:
                tb = bolusData[0][ii]
                vCGM = cgmF_values[(cgmF_time>tb-60*0) & (cgmF_time<tb+60*90)]
                tCGM = np.arange(0,len(vCGM)*5,5)
                mCGM = np.polyfit(tCGM,vCGM,1)
                if len(mealData[0])>0:
                    a_aux1 = np.array(mealData[0])
                    nMin = np.argwhere((a_aux1>tb-300) & (a_aux1<tb+300))
                else:
                    nMin = []
                if mCGM[0]<0.15 or (len(nMin)>1):
                    if len(mealData[0])>0:
                        if len(nMin)>0:
                            mealData[0].pop(nMin[0][0])
                            mealData[1].pop(nMin[0][0])
                            mealData[2].pop(nMin[0][0])
                            mealData[3].pop(nMin[0][0])
        if (bolusData_ini[9][ii]==0):
            if (abs(bolusData_ini[12][ii]-bolusData_ini[1][ii])>0.01) and (abs(bolusData_ini[12][ii]-bolusData_ini[2][ii])>0.01):
                if bolusData_ini[1][ii]!=0.0:
                    bolusData[1][ii]=bolusData_ini[12][ii]
                else:
                    bolusData[2][ii]=bolusData_ini[12][ii]
                bolusData[8][ii]=1
                if bolusData[4][ii]>0:
                    tb = bolusData[0][ii]
                    vCGM = cgmF_values[(cgmF_time>tb-60*0) & (cgmF_time<tb+60*90)]
                    tCGM = np.arange(0,len(vCGM)*5,5)
                    mCGM = np.polyfit(tCGM,vCGM,1)
                    if len(mealData[0])>0:
                        a_aux1 = np.array(mealData[0])
                        nMin = np.argwhere((a_aux1>tb-300) & (a_aux1<tb+300))
                    else:
                        nMin = []
                    if (mCGM[0]<0.15) or (len(nMin)>1):
                        if len(mealData[0])>0:
                            if len(nMin)>0:
                                mealData[0].pop(nMin[0][0])
                                mealData[1].pop(nMin[0][0])
                                mealData[2].pop(nMin[0][0])
                                mealData[3].pop(nMin[0][0])

    return mealData,bolusData
    
#####################################################################################################################
def extract_bBolus(data,utcOffset,APS_mode):
        
    basalValues = []
    basalTS = []
    basalTR = []
    basalUTCOffset = []
    basalPCM = []
    basal_final = []

    basalAP_daily_value = []
    basalAP_daily_TS    = []

    basalAP_changes_values = []
    basalAP_changes_TS     = []

    for ii in range(0,len(data)):
        
        if (data[ii]['id']==279) and (data[ii]['dataFields']['Commanded Rate']['value']!=65535):

            crs = data[ii]['dataFields']['Commanded Rate Source']['rawValue']

            basalValues.append(data[ii]['dataFields']['Commanded Rate']['value']/1000.0/12.0)
            
            if crs==2:
                try:
                    tempRate = data[ii]['dataFields']['Temp Rate']['value']*100.0/data[ii]['dataFields']['Commanded Rate']['value']
                except:
                    tempRate = 100.0
            else:
                tempRate = 100.0
            
            basalTR.append(tempRate)
            dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
            dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
            basalTS.append(dateEv)
            basalUTCOffset.append(utcOffset)

            if crs==0: # Suspended
                basalPCM.append(-1)
            elif (crs==1) or (crs==2): # 1-Profile; 2-Temp Rate. TODO: Check how to check if BIQ is active
                if APS_mode==1: # BIQ
                    basalPCM.append(1) #BIQ
                else:
                    basalPCM.append(0) #OL
            else:
                if APS_mode==1:
                    basalPCM.append(1) #BIQ
                else:
                    basalPCM.append(2) #CIQ

    basalTS_final,ind = np.unique(basalTS,return_index=True)
    basalValues_final = np.array(basalValues)[ind].tolist()
    basalTR_final = np.array(basalTR)[ind].tolist()
    basalUTCOffset_final = np.array(basalUTCOffset)[ind].tolist()
    basalPCM_final = np.array(basalPCM)[ind].tolist()

    basal_final.append(basalTS_final.tolist())
    basal_final.append(basalValues_final)
    basal_final.append(basalTR_final)
    basal_final.append(basalUTCOffset_final)
    basal_final.append(basalPCM_final)

    return basal_final

#####################################################################################################################
def extract_aBolus(data,utcOffset):
    
    aBTS        = []
    aBTS_1      = []
    aBCorr      = []
    aBMeal      = []
    aB_corrDecl = []
    aB_carbs    = []
    aB_smbg     = []
    aB_target   = []
    aB_bType    = []
    aB_userOV   = []
    aB_ext      = []
    aB_ext_per  = []
    aB_ext_dur  = []
    aB_quick    = []
    aB_dNow     = []

    aB_final    = []

    for ii in range(0,len(data)):
        if data[ii]['id']==64:
            aB_carbs.append(1000.0*data[ii]['dataFields']['CarbAmount']['value'])
            aB_smbg.append(data[ii]['dataFields']['BG']['value'])

            if data[ii]['dataFields']['BolusType']['rawValue']==2:
                aB_bType.append(1) # Automatic correction
            else:
                aB_bType.append(0) # Manual dose

    for ii in range(0,len(data)):
        if (data[ii]['id']==65):
            if data[ii]['dataFields']['StandardPercent']['value']<100.0:
                aB_ext.append(1)
                aB_ext_per.append(data[ii]['dataFields']['StandardPercent']['value'])
                aB_ext_dur.append(data[ii]['dataFields']['Duration']['value'])
            else:
                aB_ext.append(0)
                aB_ext_per.append(0)
                aB_ext_dur.append(0)
        
            if data[ii]['dataFields']['Options']['rawValue']!=3:
                aB_target.append(data[ii]['dataFields']['TargetBG']['value'])
            else:
                if len(aB_target)>0:
                    aB_target.append(aB_target[-1])
                else:
                    aB_target.append(110.0)
                    
            aB_corrDecl.append(data[ii]['dataFields']['DeclinedCorrection']['rawValue'])
        
            if data[ii]['dataFields']['Options']['rawValue']==2: # QuickBolus
                aB_userOV.append(1)
                aB_quick.append(1)
            else:
                aB_userOV.append(data[ii]['dataFields']['UserOverride']['rawValue'])
                aB_quick.append(0)

    jj = 0
    for ii in range(0,len(data)):

        if (data[ii]['id']==66):
            dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
            dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
            aBTS_1.append(dateEv)
            if (aB_quick[jj]==1) or (data[ii]['dataFields']['FoodBolusSize']['value']==0.0):
                aBCorr.append(data[ii]['dataFields']['TotalBolusSize']['value'])
                aBMeal.append(0.0)
            else: 
                aBMeal.append(data[ii]['dataFields']['TotalBolusSize']['value'])
                aBCorr.append(0.0)
            jj+=1
        
        if (data[ii]['id']==20):
            dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
            dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
            aBTS.append(dateEv)
            aB_dNow.append(data[ii]['dataFields']['InsulinDelivered']['value'])

    for ii in range(0,len(aB_smbg)):
        if aB_smbg[ii] == 0:
            if aB_carbs[ii]>0:
                aB_corrDecl[ii] = 1

    aBTS_1_final,ind1 = np.unique(aBTS_1,return_index=True)
    ind1 = np.sort(ind1)

    aBTS_final,ind    = np.unique(aBTS,return_index=True)
    aBCorr_final      = np.array(aBCorr)[ind1].tolist()
    aBMeal_final      = np.array(aBMeal)[ind1].tolist()
    aB_corrDecl_final = np.array(aB_corrDecl)[ind1].tolist()
    aB_carbs_final    = np.array(aB_carbs)[ind1].tolist()
    aB_smbg_final     = np.array(aB_smbg)[ind1].tolist()
    aB_target_final   = np.array(aB_target)[ind1].tolist()
    aB_bType_final    = np.array(aB_bType)[ind1].tolist()
    aB_userOV_final   = np.array(aB_userOV)[ind1].tolist()
    aB_ext_final      = np.array(aB_ext)[ind1].tolist()
    aB_ext_per_final  = np.array(aB_ext_per)[ind1].tolist()
    aB_ext_dur_final  = np.array(aB_ext_dur)[ind1].tolist()  
    aB_dNow_final     = np.array(aB_dNow)[ind].tolist()

    v1 = np.array(aB_ext_dur_final)
    v1_aux = np.argwhere(v1>0)

    for ii in range(0,len(v1_aux)):
        if aB_ext_per_final[v1_aux[ii][0]]==0:
            aB_dNow_final.insert(v1_aux[ii][0],0.0)
            aBTS_final = np.insert(aBTS_final,v1_aux[ii][0],aBTS_1_final[v1_aux[ii][0]])

    if len(aBCorr_final)>len(aBTS_final):
        aBTS_final = np.append(aBTS_final,aBTS_1_final[-1])
        if aBCorr_final[-1]>0:
            aB_dNow_final.append(aBCorr_final[-1])
        else:
            aB_dNow_final.append(aBMeal_final[-1])
    elif len(aBCorr_final)<len(aBTS_final):
        aBTS_final = np.delete(aBTS_final,0,0)
        aB_dNow_final.pop(0)

    aB_final.append(aBTS_final.tolist())
    aB_final.append(aBCorr_final)
    aB_final.append(aBMeal_final)
    aB_final.append(aB_corrDecl_final)
    aB_final.append(aB_carbs_final)
    aB_final.append(aB_smbg_final)
    aB_final.append(aB_target_final)
    aB_final.append(aB_bType_final)
    aB_final.append(aB_userOV_final)
    aB_final.append(aB_ext_final)
    aB_final.append(aB_ext_per_final)
    aB_final.append(aB_ext_dur_final)
    aB_final.append(aB_dNow_final)

    return aB_final    

#####################################################################################################################
def merge_ins_lag(aB,basal):

    basalTS = np.array(basal[0])

    bCorr    = np.array([0.0]*len(basal[0]))
    bMeal    = np.array([0.0]*len(basal[0]))
    corrDecl = np.array([0]*len(basal[0]))
    carbs    = np.array([0.0]*len(basal[0]))
    smbg     = np.array([0.0]*len(basal[0]))
    target   = np.array([0.0]*len(basal[0]))
    bType    = np.array([0]*len(basal[0]))
    userOv   = np.array([0]*len(basal[0]))
    ext      = np.array([0]*len(basal[0]))
    ext_per  = np.array([0.0]*len(basal[0]))
    ext_dur  = np.array([0.0]*len(basal[0]))
    lagB     = np.array([0]*len(basal[0]))

    for ii in range(0,len(aB[0])):
        indMin = np.argmin(np.abs(aB[0][ii]-basalTS))
        if (aB[0][ii]-basalTS[indMin]>=-1.5*60) and (aB[7][ii]==0):
            lagB[indMin] = 1
        
        if (bCorr[indMin]!=0.0) or (bMeal[indMin]!=0.0):
            if indMin+1>len(basal[0])-1:
                ind_acum = []
                jj = indMin
                flagCond = True
                while (jj>0) and (flagCond):
                    if (bCorr[jj]==0) and (bMeal[jj]==0):
                        flagCond = False
                    else:
                        ind_acum.append(jj)
                    jj-=1
                ind_acumF = np.array(ind_acum)
                bCorr[ind_acumF-1]    = bCorr[ind_acumF]
                bMeal[ind_acumF-1]    = bMeal[ind_acumF]
                corrDecl[ind_acumF-1] = corrDecl[ind_acumF]
                carbs[ind_acumF-1]    = carbs[ind_acumF]
                smbg[ind_acumF-1]     = smbg[ind_acumF]
                target[ind_acumF-1]   = target[ind_acumF]
                bType[ind_acumF-1]    = bType[ind_acumF]
                userOv[ind_acumF-1]   = userOv[ind_acumF] 
                ext[ind_acumF-1]      = ext[ind_acumF]
                ext_per[ind_acumF-1]  = ext_per[ind_acumF]
                ext_dur[ind_acumF-1]  = ext_dur[ind_acumF]

                bCorr[indMin]    = aB[1][ii]
                bMeal[indMin]    = aB[2][ii]
                corrDecl[indMin] = aB[3][ii]
                carbs[indMin]    = aB[4][ii]
                smbg[indMin]     = aB[5][ii]
                target[indMin]   = aB[6][ii]
                bType[indMin]    = aB[7][ii]
                userOv[indMin]   = aB[8][ii]
                ext[indMin]      = aB[9][ii]
                ext_per[indMin]  = aB[10][ii]
                ext_dur[indMin]  = aB[11][ii]

            else:
                bCorr[indMin+1]    = aB[1][ii]
                bMeal[indMin+1]    = aB[2][ii]
                corrDecl[indMin+1] = aB[3][ii]
                carbs[indMin+1]    = aB[4][ii]
                smbg[indMin+1]     = aB[5][ii]
                target[indMin+1]   = aB[6][ii]
                bType[indMin+1]    = aB[7][ii]
                userOv[indMin+1]   = aB[8][ii]
                ext[indMin+1]      = aB[9][ii]
                ext_per[indMin+1]  = aB[10][ii]
                ext_dur[indMin+1]  = aB[11][ii]
        else:
            bCorr[indMin]    = aB[1][ii]
            bMeal[indMin]    = aB[2][ii]
            corrDecl[indMin] = aB[3][ii]
            carbs[indMin]    = aB[4][ii]
            smbg[indMin]     = aB[5][ii]
            target[indMin]   = aB[6][ii]
            bType[indMin]    = aB[7][ii]
            userOv[indMin]   = aB[8][ii]
            ext[indMin]      = aB[9][ii]
            ext_per[indMin]  = aB[10][ii]
            ext_dur[indMin]  = aB[11][ii]

    ind = np.where(target>0)[0]
    if len(ind)>0:
        target[0:ind[0]+1] = [target[ind[0]]]*(ind[0]+1)
        if len(ind)>1:
            for ii in range(0,len(ind)-1):
                target[ind[ii]:ind[ii+1]] = [target[ind[ii]]]*(ind[ii+1]-ind[ii])
            target[ind[-1]:] = [target[ind[-1]]]*(len(target)-ind[-1])
        else:
            target[ind[0]:] = [target[ind[0]]]*(len(target)-ind[0])

    ins_final = basal
    ins_final.append(bCorr.tolist())
    ins_final.append(bMeal.tolist())
    ins_final.append(corrDecl.tolist())
    ins_final.append(carbs.tolist())
    ins_final.append(smbg.tolist())
    ins_final.append(target.tolist())
    ins_final.append(bType.tolist())
    ins_final.append(userOv.tolist())
    ins_final.append(ext.tolist())
    ins_final.append(ext_per.tolist())
    ins_final.append(ext_dur.tolist())
    ins_final.append(lagB.tolist())

    return ins_final

#####################################################################################################################
def extract_biqData(data,utcOffset):

    biqTS        = []
    biqUTCOffset = []
    biqInsSusp   = []
    biq_final    = []

    for ii in range(0,len(data)):
        
        if (data[ii]['id']==279) and (data[ii]['dataFields']['Commanded Rate']['value']!=65535):

            crs = data[ii]['dataFields']['Commanded Rate Source']['rawValue']

            if crs==3:            
                dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
                dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
                biqTS.append(dateEv)
                biqUTCOffset.append(utcOffset)
                biqInsSusp.append(1)

    biqTS_final,ind    = np.unique(biqTS,return_index=True)
    biqUTCOffset_final = np.array(biqUTCOffset)[ind].tolist()
    biqInsSusp_final   = np.array(biqInsSusp)[ind].tolist()

    biq_final.append(biqTS_final.tolist())
    biq_final.append(biqUTCOffset_final)
    biq_final.append(biqInsSusp_final)

    return biq_final

#####################################################################################################################
def extract_ciqData(data,utcOffset,TDIpop):

    ciqTS        = []
    ciqUTCOffset = []
    ciqTDIpop    = []
    ciqtgt       = []
    ciqsleep     = []

    ciq_final = []

    for ii in range(0,len(data)):
        dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
        dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
        
        if data[ii]['id']==227:   
            ciqTS.append(dateEv)
            ciqtgt.append(data[ii]['dataFields']['gluctgt']['value'])
            if data[ii]['dataFields']['PercentSleepX']['value']>0.0:
                ciqsleep.append(1)
            else:
                ciqsleep.append(0)

            ciqUTCOffset.append(utcOffset)
            ciqTDIpop.append(TDIpop)
    
    ciqTS_final,ind    = np.unique(ciqTS,return_index=True)
    ciqUTCOffset_final = np.array(ciqUTCOffset)[ind].tolist()
    ciqTDIpop_final    = np.array(ciqTDIpop)[ind].tolist()
    ciqtgt_final       = np.array(ciqtgt)[ind].tolist()
    ciqsleep_final     = np.array(ciqsleep)[ind].tolist()

    ciq_final.append(ciqTS_final.tolist())
    ciq_final.append(ciqUTCOffset_final)
    ciq_final.append(ciqTDIpop_final)
    ciq_final.append(ciqtgt_final)
    ciq_final.append(ciqsleep_final)

    return ciq_final

#####################################################################################################################
def extract_ciqData_ex(data,ciqF_time,utcOffset):

    flagEX = False
    ciqEX_tini = []
    ciqEX_tend = []

    ciqEX = np.array([0]*len(ciqF_time))

    for ii in range(0,len(data)):
        dateEv = datetime.datetime.strptime(data[ii]['date']+' '+data[ii]['time'],'%m/%d/%Y %H:%M:%S')
        dateEv = dateEv.replace(tzinfo=datetime.timezone.utc).timestamp()-utcOffset
        if data[ii]['id']==313:
            if data[ii]['dataFields']['usermode']==2:
                flagEX = True
                ciqEX_tini.append(dateEv)
            
        if (data[ii]['id']==229) and (flagEX):
            flagEX = False
            ciqEX_tend.append(dateEv)
        elif data[ii]['id']==229:
            if data[ii]['dataFields']['CurrentUserMode']==2:
                flagEX = True
                ciqEX_tini.append(dateEv)
    
    if len(ciqEX_tini)>len(ciqEX_tend):
        ciqEX_tend.append(ciqF_time[-1])

    for ii in range(0,len(ciqEX_tini)):
        nIndList = np.argwhere((ciqF_time>=ciqEX_tini[ii]) & (ciqF_time<=ciqEX_tend[ii])) 
        if nIndList.size!=0:
            ciqEX[nIndList] = 1
    
    return ciqEX
