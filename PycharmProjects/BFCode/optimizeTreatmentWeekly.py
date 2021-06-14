"""
Created on Thu Mar 12 11:50:05 2020
@title: Basal rate optimizer
@author: cf9qe
"""

import numpy as np
import copy

#########################################################################################################################

def recommendBasalRate(subjData):    
    # algorithm parameters
    buffHead = 6*60 #mins
    buffTail = 2*60 #mins
    basRes = 0.01
    maxBasDev = 0.1
    nBrPoints = 6
    
    # determine final optimal BR profile
    allOptBas = np.array(subjData['dailyRecBasal'])
    nOptBasDays = allOptBas.shape[1]
    if (nOptBasDays>0):
        origBas = subjData['lastBasalPrf']
        optBasFinal = np.median(allOptBas[:,int(buffHead/5):int((buffHead+24*60)/5)],axis=0)

        optBasFinal.shape = (len(optBasFinal),1)
        origBas.shape = (len(origBas),1)
        (recBasalProfileTime,recBasalProfileValue) = levelBasalRate(origBas,optBasFinal,basRes,maxBasDev,nBrPoints)
    else:
        brProfiles = subjData['profiles']['brProfiles']
        if brProfiles[0][0]<=1440:
            brPrf = []
            brPrf.append([1111111,brProfiles])
            brProfiles = copy.deepcopy(brPrf)
        brProfile = brProfiles[len(brProfiles)-1][1]
        recBasalProfileTime = np.array([i[0] for i in brProfile])
        recBasalProfileValue = np.array([i[1] for i in brProfile])
        recBasalProfileTime.shape = (1,len(recBasalProfileTime))
        recBasalProfileValue.shape = (1,len(recBasalProfileValue))
        
    # return recommended BR profile
    recBasalProfile = {'recBasalProfileTime':recBasalProfileTime,'recBasalProfileValue':recBasalProfileValue}

    return recBasalProfile

#########################################################################################################################

def levelBasalRate(originalBasal,optimalBasal,basalRes,maxBasalDev,nBreakPoints):
    origBas = np.zeros((48,1))
    optimBas = np.zeros((48,1))

    for i in range(0,48):
        origBas[i,0] = np.mean(originalBasal[int(i*30/5):int((i+1)*30/5),0])
        optimBas[i,0] = np.maximum(np.minimum(np.mean(optimalBasal[int(i*30/5):int((i+1)*30/5),0]),origBas[i,0]*(1+maxBasalDev)),origBas[i,0]*(1-maxBasalDev))
    origBas = origBas*60/1000
    optimBas = optimBas*60/1000
    
    minBasal = np.min(optimBas*0.9)
    maxBasal = np.max(optimBas*1.1)
    minLevel = basalRes*np.floor(minBasal/basalRes)
    maxLevel = basalRes*np.ceil(maxBasal/basalRes)

    levels = np.arange(minLevel,maxLevel+basalRes,basalRes)
    levels.shape = (len(levels),1)
    levels = np.round(levels,2)
    
    nTimes = len(origBas)
    nLevels = len(levels)
    
    J = np.zeros((nTimes,nLevels,nBreakPoints))
    mu1 = copy.deepcopy(J)
    mu2 = copy.deepcopy(J)
    
    # compute cumulative costs for each time and basal level
    for t in range(0,nTimes):
        for b in range(0,nLevels):
            dum = 0
            for s in range(t,nTimes):
                cost = np.abs(optimBas[s,0]-levels[b,0])**2
                dum = dum+cost
            J[t,b,nBreakPoints-1] = dum
    
    # assign cumulative costs obtained by minimizing the total cost
    for used in range(nBreakPoints-2,-1,-1):
        for t in range(0,nTimes):
            for b in range(0,nLevels):
                bestDum = J[t,b,nBreakPoints-1]
                bestTime = -1
                bestLevel = -1
                for s in range(t,nTimes):
                    transitionCost = J[t,b,nBreakPoints-1]-J[s,b,nBreakPoints-1]
                    for c in range(0,nLevels):
                        dum = transitionCost+J[s,c,used+1]
                        if dum<bestDum:
                            bestDum = dum
                            bestTime = s
                            bestLevel = c
                J[t,b,used] = bestDum
                mu1[t,b,used] = bestTime
                mu2[t,b,used] = bestLevel
    
    # reconstruct profile        
    appTimes = np.zeros((nBreakPoints,1))
    appIndices = np.zeros((nBreakPoints,1))
    appLevels = np.zeros((nBreakPoints,1))
    appTimes[0,0] = 0
    appIndices[0,0] = np.argmin(J[int(appTimes[0,0]),:,0])
    appLevels[0,0] = levels[int(appIndices[0,0]),0]
    for i in range(1,nBreakPoints):
        appTimes[i,0] = mu1[int(appTimes[i-1,0]),int(appIndices[i-1,0]),i-1]
        appIndices[i,0] = mu2[int(appTimes[i-1,0]),int(appIndices[i-1,0]),i-1]
        appLevels[i,0] = levels[int(appIndices[i,0]),0]
        
    # construct the corresponding 48-element basal profile
    appProfile = np.array([])
    for i in range(0,nBreakPoints-1):
        appProfile = np.append(appProfile,appLevels[i,0]*np.ones((int(appTimes[i+1,0]-appTimes[i,0]),1)))
    appProfile = np.append(appProfile,appLevels[nBreakPoints-1,0]*np.ones((int(nTimes-appTimes[nBreakPoints-1]),1)))
    appProfile.shape = (len(appProfile),1)
    
    # compute breakpoints
    breakPoints = np.array([0,appProfile[0,0]])
    breakPoints.shape = (1,len(breakPoints))
    currentBasal = appProfile[0,0]
    for i in range(1,48):
        if appProfile[i,0]!=currentBasal:
            breakPoint = np.array([int(24*60*30*i/60/24),appProfile[i,0]])
            breakPoint.shape = (1,len(breakPoint))
            breakPoints = np.append(breakPoints,breakPoint,axis=0)
            currentBasal = appProfile[i,0]
    basalPrfTime = breakPoints[:,0]
    basalPrfValue = breakPoints[:,1]
    basalPrfTime.shape = (1,len(basalPrfTime))
    basalPrfValue.shape = (1,len(basalPrfValue))
    
    return(basalPrfTime[0],basalPrfValue[0])

#########################################################################################################################