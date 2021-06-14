#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 11:35:30 2020
@title: Computation of eA1cROC
@author: cf9qe
"""

import numpy as np
from scipy.linalg import inv

def estimateA1cROC():
    # RUNNING SCHEDULE: run every night after the computation of eA1c
    # get eA1c estimates from previous seven days (current day included)
    eA1cVec = np.array([])
    eA1cVec.shape = (len(eA1cVec),1)
    XT = np.mat([[1,1,1,1,1,1,1],
                 [-6,-5,-4,-3,-2,-1,0]])
    X = np.transpose(XT)
    p = inv(XT*X)*XT*eA1cVec
    eA1cROC = round(p[1,0]*100000)/100000
    
    th1 = -0.01085
    th2 = -0.00414
    th3 = 0.00164
    th4 = 0.009
    
    if eA1cROC<=th1:
        eA1cROC_flag = -2
    elif eA1cROC>th1 and eA1cROC<=th2:
        eA1cROC_flag = -1
    elif eA1cROC>th2 and eA1cROC<th3:
        eA1cROC_flag = 0
    elif eA1cROC>=th3 and eA1cROC<th4:
        eA1cROC_flag = 1
    elif eA1cROC>=th4:
        eA1cROC_flag = 2
    
    return (eA1cROC_flag)
