# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 16:20:42 2019

@author: John "Jack" Corbett
- This script will read in patient data (meal, cgm, insulin) and reconstruct
the meal record either from patient data or meal detections.
"""

#########################################################################################################################

def mealReconstruction(data):
    
    ## Load Packages
    import mealDataFunctions_fromServer_v4 as mealFunctions
    import numpy as np
    
    (timeVec,datetimeVec,cgmVec,basalVec,bolusVec,mealVec,BW,TDI) = mealFunctions.getData(data) # DSS2 data

    print('paaa')
    print(timeVec)
    print(datetimeVec)
    print(cgmVec)
    print(mealVec)
    print(basalVec)
    print(bolusVec)
    
    (features) = mealFunctions.getFeaturesV2(timeVec,datetimeVec,cgmVec,bolusVec,mealVec,BW,TDI)
    
    ## Set up model
    coefficients = np.array([0.00994,0.60916,1.1931,0.060042,-0.38904,0.13234,-0.57161,2.5957,0.1074,-2099.2,-0.025257,0.030026,0.000069603])
    threshold = 0.13884
    
    ## Get meal detection times
    (detectionTimes) = mealFunctions.predict(features, coefficients, threshold)
    
    # Return first consecutive detection
    (firstDetect) = mealFunctions.findFirsts(detectionTimes)
    
    ## Get meal amounts and timing in vector form.
    (mealMatrix, indicatorMatrix) = mealFunctions.getMealMatrix(timeVec, firstDetect, mealVec)
    (reconstructedMealVec,indicatorVec) = mealFunctions.getReconstructedMealVec(timeVec,mealMatrix,indicatorMatrix)

    return reconstructedMealVec, indicatorVec

#########################################################################################################################