import numpy as np
from scipy import interpolate
from scipy import signal
import datetime

###############################################################################################################
def dataProcessing(time,signal,settings):

    # Sort time and signal
    time = np.array(time)
    signal = np.array(signal)
    t0 = settings['timeStampIni']
    
    indSort = np.argsort(time)
    sortedTime_aux = time[indSort]
    if np.ndim(signal)>1:
        sortedSignal_aux = signal[:,indSort]
    else:
        sortedSignal_aux = signal[indSort]

    sortedTime = sortedTime_aux[(sortedTime_aux>=t0) & (sortedTime_aux<t0+1440*60)]
    if np.ndim(signal)>1:
        sortedSignal = sortedSignal_aux[:,(sortedTime_aux>=t0) & (sortedTime_aux<t0+1440*60)]
    else:
        sortedSignal = sortedSignal_aux[(sortedTime_aux>=t0) & (sortedTime_aux<t0+1440*60)]

    # Sync time stamps with a predefined sampling time (ts mins)
    syncTime = np.arange(t0,t0+1440*60,settings['ts']*60)
    indList = []

    if (len(signal)==16) and (np.ndim(signal)==2):
        for ii in range(0,len(syncTime)):
            if ii==len(syncTime)-1:
                nIndList = np.argwhere((sortedTime>=syncTime[ii]-settings['dTime']*60) & (sortedTime<=syncTime[ii]+2*settings['dTime']*60)) 
            else:
                nIndList = np.argwhere((sortedTime>=syncTime[ii]-settings['dTime']*60) & (sortedTime<=syncTime[ii]+settings['dTime']*60)) 
            if nIndList.size>1:
                aux1 = np.nonzero(sortedSignal[5,nIndList])
                aux2 = np.nonzero(sortedSignal[4,nIndList])
                if (len(aux1[0])>0) or (len(aux2[0])>0):
                    if len(aux2[0])>0:
                        if len(aux1[0])>0:
                            if aux2[0][0]>aux1[0][0]:
                                if nIndList[aux2[0][0]]<288:
                                    for rr in range(4,16):
                                        sortedSignal[rr,nIndList[aux2[0][0]]+1] = sortedSignal[rr,nIndList[aux2[0][0]]]
                                        sortedSignal[rr,nIndList[aux2[0][0]]] = 0
                                else:
                                    for rr in range(4,16):
                                        sortedSignal[rr,nIndList[aux1[0][0]]-1] = sortedSignal[rr,nIndList[aux1[0][0]]]
                                        sortedSignal[rr,nIndList[aux1[0][0]]] = 0
                            else:
                                if nIndList[aux1[0][0]]<288:
                                    for rr in range(4,16):
                                        sortedSignal[rr,nIndList[aux1[0][0]]+1] = sortedSignal[rr,nIndList[aux1[0][0]]]
                                        sortedSignal[rr,nIndList[aux1[0][0]]] = 0
                                else:
                                    for rr in range(4,16):
                                        sortedSignal[rr,nIndList[aux2[0][0]]-1] = sortedSignal[rr,nIndList[aux2[0][0]]]
                                        sortedSignal[rr,nIndList[aux2[0][0]]] = 0
                        else:
                            if len(aux2[0])>1:
                                if nIndList[aux2[0][1]]<288:
                                    for rr in range(4,16):
                                        sortedSignal[rr,nIndList[aux2[0][1]]+1] = sortedSignal[rr,nIndList[aux2[0][1]]]
                                        sortedSignal[rr,nIndList[aux2[0][1]]] = 0
                                else:
                                    for rr in range(4,16):
                                        sortedSignal[rr,nIndList[aux2[0][0]]-1] = sortedSignal[rr,nIndList[aux2[0][0]]]
                                        sortedSignal[rr,nIndList[aux2[0][0]]] = 0
                    else:
                        if len(aux1[0])>1:
                            if nIndList[aux1[0][1]]<288:
                                for rr in range(4,16):
                                    sortedSignal[rr,nIndList[aux1[0][1]]+1] = sortedSignal[rr,nIndList[aux1[0][1]]]
                                    sortedSignal[rr,nIndList[aux1[0][1]]] = 0
                            else:
                                for rr in range(4,16):
                                    sortedSignal[rr,nIndList[aux1[0][0]]-1] = sortedSignal[rr,nIndList[aux1[0][0]]]
                                    sortedSignal[rr,nIndList[aux1[0][0]]] = 0
                                
    # Drop duplicate samples
    for ii in range(0,len(syncTime)):
        if ii==len(syncTime)-1:
            nIndList = np.argwhere((sortedTime>=syncTime[ii]-settings['dTime']*60) & (sortedTime<=syncTime[ii]+2*settings['dTime']*60)) 
        else:
            nIndList = np.argwhere((sortedTime>=syncTime[ii]-settings['dTime']*60) & (sortedTime<=syncTime[ii]+settings['dTime']*60)) 
        if nIndList.size!=0:
            indMDiff = np.argmin(np.abs(syncTime[ii]-sortedTime[nIndList]))
            try:
                if (len(signal)==16) and (np.ndim(signal)==2):
                    aux1 = np.nonzero(sortedSignal[5,nIndList])
                    if len(aux1[0]>0):
                        indMDiff=aux1[0][0]
                    else:
                        aux2 = np.nonzero(sortedSignal[4,nIndList])
                        if len(aux2[0]>0):
                            indMDiff=aux2[0][0]
            except:
                aux3 = 1
            nInd = nIndList[indMDiff]
        else:
            nInd = nIndList
        indList.extend(nInd)
    
    timeD = sortedTime[indList]
    if np.ndim(signal)>1:
        signalP = sortedSignal[:,indList]
        if len(signal)==16:
            if sortedTime[-1]>syncTime[-1]+settings['dTime']*60:
                if (signalP[4,-1]==0.0) and (signalP[5,-1]==0.0):
                    if (sortedSignal[4,-1]>0) or (sortedSignal[5,-1]>0):
                        for cc in range(4,16):
                            signalP[cc,-1]=sortedSignal[cc,-1]

    else:
        signalP = sortedSignal[indList]        

    # Sync timestamps
    timeP = np.zeros(timeD.shape)

    for ii in range(0,len(timeD)):
        if timeD[ii]%(60*settings['ts'])<60*settings['ts']/2:
            timeP[ii] = timeD[ii]-timeD[ii]%(60*settings['ts'])
        else:
            timeP[ii] = timeD[ii]+60*settings['ts']-timeD[ii]%(60*settings['ts'])

    # Detect gaps
    try:
        diffTime_i = np.array([timeP[0]-syncTime[0]])
    except:
        diffTime_i = []
    diffTime_m = np.diff(timeP)
    try:
        diffTime_e = np.array([syncTime[-1]-timeP[-1]])
    except:
        diffTime_e = []
    diffTime = diffTime_i
    diffTime = np.append(diffTime,diffTime_m)
    diffTime = np.append(diffTime,diffTime_e)

    if len(diffTime_e)>0:
        if diffTime_e[-1]<0:
            if diffTime_m[-1]>60*settings['ts']:
                timeP[-1] = timeP[-1]-60*settings['ts']
            else:
                if np.ndim(signalP)>1:
                    signalP = np.delete(signalP,-1,1)
                else:
                    signalP = np.delete(signalP,-1)
                timeP = np.delete(timeP,-1)

    ngaps = np.sum(diffTime>60*settings['ts'])
    gaps = np.zeros((2,ngaps))
    gaps[0,:] = np.transpose(np.argwhere((diffTime>60*settings['ts'])))[0]
    gaps[1,:] = diffTime[diffTime>60*settings['ts']]

    return timeP, signalP, gaps

###############################################################################################################
def mealProcessing(time,signal,settings):

    t0 = settings['timeStampIni']

    # Sort time and signal
    time = np.array(time)
    signal = np.array(signal)

    indSort = np.argsort(time)
    sortedTime_aux = time[indSort]
    if np.ndim(signal)>1:
        sortedSignal_aux = signal[:,indSort]
    else:
        sortedSignal_aux = signal[indSort]

    sortedTime = sortedTime_aux[(sortedTime_aux>=t0) & (sortedTime_aux<t0+1440*60)]
    if np.ndim(signal)>1:
        sortedSignal = sortedSignal_aux[:,(sortedTime_aux>=t0) & (sortedTime_aux<t0+1440*60)]
    else:
        sortedSignal = sortedSignal_aux[(sortedTime_aux>=t0) & (sortedTime_aux<t0+1440*60)]
    
    # Drop duplicate samples
    indD = np.argwhere(np.diff(sortedTime)<60*settings['ts'])
    
    timeD = sortedTime
    np.delete(timeD,indD+1)
    signalP = sortedSignal
    np.delete(signalP,indD+1)

    # Sync timestamps
    timeP = np.zeros(timeD.shape)

    for ii in range(0,len(timeD)):
        if timeD[ii]%(60*settings['ts'])<60*settings['ts']/2:
            timeP[ii] = timeD[ii]-timeD[ii]%(60*settings['ts'])
        else:
            timeP[ii] = timeD[ii]+60*settings['ts']-timeD[ii]%(60*settings['ts'])

    return timeP, signalP

###############################################################################################################
def fillSpSG(timeP,signalP,settings):   

    t0 = settings['timeStampIni']
    timeF = np.arange(t0,t0+1440*60,settings['ts']*60)
    s = interpolate.PchipInterpolator(timeP,signalP)
    iSignal = s(timeF)

    signalF = signal.savgol_filter(iSignal, 13, 3)
    signalF[signalF<settings['minV']] = settings['minV']
    signalF[signalF>settings['maxV']] = settings['maxV']

    return timeF, signalF 

###############################################################################################################
def fillLinCal(timeP,signalP,calP,settings):   

    t0 = settings['timeStampIni']
    
    if len(timeP)>0:
        if len(timeP)==1:
            timeP   = np.append(t0,timeP)
            signalP = np.append(signalP,signalP)
        timeF = np.arange(t0,t0+1440*60,settings['ts']*60)
        calGlucose = np.interp(timeF,timeP,signalP)
    else:
        timeF = np.array([])
        calGlucose = np.array([])
    
    uSignal = np.copy(calGlucose)
    indCalV = np.argwhere(calP)
    BackW = 48
    ForW = 6
    alpha = 1
    X = np.ones((4,2))
    X[:,1] = np.arange(0,20,5)
    
    for ll in range(0,len(indCalV)):
        indCal = indCalV[ll][0]
        if indCal<287:
            calVal = calGlucose[indCal+1]
            lastVal = calGlucose[indCal]
            if indCal>=3:
                Y = calGlucose[indCal-3:indCal+1]
                Mstar = np.matmul(np.matmul(np.matmul(np.array([0,1]),np.linalg.inv(np.matmul(np.transpose(X),X))),np.transpose(X)),Y)
            else:
                Mstar = 0.0

            Gammastar = calVal - (lastVal+5*Mstar)
            Deltastar = alpha*Gammastar

            if ll>0:
                indMax1 = min(indCal-indCalV[ll-1][0],min(indCal,BackW))
            else:
                indMax1 = min(indCal,BackW)
            
            for k in range(1,indMax1+1):
                calGlucose[indCal-k+1] = calGlucose[indCal-k+1]+Deltastar/(1+np.exp((k-BackW/2)/(BackW/20)))
            
            # if (ll>0) and (ll<=len(indCalV)-2):
            #     indMin1 = min(indCalV[ll+1][0]-indCal,min(287-indCal,ForW))
            # else:
            #     indMin1 = min(287-indCal,ForW)
            
            # for k in range(1,indMin1+1):
            #     Gammatau = calVal+5*Mstar-calGlucose[indCal+k+1]
            #     Deltatau = alpha*Gammatau
            #     calGlucose[indCal+k+1] = calGlucose[indCal+k+1]+Deltatau/(1+np.exp((k-ForW/2)/(ForW/20)))

    signalF = calGlucose
    signalF[signalF<settings['minV']] = settings['minV']
    signalF[signalF>settings['maxV']] = settings['maxV']

    return timeF, uSignal, signalF 

###############################################################################################################
def fillPrev(timeP,signalP,settings):   

    t0 = settings['timeStampIni']
    if len(timeP)>0:
        if len(timeP)==1:
            timeP   = np.append(t0,timeP)
            signalP = np.append(signalP,signalP)

        timeF = np.arange(t0,t0+1440*60,settings['ts']*60)
        s = interpolate.interp1d(timeP,signalP,'next',fill_value="extrapolate")
        signalF = s(timeF)
    else:
        timeF = np.array([])
        signalF = np.array([])

    return timeF, signalF 

###############################################################################################################
def fillBP(timeP,signalP,settings):   

    t0 = settings['timeStampIni']
    if len(timeP)>0:
        timeF = np.arange(t0,t0+1440*60,settings['ts']*60)

        bi = []
        bv = []
        if len(timeP)>1:
            for ii in range(0,len(signalP)-1):
                if signalP[ii]!=signalP[ii+1]:
                    bi.append(ii+1)
                    bv.append(signalP[ii+1])
        signalF = signalP[0]*np.ones(timeF.shape)
        
        if len(bi)>0:
            bt = timeP[bi]
            indIni = np.max(np.where(timeF-bt[0]<0))
            signalF[0:indIni] = signalP[0]
            signalF[indIni:] = bv[0]
            if len(bt)>1:
                for jj in range(1,len(bt)):
                    indAux = np.max(np.where(timeF-bt[jj]<0))
                    signalF[indAux:] = bv[jj]
    else:
        timeF = np.array([])
        signalF = np.array([])

    return timeF, signalF 

###############################################################################################################
def fillZero(timeP,signalP,settings):   

    t0 = settings['timeStampIni']

    if len(timeP)>0:
        timeF = np.arange(t0,t0+1440*60,settings['ts']*60)
        signalF = np.zeros(timeF.shape)

        indList = []
        for ii in range(0,len(timeP)):
            ind = np.argwhere(timeF==timeP[ii])
            if ind.size!=0:
                indList.extend(ind[0])
        
        signalF[indList] = signalP
    else:
        timeF = np.array([])
        signalF = np.array([])
    
    return timeF, signalF 

###############################################################################################################
def dataClassifier(cgmGaps,insGaps,mealF_carbs,bpF_values,cfF_values,crF_values,apSel,count_ins_mode,APS_mode):

    flagProfile = 0
    flagInsMode = 0

    cgmGaps = np.array(cgmGaps)
    insGaps = np.array(insGaps)
    
    if (len(bpF_values)==0) or (len(cfF_values)==0) or (len(crF_values)==0):
        flagProfile = 1

    if apSel!=APS_mode:
        flagInsMode = 1
    elif count_ins_mode<245:
        flagInsMode = 1

    # dataStatus = 0 -> Non-playable data
    # dataStatus = 1 -> Playable data

    flagCgm = flagGapDetector(cgmGaps)
    flagIns = flagGapDetector(insGaps)

    if flagCgm | flagIns | flagProfile | flagInsMode:
        dataStatus = 0
    else:
        dataStatus = 1
    
    return dataStatus

###############################################################################################################
def flagGapDetector(gapVector):

    flagGap = 0

    indGaps = gapVector[0,:]
    gaps = gapVector[1,:]

    indGaps_night = np.argwhere(indGaps<12*6)
    gaps_night = gaps[indGaps_night]

    indGaps_day = np.argwhere(indGaps>=12*6)
    gaps_day = gaps[indGaps_day]

    flagNight = 0
    flagDay = 0

    if len(gaps_night)>0:
        flagNight = max(gaps_night)>=3*60*60
    
    if len(gaps_day)>0:
        flagDay = max(gaps_day)>=2*60*60
    
    if flagNight | flagDay:
        flagGap = 1
    
    return flagGap

###############################################################################################################
def compute3PBackDiffROC_Python(signal):

    roc = []
    
    if len(signal)>3:
        for ii in range(2,len(signal)):
            roc.append((3*signal[ii]-4*signal[ii-1]+signal[ii-2])/2/5)
        roc.insert(0,0)
        roc.insert(0,0)
    return roc

###############################################################################################################
def mealDetection(iMealsD_size,iMrBolusD_time,cgmD,settings):

    popMealSize = settings['popMealSize']
    popTreatSize = settings['popTreatSize']
    mealPeakThr = settings['mealPeak']
    treatPeakThr = settings['treatPeak']
    gDevThr = settings['gDevThr']
    gTreatThr = settings['gTreatThr']
    peakProm = settings['peakProm']
    peakMinDist = settings['peakMDist']
    ts = 5
    # 

    timeD = np.arange(0,1440,ts)

    # SG filter
    order = 3
    framelen = 13
    
    g_sg = signal.savgol_filter(cgmD,framelen,order,deriv=0,delta=5,mode='nearest')
    d_sg = signal.savgol_filter(cgmD,framelen,order,deriv=1,delta=5,mode='nearest')
    f_sg = signal.savgol_filter(cgmD,framelen,order,deriv=2,delta=5,mode='nearest')

    posD_sg = np.multiply(d_sg,d_sg>=0)
    posF_sg = np.multiply(f_sg,f_sg>=0)

    combDF_sg = np.multiply(posD_sg,posF_sg)

    mealLocs_all,properties = signal.find_peaks(combDF_sg,height=mealPeakThr,prominence=peakProm,distance=peakMinDist)

    mealPks_all = properties['peak_heights']

    if combDF_sg[0]>mealPeakThr:
        if len(mealLocs_all)>0:
            if mealLocs_all[0]>12:
                mealLocs_all = np.insert(mealLocs_all,0,0)
                mealPks_all = np.insert(mealPks_all,0,combDF_sg[0])
        else:
            mealLocs_all = np.insert(mealLocs_all,0,0)
            mealPks_all = np.insert(mealPks_all,0,combDF_sg[0])

    mealDet_time = []
    mealDet_size = []

    # Informed meals
    timeMRPeak = np.copy(iMrBolusD_time)
    timeMRBase = np.copy(iMrBolusD_time)
    mrTimeLocs = (np.divide(iMrBolusD_time,5)).astype(int)
    mrLocs = mrTimeLocs

    for vv in range(0,len(timeMRPeak)):
        indPeak = np.argmax(combDF_sg[max(mrTimeLocs[vv]-18,0):min(len(combDF_sg),mrTimeLocs[vv]+13)])
        mrLocs[vv] = max(mrLocs[vv]+indPeak-18,0)
        timeMRPeak[vv] = max(timeMRPeak[vv]+5*indPeak-90,0)
        try:
            indBase = np.min(np.where(np.diff(combDF_sg[max(mrLocs[vv]-6,0):mrLocs[vv]+1])>0))
        except:
            indBase = np.empty(shape=(0,0))
        if indBase.size>0:
            timeMRBase[vv] = max(timeMRPeak[vv] +5*indBase-30,0)
        else:
            timeMRBase[vv] = timeMRPeak[vv]
        mealDet_time.append(timeMRBase[vv])
        mealDet_size.append(iMealsD_size[vv])
    
    # Detected meals
    timePeaks = np.copy(timeD[mealLocs_all])
    timeBase  = np.copy(timePeaks)
    mealBaseLocs_all = np.copy(mealLocs_all)

    treatDet_time = []
    treatDet_size = []

    for vv in range(0,len(mealPks_all)):
        try:
            indBaseP = np.min(np.where(np.diff(combDF_sg[max(mealLocs_all[vv]-6,0):mealLocs_all[vv]+1])>0))
        except:
            indBaseP = 6
        timeBase[vv] = max(timeBase[vv] + 5*indBaseP-30,0)
        mealBaseLocs_all[vv] = max(mealLocs_all[vv]+indBaseP-6,0)
        gDev = cgmD[min(mealBaseLocs_all[vv]+12,len(cgmD)-1)]-cgmD[mealBaseLocs_all[vv]]
        gDev1 = cgmD[min(mealBaseLocs_all[vv]+9,len(cgmD)-1)]-cgmD[mealBaseLocs_all[vv]]
        if (cgmD[mealBaseLocs_all[vv]]<=gTreatThr) & (mealPks_all[vv]>=treatPeakThr):
            treatDet_time.append(timeBase[vv])
            treatDet_size.append(min(max(round(gDev1/25.0)*popTreatSize,popTreatSize),20))
        elif gDev>=gDevThr:
            mealDet_time.append(timeBase[vv])
            mealDet_size.append(popMealSize)

    iMealDet_time = mealDet_time[0:len(iMrBolusD_time)]
    iMealDet_size = mealDet_size[0:len(iMrBolusD_time)]
    dMealDet_time = mealDet_time[len(iMrBolusD_time):len(mealDet_time)]
    dMealDet_size = mealDet_size[len(iMrBolusD_time):len(mealDet_size)]
    
    dMealDet_time_aux = []
    dMealDet_size_aux = []

    for vv in range(0,len(dMealDet_time)):
        pRep = np.array(np.where((iMealDet_time>=dMealDet_time[vv]-45) & (iMealDet_time<=dMealDet_time[vv]+45)))
        if pRep.size==0:
            dMealDet_time_aux.append(dMealDet_time[vv])
            dMealDet_size_aux.append(dMealDet_size[vv])
        if pRep.size>0:
            if iMealDet_size[pRep[0][0]] < 2:
                iMealDet_size[pRep[0][0]] = dMealDet_size[vv]

    mealDet_time = [*iMealDet_time, *dMealDet_time_aux]
    mealDet_size = [*iMealDet_size, *dMealDet_size_aux]

    indSort = np.argsort(mealDet_time,axis=0)
    mealDet_time = np.sort(mealDet_time)
    mealDet_size = np.take_along_axis(np.array(mealDet_size),indSort,axis=0)

    indIMeal = np.arange(0,len(iMealDet_time))

    diffMealDet = np.diff(mealDet_time)
    repMeals = np.where(diffMealDet<45)[0]

    ww = 0
    for vv in range(0,repMeals.size):
        if np.where(indIMeal==indSort[repMeals[vv]+1])[0].size == 0:
            mealDet_time = np.delete(mealDet_time,repMeals[vv]+1-ww)
            mealDet_size = np.delete(mealDet_size,repMeals[vv]+1-ww)
            ww = ww+1
    
    diffMealDet = np.diff(mealDet_time)
    sameTime = np.where(diffMealDet<15)[0]
    mealDet_time = np.delete(mealDet_time,sameTime+1)

    for vv in reversed(range(0,sameTime.size)):
        mealDet_size[sameTime[vv]] = mealDet_size[sameTime[vv]]+mealDet_size[sameTime[vv]+1]
    
    mealDet_size = np.delete(mealDet_size,sameTime+1)

    diffTreatDet = np.diff(treatDet_time)
    repTreats = np.where(diffTreatDet<15)
    treatDet_time = np.delete(treatDet_time,repTreats)
    treatDet_size = np.delete(treatDet_size,repTreats)

    treatDet_ind_aux = []

    for vv in range(0,len(treatDet_time)):
        pRep = np.array(np.where((mealDet_time>=treatDet_time[vv]-5) & (mealDet_time<=treatDet_time[vv]+5)))
        if pRep.size>0:
            treatDet_ind_aux.append(vv)
    
    treatDet_time = np.delete(treatDet_time,treatDet_ind_aux)
    treatDet_size = np.delete(treatDet_size,treatDet_ind_aux)

    negMTime = np.where(mealDet_time<0)
    
    for ii in range(0,len(negMTime[0])):
        mealDet_time[negMTime[0][ii]] = 0

    negTTime = np.where(treatDet_time<0)

    for ii in range(0,len(negTTime[0])):
        treatDet_time[negTTime[0][ii]] = 0

    rMeals = np.array(mealDet_time)
    rMeals = np.vstack([rMeals,mealDet_size])

    rTreats = np.array(treatDet_time)
    rTreats = np.vstack([rTreats,treatDet_size])
    
    return rMeals, rTreats

############################################################################################################################
def compute_perMealSize(prev_meals,BW):

    prev_meals_size = []
    for prev_meal in prev_meals.all():
        rFlag = getattr(prev_meal,'is_rescue')
        if rFlag==0:
            prev_meals_size.append(float(getattr(prev_meal,'carbs'))/1000.0)

    if len(prev_meals_size)>0:
        perMealSize = sum(prev_meals_size)/len(prev_meals_size) 
    else:
        perMealSize = 0.7*BW
    
    return perMealSize

############################################################################################################################
def determine_insMode(insF_mode):
    
    pIns_modes_count = [0]*4

    uniqueValues,occurCount = np.unique(insF_mode.astype(int),return_counts=True)

    for ii in range(0,uniqueValues.size):
        if uniqueValues[ii]==-1:
            pIns_modes_count[0] = occurCount[ii]
        elif uniqueValues[ii]==0:
            pIns_modes_count[1] = occurCount[ii]
        elif uniqueValues[ii]==1:
            pIns_modes_count[2] = occurCount[ii]
        elif uniqueValues[ii]==2:
            pIns_modes_count[3] = occurCount[ii]

    apSel = np.argmax(pIns_modes_count)-1
    count_ins_mod = pIns_modes_count[apSel+1]

    return apSel,count_ins_mod

############################################################################################################################
def generate_mealSignal_DB(rMeals,rTreats,timeStampIni,tOffSet):

    mealTime = []
    mealUtcOffset = []
    mealSize = []
    mealRFlag = []
    
    if len(rMeals[0])>0:
        for ii in range(0,len(rMeals[0])):
            mealTime.append(timeStampIni+60*int(rMeals[0,ii]))
            mealSize.append(1000*rMeals[1,ii])
            mealUtcOffset.append(tOffSet)
            mealRFlag.append(0)

    if len(rTreats[0])>0:
        for ii in range(0,len(rTreats[0])):
            mealTime.append(timeStampIni+60*int(rTreats[0,ii]))
            mealSize.append(1000*rTreats[1,ii])
            mealUtcOffset.append(tOffSet)
            mealRFlag.append(1)

    indSort = np.argsort(mealTime,axis=0)
    mealTime = np.sort(mealTime)
    mealSize = np.take_along_axis(np.array(mealSize),indSort,axis=0)
    mealUtcOffset = np.take_along_axis(np.array(mealUtcOffset),indSort,axis=0)
    mealRFlag = np.take_along_axis(np.array(mealRFlag),indSort,axis=0)

    return mealTime,mealUtcOffset,mealSize,mealRFlag

############################################################################################################################
def adjExtDose4Matlab(insBolus_comb,bolusData):

    cBolus = np.array(bolusData[1])
    mBolus = np.array(bolusData[2])
    tBolus = cBolus+mBolus

    insBolus_matlab = np.zeros(len(insBolus_comb))

    jj = 0
    for ii in range(0, len(insBolus_comb)):
        if insBolus_comb[ii]>0.0:
            while (bolusData[12][jj]==0.0) and (jj<len(bolusData[12])) and (bolusData[9][jj]!=1):
                jj=jj+1
            if bolusData[9][jj]==1:
                indExtBTimer = int(np.fix(bolusData[11][jj]/5))
                rDose = (tBolus[jj]-bolusData[12][jj])/indExtBTimer
                insBolus_matlab[ii] = insBolus_matlab[ii]+bolusData[12][jj]  
                insBolus_matlab[min(ii+1,288):min(ii+indExtBTimer+1,288)] = rDose
            else:
                insBolus_matlab[ii] = insBolus_matlab[ii]+bolusData[12][jj] 
            jj+=1

    return insBolus_matlab

############################################################################################################################
def prepare_dataReplay_case1(timeStampIni,input_array):

    output_list = [timeStampIni]
    output_list.extend(input_array)
    output_list = [output_list]

    return output_list

############################################################################################################################
def prepare_dataReplay_case2(timeStampIni,utcOffset,input_array):

    output_list_aux = []
    output_list_aux.append(datetime.datetime.fromtimestamp(timeStampIni+utcOffset,tz=datetime.timezone.utc).strftime('%d %b %Y'))
    output_list_aux.append(input_array.tolist())
    output_list = [output_list_aux]

    return output_list