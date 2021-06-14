# -*- coding: utf-8 -*-
"""
Created on Sun Oct  4 13:28:59 2020
New Test Script for CR/CF adaptation routine conversion matlab to python
@author: jh8be


"""


import numpy as np
import CRCFAdaptationLibrary as CRCF
#from scipy.io import loadmat
import json


with open('data/jsonData_test_1_2.json') as f:
  data = json.load(f)


CRstruct = {'values': np.array(data['CR']), 'time': np.zeros((1,))}
CFstruct = {'values': np.array(data['CF']), 'time': np.zeros((1,))}

t = np.array(data['t'])
cgm = np.array(data['cgm'])
bol = np.array(data['bolus'])
meal = np.array(data['meal'])
#t = loadmat('t.mat')['t']
#cgm = loadmat('cgm.mat')['cgm']
#bol = loadmat('bol.mat')['bol']
#meal = loadmat('meal.mat')['meal']



tdi = data['tdi']

paramAdapt = {}

CRoptStruct,CFoptStruct, paramAdapt = CRCF.crcfoptimization(t, cgm, bol, meal, CRstruct, CFstruct, tdi, paramAdapt)

print(CRoptStruct['values'])
#print(CFoptStruct)
#print(paramAdapt)





