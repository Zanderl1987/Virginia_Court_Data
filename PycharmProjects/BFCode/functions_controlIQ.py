import numpy as np
import datetime
from decimal import *

# Functions related to Control-IQ

#########################################################################################################################

# Function to get TDIpop
def get_TDIpop(elements,TDIpop,d1,d2):

    TDIpop_roll = TDIpop    

    if len(elements)>0:
        for element in elements: 
            time = getattr(element,'time')
            if (time < d2):
                if (time >= d1):
                    TDIpop_roll = float(getattr(element,'TDIpop'))
                    break
            else:
                break
                            
    return TDIpop_roll    

#########################################################################################################################

# Function to generate SumBolusMem
def gen_SumBolusMem(SumBolusMem,insulin_Froll,TDIpop_Froll,TDIpop,d1,dDiff,J24h):

    insulinValueArray = [] 
    insulinTimeArray = []
    TDIpopValueArray = []
    TDIpopTimeArray = []

    for insulin_rec in insulin_Froll.all():
        if len(J24h)>0:
            insulinValueArray.append(J24h[0]) 
            del J24h[0]
        else:
            basal = float(getattr(insulin_rec,'basal')) 
            corr = float(getattr(insulin_rec,'corr'))
            meal = float(getattr(insulin_rec,'meal'))
            insulinValueArray.append(basal+corr+meal) # numpy doesn't understand decimal
        insulinTimeArray.append(insulin_rec.time)
    
    for TDIpop_rec in TDIpop_Froll.all():
        TDIpopValueArray.append(float(TDIpop_rec.TDIpop)) # numpy doesn't understand decimal
        TDIpopTimeArray.append(TDIpop_rec.time)

    if len(TDIpopValueArray) > 0:
        TDIpopVArray = np.array(TDIpopValueArray)
        TDIpopTArray = np.array(TDIpopTimeArray)

    if len(insulinValueArray) > 0:
        insulinVArray = np.array(insulinValueArray)
        insulinTArray = np.array(insulinTimeArray)
        for a in range(144*3+1-24*dDiff*3, 144*3):
            insulinV_24roll = insulinVArray[(np.where((insulinTArray>=d1-7*24*60*60+a*20*60) & (insulinTArray<d1-6*24*60*60+a*20*60)))]
            if len(TDIpopValueArray) > 0:
                TDIpop_24roll = TDIpopVArray[(np.where((TDIpopTArray>=d1-7*24*60*60+a*20*60) & (TDIpopTArray<d1-6*24*60*60+a*20*60)))]
            else:
                TDIpop_24roll = []
            if len(TDIpop_24roll)>0:
                TDIpop_roll = TDIpop_24roll[0]
            else:
                TDIpop_roll = TDIpop
            if len(insulinV_24roll) < 0.85*288:
                SumBolus = TDIpop_roll
            else:
                SumBolus = sum(insulinV_24roll)
            SumBolusMem.append(SumBolus)
        SumBolusMem = SumBolusMem[-143:]
    else:
        SumBolusMem = [TDIpop]*143
    
    return SumBolusMem

#########################################################################################################################

# Main function of Control-IQ
def controlIQ(J24r,J6,G6,M6,tod,bh6,basal,CF,EX,indCorrTimer,sbMem,TDIpop,sleep,tgt,BW,TDIest):

    INSdif = J6-bh6/12
  
    # 1 - Estimate TDI

    #if np.mod(tod,1)==0:
    if np.mod(np.round(60.0*tod),20.0)<=1.0:
        TDIest,sbMem = controlIQ_TDI(J24r,sbMem,TDIpop)
    
    # 2 - Estimate IOB -> It is relative to basal rate

    IOBest = controlIQ_IOB(INSdif)

    # 3 - Predict glucose

    GP30,GPL,Gest = controlIQ_USSPred(INSdif,G6,M6,basal,BW)

    # 4 - Run HMS

    corrBol,indCorrTimer = controlIQ_BOP(CF,indCorrTimer,sleep,IOBest,GP30)

    # 5 - Run BRM

    du,a,gt = controlIQ_BRM(CF,EX,tgt,TDIest,IOBest,Gest,GP30)

    # 6 - Apply brakes

    usugg,apBDose,apCDose = controlIQ_FC(basal,EX,GPL,corrBol,du,a)

    return TDIest,sbMem,apBDose,apCDose,indCorrTimer,GP30

############################################################################################################################

def controlIQ_TDI(INS,SumBolusMEM,TDIpop):

    B = np.transpose([[1.17E-04,1.90E-04,3.11E-04,5.07E-04,8.28E-04,1.35E-03,2.20E-03,3.60E-03,5.87E-03,
        9.58E-03,1.56E-02,2.55E-02,1.21E-04,1.98E-04,3.24E-04,5.28E-04,8.62E-04,1.41E-03,
        2.30E-03,3.75E-03,6.12E-03,9.98E-03,1.63E-02,2.66E-02,1.27E-04,2.07E-04,3.37E-04,
        5.50E-04,8.98E-04,1.47E-03,2.39E-03,3.90E-03,6.37E-03,1.04E-02,1.70E-02,2.77E-02,
        1.32E-04,2.15E-04,3.51E-04,5.73E-04,9.35E-04,1.53E-03,2.49E-03,4.07E-03,6.64E-03,
        1.08E-02,1.77E-02,2.89E-02,1.37E-04,2.24E-04,3.66E-04,5.97E-04,9.74E-04,1.59E-03,
        2.60E-03,4.24E-03,6.91E-03,1.13E-02,1.84E-02,3.01E-02,1.43E-04,2.33E-04,3.81E-04,
        6.22E-04,1.02E-03,1.66E-03,2.70E-03,4.41E-03,7.20E-03,1.18E-02,1.92E-02,3.13E-02,
        1.49E-04,2.43E-04,3.97E-04,6.48E-04,1.06E-03,1.73E-03,2.82E-03,4.60E-03,7.50E-03,
        1.22E-02,2.00E-02,3.26E-02,1.55E-04,2.53E-04,4.13E-04,6.75E-04,1.10E-03,1.80E-03,
        2.93E-03,4.79E-03,7.81E-03,1.28E-02,2.08E-02,3.40E-02,1.62E-04,2.64E-04,4.31E-04,
        7.03E-04,1.15E-03,1.87E-03,3.06E-03,4.99E-03,8.14E-03,1.33E-02,2.17E-02,3.54E-02,
        1.68E-04,2.75E-04,4.49E-04,7.32E-04,1.20E-03,1.95E-03,3.18E-03,5.20E-03,8.48E-03,
        1.38E-02,2.26E-02,3.69E-02,1.75E-04,2.86E-04,4.67E-04,7.63E-04,1.24E-03,2.03E-03,
        3.32E-03,5.41E-03,8.83E-03,1.44E-02,2.35E-02,3.84E-02,1.83E-04,2.98E-04,4.87E-04,
        7.95E-04,1.30E-03,2.12E-03,3.45E-03,5.64E-03,9.20E-03,1.50E-02,2.45E-02,4.00E-02]])

    AX0 = 2.691e-3

    SumBolusAux = np.append(TDIpop*np.ones((1,143-len(SumBolusMEM))),SumBolusMEM[max(0,len(SumBolusMEM)-143):len(SumBolusMEM)])
    
    if len(INS)<(0.85*288):
        SumBolus = TDIpop
    else:
        SumBolus = np.sum(INS[max(0,len(INS)-288):len(INS)])

    TDIest = AX0*TDIpop+np.matmul(np.append(SumBolusAux,SumBolus),B)[0]
    
    if TDIest>2*TDIpop:
        TDIest = 2*TDIpop
    elif TDIest<0.5*TDIpop:
        TDIest = 0.5*TDIpop

    SumBolusMEM = np.append(SumBolusMEM[1:len(SumBolusMEM)], SumBolus)

    return TDIest,SumBolusMEM

############################################################################################################################

def controlIQ_IOB(INSdif):

    IOB_curve_4h = np.transpose([[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0.0013,0.0028,0.0045,0.0064,0.0085,
        0.0108,0.0135,0.0164,0.0196,0.0233,0.0273,0.0318,
        0.0369,0.0425,0.0487,0.0556,0.0633,0.0719,0.0813,
        0.0918,0.1034,0.1162,0.1304,0.1460,0.1632,0.1822,
        0.2029,0.2257,0.2506,0.2777,0.3072,0.3393,0.3739,
        0.4111,0.4510,0.4936,0.5387,0.5861,0.6355,0.6865,
        0.7383,0.7901,0.8407,0.8884,0.9312,0.9664,0.9908]])
    
    IOBest = np.clip(np.matmul(INSdif,IOB_curve_4h)[0],0,np.Inf)
    
    return IOBest

############################################################################################################################

def controlIQ_USSPred(INSdif,G6,M6,basal,BW):

    Gop = 90 

    INS_A = np.array([[0.9048, 6.256e-6, 2.996e-6/BW, 1.551e-6/BW],[0, 0.4107, 0.5301/BW, 0.28/BW],[0, 0, 0.9048, 0.0452],[0, 0, 0, 0.9048]])
    INS_B = np.array([[2.792e-6/BW,0.8035/BW,0.117,4.758]]).T
    INS_C = np.eye(4)
    INS_D = np.array([[0,0,0,0]]).T

    MEAL_A = np.array([[0.9512, 0.06959],[0, 0.9048]])
    MEAL_B = np.array([[0.1784,4.758]]).T
    MEAL_C = np.array([[0.01, 0.005], [1,0],[0,1]])
    MEAL_D = np.array([[0,0,0]]).T

    CORE_pred_A = np.array([[0.7408, -2296, -1728, 0.117/BW, 0.0744/BW, -0.0169, -0.0203/BW, -0.0347/BW],\
        [0, 0.9704, 0, 0, 0, 0, 0, 0],\
            [0, 0, 0.5488, 0, 0, 6.89e-6, 1.75e-5/BW, 2.794e-5/BW],\
                [0, 0, 0, 0.7408, 0.2880, 0, 0, 0],\
                    [0, 0, 0, 0, 0.5488, 0, 0, 0],\
                        [0, 0, 0, 0, 0, 0.0048, 0.4315/BW, 0.5836/BW],\
                            [0, 0, 0, 0, 0, 0, 0.5488, 0],\
                                [0, 0, 0, 0, 0, 0, 0.1646, 0.5488]])
    CORE_pred_C = np.array([1, 0, 0, 0, 0, 0, 0, 0])

    LIGHT_pred_A = np.array([[0.8607, -1244, -1079, 0.068/BW, 0.0388/BW, -8.29e-3, -4.34e-3/BW, -8.034e-3/BW],\
        [0, 0.9851, 0, 0, 0, 0, 0, 0],\
            [0, 0, 0.7408, 0, 0, 8.5e-06, 8.217e-6/BW, 1.472e-5/BW],\
                [0, 0, 0, 0.8607, 0.1798, 0, 0, 0],\
                    [0, 0, 0, 0, 0.7408, 0, 0, 0],\
                        [0, 0, 0, 0, 0, 0.0693, 0.4338/BW, 0.7204/BW],\
                            [0, 0, 0, 0, 0, 0, 0.7408, 0],\
                                [0, 0, 0, 0, 0, 0, 0.1111, 0.7408]])
    LIGHT_pred_B = np.array([[0.2936/BW, -0.0186/BW],\
        [0,0],\
            [0, 9.726e-05/BW],\
                [1.4552, 0],\
                    [12.9591, 0],\
                        [0, 4.6119/BW],\
                            [0, 12.9591],\
                                [0, 0.9234]])
    LIGHT_pred_C = np.array([1, 0, 0, 0, 0, 0, 0, 0])

    KF_A = np.array([[6.486e-3, -417.53],\
        [7.136e-4, 0.9048]])
    KF_B = np.array([[-2.14e-3, 2.5669/BW, 0.9447],\
        [9.5163e-6, 0, -7.136e-4]])
    KF_C = np.array([[0.353, 0],\
        [7.887e-4, 1]])
    KF_D = np.array([[0, 0, 0.647],\
        [0, 0, -7.887e-4]])

    BUFF_MEAL_A = np.array([[0.6065, 0.3033],\
        [0, 0.6065]])
    BUFF_MEAL_B = np.array([[0.0902,0.3935]]).T
    BUFF_MEAL_C = np.array([1,0])
    
    BUFF_INS_A = np.array([[0.6065, 0.3033],\
        [0, 0.6065]])
    BUFF_INS_B = np.array([[0.0902,0.3935]]).T
    BUFF_INS_C = np.array([1,0])
    
    # KF loop

    MB = np.zeros((2,len(G6)))
    MX = np.zeros((2,len(G6)+1))
    Mout = np.zeros((3,len(G6)))
    IB = np.zeros((2,len(G6)))
    IX = np.zeros((4,len(G6)+1))
    Iout = np.zeros((4,len(G6)))
    KFout = np.zeros((2,len(G6)))
    KFstate = np.zeros((2,len(G6)+1))

    for k in range(0,len(G6)):

        MB[:,k+1:k+2] = np.dot(BUFF_MEAL_A,MB[:,k:k+1])+BUFF_MEAL_B*1000.0*M6[k]/5.0
        MX[:,k+1:k+2] = np.dot(MEAL_A,MX[:,k:k+1])+np.dot(MEAL_B,np.dot(BUFF_MEAL_C,MB[:,k]))
        Mout[:,k:k+1] = np.dot(MEAL_C,MX[:,k:k+1])+np.dot(MEAL_D,np.dot(BUFF_MEAL_C,MB[:,k]))

        IB[:,k+1:k+2] = np.dot(BUFF_INS_A,IB[:,k:k+1])+BUFF_INS_B*6000.0*INSdif[k]/5.0
        IX[:,k+1:k+2] = np.dot(INS_A,IX[:,k:k+1])+np.dot(INS_B,np.dot(BUFF_INS_C,IB[:,k]))
        Iout[:,k:k+1] = np.dot(INS_C,IX[:,k:k+1])+np.dot(INS_D,np.dot(BUFF_INS_C,IB[:,k]))

        KFout[:,k:k+1] = np.dot(KF_C,KFstate[:,k:k+1])+np.dot(KF_D,np.array([[Iout[1,k],Mout[0,k],G6[k]-Gop]]).T)
        KFstate[:,k+1:k+2] = np.dot(KF_A,KFstate[:,k:k+1])+np.dot(KF_B,np.array([[Iout[1,k],Mout[0,k],G6[k]-Gop]]).T)

    XI = np.array([[KFout[0,-1],KFout[1,-1]-Iout[0,-1],Iout[0,-1]]]).T
    XI = np.append(XI,Mout[1:3,-1])
    XI = np.append(XI,Iout[1:4,-1])
    XI = XI.reshape(-1,1)

    Gest = XI[0]+Gop

    GP30 = np.dot(CORE_pred_C,np.dot(CORE_pred_A,XI))+Gop
    GPL = np.dot(LIGHT_pred_C,np.dot(LIGHT_pred_A,XI)+np.dot(LIGHT_pred_B,np.array([[-6000*basal/60,0]]).T))+Gop

    return GP30[0],GPL[0],Gest[0]

############################################################################################################################

def controlIQ_BOP(CF,indCorrTimer,sleep,IOBest,GP30):
    
    if (GP30>=180.0) and (indCorrTimer == 0):
        if sleep==0:
            Corr = min(6.0,max(0,0.6*((GP30-110.0)/CF-max(0.0,IOBest))))
        else:
            Corr = 0.0
    else:
        Corr = 0.0
    
    if Corr>0:
        indCorrTimer = 1
    
    return Corr,indCorrTimer

############################################################################################################################

def controlIQ_BRM(CF,EX,tgt,TDIest,IOBest,Gest,GP30):

    T2tgt = 30
        
    CFactive = min(max(1500.0/TDIest,CF),1800.0/TDIest)

    INSTarget_predicted = (min(90.0,GP30-tgt))/CFactive

    Rate = max(0.0,(INSTarget_predicted-IOBest)/T2tgt)

    if Gest>=180.0:
        du = min(Rate,3.0*TDIest/(48*60))
    else:
        du = min(Rate,2.0*TDIest/(48*60))

    a = controlIQ_brakes(GP30,EX)

    return du,a,tgt

############################################################################################################################

def controlIQ_brakes(GP30,EX):

    Kbrakes = 2.5
    risk    = 10.0*(GP30<=112.5)*(scaledBG(GP30)**2)
    riskEX  = 10.0*(GP30<=140)*(EXscaledBG(GP30)**2)
    
    if EX>0:
        a = 1/(1+Kbrakes*riskEX)
        if GP30<80:
            a = 0.0
    else:
        a = 1/(1+Kbrakes*risk)
        if GP30<70:
            a = 0.0

    return a

############################################################################################################################

def EXscaledBG(bg):

    if bg<20.0:
        bgSat = 20.0
    elif bg>600.0:
        bgSat = 600.0
    else:
        bgSat = bg

    scaledBG_out = 0.9283*(np.exp(1.8115*np.log(np.log(bgSat)))-18.0696)

    return scaledBG_out
        
############################################################################################################################

def scaledBG(bg):

    if bg<20.0:
        bgSat = 20.0
    elif bg>600.0:
        bgSat = 600.0
    else:
        bgSat = bg

    scaledBG_out = 1.509*(np.exp(1.084*np.log(np.log(bgSat)))-5.381)
    
    return scaledBG_out

############################################################################################################################

def controlIQ_FC(basal,EX,GPL,corrBol,du,a):

    # print('a: '+str(a))
    # print('du: '+str(5.0*du))

    if a<1.0:
        usugg = a*basal/12
        apBDose = a*basal/12
        apCDose = 0.0

    else:
        usugg = (corrBol+5.0*du+basal/12)
        apBDose = basal/12+5.0*du
        apCDose = corrBol

    Hlo = controlIQ_hypoLight(a,GPL,EX)
    
    if Hlo==2:
        usugg = 0.0
        apBDose = 0.0
        apCDose = 0.0

    return usugg,apBDose,apCDose

############################################################################################################################

def controlIQ_hypoLight(a,GPL,EX):

    if (EX==1) and (GPL<80):
        H = 2
    elif (EX==0) and (GPL<70):
        H = 2
    elif a<1.0:
        H = 1
    else:
        H = 0

    return H

############################################################################################################################

# Function to generate arrays of Control-IQ parameters
def generate_controlIQPar_5min(elements):
    
    EXV     = []
    tgtV    = []
    sleepV  = []
    TDIpopV = []

    EXD     = [0]*288
    tgtD    = [0.0]*288
    sleepD  = [0]*288
    TDIpopD = [0.0]*288

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
            
            EX     = getattr(element,'EX')
            TDIpop = float(getattr(element,'TDIpop'))
            sleep  = getattr(element,'sleep')
            tgt    = float(getattr(element,'TGT'))
            
            if day==dayp:               
                EXD[ind]     = EX
                TDIpopD[ind] = TDIpop
                sleepD[ind]  = sleep
                tgtD[ind]    = tgt
            else:
                
                EXV.append(EXD)
                tgtV.append(tgtD)
                sleepV.append(sleepD)
                TDIpopV.append(TDIpopD)

                EXD     = [0]*288
                tgtD    = [0.0]*288
                sleepD  = [0]*288
                TDIpopD = [0.0]*288

                EXD[ind]     = EX
                TDIpopD[ind] = TDIpop
                sleepD[ind]  = sleep
                tgtD[ind]    = tgt

            dayp = day
        
        EXV.append(EXD)
        tgtV.append(tgtD)
        sleepV.append(sleepD)
        TDIpopV.append(TDIpopD)

    return EXV,TDIpopV,sleepV,tgtV

############################################################################################################################