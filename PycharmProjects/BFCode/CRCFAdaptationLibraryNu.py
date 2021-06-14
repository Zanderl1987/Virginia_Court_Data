# -*- coding: utf-8 -*-
"""
Created on Wed Sep 30 13:20:20 2020

New CRCF Adaptation Library

@author: jh8be
"""
import numpy as np
from scipy.linalg import block_diag as blkdiag
from numpy import matlib
import math



def struct248(prof):
    vo = np.zeros(48)
    vo[:] = prof['values'][0]
    
    if len(prof['values'])>1:
        for idx in range(len(prof['time'])):
            pos = int(np.floor(prof['time'][idx]/30))
            vo[pos:] = prof['values'][idx]
    return vo



def getParamAlgov2(TDI = 60, timeBreakpoints = np.array([4 , 11]), gamma = 1.5, thHypo = 70, subjId = -1):
    p = {"Nopt": 1000,
        "fitTarget" : 120,
        "theTgt": 100,
        "ppStart" : 2, # in min 60 in matlab code
        "ppEnd" : 6 , # in min #diff in matlab code
        "paramDRes" : 5, # in %
        "dres": 5,
        "paramRes" : 1, #.1, # in absolute #Thibault 03/30/2020
        "paramSat" : .1, # in ratio
        "paramsat" : .1,
        'sat'      : 0.1,
        "breakPoints": 4,
        'res' : .1,
        'nbreakPoints' : 6,
        "TDI" : TDI,
        "gamma" : gamma,
        "thHypo" : thHypo,
        "timeBreakpoints" : range(24),
        "forgettingTau" : 14, # in days
        "mealBolusMaxDetaT" : 60, # in min
        "mealBolusMergeDelta" : 60, # in min
        "percCGMDataInPP" : 50, # in percent
        "minDatapointPerSegm" : 4, # number of dosing event required for the algo to run
        #"noisModels" : [noiseModel(subjId, 0)],
        #"adaptModels" : [adaptationModel()],
        "cf1800": 1800/TDI,
        "cr500": 500/TDI,
        'tdiLsat': .15,
        'tdiHsat': 8,
        'taucirc': 1,
        'tauforg': 3,
        'sEHighSat': 30,
        'sMHighSat': 35,
        'sBHighSat': 35,
        'sELowSat': 5,
        'sMLowSat': 5,
        'sBLowSat': 5,
        'priorW': np.ones((24,1)),
        'mE': 0*np.ones((24,1)),
        'sE': 20*np.ones((24,1)),
        'mM':  50*np.ones((24,1)),
        'sM': 30*np.ones((24,1)),
        'mB': 40*np.ones((24,1)),
        'sB': 30*np.ones((24,1)),
        'maxPriorDeviation': 60,
        'mealBolusMaxDeltaT': 60,
        'mealBolusMergeDelta': 60,
        'percCGMDataInPP': 50}
    return p

def noiseModel(subjId, idxB):
    crcfNoiseModel = {"avg_bg_init" : 40,
            "stb_bg_init" : 40,
            "avg_meal" : 40,
            "std_meal" : 40,
            "avg_err" : 0,
            "std_err" : 40,
            "segment_number" : idxB
            }

    return crcfNoiseModel

def adaptationModel():
    adaptMod = {
        "priorWeight" : 1,
        "maxPriorDeviation" : 60, # in percent
        "thetaU": float("nan"),
        "thetaY": float("nan"),
        "thetaR": float("nan"),
        "thetaOpt" : float("nan")
    }

    return adaptMod


def dataArray2meals(t, cgm, traw, cgmraw, bolus, meal, param):
    
    min2day = 1/24/60;
    tmeal = t[meal > 0];
    tdosing = t[bolus > 0];
    vmeal = meal[meal > 0];
    vdosing = bolus[bolus > 0];
    vcgm = cgm[bolus > 0];
    
   
    #temp = abs(tmeal-tdosing)
    tmeal = tmeal.reshape((len(tmeal),1,))
    tdosing = tdosing.reshape((len(tdosing),1,))
    #temp = temp.reshape((len(temp),1))
    temp = abs(tmeal - tdosing.transpose())
    #m  = np.where(temp == temp.min())[1]
    m = np.amin(temp,1)
    #po = np.where(temp == temp.min())[0]
    po = np.argmin(temp,1)
    #[m, po] = min(abs(tmeal - tdosing));
    tMsBgInsBgm = None
      
        
        
   
   
    
    
    for idx in range(0,len(tdosing)):
        J = np.where(idx == po)[0]
        J = J[m[J] < min2day*param['mealBolusMaxDeltaT']]
        tt = tdosing[idx]
        tmt = (tt - np.floor(tt))*24
        bolt = vdosing[idx]
        
        if J.size == 0:
            mt = 0;
        else:
            mt = np.sum(vmeal[J])
            
        if np.sum(traw < tt) == 0:
            tb = tt - 1;
        else:
            tb = np.max(traw[traw < tt])
            
            
        vcgmr = cgmraw[np.logical_and(traw >= (tt + param['ppStart']/24), traw <= (tt + param['ppEnd']/24))]
    
        if len(vcgmr) > np.logical_and(param['percCGMDataInPP']*(param['ppEnd'] - param['ppStart'])*60/5/100,  (tt - tb)  <  1/24):
            bgt = vcgm[idx]
            bgmt = min(vcgmr)
            if idx == 0:
                tMsBgInsBgm = np.array([[tt ,tmt , bgt, mt, bolt, bgmt, 0]])
            else:
                tMsBgInsBgm = np.append(tMsBgInsBgm,np.array([[tt ,tmt , bgt, mt, bolt, bgmt, 0]]), axis = 0)
                
            
    if tMsBgInsBgm.any():
        if (np.cumsum(np.diff(tMsBgInsBgm[:,0]) > param['mealBolusMergeDelta']*min2day)).any():
            Jmerge = np.concatenate((np.array([0]),np.cumsum(np.diff(tMsBgInsBgm[:,0]) > param['mealBolusMergeDelta']*min2day))) + 1
        else:
            Jmerge = np.array([0], ndmin = 1) + 1
    else:
        Jmerge = np.array([0], ndmin = 1) + 1
        
    Jmerge = Jmerge.transpose()
    
    idx = 1

    nd = Jmerge[-1]
    MtMsBgInsBgm = np.zeros_like((nd,7), dtype=float, shape = (nd,7))
    
    if not (tMsBgInsBgm is None):
        while sum(Jmerge==idx)> 0:
            J =  np.where(Jmerge==idx)
            J = J[0]
            temp_idx = idx == Jmerge
            temp_idx.shape = (len(temp_idx),1)
    
            temp015 = np.array([0,1,5], ndmin = 1)
    
            if tMsBgInsBgm.shape[0]>1:
                if tMsBgInsBgm[idx == Jmerge, 3:5].ndim > 1:
                    
                    tMsBgInsBgm_temp = tMsBgInsBgm[idx == Jmerge,:]
                    
                    MtMsBgInsBgm[idx-1,[0,1,5]] = np.amin(tMsBgInsBgm_temp[:, temp015], axis=0)
                    MtMsBgInsBgm[idx-1,[3,4]] = np.sum(tMsBgInsBgm_temp[:, [3,4]], axis = 0)
                else:
                    MtMsBgInsBgm[idx-1,[3,4]] = tMsBgInsBgm[idx == Jmerge, [3,4]]
                    MtMsBgInsBgm[idx-1,[0,1,5]] = tMsBgInsBgm[idx == Jmerge, temp015]
            else:
                MtMsBgInsBgm[idx-1,[0,1,5]] = tMsBgInsBgm[idx == Jmerge, [0,1,5]]
                MtMsBgInsBgm[idx-1,[3,4]] = tMsBgInsBgm[idx == Jmerge, [3,4]]
            
            tMsBgInsBgm_temp = tMsBgInsBgm[idx == Jmerge,:]
            MtMsBgInsBgm[idx-1,[2,6]] = np.sum(tMsBgInsBgm_temp[:, [2,6]], axis = 0)
            idx = idx + 1;
        
        

    
    return MtMsBgInsBgm


def  getNewFitv2(dummy, param, CR, CF, tnow, idx):
    # d = tMsBgInsBgm(:,1:end-1)
    # p = paramAdapt
    #CR = CR old (average?)
    #CF = CF old (average?)
    #tnow = t[-1]/1440
    #idx = dummy idx
    
    
    J =  dummy[:,4] > 0
    #np.delete(dummy, ~J)
    dummy = dummy[J]

    y = dummy[:,-1]-param['theTgt']
    x = dummy[:,2:-1]
    x[:,0] = x[:,0] - param['theTgt']
    t1 = abs(dummy[:,0]-tnow)
    t2 = abs(dummy[:,1] - ((idx-1)+(1/2)))
    t3 = np.add(np.multiply((t2 <= 12),t2),  np.multiply((t2 > 12),(24 - t2)))
    
    
    wwcirc = np.exp(-t3/param['taucirc'])
    wwforg = np.exp(-t1/param['tauforg'])
    
    ww = 20*np.multiply(wwcirc,wwforg)
    wd = np.divide(ww, param['theTgt']+y)
    
    #add priors
    mult = np.array([1.,1.,1.],ndmin = 1).transpose()
    J = np.ones((3,), dtype = bool)
    betaPrior = np.array([.5, CF/CR, -CF], ndmin = 1).transpose()
    
    
    count = 0
    while J.any() == True:
        mult = np.multiply(mult,1+J)
        wPrior = np.divide(mult*(1+param['priorW'][idx]),abs(betaPrior))/param['theTgt']
        xPrior = np.identity(3)
    
        yf = np.append(y, betaPrior, axis = 0)
        yf.shape = (len(yf),1)
        xf = np.append(x, xPrior, axis = 0)
        w1 = blkdiag(np.diag(wd), np.diag(wPrior))
        beta = np.linalg.lstsq(np.matmul(np.matmul(xf.transpose(),w1),xf),np.matmul(np.matmul(xf.transpose(),w1),yf), rcond = -1)
        beta = beta[0].transpose()
    
        J =  np.logical_or(np.multiply(beta,betaPrior) < 0, np.divide(abs(beta - betaPrior),abs(betaPrior)) > param['maxPriorDeviation']/100)[0]
        #if count == 29:
            #print('pause')
        count = count + 1
        
    
    bgmthat = np.matmul(xf,beta.transpose())
    bgmt = yf
    bgmthat = bgmthat[0:-3]
    bgmt = bgmt[0:-3]
    xf = xf[0:-3,:]
    
    
    param['mE'][idx] , param['sE'][idx] = compMean2( ww, bgmt - bgmthat, param['mE'][idx] , param['sE'][idx], param['priorW'][idx])
    param['sE'][idx] = max(min(param['sE'][idx], param['sEHighSat']),param['sELowSat'])
    
    param['mM'][idx] ,param['sM'][idx] = compMean( ww, xf[:,1], param['mM'][idx] ,param['sM'][idx], param['priorW'][idx])
    param['sM'][idx] = max(min(param['sM'][idx], param['sMHighSat']),param['sMLowSat'])
    

    param['mB'][idx] ,param['sB'][idx] = compMean( ww, xf[:,0], param['mB'][idx] ,param['sB'][idx], param['priorW'][idx])
    param['sB'][idx] = max(min(param['sB'][idx], param['sBHighSat']),param['sBLowSat'])
    
    
    theta0 = np.array([0], ndmin = 1)
    
    bias = theta0 + param['mE'][idx] + param['theTgt'] - param['thHypo']

    A = param['mB'][idx]**2 - np.matmul(np.array(param['gamma']**2,ndmin = 1),np.array(param['sB'][idx]**2, ndmin = 1))
    B = np.array(np.matmul(2*np.array(param['mB'][idx], ndmin = 1),np.array(param['mM'][idx], ndmin = 1)),ndmin = 1)
    C = np.array(param['mM'][idx]**2, ndmin = 1) - np.matmul(np.array(param['gamma']**2,ndmin =1), np.array(param['sM'][idx]**2, ndmin = 1))
    D = np.array(2*param['mB'][idx]*bias, ndmin = 1)
    E = np.array(2*param['mM'][idx]*bias, ndmin = 1)
    F = np.array(bias**2, ndmin = 1) - np.matmul(np.array(param['gamma']**2, ndmin = 1),np.array(param['sE'][idx]**2, ndmin = 1))
    
    
    yn = conicSectionSoving(param,A,B,C,D,E,F, nSample = 1000)
    
    #Z = [p.mB(idx), p.mM(idx)]*yn + bias < 0 | yn(1,:) - beta(1) > 0 | yn(2,:) - beta(2) > 0
    

    
    
    if yn.size == 0:
        CFnew = CF
        CRnew = CR
        muTgt = None
        sdtTgt = None
    else:
        Z = np.logical_or(np.logical_or((np.matmul(np.concatenate((param['mB'][idx], param['mM'][idx]), axis = 0),yn)+bias)<0,(yn[0,:]-beta[0][0])>0),(yn[1,:]-beta[0][1])>0)
        yn = yn[:,~Z]
    
        Sig2 = np.array([param['sB'][idx]**2, param['sM'][idx]**2], ndmin = 1)
        Sig2.shape = (1,len(Sig2))
        
        
        
        
        I = np.argmin(np.matmul(Sig2,yn**2))
    
        ThetaOpt = yn[:,I]
    
    
        CFnew = 1/((ThetaOpt[0] - beta[0][0])/beta[0][2])
        CRnew = 1/((ThetaOpt[1] - beta[0][1])/beta[0][2])
    
        tempMu = np.array([param['mB'][idx], param['mM'][idx]],ndmin = 1)
        tempMu.shape = (1,2)
        ThetaOpt.shape = (2,1)
        muTgt = np.matmul(tempMu,ThetaOpt) + bias + param['thHypo']
        muTgt = muTgt[0]
        sdtTgt = np.sqrt(np.matmul(Sig2,ThetaOpt**2) + param['sE'][idx]**2)
        sdtTgt = sdtTgt[0]
    
    return CRnew, CFnew, param, muTgt, sdtTgt


def compMean(w1,x1,mo,so, pror):
    x1.shape = w1.shape
    tw = np.sum(w1)
    t = (np.sum(np.multiply(w1,x1)) + pror*mo)/(tw+pror)
    s = (np.sqrt(tw*np.sum(np.multiply(w1,(x1- np.sum(np.multiply(w1,x1))/tw)**2))) + pror*so)/(tw+pror)

    return t, s
    
def compMean2(w1, x1, mo ,so, pror):
    tw = sum(w1)
    x1.shape = w1.shape
    m = (np.sum(np.multiply(w1,x1) + pror*mo))/(tw+pror)
    w2 = np.multiply(w1,x1 < m)
    tw2 = sum(w2)
    s1 = (np.sqrt(tw2*np.sum(np.multiply(w2,(x1- np.sum(np.multiply(w2,x1))/tw2)**2))) + pror*so)/(tw2+pror)
    return m, s1


def conicSectionSoving(param,A,B,C,D,E,F, nSample = 1000):
        
    Hr1 = np.concatenate((A,B/2,D/2),axis = 0)
    Hr2 = np.concatenate((B/2,C,E/2),axis = 0)
    Hr3 = np.concatenate((D/2,E/2,F),axis = 0)
    H = np.array([Hr1,Hr2,Hr3])
    
    H33 = H[0:2,0:2]
    
    if np.linalg.det(H)*np.linalg.det(H33) > 0:
        H = - H
        H33 = - H33

    detH = np.linalg.det(H)
    detH33 = np.linalg.det(H33)
    K = -detH/detH33
    

    thetaC = np.matmul(np.linalg.inv(H33), np.array([-D/2,-E/2]))
    
    eigV, W = np.linalg.eig(H33)
    
    for i in range(W.shape[1]):
        #print(i)
        if sum(W[:,i]<0) == W.shape[0]:
            W[:,i] = -1*W[:,i]
            

    idx = eigV.argsort()
    eigV = eigV[idx]
    W = W[:,idx]

    if detH33 < 0:
        minx = math.sqrt(K/eigV[1])
        x =  minx - .99*10**(-5) + np.logspace(-5,1,nSample)
    elif detH33 > 0:
        minx = 0
        if K/eigV[1] > 0:
            maxx = math.sqrt(K/eigV[1])
            x =   np.linspace(minx,maxx-10**(-5),nSample)
        else:
            x = [float("nan")]
    else:
        x = [float("nan")]

    if x[0] == x[0]:
        x = np.concatenate((x, -x), axis = 0)

        x.shape = (1,2*nSample)


        yt = np.sqrt((K-eigV[1]*np.square(x))/eigV[0])

        Y = np.concatenate((np.concatenate(( yt, x)),  np.concatenate((-yt, x))), axis = 1)
        r,c = np.shape(Y)

        
        yn = np.matmul(W, Y) + matlib.repmat(thetaC, 1, c)
    else: 
        yn = np.array([])
        
        
    return yn
    


def crcfoptimization(t, cgm, bol, meal, CRstructList, CFstructList, tdi, paramAdapt):
    
    CRall = []
    CFall =[]
    
    if len(CRstructList)>1:
        for i in range(len(CRstructList)):
        
            CRall.append(struct248(CRstructList[i]))
    else:
            CRall = CRstructList[0]
        
        
        
    if len(CFstructList)>1:    
        for i in range(len(CFstructList)):
        
            CFall.append(struct248(CFstructList[i]))
    else:
            CRall = CRstructList[0]
        
    
    if not bool(paramAdapt):
        paramAdapt = getParamAlgov2(tdi)
        
    tRaw = t
    cgmRaw = cgm
    
    #tMsBgInsBgm = dataArray2meals(t/1440, cgm, tRaw/1440, cgmRaw, bol, meal, paramAdapt)
    tMsBgInsBgm = dataArray2meals(t/86400, cgm, tRaw/86400, cgmRaw, bol, meal, paramAdapt)
    tnow = t[-1]/86400
    CRopt = np.copy(CRall[-1])
    CFopt = np.copy(CFall[-1])
    
    for idx in range(24):
        CR = np.zeros((len(CRall),48))
        for i in range(len(CRall)):
            CR[i,:] = CRall[i]
    
    for idx in range(24):
        CF = np.zeros((len(CFall),48))
        for i in range(len(CFall)):
            CF[i,:] = CFall[i]
            
        
        CRold = np.mean(CR[:,2*idx:2*idx+1])
        CFold = np.mean(CF[:,2*idx:2*idx+1])
        
        CRnew, CFnew, paramAdapt, muTgt, sdtTgt = getNewFitv2(tMsBgInsBgm[:,0:-1], paramAdapt, CRold, CFold, tnow, idx)
    
    
        diffCR = max(min(np.divide((CRnew - CRold),CRold), paramAdapt['sat']), -paramAdapt['sat'])
        diffCF = max(min(np.divide((CFnew - CFold),CFold), paramAdapt['sat']), -paramAdapt['sat'])
        CRn = (1+diffCR)*CRold
        CFn = (1+diffCF)*CFold
        CRnew = max(min(CRn, paramAdapt['cr500']*paramAdapt['tdiHsat']), paramAdapt['cr500']*paramAdapt['tdiLsat'])
        CFnew = max(min(CFn, paramAdapt['cf1800']*paramAdapt['tdiHsat']), paramAdapt['cf1800']*paramAdapt['tdiLsat'])
    
        CRopt[2*idx:2*idx+2] = CRnew
        CFopt[2*idx:2*idx+2] = CFnew
    
    CRoptStruct = structFrom48(CRopt)
    CFoptStruct = structFrom48(CFopt)
    
    CRoptStruct['values'] = np.round(CRoptStruct['values']) 
    CFoptStruct['values'] = np.round(CFoptStruct['values']) 
    
    return CRoptStruct,CFoptStruct, paramAdapt

def structFrom48(v):
    pos = np.where(~(np.diff(v) == 0))[0]
    
    if pos.size>0:
        posmin = (pos+1)*30;
    
        vo = dict()

        vo['time'] = np.concatenate((np.zeros(1),posmin))
        vo['values'] = vo['time']
        v_init = np.array([v[pos[0]]])
        vo['values'] = np.concatenate((v_init, v[pos+1]))
    else:
        vo = dict()
        vo['time'] = np.array([0])
        vo['values'] = np.array([v[0]])
    
    return(vo)



def data_preprocessfromABC(crData,cfData):
    
    CRstructList = []
    CFstructList = [] 
    
    for i in range(len(crData)):
        values_temp = np.zeros((len(crData[i][1]),1))
        times_temp  = np.zeros((len(crData[i][1]),1))
        
        for t in range(len(crData[i][1])):
            values_temp[t] = crData[i][1][t][1]
            times_temp[t]  = crData[i][1][t][0]
        
        
        
        
        CRstruct = {'values': values_temp, 'time': times_temp}
        
        CRstructList.append(CRstruct)
        
        
    for i in range(len(cfData)):
        values_temp = np.zeros((len(cfData[i][1]),1))
        times_temp  = np.zeros((len(cfData[i][1]),1))
        
        for t in range(len(cfData[i][1])):
            values_temp[t] = cfData[i][1][t][1]
            times_temp[t]  = cfData[i][1][t][0]
        
        
        
        
        CFstruct = {'values': values_temp, 'time': times_temp}
        
        CFstructList.append(CFstruct)
    
    
    
    return CRstructList, CFstructList