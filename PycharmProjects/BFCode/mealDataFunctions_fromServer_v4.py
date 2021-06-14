# -*- coding: utf-8 -*-
"""
Created on Thu Jan 30 11:01:45 2020

@author: jpc5s
Functions used to process meal data

"""
import numpy as np
import datetime as dt
import math
import scipy as sp
from scipy.linalg import toeplitz
from scipy.linalg import tril

#########################################################################################################################

def getData(data):

    timeString = np.asarray([i[0] for i in data['cgm']])
    dateVec= np.empty((len(timeString)))
    datetimeVec= np.empty((len(timeString)),dtype='datetime64[s]')

    for t in range(len(timeString)):
#        dateTimeArray = dt.datetime.fromtimestamp(timeString[t])
        dateTimeArray = dt.datetime.utcfromtimestamp(timeString[t])

        mdn = dateTimeArray+dt.timedelta(days=366)
        frac = (dateTimeArray - dt.datetime(dateTimeArray.year,dateTimeArray.month,dateTimeArray.day,0,0,0)).seconds/(24.0*60.0*60)
        dateVec[t] = mdn.toordinal()+frac
        datetimeVec[t] = roundTime(dt.datetime.fromordinal(int(dateVec[t])) + dt.timedelta(days=dateVec[t]%1) - dt.timedelta(days = 366),roundTo=60)

    cgmVec = np.asarray([i[1] for i in data['cgm']], dtype = np.float)
    basalVec = np.asarray([i[1] for i in data['basal']], dtype = np.float)
    insulinVec = np.asarray([i[1] for i in data['insulin']], dtype = np.float)
    mealVec = np.asarray([i[1] for i in data['meal']], dtype = np.float)
    
    basalVec[np.where(np.isnan(basalVec))] = 0
    insulinVec[np.where(np.isnan(insulinVec))] = 0
    mealVec[np.where(np.isnan(mealVec))] = 0
    bolusVec = insulinVec-basalVec

    BW = data['subjInfo']['Weight']
    TDI = data['subjInfo']['TDI']
    
    return dateVec, datetimeVec, cgmVec, basalVec, bolusVec, mealVec, BW, TDI

#########################################################################################################################

def roundTime(dateTime=None, roundTo=60):
   """Round a datetime object to any time lapse in seconds
   dt : datetime.datetime object, default now.
   roundTo : Closest number of seconds to round to, default 1 minute.
   Author: Thierry Husson 2012 - Use it as you want but don't blame me.
   """
   if dateTime == None : dateTime = dt.datetime.now()
   seconds = (dateTime.replace(tzinfo=None) - dateTime.min).seconds
   rounding = (seconds+roundTo/2) // roundTo * roundTo
   return dateTime + dt.timedelta(0,rounding-seconds,-dateTime.microsecond)

#########################################################################################################################

def getFeaturesV2(dateVec, datetimeVec, cgmVec, bolusVec, mealVec, BW, TDI):
    
    TBI = TDI/2
    InsOp = 0
    Gop  = np.average(cgmVec)
    nMeals = 1
    regCiNE = 1e4
    X0 = np.zeros((5+2*nMeals,1))
    (SG,Gb,p2,SI,f,Vg,Vi,kq1,kq2,kq12,ki1,ki2,ki12,kicl,Gop,InsOp) = getParam(nMeals,BW)
    Gop = cgmVec[0]
    InsOp = bolusVec[0]
    (x0, SI) = firstEstimates(Vi,SG,BW,TDI,TBI,InsOp,Gop,X0,kicl,ki12,ki2,ki1)
    regIni = 1./(x0+1e-4)
    tStep = 1

    pPrior = {   "p2": p2,
            "BW": BW,
            "SI": SI,
             "f": f,
            "Vg": Vg,
            "Vi": Vi,
           "kq1": kq1,
           "kq2": kq2,
          "kq12": kq12,
           "ki1": ki1,
           "ki2": ki2,
          "ki12": ki12,
          "kicl": kicl,
          "Gop": Gop,
          "InsOp": InsOp,
          "SG": SG,
          "Gb": Gb}
    uList = [dateVec, bolusVec, np.zeros((np.shape(mealVec)))]
    u = np.asarray(np.transpose(uList))
    fitList = [dateVec, cgmVec]
    fit = np.asarray(np.transpose(fitList))

    (x01, omega) = computeNetEffect(pPrior, u, fit, tStep, regIni, regCiNE)
    omega = omega[:,0]
    
    # Get derivative values for cgm and NE
    (firstD, secondD, firstD_positive, secondD_positive, crossD_positive) = deltaValues(dateVec, cgmVec);
    (firstD_NE, secondD_NE, firstD_positive_NE, secondD_positive_NE, crossD_positive_NE) = deltaValues(dateVec, omega);

    # Get mean/max over a window of 1 hr
    timeForward = 30
    timeBackward = 30
    featureData = np.column_stack((firstD,secondD,firstD_positive,secondD_positive,crossD_positive,bolusVec,cgmVec,firstD_NE,secondD_NE,firstD_positive_NE,secondD_positive_NE,crossD_positive_NE,omega))
    (meanForwardFeatures, maxForwardFeatures) = getMeanMax(featureData, dateVec, datetimeVec, timeBackward, timeForward)

    features = np.column_stack((featureData,meanForwardFeatures,maxForwardFeatures))
    
    return features[:,[1,4,5,7,13,14,16,18,24,25,31,32]]

#########################################################################################################################

def firstEstimates(Vi,SG,BW,TDI,TBI,InsOp,Gop,X0,kicl,ki12,ki2,ki1):

    SI = math.exp(-6.4417 - 0.063546*TDI + 0.057944*TBI)
    x0 = (SG*Gop/Gop - SG)/SI
    ins0 = InsOp + x0*Vi*BW*kicl
    
    X0[0] = Gop
    X0[1] = x0
    X0[2] = x0 + InsOp/(Vi*BW*kicl)
    X0[3] = ins0*ki12/ki2/(ki12+ki1)
    X0[4] = ins0/(ki12+ki1)
    
    return(X0, SI) # May not have to return SI. See if this is used later

#########################################################################################################################
 
def getParam(nmeals, BW):

    SG = .01
    Gb = 140
    p2 = .01
    SI = 5e-4    
    f = 0.9
    Vg = 1.6 
    Vi = 0.06005 
    
    kq1 = 0.01*np.ones((1,nmeals))
    kq2 = 0.01*np.ones((1,nmeals))
    kq12 = 0.01*np.ones((1,nmeals))
    ki1 = 0.0018
    ki2 = 0.0182
    ki12 = 0.0164
    kicl = 0.16
   
    Gop = 120
    InsOp = 15
    
    return(SG,Gb,p2,SI,f,Vg,Vi,kq1,kq2,kq12,ki1,ki2,ki12,kicl,Gop,InsOp)

#########################################################################################################################

def computeNetEffect(p, u, fit, tStep, regIni, regCiNE):
    
# Get discretized LTI model
    (Ad, Bd, Cd, _, Ed, _, BNetEff) = ltiSogmm(tStep, p, True)

# Sample regularly to compute the virtual grid:
    t_array = u[:,0]
    
    u1 = u
    
    Tp1 = t_array.size
    T = Tp1+1

# Build the input-output matrix
    (ny,nx) = Cd.shape
    AA = np.zeros((ny*T,nx))
    AA[0:ny,:] = Cd
    B = np.concatenate((Bd,Ed),axis = 1)
    BBend = np.zeros((ny*T,len(B[0,:]))) # all input
    GGend = np.zeros((ny*T,1)) # net effect input
    
    for t in range(1,Tp1+1):
        AA[ny*t:ny*(t+1), :]= np.matmul(Cd,np.linalg.matrix_power(Ad,t))
        BBend[ny*t: ny*(t+1), :] = np.matmul(Cd,np.matmul(np.linalg.matrix_power(Ad,t-1),B))
        GGend[ny*t: ny*(t+1)] = np.matmul(Cd,np.matmul(np.linalg.matrix_power(Ad,t-1),BNetEff))
    
    GG = np.tril(toeplitz(GGend))
    BB = np.zeros((ny*T, ny*T, B[0,:].size-1))

    for idxInput in range(1,(B[0,:].size)):
        BB[:,:,idxInput-1] = tril(toeplitz(BBend[:,idxInput-1]))
        
    EE = np.sum(tril(toeplitz(BBend[:,-1])),1)

# Compute second order regularization weights

    sqrtW = np.identity(T) - tril(np.ones((T,T)),1) + tril(np.ones((T,T)),0)
    W = np.matmul(sqrtW,sqrtW.transpose())

#% Keep rows according to time of measurements
    t_array.shape = (np.shape(u)[0],1)
    fit_star = fit[:,0]
    fit_star.shape = (np.shape(fit)[0],1)
    diff_abs_t = (abs(fit_star - t_array.transpose()))
    
    temp_row = (diff_abs_t - np.tile(np.amin(diff_abs_t,1), (t_array.size,1)).transpose())
    (row,real_grid)  =   np.where(temp_row == 0)
    
    real_grid = np.delete(real_grid,real_grid[np.where(np.diff(row)==0)])
    row = np.delete(row, row[np.where(np.diff(row)==0)])

# Perform the deconvolution
    Lambdafit = np.identity(fit[:,0].shape[0]) #% Wieight on measurments
    Lambdareg1 = np.matmul(np.diagflat(regIni),np.diagflat(regIni)) #% Reg on the initial state
    Lambdareg2 =  regCiNE*W #% Reg on net Effect
    Lambdareg = sp.linalg.block_diag(Lambdareg1, Lambdareg2)
    
    Mfit = np.concatenate((AA, GG), axis = 1)
    Mfit_extract = Mfit[real_grid,:]

    EE.shape = (len(EE),1)
    f = fit[:,1]
    f.shape = (len(f),1)
    x = f - EE[real_grid,:]

    for idx in range(1, len(B[0,:])): 
        q = np.concatenate((np.array([0]),u1[:,idx]),axis = 0)
        q. shape = (len(q),1)
        x1 = x - np.matmul(BB[real_grid,:,idx-1],q)
        x = x1
   #Matlab Formate
   
    x0_nu,_,_,_ = np.linalg.lstsq(np.add(np.matmul(Mfit_extract.transpose(),np.matmul(Lambdafit,Mfit_extract)),Lambdareg),np.matmul(Mfit_extract.transpose(),np.matmul(Lambdafit,x)), rcond = -1)
    
# Extract estimates of x0 and net effect
    x01 = x0_nu[0:nx]
    omega1 = x0_nu[nx:-1]
  
    return (x01, omega1) 

#########################################################################################################################

def ltiSogmm( tStep, p, withIb):

    withIb = True

#% Linearize SOGMM
    (Ac, Bc, Cc, Dc, Ec, Fc) = linearize(p,withIb)

#% Discretize SOGMM
    (Ad, Bd, Cd, Dd, Ed, Fd) = discretize(tStep, Ac, Bc, Cc, Dc, Ec, Fc)
    BdNetEffect = Bd[:,-1]
    Bd = np.delete(Bd,-1,1)

    return (Ad, Bd, Cd, Dd, Ed, Fd, BdNetEffect)

#########################################################################################################################

def linearize(p, withIb):
    if withIb:
        nmeals = len(p["kq12"])
        nstates = 5+2*nmeals
        Ac = np.zeros((nstates,nstates))
    
    # Core minimal model and insulin path
        Ac[0:5,0:5] = np.array([[- p["SG"]                 , -p["SI"]*p["Gop"]        , 0               , 0                             ,  0  ],                    
                      [ 0                      , -p["p2"]              , p["p2"]            , 0                             ,  0],                      
                      [ 0                      , 0                  , -p["kicl"]         ,  p["ki2"]/(p["Vi"]*p["BW"])            , p["ki1"]/(p["Vi"]*p["BW"])],
                      [ 0                      , 0                  , 0               ,  - p["ki2"]                      , p["ki12"]],
                      [ 0                      , 0                  , 0               , 0                             , -(p["ki12"] +  p["ki1"])      ]])
    
        IpOp = p["InsOp"]/(p["Vi"]*p["BW"])/p["kicl"]
        
        Ec = np.zeros((nstates,1))
        Ec[0] = p["SG"]*p["Gop"]
        Ec[1] = - p["p2"]*IpOp
        Bc = np.zeros((nstates,nmeals+2))
        Bc[4,0] = 1
        Bc[0,nmeals+2-1] = 1
    
    # Multi meal threads
        for idxMeal in range(1,nmeals+1):
            Ac[0,2*idxMeal+4-1] = np.divide(np.multiply(p["f"],p["kq2"][idxMeal-1]),(p["BW"]*p["Vg"]))
            Ac[0,2*idxMeal+5-1] = np.divide(np.multiply(p["f"],p["kq1"][idxMeal-1]),(p["BW"]*p["Vg"]))
            Ac[2*idxMeal+4-1,2*idxMeal+4-1] = - p["kq2"][idxMeal-1]
            Ac[2*idxMeal+5-1,2*idxMeal+5-1] = -(p["kq12"][idxMeal-1]  +  p["kq1"][idxMeal-1])
            Ac[2*idxMeal+4-1,2*idxMeal+5-1] = p["kq12"][idxMeal-1]
            Bc[2*idxMeal+5-1, idxMeal+1-1] = 1
   
        Cc = np.zeros((1,nstates))
        Cc[0,0] = 1
    
        Dc = np.zeros((1,nmeals+1))
        Fc = 0
    
    else:
        xO = p["InsOp"]/(p["Vi"]*p["BW"])/p["kicl"]
    
        nmeals = p["kq12"].size()
        nstates = 5+2*nmeals
        Ac = np.zeros((nstates,nstates))
    
    #% Core minimal model and insulin path
        Ac[0:5,0:5] = [
                      [- (p["SG"]+p["SI"]*xO) , -p["SI"]*p["Gop"], 0               , 0                             ,  0                            ]
                      [0                      , -p["p2"]         , p["p2"]         , 0                             ,  0                        ]    
                      [0                      , 0                , -p["kicl"]      ,  p["ki2"]/(p["Vi"]*p["BW"])   , p["ki1"]/(p["Vi"]*p["BW"])    ]
                      [0                      , 0                , 0               ,  - p["ki2"]                   , p["ki12"]       ]              
                      [0                      , 0                , 0               , 0                             , -(p["ki12"] +  p["ki1"]) ]     
                      ]
    
        Ec = np.zeros((nstates,1))
        Ec[0] = p["SG"]*p["Gb"] + p["SI"]*xO*p["Gop"]
        Bc = np.zeros((nstates,nmeals+2))
        Bc[4,0] = 1
        Bc[0,nmeals+2-1] = 1
    
    #% Multi meal threads
        for idxMeal in range(1,nmeals):
           Ac[0,2*idxMeal+4-1] = p["f"]*p["kq2"][idxMeal-1] /(p["BW"]*p["Vg"])
           Ac[0,2*idxMeal+5-1] = p["f"]*p["kq1"][idxMeal-1] /(p["BW"]*p["Vg"])
           Ac[2*idxMeal+4-1,2*idxMeal+4-1] = - p["kq2"][idxMeal-1]
           Ac[2*idxMeal+5-1,2*idxMeal+5-1] = -(p["kq12"][idxMeal-1]  +  p["kq1"][idxMeal-1])
           Ac[2*idxMeal+4-1,2*idxMeal+5-1] = p["kq12"][idxMeal-1]
           Bc[2*idxMeal+5-1, idxMeal+1-1] = 1
    
        Cc = np.zeros((1,nstates))
        Cc[0] = 1
        Dc = np.zeros((1,nmeals+1))
        Fc = 0
          
    return (Ac, Bc, Cc, Dc, Ec, Fc)

#########################################################################################################################

def  discretize(tStep, Ac, Bc, Cc, Dc, Ec, Fc):

    (n, m) = Bc.shape
    m2 = Ec.shape[1]

    AT = np.zeros((n+m+m2, n+m+m2))
    AT[0:n,0:n] = Ac*tStep
    AT[0:n,n:n+m] = Bc*tStep
    AT[0:n,n+m:n+m+m2] = Ec*tStep

    F = sp.linalg.expm(AT)
    Ad = F[0:n,0:n]
    Bd = F[0:n,n:n+m]
    Ed = F[0:n,n+m:n+m+m2]
    Dd = Dc
    Cd = Cc
    Fd = Fc

    return (Ad, Bd, Cd, Dd, Ed, Fd)

#########################################################################################################################

def deltaValues(cgmT_per, cgmV_per):
    
    #% Function parameters
    nl = 25
    ns = 14
    tStep = 1
    min2day = 1/(60*24)
    
    Jkeep = np.where(~np.isnan(cgmV_per))
    cgmT = cgmT_per[Jkeep]
    CGM = cgmV_per[Jkeep]
    T = cgmT*60*24
    
#    #% Interpolate on a virtual grid
    tGrid = np.arange(T[0],T[-1]+1,tStep)
    vGrid = np.interp(tGrid,T,CGM)

    nbuff = math.floor(1.5*ns)
    vGrid[0:nbuff] = vGrid[nbuff]
#    #% Smooth take the 1st and 2nd derivative
    vS = mySmooth(vGrid,nl,ns)
    dummy1 = np.diff(vS)/tStep
    dvS = np.vstack((0,dummy1[:,None]))
    dummy2 = np.diff(dvS[:,0])/tStep
    ddvS = np.vstack((0,dummy2[:,None]))
#    #% Impose the positivity of 1st and 2nd derivative
    dvSp = np.multiply(dvS,(dvS > 0))
    ddvSp = np.multiply(ddvS,(ddvS > 0))
    detV = np.multiply(dvSp,ddvSp)
    dvS_realGrid = np.zeros((len(cgmT)))
    ddvS_realGrid = np.zeros((len(cgmT)))
    dvSp_realGrid = np.zeros((len(cgmT)))
    ddvSp_realGrid = np.zeros((len(cgmT)))
    detV_realGrid = np.zeros((len(cgmT)))
    virtualT = tGrid*min2day
    for i in range(len(cgmT)):
        tLower = cgmT_per[i]-(1/1440)*2.5
        tUpper = cgmT_per[i]+(1/1440)*2.5
        idx = (virtualT>=tLower)*(virtualT<=tUpper)
        tf = np.where(idx)
        dvS_realGrid[i] = np.average(dvS[tf])
        ddvS_realGrid[i] = np.average(ddvS[tf])
        dvSp_realGrid[i] = np.average(dvSp[tf])
        ddvSp_realGrid[i] = np.average(ddvSp[tf])
        detV_realGrid[i] = np.average(detV[tf])
    return(dvS_realGrid, ddvS_realGrid, dvSp_realGrid, ddvSp_realGrid, detV_realGrid)

#########################################################################################################################
#  
def mySmooth(v,dt,n):
    for index in range(0,n):
        v = smooth(v,dt)
    return(v)

#########################################################################################################################
  
def smooth(a,WSZ):
    # a: NumPy 1-D array containing the data to be smoothed
    # WSZ: smoothing window size needs, which must be odd number,
    # as in the original MATLAB implementation
    out0 = np.convolve(a,np.ones(WSZ,dtype=int),'valid')/WSZ    
    r = np.arange(1,WSZ-1,2)
    start = np.cumsum(a[:WSZ-1])[::2]/r
    stop = (np.cumsum(a[:-WSZ:-1])[::2]/r)[::-1]
    return np.concatenate((  start , out0, stop  ))

#########################################################################################################################

def getMeanMax(data,timeVec,datetimeVec, timeBackward, timeForward):
    nCols = np.shape(data)[1]
    nRows = np.shape(data)[0]
    meanForward = np.zeros((nRows,nCols))
    maxForward = np.zeros((nRows,nCols))
    
    for i in range(nRows):
        tLower_dt = datetimeVec[i]-np.timedelta64(30,'m')
        tUpper_dt = datetimeVec[i]+np.timedelta64(30,'m')
        idx_dt = (datetimeVec>tLower_dt)*(datetimeVec<tUpper_dt)
        tf_dt = np.where(idx_dt)

        for j in range(nCols):
            meanForward[i,j] = np.mean(data[tf_dt,j])
            maxForward[i,j] = np.max(data[tf_dt,j])
    return(meanForward, maxForward)

#########################################################################################################################
   
def predict(features, coefficients, threshold):
    nRows = np.shape(features)[0]
    coefMatrix  = np.tile(coefficients,(nRows,1))
    featureMatrix = np.column_stack((np.ones((nRows)),features))
    varVals = np.multiply(featureMatrix,coefMatrix)
    logOutput = np.sum(varVals,1)
    detectionTimes = np.where(logOutput>threshold)[0]
    return(detectionTimes)

#########################################################################################################################

def findFirsts(nums):
    nums = sorted(set(nums))
    gaps = [[s, e] for s, e in zip(nums, nums[1:]) if s+1 < e]
    edges = iter(nums[:1] + sum(gaps, []) + nums[-1:])
    firstandlast = list(edges)
    firsts = np.asarray(firstandlast[::2])
    return firsts

#########################################################################################################################

def getMealMatrix(dateVec, firstDetect, mealVec):
    days = np.sort(np.unique(np.floor(dateVec)))
    nDays = len(days)
    mealMatrix = np.zeros((288,nDays))
    indicatorMatrix = np.zeros((288,nDays))

    mealTimes = np.where(mealVec>0)
    window = 12 # number of 5 minute intervals (+-)
    if mealTimes[0].size != 0:
        avgMealSize = np.average(mealVec[mealTimes])
        for i in range(len(firstDetect)):
            detectInd = firstDetect[i]
            
            (mealIdx, nearestMealInd) = getNearestInd(mealTimes[0],detectInd)
            if abs(nearestMealInd - detectInd)<=window:
                (row, col) = getMatrixInd(detectInd, dateVec)
                indicatorMatrix[row,col] = 1 #1-Detected Meal Associated with a Recorded Meal
    
                if detectInd-window>=0 & detectInd+window<=len(mealVec):
                    mealMatrix[row,col] = sum(mealVec[detectInd-window:detectInd+window])
                elif detectInd-window<0:
                    mealMatrix[row,col] = sum(mealVec[0:detectInd+window])
                elif detectInd+window>len(mealVec):
                    mealMatrix[row,col] = sum(mealVec[detectInd-window:len(mealVec)])# should this have a +1?
                    
            else:
                detectTime = dateVec[detectInd]
                (col, val)  = getNearestInd(days,detectTime)
                row = int(np.round((((detectTime-np.floor(detectTime))*1440)/5)))
                if row == 288:
                    row == 287  
                mealMatrix[row,col] = avgMealSize
                indicatorMatrix[row,col] = 2 #2-Detection with no meal associated
    else:
        for i in range(len(firstDetect)):
            detectInd = firstDetect[i]
            detectTime = dateVec[detectInd]
            (col, val)  = getNearestInd(days,detectTime)
            row = int(np.round((((detectTime-np.floor(detectTime))*1440)/5)))
            if row == 288:
                row == 287
            mealMatrix[row,col] = 25*1000/5 #mg/min
            indicatorMatrix[row,col] = 2
                
    for j in range(len(mealTimes[0])):
        mealInd = mealTimes[0][j]
        if len(firstDetect) > 0:
            (detectIdx, nearestDetectInd) = getNearestInd(firstDetect,mealInd)
        else:
            nearestDetectInd = float('nan')
            
        if abs(nearestDetectInd - mealInd)>=window or  np.isnan(nearestDetectInd):
            (row, col) = getMatrixInd(mealInd, dateVec)
            mealMatrix[row,col] = mealVec[mealInd]
            print("Undetected meal at (" + str(row) + "," + str(col) + ")")
            indicatorMatrix[row,col] = 3 #3-Recorded meal without a detection

    return mealMatrix, indicatorMatrix

#########################################################################################################################

def getNearestInd(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx, array[idx]

#########################################################################################################################

def getMatrixInd(detectInd,timeVec):
    time = timeVec[detectInd]
    days = np.sort(np.unique(np.floor(timeVec)))
    (indCol, val) = getNearestInd(days,np.floor(timeVec[detectInd]))
    indRow = int(np.round(((time-np.floor(time))*1440)/5))
    if indRow == 288:
        indRow == 287
    return indRow, indCol

#########################################################################################################################

def getReconstructedMealVec(timeVec,mealMatrix,indicatorMatrix):
    startRow = int(round(288*(timeVec[0]-np.floor(timeVec[0]))))
    endRow = int(round(288*(timeVec[-1]-np.floor(timeVec[-1]))))
    endColumn = np.shape(mealMatrix)[1]-1
    for c in range(endColumn+1):
        if c == 0:
            reconstructedMealVec = mealMatrix[startRow:,0]
            indicatorVec = indicatorMatrix[startRow:,0]
        elif c != endColumn:
            reconstructedMealVec = np.concatenate((reconstructedMealVec,mealMatrix[:,c]))
            indicatorVec = np.concatenate((indicatorVec,indicatorMatrix[:,c]))
        else:
            reconstructedMealVec = np.concatenate((reconstructedMealVec,mealMatrix[:endRow,-1]))
            indicatorVec = np.concatenate((indicatorVec,indicatorMatrix[:endRow,-1]))
        
#    # Added because vectors were 1 short of time vector    
    reconstructedMealVec = np.append(reconstructedMealVec,0)
    indicatorVec = np.append(indicatorVec,0)
    return reconstructedMealVec, indicatorVec

#########################################################################################################################