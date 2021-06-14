import numpy as np
import datetime
from decimal import *

# Functions related to Basal-IQ

#########################################################################################################################

# Function to compute time of insulin suspension under Basal-IQ
def compute_time_insSusp(elements):
    
    timeSusp = 0

    if len(elements)>0:
        for element in elements: 
            flagSusp = int(getattr(element,insSusp))
            timeSusp = timeSusp+5*flagSusp
        
    return timeSusp

#########################################################################################################################

# Function to run the Basal-IQ algorithm
def basalIQ(gTPred,gVPred,tInsSusp,basal,flagInsSusp):

    gPredModel = np.polyfit(gTPred,gVPred,1)
    LGPred = np.poly1d(gPredModel)
    g30min = LGPred(30)

    preFlagInsSusp = 0
    preFlagInsRes = 0

    if (gVPred[-1]<70.0) or (g30min<80.0):
        preFlagInsSusp = 1

    if flagInsSusp==1 and ((gVPred[-1] > gVPred[-2]) or (g30min>=80) or (tInsSusp>120)):
        preFlagInsRes = 1
        
    if (preFlagInsSusp==1) and (preFlagInsRes==0):
        flagInsSusp = 1
    elif preFlagInsRes==1:
        flagInsSusp = 0

    if flagInsSusp==1:
        apDose = 0.0
        tInsSusp = tInsSusp+5
    else:
        apDose = basal
        tInsSusp = min(tInsSusp-5,0)
    
    return apDose,tInsSusp,flagInsSusp

#########################################################################################################################