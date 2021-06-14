from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash
from forms import LoginForm, RequestResetForm, ResetPasswordForm
import logging
import atexit
import matlab.engine
from pytz import utc
import numpy as np
import simplejson as json
from sqlalchemy import exc
from functions import *
from functions_basalIQ import *
from functions_controlIQ import *
import pdfkit
import datetime
from dateutil.tz import *
import traceback
from sqlalchemy.ext.automap import automap_base
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import InputRequired, Email, Length, EqualTo
from functions_DP import *
from functions_DP_newM import *
from functions_BAM import *
import mealreconstruction_v2 as MR
import pandas as pd
import optimizeTreatmentWeekly as wBROpt
import time
from cryptography.fernet import Fernet
import sys
from fetching_API_Python import *
import random
if sys.version_info >= (3, 7):
    import zipfile
else:
    import zipfile37 as zipfile
import CRCFAdaptationLibraryNu as CRCF
import requests

import scipy.io as sio # For testing purposes!

#########################################################################################################################
# Scheduler
#########################################################################################################################

#########################################################################################################################
def sensor():

    for ii in range(10):
        time.sleep(1)
        print('Scheduler! '+str(ii))

#########################################################################################################################
def sensor1():

    for ii in range(10):
        time.sleep(1)
        print('Voila1! '+str(ii))

#########################################################################################################################
def fetchTandemData():

    app.logger.info('/scheduler/fetchTandemData. The scheduler has been called. Starting to pull out data from Tandem server.')

    # Get all active subjects
    attemps = 5
    while attemps>0:
        app.logger.info('/scheduler/fetchTandemData. Remaining attemps to get active users: '+str(attemps))
        try:
            allActUsers = db.session.query(Subject).filter(Subject.active==1, Subject.username != 'fakeUser').all()
            break
        except exc.SQLAlchemyError as e:
            attemps -=1
            db.session.close()
    
    app.logger.info('/scheduler/fetchTandemData. # detected active users: '+str(len(allActUsers)))

    cc = 1
    for act_subj in allActUsers:
        app.logger.info('/scheduler/fetchTandemData. Active user #'+str(cc)+': '+act_subj.username)
        cc+=1

    # Iterate over all active subjects
    for act_subj in allActUsers:
        for ii in range(0,1):
            # Active subject
            app.logger.info('/scheduler/fetchTandemData. Username: ' + act_subj.username)

            # Get tz from insulin pump
            ins_device        = db.session.query(PumpDevice).filter_by(subject_id=act_subj.id).order_by(PumpDevice.id.desc()).first()
            ins_device_tz_str = ins_device.tz
            ins_device_tz     = gettz(ins_device_tz_str)
            insDur            = ins_device.ins_dur

            local_time_now = datetime.datetime.now()

            t0_utc   = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc).timestamp())
            t0_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
            utcOffset = t0_utc - t0_local
            
            g = db.session.query(CGM).filter_by(cgm_device_subject_id=act_subj.id).order_by(CGM.id.desc()).first()

            if g is not None:
                utcOffsetPrev = g.utcOffset
            else:
                utcOffsetPrev = utcOffset
            
            utcOffsetDiff = utcOffset-utcOffsetPrev

            #########################################################
            # Fetch data from Tandem server
            #########################################################

            # Get model and serial numbers
            insdev_key = os.environ.get('INSDEV_KEY')
            f = Fernet(insdev_key)
            
            modelNumber_decrypted  = f.decrypt(ins_device.modelNumber.encode())
            serialNumber_decrypted = f.decrypt(ins_device.serialNumber.encode())
            
            modelNumber  = modelNumber_decrypted.decode()
            serialNumber = serialNumber_decrypted.decode()
            
            # Study start date
            today_utc = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc)
            today_local = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day)
            yest_utc = today_utc-datetime.timedelta(days=1)

            studyStartDate = str(yest_utc.year)+'-'+str(yest_utc.month)+'-'+str(yest_utc.day)
            studyEndDate = str(today_utc.year)+'-'+str(today_utc.month)+'-'+str(today_utc.day)
            date_file = str(today_local.year)+'-'+str(today_local.month)+'-'+str(today_local.day)

            # studyStartDate = '2021-01-26'
            # studyEndDate = '2021-01-27'
            # date_file = '2021-01-27'

            # Zip file
            zipName = 'backendFiles/'+act_subj.username+'_'+date_file

            # Tandem credentials
            tandem_username = os.environ.get('TANDEM_USERNAME')
            tandem_password = os.environ.get('TANDEM_PASSWORD')

            # Get access token
            payload = {'grant_type': 'password', 'username': tandem_username, 'password': tandem_password, 'scope': 'cloud.upload cloud.account cloud.password'}
            headers = {'Content-Type': 'application/x-www-form-urlencoded','x-api-version': '1','Authorization': 'Basic ODIwNTNkNmItZjA0YS00ZmRlLTgzMWEtNWIxNGJkODUyNDI1OmxpIzVBQSRmaV40UnlXMSElYm1m'}
            url     = 'https://tdcservices.tandemdiabetes.com/cloud/oauth2/token'
            
            ii = 1
            flagWhile = True

            while (flagWhile) and (ii<10):
                r = requests.post(url,headers=headers,data=payload)
                if r.status_code==200:
                    flagWhile = False
                app.logger.info('/scheduler/fetchTandemData. Username: ' + act_subj.username + '. Attemp to get token: '+str(ii)+'; status code: ' +str(r.status_code))
                ii+=1
            
            if r.status_code==200:
                try:
                    r_json = r.json()
                    accessToken = r_json['accessToken']
                except:
                    app.logger.error('/scheduler/fetchTandemData. Username: ' +act_subj.username +'. No token was available. Stoping process...')
                    break
            else:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. No token was available. Stoping process...')
                break

            # Get JSON data
            payload = {'format': 'json','studyStartDate': studyStartDate,'studyEndDate': studyEndDate}
            headers = {'x-api-version': '1','Authorization': 'Bearer ' +accessToken}
            url     = 'https://tdcservices.tandemdiabetes.com/cloud/uploadretrieval/api/bulkdownload/'+modelNumber+'/'+serialNumber

            ii = 1
            flagWhile = True

            flagFetch = True

            if flagFetch:
                while (flagWhile) and (ii<10):
                    r = requests.get(url,headers=headers,params=payload,stream=True)
                    
                    if r.status_code==200:
                        flagWhile = False
                    app.logger.info('/scheduler/fetchTandemData. Username: ' + act_subj.username + '. Attemp to get JSON data: '+str(ii)+'; status code: ' +str(r.status_code))
                    ii+=1

                if r.status_code==200:
                    try:
                        with open(zipName+'.zip','wb') as f:
                            f.write(r.content)

                        with zipfile.ZipFile(zipName+'.zip','r') as my_zip:
                            my_zip.extractall(zipName)
                            filename_old = os.path.join("backendFiles/"+act_subj.username+"_"+date_file,modelNumber+str('-')+serialNumber+'.json')
                            filename_new = os.path.join("backendFiles/"+act_subj.username+"_"+date_file,act_subj.username+'.json')
                            if not os.path.exists(filename_new):
                                os.rename(filename_old,filename_new)
                            else:
                                os.remove(filename_new)
                                os.rename(filename_old,filename_new)
                    except:
                        app.logger.error('/scheduler/fetchTandemData. Username: ' +act_subj.username +'. No data was available. Stoping process...')
                        break

                    app.logger.info('/scheduler/fetchTandemData. Username: ' + act_subj.username + '. JSON files has been successfully extracted.')

                else:
                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. No data was available. Stoping process...')
                    break

#########################################################################################################################

def dailyOptimizer():
    
    app.logger.info('/scheduler. The scheduler has been called. Starting to optimize the basal rate profile.')

    # Get all active subjects
    attemps = 5
    while attemps>0:
        app.logger.info('/scheduler. Remaining attemps to get active users: '+str(attemps))
        try:
            allActUsers = db.session.query(Subject).filter(Subject.active==1, Subject.username != 'fakeUser').all()
            break
        except exc.SQLAlchemyError as e:
            attemps -=1
            db.session.close()
    
    app.logger.info('/scheduler. # detected active users: '+str(len(allActUsers)))

    cc = 1
    for act_subj in allActUsers:
        app.logger.info('/scheduler. Active user #'+str(cc)+': '+act_subj.username)
        cc+=1

    # Iterate over all active subjects
    for act_subj in allActUsers:
        for ii in range(0,1):
            # Active subject
            app.logger.info('/scheduler. Username: ' + act_subj.username)

            ins_device        = db.session.query(PumpDevice).filter_by(subject_id=act_subj.id).order_by(PumpDevice.id.desc()).first()
            ins_device_tz_str = ins_device.tz
            ins_device_tz     = gettz(ins_device_tz_str)
            #ins_device_tz     = gettz('America/Chicago')
            APS_mode          = act_subj.apSystem

            local_time_now = datetime.datetime.now()
            today_utc = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc)

            sfData = np.array([])
            bpData = []
            crData = []
            cfData = []

            # Fetch data from previous day
            for jj in range(1,-1,-1):
                odf_utc = today_utc-datetime.timedelta(days=jj)
                date_file = str(odf_utc.year)+'-'+str(odf_utc.month)+'-'+str(odf_utc.day)
                t0_utc   = int(datetime.datetime(odf_utc.year,odf_utc.month,odf_utc.day,tzinfo=datetime.timezone.utc).timestamp())
                t0_local = int(datetime.datetime(odf_utc.year,odf_utc.month,odf_utc.day,tzinfo=ins_device_tz).timestamp())
                utcOffset = t0_utc - t0_local
                fileName = 'backendFiles/'+act_subj.username+'_'+date_file
                fileName = fileName+'/'+act_subj.username+'.json'
                
                try:
                    data = read_jsonFile(fileName)
                    if jj==1:
                        timeStampIni = t0_local-6*60*60 # 
                        timeStampEnd = t0_local-1 #
                    else:
                        timeStampIni = t0_local-24*60*60 # 
                        timeStampEnd = t0_local+2*60*60 #
                    sfData_aux = sort_filter_data(data,timeStampIni,timeStampEnd,utcOffset)
                    if jj==0:
                        timeStampIni = int(datetime.datetime(odf_utc.year,odf_utc.month,odf_utc.day,tzinfo=ins_device_tz).timestamp())-24*60*60 # 
                        timeStampEnd = int(datetime.datetime(odf_utc.year,odf_utc.month,odf_utc.day,tzinfo=ins_device_tz).timestamp())-1 #
                        print(timeStampIni)
                        print(timeStampEnd)
                        sfData_prof = sort_filter_data(data,timeStampIni,timeStampEnd,utcOffset)
                        print(sfData_prof)
                        bpData_aux,crData_aux,cfData_aux = extract_profData(sfData_prof,utcOffset)
                        bpData.append([timeStampIni,bpData_aux])
                        crData.append([timeStampIni,crData_aux])
                        cfData.append([timeStampIni,cfData_aux])

                except:
                    sfData_aux = np.array([])
                
                sfData = np.append(sfData,sfData_aux)

            # Extract glucose, meal, and insulin records
            glucoseData   = extract_glucoseData(sfData,utcOffset)
            mealData_ini  = extract_mealData(sfData,utcOffset)
            basalData     = extract_bBolus(sfData,utcOffset,APS_mode)
            bolusData_ini = extract_aBolus(sfData,utcOffset) 
            if len(bolusData_ini[0])!=len(bolusData_ini[1]):
                if len(bolusData_ini[0])>len(bolusData_ini[1]):
                    if (abs(bolusData_ini[1][0]-bolusData_ini[12][0])>1e-1) and (abs(bolusData_ini[2][0]-bolusData_ini[12][0])>1e-1) and (bolusData_ini[9][0]==0) and (bolusData_ini[8][0]!=1):
                        bolusData_ini[0].pop(0)
                        bolusData_ini[12].pop(0)
                    elif (abs(bolusData_ini[1][-1]-bolusData_ini[12][-1])>1e-1) and (abs(bolusData_ini[2][-1]-bolusData_ini[12][-1])>1e-1) and (bolusData_ini[9][-1]==0) and (bolusData_ini[8][-1]!=1):
                        bolusData_ini[0].pop(-1)
                        bolusData_ini[12].pop(-1)
            mealData,bolusData = updateAbBol(mealData_ini,bolusData_ini)       
            insData = merge_ins_lag(bolusData,basalData)

            # Prepare data for pre-processing module
            rawData = {}
            cgm_data = []
            for idx, val in enumerate(glucoseData[0]):
                #cgm_data.append([val+glucoseData[2][idx],glucoseData[1][idx]])
                cgm_data.append([val,glucoseData[1][idx]])

            meal_data = []
            for idx, val in enumerate(mealData[0]):
                meal_data.append([val,mealData[1][idx]])

            basal_data = []
            for idx, val in enumerate(insData[0]):
                basal_data.append([val,insData[1][idx]])

            insulin_data = []
            for idx, val in enumerate(insData[0]):
                insulin_data.append([val,insData[1][idx]+insData[5][idx]+insData[6][idx]]) # Only meal doses

            selected_br_profiles = []
            br_profile = []
            for pp in range(0,len(bpData)):
                br_profile_values_aux = np.array(bpData[pp][1][1])
                br_profile_values_diff = np.diff(br_profile_values_aux)
                ind = np.where(br_profile_values_diff!=0)
                ind = ind+np.ones((1,len(ind)))
                ind = np.insert(ind,0,0)
                ind = ind.astype(int)
                br_profile_times_aux = np.array(bpData[pp][1][0])
                br_profile_times_aux1 = [(time-bpData[pp][0])/60 for time in br_profile_times_aux[np.sort(ind)]]
                br_profile_times = [br_time-np.divmod(br_time,15)[1] for br_time in br_profile_times_aux1]
                br_profile_values = br_profile_values_aux[np.sort(ind)]
                for jj in range(0,len(br_profile_times)):
                    br_profile.append([br_profile_times[jj],br_profile_values[jj]])
                selected_br_profiles.append([bpData[pp][0],br_profile])
                br_profile = []

            selected_cr_profiles = []
            cr_profile = []
            for pp in range(0,len(crData)):
                cr_profile_values_aux = np.array(crData[pp][1][1])
                cr_profile_values_diff = np.diff(cr_profile_values_aux)
                ind = np.where(cr_profile_values_diff!=0)
                ind = ind+np.ones((1,len(ind)))
                ind = np.insert(ind,0,0)
                ind = ind.astype(int)
                cr_profile_times_aux = np.array(crData[pp][1][0])
                cr_profile_times_aux1 = [(time-crData[pp][0])/60 for time in cr_profile_times_aux[np.sort(ind)]]
                cr_profile_times = [cr_time-np.divmod(cr_time,15)[1] for cr_time in cr_profile_times_aux1]
                cr_profile_values = cr_profile_values_aux[np.sort(ind)]
                for jj in range(0,len(cr_profile_times)):
                    if jj==0:
                        cr_profile.append([0,cr_profile_values[jj]])
                    else:
                        cr_profile.append([cr_profile_times[jj],cr_profile_values[jj]])
                selected_cr_profiles.append([crData[pp][0],cr_profile])
                cr_profile = []
            
            selected_cf_profiles = []
            cf_profile = []
            for pp in range(0,len(cfData)):
                cf_profile_values_aux = np.array(cfData[pp][1][1])
                cf_profile_values_diff = np.diff(cf_profile_values_aux)
                ind = np.where(cf_profile_values_diff!=0)
                ind = ind+np.ones((1,len(ind)))
                ind = np.insert(ind,0,0)
                ind = ind.astype(int)
                cf_profile_times_aux = np.array(cfData[pp][1][0])
                cf_profile_times_aux1 = [(time-cfData[pp][0])/60 for time in cf_profile_times_aux[np.sort(ind)]]
                cf_profile_times = [cf_time-np.divmod(cf_time,15)[1] for cf_time in cf_profile_times_aux1]
                cf_profile_values = cf_profile_values_aux[np.sort(ind)]
                for jj in range(0,len(cf_profile_times)):
                    if jj==0:
                        cf_profile.append([0,cf_profile_values[jj]])
                    else:
                        cf_profile.append([cf_profile_times[jj],cf_profile_values[jj]])
                selected_cf_profiles.append([cfData[pp][0],cf_profile])
                cf_profile = []

            # Build dictionary for fetching module
            rawData['cgm_data'] = cgm_data
            rawData['raw_cgm'] = cgm_data
            rawData['selected_br_profiles'] = selected_br_profiles
            rawData['selected_cr_profiles'] = selected_cr_profiles
            rawData['selected_cf_profiles'] = selected_cf_profiles
            rawData['basal_data'] = basal_data
            rawData['insulin_data'] = insulin_data
            rawData['meal_data'] = meal_data
            
            today_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
            t0_utc   = int((today_utc).timestamp())
            t0_pump = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
            t0_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day).timestamp())
            utcOffset_pl = t0_pump - t0_local
            utcOffset_today = t0_utc-t0_local

            endDateTime = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,2,tzinfo=ins_device_tz)
            requestLength = (24+6+2)*60
            requestInterval = 5

            print('bu')
            print(selected_br_profiles)

            procData = preProcessData(rawData,ins_device_tz_str,utcOffset_pl,endDateTime,requestLength,requestInterval,Gb=120,display=False,rawCGM=False)
            
            # Run meal detection algorithm

            procData_aux = {
                'subjInfo': {
                    'Weight': float(act_subj.weight),
                    'TDI': float(act_subj.TDIpop)
                }
            }

            procData.update(procData_aux)

            mealR = MR.mealReconstruction(procData)
            
            np.savetxt('cgmT.txt',procData['cgm'])
            np.savetxt('mealR.txt',mealR[0])
            print(meal_data)
            
            meal = []
            for pp in range(0,len(procData['meal'])):
                meal.append(procData['meal'][pp][1])

            insulinT = []
            for pp in range(0,len(procData['insulin'])):
                insulinT.append(procData['insulin'][pp][1])

            np.savetxt('mealT.txt',meal)
            np.savetxt('insulinT.txt',insulinT)

            print('patri')
            print(bpData)

            br_profile_values_aux = np.array(bpData[0][1][1])
            br_profile_values_diff = np.diff(br_profile_values_aux)
            ind = np.where(br_profile_values_diff!=0)
            ind = ind+np.ones((1,len(ind)))
            ind = np.insert(ind,0,0)
            ind = ind.astype(int)
            br_profile_times_aux = np.array(bpData[0][1][0])
            br_profile_times_aux1 = [(time-bpData[0][0])/60 for time in br_profile_times_aux[np.sort(ind)]]
            br_profile_times = [br_time-np.divmod(br_time,15)[1] for br_time in br_profile_times_aux1]
            br_profile_times1 = br_profile_times_aux[np.sort(ind)]
            br_profile_values = br_profile_values_aux[np.sort(ind)]
            
            cr_profile_values_aux = np.array(crData[0][1][1])
            cr_profile_values_diff = np.diff(cr_profile_values_aux)
            ind = np.where(cr_profile_values_diff!=0)
            ind = ind+np.ones((1,len(ind)))
            ind = np.insert(ind,0,0)
            ind = ind.astype(int)
            cr_profile_times_aux = np.array(crData[0][1][0])
            cr_profile_times_aux1 = [(time-crData[0][0])/60 for time in cr_profile_times_aux[np.sort(ind)]]
            cr_profile_times = [cr_time-np.divmod(cr_time,15)[1] for cr_time in cr_profile_times_aux1]
            cr_profile_times.insert(0,0)
            cr_profile_values = cr_profile_values_aux[np.sort(ind)]
            cr_profile_values = np.insert(cr_profile_values,0,cr_profile_values[0])
            
            cf_profile_values_aux = np.array(cfData[0][1][1])
            cf_profile_values_diff = np.diff(cf_profile_values_aux)
            ind = np.where(cf_profile_values_diff!=0)
            ind = ind+np.ones((1,len(ind)))
            ind = np.insert(ind,0,0)
            ind = ind.astype(int)
            cf_profile_times_aux = np.array(cfData[0][1][0])
            cf_profile_times_aux1 = [(time-cfData[0][0])/60 for time in cf_profile_times_aux[np.sort(ind)]]
            cf_profile_times = [cf_time-np.divmod(cf_time,15)[1] for cf_time in cf_profile_times_aux1]
            cf_profile_times.insert(0,0)
            cf_profile_values = cf_profile_values_aux[np.sort(ind)]
            cf_profile_values = np.insert(cf_profile_values,0,cf_profile_values[0])
            
            mealR[0].shape = (1,len(mealR[0]))
            mealInput = mealR[0]*5/1000
            print(mealInput.tolist())
            np.savetxt('mealB.txt',mealInput)

            t = []
            for pp in range(0,len(procData['meal'])):
                t.append(procData['meal'][pp][0])
            
            subjData = {
                'basalRate': {
                    'time': matlab.double(br_profile_times),
                    'value': matlab.double(br_profile_values.tolist())
                },
                'carbRatio': {
                    'time': matlab.double(cr_profile_times),
                    'value': matlab.double(cr_profile_values.tolist())
                },
                'corrFactor': {
                    'time': matlab.double(cf_profile_times),
                    'value': matlab.double(cf_profile_values.tolist())
                },
                'cgm': {
                    'time': matlab.double(glucoseData[0]),
                    'value': matlab.double(glucoseData[1])
                },
                'bolus': {
                    'time': matlab.double(insData[0]),
                    'value': matlab.double([insData[5][i]+insData[6][i] for i in range(len(insData[0]))])
                },
                'basal': {
                    'time': matlab.double(br_profile_times1.tolist()),
                    'value': matlab.double(br_profile_values.tolist())
                },
                'meal': {
                     'time': matlab.double(t),
                     'value': matlab.double(mealInput[0].tolist())
                },
                'BW': np.array(act_subj.weight,dtype=np.float64).tolist(),
                'BH': np.array(act_subj.height,dtype=np.float64).tolist(),
                'age': np.array(act_subj.age,dtype=np.float64).tolist(),
                'tz': ins_device_tz_str
            }

            print('check')
            print(br_profile_times1)
            print(br_profile_times)
            print(t)
            print(mealInput[0].tolist())
            
            currDir = eng.pwd()
            eng.addpath(currDir+'/basalOptimizer',nargout=0)
            optimBas = eng.optimizeTreatmentDaily_shell('local',subjData)
            optimBas = np.array(optimBas)
            optimBas_shape = optimBas.shape
            if len(optimBas)>0:
                optimBas_nrows = optimBas_shape[0]
                optimBas_ncols = optimBas_shape[1]
            else:
                optimBas_nrows = 0
                optimBas_ncols = 0

            optimBas_dtype = optimBas.dtype.str
            optimBas_data = optimBas.tobytes()

            print('check')
            print(optimBas)

            # Save new parameters
            flagSave = False

            if flagSave:
                try:
                    BasalRateOpt_record = BasalRateOpt(time=today_local,utcOffset=utcOffset_today,optimBas=optimBas_data,
                                        optimBas_dtype=optimBas_dtype,optimBas_nrows=optimBas_nrows,optimBas_ncols=optimBas_ncols,
                                        subject_id=act_subj.id)
                    db.session.add(BasalRateOpt_record)
                    db.session.commit()       
                    app.logger.info('/scheduler. Username: ' +act_subj.username +'. BasalRateOpt records were successfully saved') 

                except exc.SQLAlchemyError as e:
                    db.session.rollback()
                    error = str(e.__dict__['orig'])
                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving BasalRateOpt data: ' +error)

#########################################################################################################################

def weeklyOptimizer():
    
    app.logger.info('/scheduler. The scheduler has been called. Starting to optimize the CR/CF profiles.')

    # Get all active subjects
    attemps = 5
    while attemps>0:
        app.logger.info('/scheduler. Remaining attemps to get active users: '+str(attemps))
        try:
            allActUsers = db.session.query(Subject).filter(Subject.active==1, Subject.username != 'fakeUser').all()
            break
        except exc.SQLAlchemyError as e:
            attemps -=1
            db.session.close()
    
    app.logger.info('/scheduler. # detected active users: '+str(len(allActUsers)))

    cc = 1
    for act_subj in allActUsers:
        app.logger.info('/scheduler. Active user #'+str(cc)+': '+act_subj.username)
        cc+=1

    # Iterate over all active subjects
    for act_subj in allActUsers:
        for ii in range(0,1):
            # Active subject
            app.logger.info('/scheduler. Username: ' + act_subj.username)

            ins_device        = db.session.query(PumpDevice).filter_by(subject_id=act_subj.id).order_by(PumpDevice.id.desc()).first()
            ins_device_tz_str = ins_device.tz
            ins_device_tz     = gettz(ins_device_tz_str)
            APS_mode          = act_subj.apSystem

            local_time_now = datetime.datetime.now()
            today_utc = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc)
            today_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
            t0_utc   = int((today_utc).timestamp())
            t0_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
            utcOffset_today = t0_utc - t0_local

            sfData = np.array([])
            bpData = []
            crData = []
            cfData = []
            pOptimBasM = []

            # Fetch data from previous 7 days
            for jj in range(6,-1,-1):
                odf_utc = today_utc-datetime.timedelta(days=jj)
                date_file = str(odf_utc.year)+'-'+str(odf_utc.month)+'-'+str(odf_utc.day)
                t0_utc   = int(datetime.datetime(odf_utc.year,odf_utc.month,odf_utc.day,tzinfo=datetime.timezone.utc).timestamp())
                t0_local = int(datetime.datetime(odf_utc.year,odf_utc.month,odf_utc.day,tzinfo=ins_device_tz).timestamp())
                utcOffset = t0_utc - t0_local
                fileName = 'backendFiles/'+act_subj.username+'_'+date_file
                fileName = fileName+'/'+act_subj.username+'.json'
                
                try:
                    data = read_jsonFile(fileName)
                    timeStampIni = t0_local-24*60*60 # 
                    timeStampEnd = t0_local-1 #
                    sfData_aux = sort_filter_data(data,timeStampIni,timeStampEnd,utcOffset)

                    bpData_aux,crData_aux,cfData_aux = extract_profData(sfData_aux,utcOffset)
                    bpData.append([timeStampIni,bpData_aux])
                    crData.append([timeStampIni,crData_aux])
                    cfData.append([timeStampIni,cfData_aux])
                except:
                    sfData_aux = np.array([])
                
                BasalRateOpt_records = db.session.query(BasalRateOpt).filter(BasalRateOpt.time == t0_local, BasalRateOpt.subject_id == act_subj.id)
                BasalRateOpt_record = BasalRateOpt_records.first()

                if BasalRateOpt_record is None:
                    pOptimBas = []
                else:
                    pOptimBas_dtype = BasalRateOpt_record.optimBas_dtype
                    pOptimBas_shape = (BasalRateOpt_record.optimBas_ncols,BasalRateOpt_record.optimBas_nrows)
                    pOptimBas = np.copy(np.frombuffer(BasalRateOpt_record.optimBas, dtype=pOptimBas_dtype).reshape(pOptimBas_shape)).tolist()
                    
                    pOptimBasM.append(pOptimBas[0])

                if jj==0:
                    settings = {
                        'ts': 5.0,
                        'dTime': 2.5,
                        'timeStampIni': timeStampIni
                    }
                    bpF_time, bpF_values = fillBP(np.array(bpData_aux[0]),np.array(bpData_aux[1])*1000/60,settings)

                sfData = np.append(sfData,sfData_aux)

            # Extract glucose, meal, and insulin records
            glucoseData          = extract_glucoseData(sfData,utcOffset)
            mealData_ini         = extract_mealData(sfData,utcOffset)
            basalData            = extract_bBolus(sfData,utcOffset,APS_mode)
            bolusData_ini        = extract_aBolus(sfData,utcOffset)  
            mealData,bolusData   = updateAbBol(mealData_ini,bolusData_ini)       
            insData              = merge_ins_lag(bolusData,basalData)

            # Prepare data for fetching module
            rawData = {}
            cgm_data = []
            for idx, val in enumerate(glucoseData[0]):
                cgm_data.append([val+glucoseData[2][idx],glucoseData[1][idx]])

            meal_data = []
            for idx, val in enumerate(mealData[0]):
                meal_data.append([val+mealData[3][idx],mealData[1][idx]])

            basal_data = []
            for idx, val in enumerate(insData[0]):
                basal_data.append([val+insData[3][idx],insData[1][idx]])

            insulin_data = []
            for idx, val in enumerate(insData[0]):
                insulin_data.append([val+insData[3][idx],insData[1][idx]+insData[6][idx]]) # Only meal doses

            selected_br_profiles = []
            br_profile = []
            for pp in range(0,len(bpData)):
                br_profile_values_aux = np.array(bpData[pp][1][1])
                br_profile_values_diff = np.diff(br_profile_values_aux)
                ind = np.where(br_profile_values_diff!=0)
                ind = ind+np.ones((1,len(ind)))
                ind = np.insert(ind,0,0)
                ind = ind.astype(int)
                br_profile_times_aux = np.array(bpData[pp][1][0])
                br_profile_times_aux1 = [(time-bpData[pp][0])/60 for time in br_profile_times_aux[np.sort(ind)]]
                br_profile_times = [br_time-np.divmod(br_time,15)[1] for br_time in br_profile_times_aux1]
                br_profile_values = br_profile_values_aux[np.sort(ind)]
                for jj in range(0,len(br_profile_times)):
                    br_profile.append([br_profile_times[jj],br_profile_values[jj]])
                selected_br_profiles.append([bpData[pp][0],br_profile])
                br_profile = []

            selected_cr_profiles = []
            cr_profile = []
            for pp in range(0,len(crData)):
                cr_profile_values_aux = np.array(crData[pp][1][1])
                cr_profile_values_diff = np.diff(cr_profile_values_aux)
                ind = np.where(cr_profile_values_diff!=0)
                ind = ind+np.ones((1,len(ind)))
                ind = np.insert(ind,0,0)
                ind = ind.astype(int)
                cr_profile_times_aux = np.array(crData[pp][1][0])
                cr_profile_times_aux1 = [(time-crData[pp][0])/60 for time in cr_profile_times_aux[np.sort(ind)]]
                cr_profile_times = [cr_time-np.divmod(cr_time,15)[1] for cr_time in cr_profile_times_aux1]
                cr_profile_values = cr_profile_values_aux[np.sort(ind)]
                for jj in range(0,len(cr_profile_times)):
                    if jj==0:
                        cr_profile.append([0,cr_profile_values[jj]])
                    else:
                        cr_profile.append([cr_profile_times[jj],cr_profile_values[jj]])
                selected_cr_profiles.append([crData[pp][0],cr_profile])
                cr_profile = []
            
            selected_cf_profiles = []
            cf_profile = []
            for pp in range(0,len(cfData)):
                cf_profile_values_aux = np.array(cfData[pp][1][1])
                cf_profile_values_diff = np.diff(cf_profile_values_aux)
                ind = np.where(cf_profile_values_diff!=0)
                ind = ind+np.ones((1,len(ind)))
                ind = np.insert(ind,0,0)
                ind = ind.astype(int)
                cf_profile_times_aux = np.array(cfData[pp][1][0])
                cf_profile_times_aux1 = [(time-cfData[pp][0])/60 for time in cf_profile_times_aux[np.sort(ind)]]
                cf_profile_times = [cf_time-np.divmod(cf_time,15)[1] for cf_time in cf_profile_times_aux1]
                cf_profile_values = cf_profile_values_aux[np.sort(ind)]
                for jj in range(0,len(cf_profile_times)):
                    if jj==0:
                        cf_profile.append([0,cf_profile_values[jj]])
                    else:
                        cf_profile.append([cf_profile_times[jj],cf_profile_values[jj]])
                selected_cf_profiles.append([cfData[pp][0],cf_profile])
                cf_profile = []

            # Build dictionary for fetching module
            rawData['cgm_data'] = cgm_data
            rawData['raw_cgm'] = cgm_data
            rawData['selected_br_profiles'] = selected_br_profiles
            rawData['selected_cr_profiles'] = selected_cr_profiles
            rawData['selected_cf_profiles'] = selected_cf_profiles
            rawData['basal_data'] = basal_data
            rawData['insulin_data'] = insulin_data
            rawData['meal_data'] = meal_data

            endDateTime = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).strftime("%Y-%m-%d %H:%M:%S")
            requestLength = 7*24*60
            requestInterval = 5

            procData = preProcessData(rawData,ins_device_tz_str,endDateTime,requestLength,requestInterval,Gb=120,display=False,rawCGM=False)
            
            # Run meal detection algorithm

            procData_aux = {
                'subjInfo': {
                    'Weight': float(act_subj.weight),
                    'TDI': float(act_subj.TDIpop)
                }
            }
            procData.update(procData_aux)

            mealR = MR.mealReconstruction(procData)            

            # Prepare data for the CR/CF optimizer

            cgm = []
            t = []
            for pp in range(0,len(procData['cgm'])):
                cgm.append(procData['cgm'][pp][1])
                t.append(procData['cgm'][pp][0])
            
            bol = []
            for pp in range(0,len(procData['insulin'])):
                bol.append(procData['insulin'][pp][1]-procData['basal'][pp][1])

            meal = []
            for pp in range(0,len(procData['meal'])):
                meal.append(procData['meal'][pp][1])
            
            tdi = float(act_subj.TDIpop)
            t = np.array(t)
            cgm = np.array(cgm)
            bol = np.array(bol)
            #meal = np.array(meal) # Only bolused meals

            meal = mealR[0]
            
            #Example case
            # with open('data/jsonData_test_1_2.json') as f:
            #     data = json.load(f)

            # t = np.array(data['t'])
            # cgm = np.array(data['cgm'])
            # bol = np.array(data['bolus'])
            # meal = np.array(data['meal'])
            # tdi = data['tdi']

            # Get last record to update, if possible, paramAdapt
            CRCFOpt_lastRecord = db.session.query(CRCFOpt).filter_by(subject_id=act_subj.id).order_by(CRCFOpt.id.desc()).first()

            if CRCFOpt_lastRecord is None:
                paramAdapt = {}
            else:
                paramAdapt = CRCF.getParamAlgov2(tdi)
                mEp_dtype = CRCFOpt_lastRecord.mE_dtype
                mEp_shape = (CRCFOpt_lastRecord.mE_nrows,CRCFOpt_lastRecord.mE_ncols)
                mEp = np.frombuffer(CRCFOpt_lastRecord.mE, dtype=mEp_dtype).reshape(mEp_shape)
                paramAdapt['mE'] = np.copy(mEp)
                #
                sEp_dtype = CRCFOpt_lastRecord.sE_dtype
                sEp_shape = (CRCFOpt_lastRecord.sE_nrows,CRCFOpt_lastRecord.sE_ncols)
                sEp = np.frombuffer(CRCFOpt_lastRecord.sE, dtype=sEp_dtype).reshape(sEp_shape)
                paramAdapt['sE'] = np.copy(sEp)
                #
                mMp_dtype = CRCFOpt_lastRecord.mM_dtype
                mMp_shape = (CRCFOpt_lastRecord.mM_nrows,CRCFOpt_lastRecord.mM_ncols)
                mMp = np.frombuffer(CRCFOpt_lastRecord.mM, dtype=mMp_dtype).reshape(mMp_shape)
                paramAdapt['mM'] = np.copy(mMp)
                #
                sMp_dtype = CRCFOpt_lastRecord.sM_dtype
                sMp_shape = (CRCFOpt_lastRecord.sM_nrows,CRCFOpt_lastRecord.sM_ncols)
                sMp = np.frombuffer(CRCFOpt_lastRecord.sM, dtype=sMp_dtype).reshape(sMp_shape)
                paramAdapt['sM'] = np.copy(sMp)
                #
                mBp_dtype = CRCFOpt_lastRecord.mB_dtype
                mBp_shape = (CRCFOpt_lastRecord.mB_nrows,CRCFOpt_lastRecord.mB_ncols)
                mBp = np.frombuffer(CRCFOpt_lastRecord.mB, dtype=mBp_dtype).reshape(mBp_shape)
                paramAdapt['mB'] = np.copy(mBp)
                #
                sBp_dtype = CRCFOpt_lastRecord.sB_dtype
                sBp_shape = (CRCFOpt_lastRecord.sB_nrows,CRCFOpt_lastRecord.sB_ncols)
                sBp = np.frombuffer(CRCFOpt_lastRecord.sB, dtype=sBp_dtype).reshape(sBp_shape)
                paramAdapt['sB'] = np.copy(sBp)

            # Prepare profiles for CR/CF optimizer
            CRstructList, CFstructList = CRCF.data_preprocessfromABC(procData['profiles']['crProfiles'],procData['profiles']['cfProfiles'])

            paramAdapt = {}
            # Run CR/CF optimizer
            CRoptStruct,CFoptStruct, paramAdapt = CRCF.crcfoptimization(t, cgm, bol, meal, CRstructList, CFstructList, tdi, paramAdapt)

            # Prepare data for database
            mE = paramAdapt['mE']
            mE_dtype = mE.dtype.str
            mE_shape = mE.shape
            mE_nrows = mE_shape[0]
            mE_ncols = mE_shape[1]
            mE_data = mE.tobytes()
            #
            sE = paramAdapt['sE']
            sE_dtype = sE.dtype.str
            sE_shape = sE.shape
            sE_nrows = sE_shape[0]
            sE_ncols = sE_shape[1]
            sE_data = sE.tobytes()
            #
            mM = paramAdapt['mM']
            mM_dtype = mM.dtype.str
            mM_shape = mM.shape
            mM_nrows = mM_shape[0]
            mM_ncols = mM_shape[1]
            mM_data = mM.tobytes()
            #
            sM = paramAdapt['sM']
            sM_dtype = sM.dtype.str
            sM_shape = sM.shape
            sM_nrows = sM_shape[0]
            sM_ncols = sM_shape[1]
            sM_data = sM.tobytes()
            #
            mB = paramAdapt['mB']
            mB_dtype = mB.dtype.str
            mB_shape = mB.shape
            mB_nrows = mB_shape[0]
            mB_ncols = mB_shape[1]
            mB_data = mB.tobytes()
            #
            sB = paramAdapt['sB']
            sB_dtype = sB.dtype.str
            sB_shape = sB.shape
            sB_nrows = sB_shape[0]
            sB_ncols = sB_shape[1]
            sB_data = sB.tobytes()

            # Save new parameters
            flagSave = False

            if flagSave:
                try:
                    CRCFOpt_record = CRCFOpt(time=today_local,utcOffset=utcOffset_today,mE=mE_data,mE_dtype=mE_dtype,mE_nrows=mE_nrows,mE_ncols=mE_ncols,
                                        sE=sE_data,sE_dtype=sE_dtype,sE_nrows=sE_nrows,sE_ncols=sE_ncols,
                                        mM=mM_data,mM_dtype=mM_dtype,mM_nrows=mM_nrows,mM_ncols=mM_ncols,
                                        sM=sM_data,sM_dtype=sM_dtype,sM_nrows=sM_nrows,sM_ncols=sM_ncols,
                                        mB=mB_data,mB_dtype=mB_dtype,mB_nrows=mB_nrows,mB_ncols=mB_ncols,
                                        sB=sB_data,sB_dtype=sB_dtype,sB_nrows=sB_nrows,sB_ncols=sB_ncols,
                                        subject_id=act_subj.id)
                    db.session.add(CRCFOpt_record)
                    db.session.commit()       
                    app.logger.info('/scheduler. Username: ' +act_subj.username +'. CRCFOpt records were successfully saved') 

                except exc.SQLAlchemyError as e:
                    db.session.rollback()
                    error = str(e.__dict__['orig'])
                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving CRCFOpt data: ' +error)

            subjData = {
                'dailyRecBasal': pOptimBasM,
                'profile': {
                    'brProfiles': selected_br_profiles
                },
                'lastBasalPrf': bpF_values
            }
                        
            recBasalProfile = wBROpt.recommendBasalRate(subjData)

            BRoptStruct = {
                'time': recBasalProfile['recBasalProfileTime'],
                'values': recBasalProfile['recBasalProfileValue']
            }

            indCF = 0
            indCR = 0
            indBR = 0

            lenCF = len(CRoptStruct['time'])
            lenCR = len(CFoptStruct['time'])
            lenBR = len(BRoptStruct['time'])

            extVT = np.append(CFoptStruct['time'],CRoptStruct['time'])
            extVT2 = np.append(extVT,BRoptStruct['time'])
            extVT2_aux,ind = np.unique(extVT2,return_index=True) 

            optProfLen = len(extVT2_aux)
            optProfV = np.zeros((3,optProfLen))
            optProfT = np.zeros((1,optProfLen))

            optProfT[0,0] = 0
            optProfV[0,0] = CFoptStruct['values'][0]
            optProfV[1,0] = CRoptStruct['values'][0]
            optProfV[2,0] = BRoptStruct['values'][0]

            for ll in range(0,len(extVT2_aux)):
                optProfT[0,ll] = extVT2_aux[ll]
                if ll>0:
                    if optProfT[0,ll]>=CFoptStruct['time'][min(indCF+1,lenCF-1)]:
                        indCF = min(indCF+1,lenCF-1)
                    if optProfT[0,ll]>=CRoptStruct['time'][min(indCR+1,lenCR-1)]:
                        indCR = min(indCR+1,lenCR-1)
                    if optProfT[0,ll]>=BRoptStruct['time'][min(indBR+1,lenBR-1)]:
                        indBR = min(indBR+1,lenBR-1)

                    optProfV[0,ll] = CFoptStruct['values'][indCF]
                    optProfV[1,ll] = CRoptStruct['values'][indCR]
                    optProfV[2,ll] = BRoptStruct['values'][indBR]
            
            # Send email with new profiles
            flagSendEmail = False

            if flagSendEmail:
                # msg = Message('Password Reset Request', 
                #     recipients=[act_subj.email])
                msg = Message('New profiles', 
                    recipients=['phcolmegna@gmail.com']) # For testing purposes
                msg_part1 = "These are the new recommended profiles. Please change settings on your pump"                
                msg_part2a = 'Ti: ' +np.array_str(optProfT[0]/60) + ' [h]'
                msg_part2b = 'CF: ' +np.array_str(optProfV[0]) + '  [mg/dl/U]'
                msg_part2c = 'CR: ' +np.array_str(optProfV[1]) + '  [g/U]'
                msg_part2d = 'BR: ' +np.array_str(optProfV[2]) + '  [U/h]'

                msg.html = msg_part1+'<br><br>'+msg_part2a+'<br>'+msg_part2b+'<br>'+msg_part2c+'<br>'+msg_part2d

                try:
                    mail.send(msg)

                    app.logger.info('/scheduler/send_email. Username: ' +act_subj.username +'. The message has been successfully sent')
                except Exception:
                    error_message = traceback.format_exc()
                    app.logger.error('/scheduler/send_email. Username: ' +act_subj.username +'. An error has occurred when delivering the email. Error_message = ' + error_message)

#########################################################################################################################

def estimateA1c_wrapper():

    app.logger.info('/scheduler. The scheduler has been called. Starting to estimate A1c.')

    # Get all active subjects
    attemps = 5
    while attemps>0:
        app.logger.info('/scheduler. Remaining attemps to get active users: '+str(attemps))
        try:
            allActUsers = db.session.query(Subject).filter(Subject.active==1, Subject.username != 'fakeUser').all()
            break
        except exc.SQLAlchemyError as e:
            attemps -=1
            db.session.close()
    
    app.logger.info('/scheduler. # detected active users: '+str(len(allActUsers)))

    cc = 1
    for act_subj in allActUsers:
        app.logger.info('/scheduler. Active user #'+str(cc)+': '+act_subj.username)
        cc+=1

    # Iterate over all active subjects
    for act_subj in allActUsers:
        for ii in range(0,1):
            # Active subject
            app.logger.info('/scheduler. Username: ' + act_subj.username)

            # Get tz from insulin pump
            ins_device        = db.session.query(PumpDevice).filter_by(subject_id=act_subj.id).order_by(PumpDevice.id.desc()).first()
            ins_device_tz_str = ins_device.tz
            ins_device_tz     = gettz(ins_device_tz_str)

            local_time_now = datetime.datetime.now()

            today_utc = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc)
            yest_utc = today_utc-datetime.timedelta(days=1)

            #########################################################
            # Fetch data from Tandem server
            #########################################################

            # Get model and serial numbers
            insdev_key = os.environ.get('INSDEV_KEY')
            f = Fernet(insdev_key)
            
            modelNumber_decrypted  = f.decrypt(ins_device.modelNumber.encode())
            serialNumber_decrypted = f.decrypt(ins_device.serialNumber.encode())
            
            modelNumber  = modelNumber_decrypted.decode()
            serialNumber = serialNumber_decrypted.decode()

            # Study start date
            #date_file = str(yest_utc.year)+'-'+str(yest_utc.month)+'-'+str(yest_utc.day)
            date_file = str(today_utc.year)+'-'+str(today_utc.month)+'-'+str(today_utc.day)

            # Zip file
            zipName = 'backendFiles/'+act_subj.username+'_'+date_file
            zipName = zipName+'/'+act_subj.username+'.json'

            try:
                data = read_jsonFile(zipName)
            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when reading the JSON file. Stoping process...')
                break
            
            t0_utc   = int((today_utc).timestamp())
            t0_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
            utcOffset = t0_utc - t0_local

            app.logger.info('/scheduler. Username: ' + act_subj.username + '. utcOffset: ' + str(utcOffset))

            timeStampIni = t0_local-24*60*60 # Yesterday
            timeStampEnd = t0_local-1 # Today

            app.logger.info('/scheduler. Username: ' + act_subj.username + '. tIni_local: ' + str(timeStampIni) + '; tEnd_local: ' + str(timeStampEnd))
            app.logger.info('/scheduler. Username: ' + act_subj.username + '. d1 = ' + datetime.datetime.utcfromtimestamp(t0_utc-24*60*60).strftime("%m/%d/%y") + 
            '; d2 = ' + datetime.datetime.utcfromtimestamp(t0_utc).strftime("%m/%d/%y"))
            
            # Read JSON data
            try:
                data = read_jsonFile(zipName)
            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when reading the JSON file. Stoping process...')
                break
            
            # Sort and filter data between yesterday and today
            try:
                sfData = sort_filter_data(data,timeStampIni,timeStampEnd,utcOffset)
            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when processing the JSON file. Probably, no data available within selected date range. Stoping process...')
                break
            
            glucoseData = extract_glucoseData(sfData,utcOffset)

            cgm_time = np.array(glucoseData[0])
            cgm_values = np.array(glucoseData[1])

            eA1c_records = db.session.query(EA1c).filter(EA1c.time == timeStampIni,EA1c.subject_id == act_subj.id)
            eA1c_record = eA1c_records.first()

            if eA1c_record is None:
                eA1cPrev = -1
                muTIRprev = -1
                gamma = 1
            else:
                eA1cPrev = getattr(eA1c_record,'eA1c')
                eA1cPrev_d1 = getattr(eA1c_record,'eA1cPrev_d1')
                eA1cPrev_d2 = getattr(eA1c_record,'eA1cPrev_d2')
                eA1cPrev_d3 = getattr(eA1c_record,'eA1cPrev_d3')
                eA1cPrev_d4 = getattr(eA1c_record,'eA1cPrev_d4')
                eA1cPrev_d5 = getattr(eA1c_record,'eA1cPrev_d5')
                eA1cPrev_d6 = getattr(eA1c_record,'eA1cPrev_d6')
                muTIRprev = getattr(eA1c_record,'muTIR')
                gamma = getattr(eA1c_record,'gamma')

            eA1c_output = estimateA1c(cgm_time,cgm_values,eA1cPrev,muTIRprev,gamma,timeStampIni,timeStampEnd)
            eA1c = eA1c_output[0]
            muTIR = eA1c_output[1]

            print(eA1c_output)

            if eA1cPrev==-1:
                eA1cPrev = eA1c
                eA1cPrev_d1 = eA1c
                eA1cPrev_d2 = eA1c
                eA1cPrev_d3 = eA1c
                eA1cPrev_d4 = eA1c
                eA1cPrev_d5 = eA1c
                eA1cPrev_d6 = eA1c

            arrow_index = estimateA1cROC([eA1cPrev_d6,eA1cPrev_d5,eA1cPrev_d4,eA1cPrev_d3,eA1cPrev_d2,eA1cPrev_d1,eA1cPrev])

            flagSave = True
            if flagSave:
                try:
                    eA1c_newRecord = EA1c()
                    setattr(eA1c_newRecord,'time',t0_local)
                    setattr(eA1c_newRecord,'utcoffset',int(utcOffset))
                    setattr(eA1c_newRecord,'eA1c',eA1c)
                    setattr(eA1c_newRecord,'eA1cPrev_d1',eA1cPrev)
                    setattr(eA1c_newRecord,'eA1cPrev_d2',eA1cPrev_d1)
                    setattr(eA1c_newRecord,'eA1cPrev_d3',eA1cPrev_d2)
                    setattr(eA1c_newRecord,'eA1cPrev_d4',eA1cPrev_d3)
                    setattr(eA1c_newRecord,'eA1cPrev_d5',eA1cPrev_d4)
                    setattr(eA1c_newRecord,'eA1cPrev_d6',eA1cPrev_d5)
                    setattr(eA1c_newRecord,'muTIR',muTIR)
                    setattr(eA1c_newRecord,'gamma',gamma)
                    setattr(eA1c_newRecord,'arrow',arrow_index)
                    setattr(eA1c_newRecord,'subject_id',act_subj.id)
                    db.session.add(eA1c_newRecord)
                    db.session.commit()
                    app.logger.info('/scheduler. Username: ' +act_subj.username +'. eA1c parameters were successfully saved')    

                except exc.SQLAlchemyError as e:
                    db.session.rollback()
                    error = str(e.__dict__['orig'])
                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving eA1c data: ' +error)

#########################################################################################################################

def VIP():

    app.logger.info('/scheduler. The scheduler has been called. Starting to pull out data from Tandem server.')

    # Get all active subjects
    attemps = 5
    while attemps>0:
        app.logger.info('/scheduler. Remaining attemps to get active users: '+str(attemps))
        try:
            allActUsers = db.session.query(Subject).filter(Subject.active==1, Subject.username != 'fakeUser').all()
            break
        except exc.SQLAlchemyError as e:
            attemps -=1
            db.session.close()
    
    app.logger.info('/scheduler. # detected active users: '+str(len(allActUsers)))

    cc = 1
    for act_subj in allActUsers:
        app.logger.info('/scheduler. Active user #'+str(cc)+': '+act_subj.username)
        cc+=1

    # Iterate over all active subjects
    for act_subj in allActUsers:
        for ii in range(0,1):
            # Active subject
            app.logger.info('/scheduler. Username: ' + act_subj.username)

            # Get tz from insulin pump
            ins_device        = db.session.query(PumpDevice).filter_by(subject_id=act_subj.id).order_by(PumpDevice.id.desc()).first()
            ins_device_tz_str = ins_device.tz
            ins_device_tz     = gettz(ins_device_tz_str)
            insDur            = ins_device.ins_dur

            local_time_now = datetime.datetime.now()

            t0_utc   = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc).timestamp())
            t0_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
            utcOffset = t0_utc - t0_local
            
            g = db.session.query(CGM).filter_by(cgm_device_subject_id=act_subj.id).order_by(CGM.id.desc()).first()

            if g is not None:
                utcOffsetPrev = g.utcOffset
            else:
                utcOffsetPrev = utcOffset
            
            utcOffsetDiff = utcOffset-utcOffsetPrev

            app.logger.info('/scheduler. Username: ' + act_subj.username + '. utcOffset: ' + str(utcOffset))
            app.logger.info('/scheduler. Username: ' + act_subj.username + '. utcOffsetPrev: ' + str(utcOffsetPrev))
            app.logger.info('/scheduler. Username: ' + act_subj.username + '. utcOffsetDiff: ' + str(utcOffsetDiff))

            #########################################################
            # Fetch data from Tandem server
            #########################################################

            # Get model and serial numbers
            # insdev_key = os.environ.get('INSDEV_KEY')
            # f = Fernet(insdev_key)
            
            # modelNumber_decrypted  = f.decrypt(ins_device.modelNumber.encode())
            # serialNumber_decrypted = f.decrypt(ins_device.serialNumber.encode())
            
            # modelNumber  = modelNumber_decrypted.decode()
            # serialNumber = serialNumber_decrypted.decode()

            # Study start date
            today_utc = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc)
            today_local = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day)
            yest_utc = today_utc-datetime.timedelta(days=1)
            
            studyStartDate = str(yest_utc.year)+'-'+str(yest_utc.month)+'-'+str(yest_utc.day)
            studyEndDate = str(today_utc.year)+'-'+str(today_utc.month)+'-'+str(today_utc.day)
            date_file = str(today_local.year)+'-'+str(today_local.month)+'-'+str(today_local.day)

            # studyStartDate = '2021-01-26'
            # studyEndDate = '2021-01-27'
            # date_file = '2021-01-27'
            
            # Zip file
            zipName = 'backendFiles/'+act_subj.username+'_'+date_file
            
            # Tandem credentials
            # tandem_username = os.environ.get('TANDEM_USERNAME')
            # tandem_password = os.environ.get('TANDEM_PASSWORD')

            # Get access token
            # payload = {'grant_type': 'password', 'username': tandem_username, 'password': tandem_password, 'scope': 'cloud.upload cloud.account cloud.password'}
            # headers = {'Content-Type': 'application/x-www-form-urlencoded','x-api-version': '1','Authorization': 'Basic ODIwNTNkNmItZjA0YS00ZmRlLTgzMWEtNWIxNGJkODUyNDI1OmxpIzVBQSRmaV40UnlXMSElYm1m'}
            # url     = 'https://tdcservices.tandemdiabetes.com/cloud/oauth2/token'

            # ii = 1
            # flagWhile = True

            # while (flagWhile) and (ii<10):
            #     r = requests.post(url,headers=headers,data=payload)
            #     if r.status_code==200:
            #         flagWhile = False
            #     app.logger.info('/scheduler. Username: ' + act_subj.username + '. Attemp to get token: '+str(ii)+'; status code: ' +str(r.status_code))
            #     ii+=1
            
            # if r.status_code==200:
            #     try:
            #         r_json = r.json()
            #         accessToken = r_json['accessToken']
            #     except:
            #         app.logger.error('/scheduler. Username: ' +act_subj.username +'. No token was available. Stoping process...')
            #         break
            # else:
            #     app.logger.error('/scheduler. Username: ' +act_subj.username +'. No token was available. Stoping process...')
            #     break

            # Get JSON data
            # payload = {'format': 'json','studyStartDate': studyStartDate,'studyEndDate': studyEndDate}
            # headers = {'x-api-version': '1','Authorization': 'Bearer ' +accessToken}
            # url     = 'https://tdcservices.tandemdiabetes.com/cloud/uploadretrieval/api/bulkdownload/'+modelNumber+'/'+serialNumber

            # ii = 1
            # flagWhile = True

            # flagFetch = True

            # if flagFetch:
            #     while (flagWhile) and (ii<10):
            #         r = requests.get(url,headers=headers,params=payload,stream=True)
                    
            #         if r.status_code==200:
            #             flagWhile = False
            #         app.logger.info('/scheduler. Username: ' + act_subj.username + '. Attemp to get JSON data: '+str(ii)+'; status code: ' +str(r.status_code))
            #         ii+=1

            #     if r.status_code==200:
            #         try:
            #             with open(zipName+'.zip','wb') as f:
            #                 f.write(r.content)

            #             with zipfile.ZipFile(zipName+'.zip','r') as my_zip:
            #                 my_zip.extractall(zipName)
            #                 filename_old = os.path.join("backendFiles/"+act_subj.username+"_"+date_file,modelNumber+str('-')+serialNumber+'.json')
            #                 filename_new = os.path.join("backendFiles/"+act_subj.username+"_"+date_file,act_subj.username+'.json')
            #                 if not os.path.exists(filename_new):
            #                     os.rename(filename_old,filename_new)
            #                 else:
            #                     os.remove(filename_new)
            #                     os.rename(filename_old,filename_new)
            #         except:
            #             app.logger.error('/scheduler. Username: ' +act_subj.username +'. No data was available. Stoping process...')
            #             break
            #     else:
            #         app.logger.error('/scheduler. Username: ' +act_subj.username +'. No data was available. Stoping process...')
            #         break
            
            #########################################################
            # Extract JSON data
            #########################################################

            zipName = zipName+'/'+act_subj.username+'.json'
            
            # Define settings for array processing
            settings = {
                'ts': 5.0,
                'dTime': 2.5,
                'minV': 40.0,
                'maxV': 400.0
            }

            # Define settings for meal detection
            md_settings = {
                'popMealSize': 50,
                'popTreatSize': 7,
                'mealPeak': 0.0075,
                'treatPeak': 0.03,
                'gDevThr': 40,
                'gTreatThr': 90,
                'peakProm': 0.0025,
                'peakMDist': 6
            }

            # timeStampIni = int(datetime.datetime(2021,1,26,tzinfo=ins_device_tz).timestamp())
            # timeStampEnd = timeStampIni+24*60*60-1

            timeStampIni = t0_local-24*60*60 # Yesterday
            timeStampEnd = t0_local-1 # Today

            app.logger.info('/scheduler. Username: ' + act_subj.username + '. tIni_local: ' + str(timeStampIni) + '; tEnd_local: ' + str(timeStampEnd))
            app.logger.info('/scheduler. Username: ' + act_subj.username + '. d1 = ' + datetime.datetime.utcfromtimestamp(t0_utc-24*60*60).strftime("%m/%d/%y") + 
            '; d2 = ' + datetime.datetime.utcfromtimestamp(t0_utc).strftime("%m/%d/%y"))
            
            settings['timeStampIni'] = timeStampIni

            # Read JSON data
            try:
                data = read_jsonFile(zipName)
            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when reading the JSON file. Stoping process...')
                break

            # Determine what APS has been installed on pump
            flagBIQ,flagCIQ = determine_APSMode(data)
            
            if (flagBIQ) and (flagCIQ):
                APS_mode = -1 # Unknown
            elif flagCIQ:
                APS_mode = 2 # CIQ
            elif flagBIQ:
                APS_mode = 1 # BIQ
            else:
                APS_mode = 0 # OL
            
            app.logger.info('/scheduler. Username: ' + act_subj.username + '. flagBIQ: '+str(flagBIQ)+'; flagCIQ: '+str(flagCIQ)+'; APS_mode: '+str(APS_mode))
            
            # If APS_mode is unknown, stop the process
            if APS_mode==-1:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. APS_mode=-1 (Unknown). Stoping process...')
                break
            
            # Sort and filter data between yesterday and today
            try:
                sfData = sort_filter_data(data,timeStampIni,timeStampEnd,utcOffset)
            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when processing the JSON file. Probably, no data available within selected date range. Stoping process...')
                break

            # Extract data from JSON file
            try:
                glucoseData          = extract_glucoseData(sfData,utcOffset)
                bpData,crData,cfData = extract_profData(sfData,utcOffset)
                mealData_ini         = extract_mealData(sfData,utcOffset)
                basalData            = extract_bBolus(sfData,utcOffset,APS_mode)
                bolusData_ini        = extract_aBolus(sfData,utcOffset)  

            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when extracting data. Stoping process...')
                break

            #########################################################
            # Process JSON data
            #########################################################

            ############ GLUCOSE DATA #############
            try:
                # Generate list of cgm data
                cgm_data = []
                cgm_data.extend([glucoseData[1],glucoseData[2],glucoseData[3],glucoseData[4],glucoseData[5]]) 
                # (values,utcOffset,cal,trend,status)

                # Process glucose data
                cgmP_time, cgmP_data, cgmP_gaps = dataProcessing(glucoseData[0],cgm_data,settings)
                cgmP_values    = cgmP_data[0]
                cgmP_utcOffset = cgmP_data[1]
                cgmP_cal       = cgmP_data[2]
                cgmP_trend     = cgmP_data[3]
                cgmP_status    = cgmP_data[4]

                # Fill gaps and calibrate ala Control-IQ
                cgmF_time,cgmF_cal                   = fillZero(cgmP_time,cgmP_cal,settings)
                cgmF_time_nu,ucgm_values,cgmF_values = fillLinCal(cgmP_time,cgmP_values,cgmF_cal,settings)
                cgmF_time_nu, cgmF_utcOffset         = fillPrev(cgmP_time,cgmP_utcOffset,settings)
                cgmF_time_nu, cgmF_trend             = fillPrev(cgmP_time,cgmP_trend,settings)
                cgmF_time_nu, cgmF_status            = fillPrev(cgmP_time,cgmP_status,settings)

                app.logger.info('/scheduler. Username: ' +act_subj.username +'. Glucose data have been successfully processed.')

            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when processing the glucose data. Stoping DP process...')
                break
            
            mealData,bolusData   = updateAbBol(mealData_ini,bolusData_ini,cgmF_time,cgmF_values)       
            insData              = merge_ins_lag(bolusData,basalData)

            ############ INSULIN DATA #############
            try:
                # Generate list of insulin data
                ins_data = []
                ins_data.extend([insData[1],insData[2],insData[3],insData[4],insData[5],insData[6],insData[7],insData[8],insData[9],
                                insData[10],insData[11],insData[12],insData[13],insData[14],insData[15],insData[16]])
                # (basal, TR, utcOffset, PCM, bCorr, bMeal, corrDecl, carbs, smbg, target, bType, userOv, extB, extBP, extBD, lagB)

                # Process insulin data
                insP_time, insP_data, insP_gaps = dataProcessing(insData[0],ins_data,settings)
                
                # Fill gaps
                insF_time, insF_basal        = fillPrev(insP_time,insP_data[0],settings)
                insF_time_nu, insF_tempR     = fillPrev(insP_time,insP_data[1],settings)
                insF_time_nu, insF_utcOffset = fillPrev(insP_time,insP_data[2],settings)
                insF_time_nu, insF_mode      = fillPrev(insP_time,insP_data[3],settings)
                insF_time_nu, insF_corr      = fillZero(insP_time,insP_data[4],settings)
                insF_time_nu, insF_meal      = fillZero(insP_time,insP_data[5],settings)
                insF_time_nu, insF_corrDecl  = fillZero(insP_time,insP_data[6],settings)
                insF_time_nu, insF_cho       = fillZero(insP_time,insP_data[7],settings)
                insF_time_nu, insF_smbg      = fillZero(insP_time,insP_data[8],settings)
                insF_time_nu, insF_target    = fillPrev(insP_time,insP_data[9],settings)
                insF_time_nu, insF_BT        = fillZero(insP_time,insP_data[10],settings)
                insF_time_nu, insF_userOv    = fillZero(insP_time,insP_data[11],settings)
                insF_time_nu, insF_extB      = fillZero(insP_time,insP_data[12],settings)
                insF_time_nu, insF_extBP     = fillZero(insP_time,insP_data[13],settings)
                insF_time_nu, insF_extBD     = fillZero(insP_time,insP_data[14],settings)
                insF_time_nu, insF_lagB      = fillZero(insP_time,insP_data[15],settings)
                
                app.logger.info('/scheduler. Username: ' +act_subj.username +'. Insulin data have been successfully processed.')

            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when processing the insulin data. Stoping DP process...')
                break

            ############ TP DATA #############
            try:
                # Process bp values
                # Process cf values
                # Process cr values

                bpP_time, bpP_values, bpP_gaps = dataProcessing(bpData[0],bpData[1],settings)
                cfP_time, cfP_values, cfP_gaps = dataProcessing(cfData[0],cfData[1],settings)
                crP_time, crP_values, crP_gaps = dataProcessing(crData[0],crData[1],settings)

                # Update settings
                settings['ts'] = 30
                settings['dTime'] = 15

                bpF_time, bpF_values = fillBP(np.array(bpData[0]),np.array(bpData[1]),settings)
                cfF_time, cfF_values = fillPrev(np.array(cfData[0]),np.array(cfData[1]),settings)
                crF_time, crF_values = fillPrev(np.array(crData[0]),np.array(crData[1]),settings)

                app.logger.info('/scheduler. Username: ' +act_subj.username +'. TP data have been successfully processed.')

            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when processing the TP data. Stoping DP process...')
                break
            
            ############ MEAL DATA #############
            try:
                # Process meal data
                meal_data = []
                meal_data.extend([mealData[1],mealData[2],mealData[3]])
                # (size, isRescue, utcOffset)

                # Update settings
                settings['ts'] = 5
                settings['dTime'] = 2.5

                mealP_time, mealP_data = mealProcessing(mealData[0],meal_data,settings)
                
                mealP_carbs     = 1000.0*mealP_data[0] # g 2 mg
                mealP_isRescue  = mealP_data[1]
                mealP_utcOffset = mealP_data[2]
                app.logger.info('/scheduler. Username: ' +act_subj.username +'. Meal data have been successfully processed.')
        
            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when processing the meal data. Stoping DP process...')
                break

            #########################################################
            # Determine ins mod
            #########################################################

            try:
                apSel,count_ins_mod = determine_insMode(insP_data[3])
                app.logger.info('/scheduler. Username: ' +act_subj.username +'. Ins mode: ' +str(apSel)+'. count_ins_mod: ' +str(count_ins_mod))
            
            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when determining the insulin mode. Stoping DP process...')
                break

            #########################################################
            # AP data
            #########################################################

            if apSel == 1:
                
                try:
                    biqData = extract_biqData(sfData,utcOffset)
                
                except:
                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when fetching the Basal-IQ data. Stoping DP process...')
                    break
                
                try:
                    if len(biqData[0])>0:

                        # Generate list of Basal-IQ data
                        biq_data = []
                        biq_data.extend([biqData[1],biqData[2]])
                        # (utcOffset, insSusp)

                        # Process Basal-IQ data
                        biqP_time, biqP_data, biqP_gaps = dataProcessing(biqData[0],biq_data,settings)
                        
                        # Fill gaps
                        biqF_time_nu, biqF_utcOffset = fillPrev(biqP_time,biqP_data[0],settings)
                        biqF_time, biqF_insSusp      = fillZero(biqP_time,biqP_data[1],settings)
                        
                    else:
                        t0 = settings['timeStampIni']
                        biqF_time      = np.arange(t0,t0+1440*60,settings['ts']*60)
                        biqF_utcOffset = np.array([utcOffset]*len(biqF_time)) 
                        biqF_insSusp   = np.zeros(biqF_time.shape)

                    app.logger.info('/scheduler. Username: ' +act_subj.username +'. Basal-IQ data have been successfully processed.')

                except:
                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when processing the Basal-IQ data. Stoping DP process...')
                    break
            
            elif apSel == 2: # ControlIQ

                try:
                    ciqData = extract_ciqData(sfData,utcOffset,act_subj.TDIpop)
                    app.logger.info('/scheduler. Username: ' +act_subj.username +'. Control-IQ data have been successfully fetched.')

                except:
                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when fetching the Control-IQ data. Stoping DP process...')
                    break
                
                try:
                    if len(ciqData[0])>0:
                        # Generate list of Control-IQ data
                        ciq_data = []
                        ciq_data.extend([ciqData[1],ciqData[2],ciqData[3],ciqData[4]])
                        # (utcOffset, TDIpop, TGT, sleep)

                        # Process Control-IQ data
                        ciqP_time, ciqP_data, ciqP_gaps = dataProcessing(ciqData[0],ciq_data,settings)
                        
                        # Fill gaps
                        ciqF_time, ciqF_utcOffset = fillPrev(ciqP_time,ciqP_data[0],settings)
                        ciqF_time_nu, ciqF_TDIpop = fillPrev(ciqP_time,ciqP_data[1],settings)
                        ciqF_time_nu, ciqF_TGT    = fillPrev(ciqP_time,ciqP_data[2],settings)
                        ciqF_time_nu, ciqF_sleep  = fillPrev(ciqP_time,ciqP_data[3],settings)
                    
                        ciqF_EX = extract_ciqData_ex(data,ciqF_time,utcOffset)

                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. Control-IQ data have been successfully processed.')

                    else:
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. No Control-IQ data. Stoping DP process...')
                        break

                except:
                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when processing the Control-IQ data. Stoping DP process...')
                    break
            
            #########################################################
            # Data classification
            #########################################################

            try:
                cgmGaps = cgmP_gaps
                insGaps = insP_gaps
                thGaps  = bpP_gaps

                dataStatus = dataClassifier(cgmGaps,insGaps,mealP_carbs,bpF_values,cfF_values,crF_values,apSel,count_ins_mod,APS_mode)

                # Generate array of column names
                tmtiV = [a for a in dir(BasalProfile) if a.startswith('tmti')]
                tmtiV.sort(key=len)

                if len(cfF_values)==0:
                    cfF_values_aux = []
                    try:
                        CFP = db.session.query(CFProfile).filter(CFProfile.timeini >= timeStampIni-36*60*60, CFProfile.timeini < timeStampIni,
                                            CFProfile.subject_id == act_subj.id).order_by(CFProfile.id.desc()).first()
                        for i in range(0,len(tmtiV)):
                            value = getattr(CFP,tmtiV[i])
                            cfF_values_aux.append(float(value))
                        cfF_values = np.array(cfF_values_aux)
                    except:
                        cfPop = act_subj.CFpop
                        cfF_values = np.array([float(cfPop)]*48)
                
                if len(crF_values)==0:
                    crF_values_aux = []
                    try:
                        CRP = db.session.query(CRProfile).filter(CRProfile.timeini >= timeStampIni-36*60*60, CRProfile.timeini < timeStampIni,
                                            CRProfile.subject_id == act_subj.id).order_by(CRProfile.id.desc()).first()
                        for i in range(0,len(tmtiV)):
                            value = getattr(CRP,tmtiV[i])
                            crF_values_aux.append(float(value))
                        crF_values = np.array(crF_values_aux)
                    except:
                        crPop = act_subj.CRpop
                        crF_values = np.array([float(crPop)]*48)

                app.logger.info('/scheduler. Username: ' +act_subj.username +'. Data status: ' +str(dataStatus))
            
            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when classifying the day. Stoping DP process...')
                break

            #########################################################
            # Meal detection
            #########################################################
            
            # Get previous meal records and compute mean size excluding rescue carbs
            prevNDays = 150
            try:
                prev_meals = db.session.query(Meal).filter(Meal.time >= timeStampIni+utcOffsetDiff-60*60*24*prevNDays, Meal.time < timeStampIni,
                                    Meal.subject_id == act_subj.id) 
            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the meal table')
            
            try:
                perMealSize = compute_perMealSize(prev_meals,float(act_subj.weight))
            
            except:
                perMealSize = 0.7*float(act_subj.weight)
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when computing the personalized meal size. 0.7g/kg is used instead')

            app.logger.info('/scheduler. Username: ' +act_subj.username +'. perMealSize: ' +str(perMealSize))

            try:
                # Run meal detector
                md_settings['popMealSize'] = perMealSize

                mealP_carbs_g = [i/1000.0 for i in mealP_carbs]
                mealP_tod = []
                for ii in range(0,len(mealP_time)):
                    m_hour = float(datetime.datetime.fromtimestamp(mealP_time[ii]+mealP_utcOffset[ii],tz=datetime.timezone.utc).strftime('%H'))
                    m_min = float(datetime.datetime.fromtimestamp(mealP_time[ii]+mealP_utcOffset[ii],tz=datetime.timezone.utc).strftime('%M'))
                    if (m_hour==0) and (m_min==0):
                        if (timeStampIni<mealP_time[ii]):
                            mealP_tod.extend([1435])
                        else:
                            mealP_tod.extend([m_hour*60+m_min])
                    else:
                        mealP_tod.extend([m_hour*60+m_min])

                rMeals,rTreats = mealDetection(mealP_carbs_g,mealP_tod,cgmF_values,md_settings)
                
                if len(rMeals[0])>0:
                    app.logger.info('/scheduler. Username: ' +act_subj.username +'. Meals -> Time: ' +str(rMeals[0,:])+'. Size: ' +str(rMeals[1,:]))
                else:
                    app.logger.info('/scheduler. Username: ' +act_subj.username +'. No meal detected')
                
                if len(rTreats[0])>0:
                    app.logger.info('/scheduler. Username: ' +act_subj.username +'. Treats -> Time: ' +str(rTreats[0,:])+'. Size: ' +str(rTreats[1,:]))
                else:
                    app.logger.info('/scheduler. Username: ' +act_subj.username +'. No rescue detected')

            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when running the meal detector. Stoping DP process...')
                break
            
            try:
                mealTime,mealUtcOffset,mealSize,mealRFlag = generate_mealSignal_DB(rMeals,rTreats,timeStampIni,utcOffset)
                app.logger.info('/scheduler. Username: ' +act_subj.username +'. The meal DB signal has been successfully generated.')

            except:
                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when generating the meal DB signal. Stoping DP process...')
                break

            #########################################################
            # Flags for DB
            #########################################################

            flagSave = False
            flagModelPar = True
            flagGlucose = True
            flagTH = True
            flagMeals = True
            flagIns = True
            flagAPS = True

            #########################################################
            # Avatars 
            #########################################################

            if dataStatus==100:

                #########################################################
                # Generate avatars 
                #########################################################

                flagOptimization = True

                #########################################################
                # Data for avatars 
                #########################################################
                try:
                    
                    ############ Insulin ############

                    insBolus_comb   = np.array(insF_corr)+np.array(insF_meal)
                    insBolus_matlab = adjExtDose4Matlab(insBolus_comb,bolusData)                
                    
                    insulin = np.array(insF_basal)/5+insBolus_matlab/5
                    basal   = np.array(insF_basal)/5

                    ############ Meals ############
                    ht = [0.0]*288
                    m = [0.0]*288

                    if len(rTreats[0])>0:
                        for ii in range(0,len(rTreats[0])):
                            ht[int(np.fix(rTreats[0,ii]/5))] = rTreats[1,ii]
                        HTimer = int(np.fix(1440-rTreats[0,len(rTreats[0])-1])/5)
                    else:
                        HTimer = 288
                    
                    for ii in range(0,len(rMeals[0])):
                        m[int(np.fix(rMeals[0,ii]/5))] = rMeals[1,ii]

                    meal = (1000/5)*np.array(ht)+(1000/5)*np.array(m)

                    ############ Corr timer ############
                    corr_ind = np.argwhere(np.array(insF_corr))
                    if len(corr_ind)>0:
                        corrTimer = int(288-corr_ind[len(corr_ind)-1][0])
                    else:
                        corrTimer = 288

                    ############ Model parameters ############
                    # Get model parameters from previous day (if any)
                    try:
                        modelPar_previousD = db.session.query(ModelParameters).filter(ModelParameters.timeini >= timeStampIni+utcOffsetDiff-60*60*24, ModelParameters.timeini < timeStampIni,
                                                                                    ModelParameters.subject_id == act_subj.id)
                    except:
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the model_parameters table - Previous day')

                    # Generate array of column names for ModelParameters
                    xV = [a for a in dir(ModelParameters) if a.startswith('x')]
                    xV.sort(key=len)

                    # Generate array of previous day's model parameters
                    try:
                        modelPars_previousD = generate_parArray(xV, modelPar_previousD.all(), False)

                    except:
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when generating modelPars_previousD')
                        modelPars_previousD = []

                    # Order of Fourier series
                    fourierOrder = 12
                    
                    if len(modelPars_previousD)>0:
                        iCond = modelPars_previousD[0][10+1+2*fourierOrder+1:10+1+2*fourierOrder+1+18] # Initial model states + dosekempt + lastMeal
                        pfCoeff = modelPars_previousD[0][11:10+1+2*fourierOrder+1] # Fourier coefficients
                        pivcSig = buildNE(pfCoeff,5)
                        pivcSig_x = pivcSig[0,pivcSig.size-288:pivcSig.size].tolist()
                        dosekempt_rSim = modelPars_previousD[0][10+1+2*fourierOrder+1+16]
                        lastMeal_rSim = modelPars_previousD[0][10+1+2*fourierOrder+1+17]
                        HTimer_rSim = modelPars_previousD[0][10+1+2*fourierOrder+1+18]
                        corrTimer_rSim = modelPars_previousD[0][10+1+2*fourierOrder+1+19]
                    else:
                        iCond = []
                        pivcSig_x = [1.0]*288
                        dosekempt_rSim = 0.0
                        lastMeal_rSim = 0.0
                        HTimer_rSim = 0
                        corrTimer_rSim = 0

                    ############ Inputs for Matlab ############
                    BW = np.array(act_subj.weight,dtype=np.float64).tolist() # Subject's BW
                    baseV = matlab.double(random.sample(range(1,101),19)) # Array of initial in silico subjs
                    glucose_avatarGen = matlab.double(cgmF_values.tolist())
                    meal_avatarGen = matlab.double(meal.tolist())
                    insulin_avatarGen = matlab.double(insulin.tolist())
                    basal_avatarGen = matlab.double(basal.tolist())
                    pivcSig_x_avatarGen = matlab.double(pivcSig_x)
                    iCond_avatarGen = matlab.double(iCond)

                    CR_matlab = np.zeros(288)
                    CF_matlab = np.zeros(288)
                    basalP_matlab = np.zeros(288)

                    for zz in range(0,48):
                        basalP_matlab[zz*6:zz*6+6] = bpF_values[zz]
                        CR_matlab[zz*6:zz*6+6] = crF_values[zz]
                        CF_matlab[zz*6:zz*6+6] = cfF_values[zz]

                    basalPM_matlab = np.multiply(basalP_matlab,0.01*insF_tempR)

                    # Get previous day's basal profile
                    try:
                        basalP_6 = db.session.query(BasalProfile).filter(BasalProfile.timeini >= timeStampIni+utcOffsetDiff-24*60*60, BasalProfile.timeini <timeStampIni,
                                                                        BasalProfile.subject_id == act_subj.id)
                    except:
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the basal_profile table')

                    # Generate array of column names
                    tmtiV = [a for a in dir(BasalProfile) if a.startswith('tmti')]
                    tmtiV.sort(key=len)

                    # Generate previous day's basal profiles (6 h & 24 h)
                    try:
                        # If there is no previous day's profile, get the current one
                        if len(basalP_6.all()) == 0:
                            bProfiles_24 = [0]*288
                            for qq in range(0,len(bpF_values)):
                                bProfiles_24[qq*6:qq*6+6] = [bpF_values[qq]]*6
                            bProfiles_6 = bProfiles_24[-72:]
                        # Otherwise, use it
                        else:
                            bProfiles_6 = generate_xhparArray(tmtiV, basalP_6.first(), 6)
                            bProfiles_24 = generate_xhparArray(tmtiV, basalP_6.first(), 24)

                        app.logger.info('/scheduler[generate_xhparArray]. Username: ' +act_subj.username +'. bProfiles_6 and _24 profiles successfully extracted')

                    except:
                        app.logger.error('/scheduler[generate_xhparArray]. Username: ' +act_subj.username +'. An error has occurred when extracting the basal_6 and _24 profiles. Stoping DP process...')

                    # Get last 6 hour insulin records
                    try:
                        insulin_6 = db.session.query(Insulin).filter(Insulin.time >= timeStampIni+utcOffsetDiff-6*60*60, Insulin.time < timeStampIni,
                                                                    Insulin.pump_device_subject_id == act_subj.id)
                    except:
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the insulin table - insulin_6')

                    # Generate array of last 6 hour insulin records
                    try:
                        insulinV_6 = generate_xh_InsArray_5min(insulin_6.all(), 6)

                        app.logger.info('/scheduler[generate_xh_InsArray_5min]. Username: ' +
                                        act_subj.username + '. insulinV_6 array successfully generated')
                    except:
                        app.logger.error('/scheduler[generate_xh_InsArray_5min]. Username: ' +
                                        act_subj.username + '. An error has occurred when generating the insulinV_6 array. '
                                        'Probably no data available. Setting insulinV_6 to empty list')
                        insulinV_6 = []

                    # If insulinV_6 is empty, set it using basal rate pattern
                    if len(insulinV_6) == 0:
                        insulinV_6 = np.array(bProfiles_6)/12.0

                    insulinV_6 = np.array(insulinV_6)
                    insulinV_6 = insulinV_6.tolist()

                    # Generate array of last 6 hour temp basal rate
                    try:
                        tempRV_6 = generate_xh_Ins_Attr_5min(
                            insulin_6.all(), 'temp_rate', 6)

                        app.logger.info('/scheduler[generate_xh_Ins_Attr_5min]. Username: ' +
                                        act_subj.username + '. tempRV_6 array successfully generated')
                    except:
                        app.logger.error('/scheduler[generate_xh_Ins_Attr_5min]. Username: ' +
                                        act_subj.username + '. An error has occurred when generating the tempRV_6 array')

                    # If tempRV_6 is empty, set it to 100%
                    if len(tempRV_6) == 0:
                        tempRV_6 = [100.0]*72

                    # Modify original basal profile using temp rate
                    bProfilesM_6 = np.multiply(np.array(bProfiles_6), 0.01*np.array(tempRV_6))

                    # Generate INSdif_6 array
                    INSdif_6 = np.subtract(insulinV_6, bProfilesM_6/12.0)
                    
                    # Original, processed glucose array
                    cgmValueArray = cgmF_values.tolist()

                    ###########################################################################
                    # OL; Basal-IQ; Control-IQ
                    ###########################################################################

                    ###########################################################################
                    # Basal IQ activated
                    if apSel == 1:

                        # Get last 20 min cgm records
                        try:
                            gVPred = db.session.query(CGM).filter(CGM.time > timeStampIni+utcOffsetDiff-60*20, CGM.time <= timeStampIni,
                                                                    CGM.cgm_device_subject_id == act_subj.id)  
                        except:
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the cgm table')

                        # Generate last 20 min glucose array
                        try:
                            gVPred_20m = generate_xh_glucoseArray_5min(gVPred.all(), 4, cgmValueArray[0])

                            app.logger.info('/scheduler. Username: ' +act_subj.username +'. gVPred_20m array successfully generated')

                        except:
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when generating the gVPred_20m array.'
                                            'Setting all samples to first cgm record.')
                            gVPred_20m = [cgmValueArray[0]]*4
                        
                        # Compute time of insulin suspension
                        try:
                            rollWin = db.session.query(BasalIQ).filter(BasalIQ.time > timeStampIni+utcOffsetDiff-60*60*2.5, BasalIQ.time <= timeStampIni,
                                                                    BasalIQ.subject_id == act_subj.id)
                        except:
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the basalIQ table')
                            rollWin = []
                        
                        try:
                            tInsSusp = compute_time_insSusp(rollWin.all())
                        except:
                            tInsSusp = 0
                        
                        # Check if last record indicates current suspension
                        try:
                            rollWin_last = rollWin.order_by(rollWin.id.desc()).first()
                            flagInsSusp = int(rollWin_last.insSusp)
                        except:
                            flagInsSusp = 0

                        # Generate dictionary with data for Basal-IQ to run
                        apData_matlab = {
                            'flagInsSusp': flagInsSusp,
                            'tInsSusp': tInsSusp,
                            'gTPred': matlab.double([-15, -10, -5, 0]),
                            'gVPred': matlab.double(gVPred_20m)
                        }

                    ###########################################################################
                    # Control IQ activated
                    elif apSel == 2:

                        # Get last 24 hour insulin records
                        try:
                            insulin_24 = db.session.query(Insulin).filter(Insulin.time >= timeStampIni+utcOffsetDiff-24*60*60, Insulin.time < timeStampIni,
                                                                        Insulin.pump_device_subject_id == act_subj.id)  
                        except:
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the insulin table - insulin_24')

                        # Generate array of last 24 hour insulin records
                        try:
                            insulinV_24 = generate_xh_InsArray_5min(insulin_24.all(), 24)

                            app.logger.info('/scheduler[generate_xh_InsArray_5min]. Username: ' +
                                            act_subj.username + '. insulinV_24 array successfully generated')
                        except:
                            app.logger.error('/scheduler[generate_xh_InsArray_5min]. Username: ' +
                                            act_subj.username + '. An error has occurred when generating the insulinV_24 array')
                            insulinV_24 = []

                        # If there is no data, use the basal rate
                        # if len(insulinV_24) == 0:
                        #     insulinV_24 = np.array(bProfiles_24)/12.0

                        dDiff = 6
                        
                        # Get previous insulin records
                        try:
                            insulin_Froll = db.session.query(Insulin).filter(Insulin.time >= timeStampIni-7*24*60*60+(144-24*dDiff)*60*60, Insulin.time < timeStampIni,
                                                                                Insulin.pump_device_subject_id == act_subj.id)  
                        except:
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the insulin table - insulin_Froll')
                            insulinV_Froll = []

                        # Get previous TDIpop records
                        try:
                            TDIpop_Froll = db.session.query(ControlIQ).filter(ControlIQ.time >= timeStampIni-7*24*60*60+(144-24*dDiff)*60*60, ControlIQ.time < timeStampIni,
                                                                                ControlIQ.subject_id == act_subj.id)
                        except:
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the controlIQ table - TDIpop_Froll')
                            TDIpop_Froll = []

                        # Generate SumBolusMem variable
                        SumBolusMem = gen_SumBolusMem([],insulin_Froll,TDIpop_Froll,ciqF_TDIpop[0],timeStampIni,dDiff,[])

                        # Get last 6 hour meal records (as informed)
                        try:
                            meals_6 = db.session.query(Insulin).filter(Insulin.time >= timeStampIni+utcOffsetDiff-6*60*60, Insulin.time < timeStampIni,
                                                                    Insulin.pump_device_subject_id == act_subj.id)
                        except:
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the meal table - meals_6')                                     

                        # Generate array of last 6 hour meal records (as informed)
                        try:
                            mealsV_6 = generate_xh_mealArray_Ins_5min(meals_6.all(), 6)

                            app.logger.info('/scheduler[generate_xh_mealArray_Ins_5min]. Username: ' +
                                            act_subj.username + '. mealsV_6 array successfully generated')
                        except:
                            app.logger.error('/scheduler[generate_xh_mealArray_Ins_5min]. Username: ' +
                                            act_subj.username + '. An error has occurred when generating the mealsV_6 array')
                            mealsV_6 = [0.0]*72

                        # Get last 6 hour cgm records
                        try:
                            glucose_6 = db.session.query(CGM).filter(CGM.time >= timeStampIni+utcOffsetDiff-6*60*60, CGM.time < timeStampIni,
                                                                    CGM.cgm_device_subject_id == act_subj.id)
                        except:
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the cgm table - glucose_6')

                        # Generate array of last 6 hour cgm records
                        try:
                            glucoseV_6 = generate_xh_glucoseArray_5min(glucose_6.all(), 72, cgmValueArray[0])

                            app.logger.info('/scheduler[generate_xh_glucoseArray_5min]. Username: ' +
                                            act_subj.username + '. glucoseV_6 array successfully generated')
                        except:
                            app.logger.error('/scheduler[generate_xh_glucoseArray_5min]. Username: ' +
                                            act_subj.username + '. An error has occurred when generating the glucoseV_6 array.'
                                            'Probably no available data. Setting all samples to first cgm record.')                 
                            glucoseV_6 = [cgmValueArray[0]]*72

                        TDIest_0,auxVar = controlIQ_TDI(insulinV_24,SumBolusMem,ciqF_TDIpop[0])

                        # Generate dictionary with data for Control-IQ to run
                        apData_matlab = {
                            'EX': matlab.double(ciqF_EX.tolist()),
                            'tgt': matlab.double(ciqF_TGT.tolist()),
                            'sleep': matlab.double(ciqF_sleep.tolist()),
                            'TDIpop': matlab.double(ciqF_TDIpop.tolist()),
                            'sbMem': matlab.double(SumBolusMem),
                            'M6': matlab.double(mealsV_6),
                            'G6': matlab.double(glucoseV_6),
                            'J6': matlab.double(insulinV_6),
                            'J24h': matlab.double(insulinV_24),
                            'TDIest': np.array(TDIest_0,dtype=np.float64).tolist()
                        }

                    # If no APS is selected, set apData to an empty list
                    else:
                        apData_matlab = []

                    #apData_matlab = []

                    profile_replay_matlab = {
                        'basalPM': matlab.double(basalPM_matlab.tolist()),
                        'CR': matlab.double(CR_matlab.tolist()),
                        'CF': matlab.double(CF_matlab.tolist()),
                        'target': matlab.double(insF_target.tolist()),
                        'userOv': matlab.double(insF_userOv.tolist()),
                        'bBolusV': matlab.double(insF_basal.tolist()),
                        'mBolusV': matlab.double(insF_meal.tolist()),
                        'cBolusV': matlab.double(insF_corr.tolist()),
                        'BT': matlab.double(insF_BT.tolist()),
                        'lagB': matlab.double(insF_lagB.tolist()),
                        'corrDecl': matlab.double(insF_corrDecl.tolist()),
                        'choV': matlab.double(insF_cho.tolist()),
                        'extB': matlab.double(insF_extB.tolist()),
                        'extB_per': matlab.double(insF_extBP.tolist()),
                        'extB_dur': matlab.double(insF_extBD.tolist()),
                        'bProfiles_6': matlab.double(bProfiles_6),
                        'insulinV_6': matlab.double(insulinV_6),
                        'INSdif_6': matlab.double(INSdif_6.tolist()),
                        'insDur': insDur,
                        'ap': apData_matlab,
                        'HTimer': int(HTimer_rSim),
                        'corrTimer': int(corrTimer_rSim)
                    }

                    options_replay_matlab = {
                        'apSel': int(apSel),
                        'adjIns': 0,
                        'genIns': 0,
                        'adjHTs': 0,
                        'genHTs': 0
                    }

                    app.logger.info('/scheduler. Username: ' +act_subj.username +'. Inputs for Matlab optimizer have been successfully generated.')

                except:
                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when generating inputs for Matlab optimizer. No optimization will be run. simGlucose = cgmF_values')
                    flagOptimization = False
                    flagModelPar = False
                    simGlucose = cgmF_values
                    lastBasalReplay_f = np.copy(insF_basal)
                    lastCBolusReplay_f = np.copy(insF_corr)
                    lastMBolusReplay_f = np.copy(insF_meal)
                    lastBTReplay_f = np.copy(insF_BT) 

                if flagOptimization:
                    
                    flagReplay = True

                    #########################################################
                    # Optimizer
                    #########################################################
                    try:
                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. Running Matlab optimizer. This can take a while...')

                        res = eng.avatarGen_Step1('WITCluster1',baseV,glucose_avatarGen,meal_avatarGen,insulin_avatarGen,basal_avatarGen,BW,iCond_avatarGen,pivcSig_x_avatarGen,options_replay_matlab,profile_replay_matlab)

                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. Matlab optimizer has been executed successfully.')
                    
                    except:
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when executing the Matlab optimizer. flagModelPar = 0; simGlucose = cgmF_values')
                        flagModelPar = False
                        simGlucose = cgmF_values
                        lastBasalReplay_f = np.copy(insF_basal)
                        lastCBolusReplay_f = np.copy(insF_corr)
                        lastMBolusReplay_f = np.copy(insF_meal)
                        lastBTReplay_f = np.copy(insF_BT) 
                        flagReplay = False
                    
                    #########################################################
                    # Outputs
                    #########################################################
                    try:
                        tEnd = res['tEnd']
                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. Matlab optimizer -> Time spent: '+str(tEnd))

                        glucose_ident = res['simGlucose']
                        modelPar_values_ident = res['modelPar'][0][0:10+2*fourierOrder+1] # Model pars + Fourier coeffs
                        
                        model_x0_rSim_aux = res['struttura']['model_x0'] # Initial states
                        model_x0_rSim = []
                        for qq in range(0,len(model_x0_rSim_aux)):
                            model_x0_rSim.append(model_x0_rSim_aux[qq][0])

                        model_xf_rSim_aux = res['struttura']['model_xf'] # Final states
                        model_xf_rSim = []
                        for qq in range(0,len(model_xf_rSim_aux)):
                            model_xf_rSim.append(model_xf_rSim_aux[qq][0])

                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. Outputs from Matlab optimizer have been successfully fetched.')

                    except:
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when fetching outputs from Matlab optimizer. flagModelPar = 0; simGlucose = cgmF_values')
                        flagModelPar = False
                        simGlucose = cgmF_values
                        lastBasalReplay_f = np.copy(insF_basal)
                        lastCBolusReplay_f = np.copy(insF_corr)
                        lastMBolusReplay_f = np.copy(insF_meal)
                        lastBTReplay_f = np.copy(insF_BT) 
                        flagReplay = False
                    
                    #########################################################
                    # Run replay
                    #########################################################

                    if flagReplay:
                        try:
                            ############ DATA PREPARATION: SET 1 ############
                            try:
                                # UTC offset
                                tOffV = [utcOffset]

                                # TP
                                bProfiles = prepare_dataReplay_case1(timeStampIni,bpF_values)
                                crProfiles = prepare_dataReplay_case1(timeStampIni,crF_values)
                                cfProfiles = prepare_dataReplay_case1(timeStampIni,cfF_values)
                                
                                # Insulin
                                bBolusV = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_basal)
                                cBolusV = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_corr)
                                mBolusV = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_meal)
                                choV = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_cho)
                                target = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_target)
                                BT = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_BT)
                                lagB = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_lagB)
                                corrDecl = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_corrDecl)
                                userOv = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_userOv)
                                tempR = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_tempR)
                                extB = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_extB)
                                extB_per = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_extBP)
                                extB_dur = prepare_dataReplay_case2(timeStampIni,utcOffset,insF_extBD)

                                # Meals
                                moM_block = prepare_dataReplay_case2(timeStampIni,utcOffset,np.array(m))
                                moH_block = prepare_dataReplay_case2(timeStampIni,utcOffset,np.array(ht))

                                app.logger.info('/scheduler. Username: ' +act_subj.username +'. Set 1 of data preparation has been successfully executed')

                            except:
                                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when executing Set 1 of data preparation')
                            
                            ############ DATA PREPARATION: SET 2 ###########
                            try:
                                # Get previous day's basal profile
                                try:
                                    basalP_6 = db.session.query(BasalProfile).filter(BasalProfile.timeini >= timeStampIni+utcOffsetDiff-24*60*60, BasalProfile.timeini <timeStampIni,
                                                                                    BasalProfile.subject_id == act_subj.id)
                                except:
                                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the basal_profile table')

                                # Generate array of column names
                                tmtiV = [a for a in dir(BasalProfile) if a.startswith('tmti')]
                                tmtiV.sort(key=len)

                                # Generate previous day's basal profiles (6 h & 24 h)
                                try:
                                    # If there is no previous day's profile, get the current one
                                    if len(basalP_6.all()) == 0:
                                        bProfiles_24 = [0]*288
                                        for qq in range(0,len(bProfiles[0][1:])):
                                            bProfiles_24[qq*6:qq*6+6] = [bProfiles[0][1+qq]]*6
                                        bProfiles_6 = bProfiles_24[-72:]
                                    # Otherwise, use it
                                    else:
                                        bProfiles_6 = generate_xhparArray(tmtiV, basalP_6.first(), 6)
                                        bProfiles_24 = generate_xhparArray(tmtiV, basalP_6.first(), 24)

                                    app.logger.info('/scheduler[generate_xhparArray]. Username: ' +act_subj.username +'. bProfiles_6 and _24 profiles successfully extracted')

                                except:
                                    app.logger.error('/scheduler[generate_xhparArray]. Username: ' +act_subj.username +'. An error has occurred when extracting the basal_6 and _24 profiles. Stoping DP process...')

                                # Get last 6 hour insulin records
                                try:
                                    insulin_6 = db.session.query(Insulin).filter(Insulin.time >= timeStampIni+utcOffsetDiff-6*60*60, Insulin.time < timeStampIni,
                                                                                Insulin.pump_device_subject_id == act_subj.id)
                                except:
                                    app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the insulin table - insulin_6')

                                # Generate array of last 6 hour insulin records
                                try:
                                    insulinV_6 = generate_xh_InsArray_5min(insulin_6.all(), 6)

                                    app.logger.info('/scheduler[generate_xh_InsArray_5min]. Username: ' +
                                                    act_subj.username + '. insulinV_6 array successfully generated')
                                except:
                                    app.logger.error('/scheduler[generate_xh_InsArray_5min]. Username: ' +
                                                    act_subj.username + '. An error has occurred when generating the insulinV_6 array. '
                                                    'Probably no data available. Setting insulinV_6 to empty list')
                                    insulinV_6 = []

                                # If insulinV_6 is empty, set it using basal rate pattern
                                if len(insulinV_6) == 0:
                                    insulinV_6 = np.array(bProfiles_6)/12.0

                                # Generate array of last 6 hour temp basal rate
                                try:
                                    tempRV_6 = generate_xh_Ins_Attr_5min(
                                        insulin_6.all(), 'temp_rate', 6)

                                    app.logger.info('/scheduler[generate_xh_Ins_Attr_5min]. Username: ' +
                                                    act_subj.username + '. tempRV_6 array successfully generated')
                                except:
                                    app.logger.error('/scheduler[generate_xh_Ins_Attr_5min]. Username: ' +
                                                    act_subj.username + '. An error has occurred when generating the tempRV_6 array')

                                # If tempRV_6 is empty, set it to 100%
                                if len(tempRV_6) == 0:
                                    tempRV_6 = [100.0]*72

                                # Modify original basal profile using temp rate
                                bProfilesM_6 = np.multiply(np.array(bProfiles_6), 0.01*np.array(tempRV_6))

                                # Generate INSdif_6 array
                                INSdif_6 = np.subtract(insulinV_6, bProfilesM_6/12.0)

                                # Original, processed glucose array
                                cgmValueArray = cgmF_values.tolist()

                                # Set options to default values
                                adjIns = 0
                                genIns = 0
                                adjHTs = 0
                                genHTs = 0

                                app.logger.info('/scheduler. Username: ' +act_subj.username +'. Set 2 of data preparation has been successfully executed')

                            except:
                                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when executing Set 2 of data preparation')

                            ############ DATA PREPARATION: SET 3 ############
                            try:
                                ###########################################################################
                                # OL; Basal-IQ; Control-IQ
                                ###########################################################################

                                ###########################################################################
                                # Basal IQ activated
                                if apSel == 1:

                                    # Get last 20 min cgm records
                                    try:
                                        gVPred = db.session.query(CGM).filter(CGM.time > timeStampIni+utcOffsetDiff-60*20, CGM.time <= timeStampIni,
                                                                                CGM.cgm_device_subject_id == act_subj.id)  
                                    except:
                                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the cgm table')

                                    # Generate last 20 min glucose array
                                    try:
                                        gVPred_20m = generate_xh_glucoseArray_5min(gVPred.all(), 4, cgmValueArray[0])

                                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. gVPred_20m array successfully generated')

                                    except:
                                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when generating the gVPred_20m array.'
                                                        'Setting all samples to first cgm record.')
                                        gVPred_20m = [cgmValueArray[0]]*4
                                    
                                    # Compute time of insulin suspension
                                    try:
                                        rollWin = db.session.query(BasalIQ).filter(BasalIQ.time > timeStampIni+utcOffsetDiff-60*60*2.5, BasalIQ.time <= timeStampIni,
                                                                                BasalIQ.subject_id == act_subj.id)
                                    except:
                                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the basalIQ table')
                                        rollWin = []
                                    
                                    try:
                                        tInsSusp = compute_time_insSusp(rollWin.all())
                                    except:
                                        tInsSusp = 0
                                    
                                    # Check if last record indicates current suspension
                                    try:
                                        rollWin_last = rollWin.order_by(rollWin.id.desc()).first()
                                        flagInsSusp = int(rollWin_last.insSusp)
                                    except:
                                        flagInsSusp = 0

                                    # Generate dictionary with data for Basal-IQ to run
                                    apData = {
                                        'flagInsSusp': flagInsSusp,
                                        'tInsSusp': tInsSusp,
                                        'gTPred': np.array([-15, -10, -5, 0]),
                                        'gVPred': np.array(gVPred_20m)
                                    }

                                ###########################################################################
                                # Control IQ activated
                                elif apSel == 2:

                                    # Get last 24 hour insulin records
                                    try:
                                        insulin_24 = db.session.query(Insulin).filter(Insulin.time >= timeStampIni+utcOffsetDiff-24*60*60, Insulin.time < timeStampIni,
                                                                                    Insulin.pump_device_subject_id == act_subj.id)  
                                    except:
                                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the insulin table - insulin_24')

                                    # Generate array of last 24 hour insulin records
                                    try:
                                        insulinV_24 = generate_xh_InsArray_5min(insulin_24.all(), 24)

                                        app.logger.info('/scheduler[generate_xh_InsArray_5min]. Username: ' +
                                                        act_subj.username + '. insulinV_24 array successfully generated')
                                    except:
                                        app.logger.error('/scheduler[generate_xh_InsArray_5min]. Username: ' +
                                                        act_subj.username + '. An error has occurred when generating the insulinV_24 array')
                                        insulinV_24 = []

                                    # If there is no data, use the basal rate
                                    # if len(insulinV_24) == 0:
                                    #     insulinV_24 = np.array(bProfiles_24)/12.0

                                    dDiff = 6
                                    
                                    # Get previous insulin records
                                    try:
                                        insulin_Froll = db.session.query(Insulin).filter(Insulin.time >= timeStampIni-7*24*60*60+(144-24*dDiff)*60*60, Insulin.time < timeStampIni,
                                                                                            Insulin.pump_device_subject_id == act_subj.id)  
                                    except:
                                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the insulin table - insulin_Froll')
                                        insulinV_Froll = []

                                    # Get previous TDIpop records
                                    try:
                                        TDIpop_Froll = db.session.query(ControlIQ).filter(ControlIQ.time >= timeStampIni-7*24*60*60+(144-24*dDiff)*60*60, ControlIQ.time < timeStampIni,
                                                                                            ControlIQ.subject_id == act_subj.id)
                                    except:
                                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the controlIQ table - TDIpop_Froll')
                                        TDIpop_Froll = []

                                    # Generate SumBolusMem variable
                                    SumBolusMem = gen_SumBolusMem([],insulin_Froll,TDIpop_Froll,ciqF_TDIpop[0],timeStampIni,dDiff,[])

                                    # Get last 6 hour meal records (as informed)
                                    try:
                                        meals_6 = db.session.query(Insulin).filter(Insulin.time >= timeStampIni+utcOffsetDiff-6*60*60, Insulin.time < timeStampIni,
                                                                                Insulin.pump_device_subject_id == act_subj.id)
                                    except:
                                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the meal table - meals_6')                                     

                                    # Generate array of last 6 hour meal records (as informed)
                                    try:
                                        mealsV_6 = generate_xh_mealArray_Ins_5min(meals_6.all(), 6)

                                        app.logger.info('/scheduler[generate_xh_mealArray_Ins_5min]. Username: ' +
                                                        act_subj.username + '. mealsV_6 array successfully generated')
                                    except:
                                        app.logger.error('/scheduler[generate_xh_mealArray_Ins_5min]. Username: ' +
                                                        act_subj.username + '. An error has occurred when generating the mealsV_6 array')
                                        mealsV_6 = [0.0]*72

                                    # Get last 6 hour cgm records
                                    try:
                                        glucose_6 = db.session.query(CGM).filter(CGM.time >= timeStampIni+utcOffsetDiff-6*60*60, CGM.time < timeStampIni,
                                                                                CGM.cgm_device_subject_id == act_subj.id)
                                    except:
                                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when querying the cgm table - glucose_6')

                                    # Generate array of last 6 hour cgm records
                                    try:
                                        glucoseV_6 = generate_xh_glucoseArray_5min(glucose_6.all(), 72, cgmValueArray[0])

                                        app.logger.info('/scheduler[generate_xh_glucoseArray_5min]. Username: ' +
                                                        act_subj.username + '. glucoseV_6 array successfully generated')
                                    except:
                                        app.logger.error('/scheduler[generate_xh_glucoseArray_5min]. Username: ' +
                                                        act_subj.username + '. An error has occurred when generating the glucoseV_6 array.'
                                                        'Probably no available data. Setting all samples to first cgm record.')                 
                                        glucoseV_6 = [cgmValueArray[0]]*72

                                    # Generate dictionary with data for Control-IQ to run
                                    apData = {
                                        'EX': [ciqF_EX],
                                        'tgt': [ciqF_TGT],
                                        'sleep': [ciqF_sleep],
                                        'TDIpop': [ciqF_TDIpop],
                                        'SumBolusMem': SumBolusMem,
                                        'mealsV_6': mealsV_6,
                                        'glucoseV_6': glucoseV_6,
                                        'insulinV_6': insulinV_6,
                                        'insulinV_24': insulinV_24
                                    }

                                # If no APS is selected, set apData to an empty list
                                else:
                                    apData = []

                                app.logger.info('/scheduler. Username: ' +act_subj.username +'. Set 3 of data preparation has been successfully executed')

                            except:
                                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when executing Set 3 of data preparation')

                            ############ DATA PREPARATION: SET 4 ############
                            try:
                                # Define dictionary for replay simulation
                                dataSim = {
                                    'tOffV': tOffV,
                                    'bProfiles': bProfiles,
                                    'crProfiles': crProfiles,
                                    'cfProfiles': cfProfiles,
                                    'bBolusV': bBolusV,
                                    'cBolusV': cBolusV,
                                    'mBolusV': mBolusV,
                                    'choV': choV,
                                    'target': target,
                                    'BT': BT,
                                    'lagB': lagB,
                                    'corrDecl': corrDecl,
                                    'userOv': userOv,
                                    'tempR': tempR,
                                    'extB': extB,
                                    'extB_per': extB_per,
                                    'extB_dur': extB_dur,
                                    'moM': moM_block,
                                    'moH': moH_block,
                                    'INSdif_6': INSdif_6,
                                    'bProfiles_6': bProfiles_6,
                                    'insulinV_6': insulinV_6,
                                    'modelPars_previousD': modelPars_previousD,
                                    'cgmValueArray': cgmValueArray,
                                    'apSel': str(apSel),
                                    'adjIns': adjIns,
                                    'genIns': genIns,
                                    'adjHTs': adjHTs,
                                    'genHTs': genHTs,
                                    'apData': apData,
                                    'BW': BW,
                                    'insDur': insDur
                                }

                                # Define modelPars
                                modelPars = []
                                modelPars.append(timeStampIni)
                                modelPars.extend(modelPar_values_ident)
                                modelPars.extend(model_x0_rSim)
                                modelPars.extend([dosekempt_rSim,lastMeal_rSim,HTimer_rSim,corrTimer_rSim,0])
                                modelPars = [modelPars]

                                app.logger.info('/scheduler. Username: ' +act_subj.username +'. Set 4 of data preparation has been successfully executed')

                            except:
                                app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when executing Set 4 of data preparation')

                            ############ RUN REPLAY ############

                            app.logger.info('/scheduler. Username: ' +act_subj.username +'. Executing replay simulation')

                            resSim = replaySim_preProc_v2(modelPars, dataSim)

                            app.logger.info('/scheduler. Username: ' +act_subj.username +'. The replay simulation has been successfully executed')

                            ############ OUTPUTS ############

                            simGlucose = resSim['lastSimGlucose']
                            simDosekempt = resSim['lastDosekempt']
                            simLastMeal = resSim['lastLastMeal']
                            simHTimer = resSim['lastHTimer']
                            simCorrTimer = resSim['lastCorrTimer']
                            simModel_xf = resSim['lastModel_xf']

                            lastBasalReplay_f = resSim['lastBasalReplay_f']
                            lastCBolusReplay_f = resSim['lastCBolusReplay_f']
                            lastMBolusReplay_f = resSim['lastMBolusReplay_f']
                            lastBTReplay_f = resSim['lastBTReplay_f']

                            modelPar_values = []
                            modelPar_values.extend(modelPar_values_ident)
                            modelPar_values.extend(simModel_xf)
                            modelPar_values.extend([simDosekempt,simLastMeal,simHTimer,simCorrTimer,0])

                            app.logger.info('/scheduler. Username: ' +act_subj.username +'. The replay process has been successfully executed.')

                        except:
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when executing the replay simulation. flagModelPar = 0; simGlucose = cgmF_values')
                            flagModelPar = False
                            simGlucose = cgmF_values
                            lastBasalReplay_f = np.copy(insF_basal)
                            lastCBolusReplay_f = np.copy(insF_corr)
                            lastMBolusReplay_f = np.copy(insF_meal)
                            lastBTReplay_f = np.copy(insF_BT) 
            else:
                simGlucose = cgmF_values
                lastBasalReplay_f = np.copy(insF_basal)
                lastCBolusReplay_f = np.copy(insF_corr)
                lastMBolusReplay_f = np.copy(insF_meal)
                lastBTReplay_f = np.copy(insF_BT)  
                
            #########################################################
            # Update database
            #########################################################

            if flagSave:
                ############ MODEL DATA ############
                if dataStatus==1:
                    
                    if flagModelPar:
                        try:
                            model_par = ModelParameters()
                            xV = [a for a in dir(model_par) if a.startswith('x')]
                            xV.sort(key=len)
                            for i in range(0,len(xV)):
                                setattr(model_par,xV[i],float(modelPar_values[i]))

                            setattr(model_par,'timeini',timeStampIni)
                            setattr(model_par,'utcOffset',int(utcOffset))
                            setattr(model_par,'subject_id',act_subj.id)
                            db.session.add(model_par)
                            db.session.commit()
                            app.logger.info('/scheduler. Username: ' +act_subj.username +'. Model parameters were successfully saved')    

                        except exc.SQLAlchemyError as e:
                            db.session.rollback()
                            error = str(e.__dict__['orig'])
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving model data: ' +error)

                ############ GLUCOSE DATA ############
                # Get last CGM device
                cgm_device = db.session.query(CGMDevice).filter_by(subject_id=act_subj.id).order_by(CGMDevice.id.desc()).first()

                simGlucose     = simGlucose.tolist()
                cgmF_utcOffset = cgmF_utcOffset.tolist()
                cgmF_trend     = cgmF_trend.tolist()
                cgmF_status    = cgmF_status.tolist()
                cgmF_cal       = cgmF_cal.tolist()
                cgmF_time      = cgmF_time.tolist()

                if flagGlucose:
                    try:
                        cgm_records = []
                        for ii in range(0, len(simGlucose)):
                            cgm_record = CGM(value=simGlucose[ii],trend=cgmF_trend[ii],state=cgmF_status[ii],cal=cgmF_cal[ii],time=cgmF_time[ii],
                                utcOffset=cgmF_utcOffset[ii],cgm_device_id=cgm_device.id,cgm_device_subject_id=act_subj.id)
                            cgm_records.append(cgm_record)
                        db.session.add_all(cgm_records)
                        db.session.commit()       
                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. Glucose records were successfully saved') 

                    except exc.SQLAlchemyError as e:
                        db.session.rollback()
                        error = str(e.__dict__['orig'])
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving glucose data: ' +error)
                
                ############ TP DATA ############
                bpF_values = bpF_values.tolist()                
                cfF_values = cfF_values.tolist()
                crF_values = crF_values.tolist()

                if flagTH:
                    try:
                        basal_profile = BasalProfile()
                        tmtiV = [a for a in dir(basal_profile) if a.startswith('tmti')]
                        tmtiV.sort(key=len)
                        for i in range(0,len(tmtiV)):
                            setattr(basal_profile,tmtiV[i],bpF_values[i])
                        setattr(basal_profile,'timeini',timeStampIni)
                        setattr(basal_profile,'utcOffset',int(utcOffset))
                        setattr(basal_profile,'subject_id',act_subj.id)
                        db.session.add(basal_profile)
                        db.session.commit()
                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. BP records were successfully saved') 

                    except exc.SQLAlchemyError as e:
                        db.session.rollback()
                        error = str(e.__dict__['orig'])
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving BP data: '+error)

                    try:
                        cf_profile = CFProfile()
                        for i in range(0,len(tmtiV)):
                            setattr(cf_profile,tmtiV[i],cfF_values[i])
                        setattr(cf_profile,'timeini',timeStampIni)
                        setattr(cf_profile,'utcOffset',int(utcOffset))
                        setattr(cf_profile,'subject_id',act_subj.id)
                        db.session.add(cf_profile)
                        db.session.commit()
                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. CF records were successfully saved') 

                    except exc.SQLAlchemyError as e:
                        db.session.rollback()
                        error = str(e.__dict__['orig'])
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving CF data: '+error)
                    
                    try:
                        cr_profile = CRProfile()
                        for i in range(0,len(tmtiV)):
                            setattr(cr_profile,tmtiV[i],crF_values[i])
                        setattr(cr_profile,'timeini',timeStampIni)
                        setattr(cr_profile,'utcOffset',int(utcOffset))
                        setattr(cr_profile,'subject_id',act_subj.id)
                        db.session.add(cr_profile)
                        db.session.commit()
                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. CR records were successfully saved') 

                    except exc.SQLAlchemyError as e:
                        db.session.rollback()
                        error = str(e.__dict__['orig'])
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving CR data: '+error)

                ############ MEAL DATA ############
                if flagMeals:
                    try:
                        
                        mealTime = mealTime.tolist()
                        mealSize = mealSize.tolist()
                        mealUtcOffset = mealUtcOffset.tolist()
                        mealRFlag = mealRFlag.tolist()

                        meal_records = []
                        for ii in range(0, len(mealTime)):
                            meal_record = Meal(carbs=mealSize[ii],is_rescue=mealRFlag[ii],time=mealTime[ii],utcOffset=mealUtcOffset[ii],
                                subject_id=act_subj.id)
                            meal_records.append(meal_record)  
                        db.session.add_all(meal_records)
                        db.session.commit()
                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. Meal records were successfully saved') 
                        
                    except exc.SQLAlchemyError as e:
                        db.session.rollback()
                        error = str(e.__dict__['orig'])
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving meal data: ' +error)
                
                ############ INSULIN DATA ############
                # Get last insulin device
                ins_device = db.session.query(PumpDevice).filter_by(subject_id=act_subj.id).order_by(PumpDevice.id.desc()).first()

                insF_time = insF_time.tolist() 
                # insF_basal = insF_basal.tolist()
                # insF_corr = insF_corr.tolist()
                # insF_meal = insF_meal.tolist()
                insF_basal = lastBasalReplay_f.tolist() 
                insF_corr = lastCBolusReplay_f.tolist() 
                insF_meal = lastMBolusReplay_f.tolist() 
                insF_smbg = insF_smbg.tolist()
                #insF_BT = insF_BT.tolist()
                insF_BT = lastBTReplay_f.tolist() 
                insF_lagB = insF_lagB.tolist()
                insF_corrDecl = insF_corrDecl.tolist()
                insF_target = insF_target.tolist()
                insF_userOv = insF_userOv.tolist()
                insF_tempR = insF_tempR.tolist()
                insF_cho = insF_cho.tolist()
                insF_utcOffset = insF_utcOffset.tolist()
                insF_extB = insF_extB.tolist()
                insF_extBP = insF_extBP.tolist()
                insF_extBD = insF_extBD.tolist()
                insF_mode = insF_mode.tolist()

                if flagIns:
                    try:
                        ins_records = []
                        for ii in range(0, len(insF_basal)):
                            ins_record = Insulin(basal=insF_basal[ii],corr=insF_corr[ii],meal=insF_meal[ii],corrDeclined=insF_corrDecl[ii],cho=insF_cho[ii],smbg=insF_smbg[ii],
                                        target=insF_target[ii],bolusType=insF_BT[ii],userOverW=insF_userOv[ii],temp_rate=insF_tempR[ii],extended_bolus=insF_extB[ii],
                                        extended_bolus_per=insF_extBP[ii],extended_bolus_dur=insF_extBD[ii],time=insF_time[ii],utcOffset=insF_utcOffset[ii],
                                        lagB=insF_lagB[ii],ap_mode=insF_mode[ii],pump_device_id=ins_device.id,pump_device_subject_id=act_subj.id)
                            ins_records.append(ins_record)
                        db.session.add_all(ins_records)
                        db.session.commit()  
                        app.logger.info('/scheduler. Username: ' +act_subj.username +'. Insulin records were successfully saved') 

                    except exc.SQLAlchemyError as e:
                        db.session.rollback()
                        error = str(e.__dict__['orig'])
                        app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving insulin data: '+error)

                ############ AP DATA ############
                if flagAPS:
                    
                    if apSel==1:

                        biqF_insSusp = biqF_insSusp.tolist()
                        biqF_utcOffset = biqF_utcOffset.tolist()
                        biqF_time = biqF_time.tolist()
                        
                        try:
                            basalIQ_records = []
                            for ii in range(0, len(biqF_time)):
                                basalIQ_record = BasalIQ(time=biqF_time[ii],utcOffset=biqF_utcOffset[ii],insSusp=biqF_insSusp[ii],subject_id=act_subj.id)
                                basalIQ_records.append(basalIQ_record)
                            
                            db.session.add_all(basalIQ_records)
                            db.session.commit()       
                            app.logger.info('/scheduler. Username: ' +act_subj.username +'. Basal-IQ records were successfully saved') 

                        except exc.SQLAlchemyError as e:
                            db.session.rollback()
                            error = str(e.__dict__['orig'])
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving Basal-IQ data: '+error)

                    elif apSel == 2:

                        ciqF_time      = ciqF_time.tolist()
                        ciqF_EX        = ciqF_EX.tolist()
                        ciqF_TDIpop    = ciqF_TDIpop.tolist()
                        ciqF_sleep     = ciqF_sleep.tolist()
                        ciqF_TGT       = ciqF_TGT.tolist()
                        ciqF_utcOffset = ciqF_utcOffset.tolist()

                        try:
                            controlIQ_records = []
                            for ii in range(0, len(ciqF_time)):
                                controlIQ_record = ControlIQ(time=ciqF_time[ii],utcOffset=ciqF_utcOffset[ii],EX=ciqF_EX[ii],TDIpop=ciqF_TDIpop[ii],
                                sleep=ciqF_sleep[ii],TGT=ciqF_TGT[ii],subject_id=act_subj.id)
                                controlIQ_records.append(controlIQ_record)
                            db.session.add_all(controlIQ_records)
                            db.session.commit()       
                            app.logger.info('/scheduler. Username: ' +act_subj.username +'. Control-IQ records were successfully saved') 

                        except exc.SQLAlchemyError as e:
                            db.session.rollback()
                            error = str(e.__dict__['orig'])
                            app.logger.error('/scheduler. Username: ' +act_subj.username +'. An error has occurred when saving Control-IQ data: '+error)
            
            app.logger.info('/scheduler. Username: ' +act_subj.username +'. Process completed.') 

#########################################################################################################################
def wakeUpCluster1():

    flagWakeUp = True

    if flagWakeUp:
        app.logger.info('/scheduler/wakeUpCluster1. The scheduler has been called. Running something in Matlab to wake up the workers...')

        resWake = eng.wakeUpCluster_shell('WITCluster1')

        app.logger.info('/scheduler. Workers have been awaken, now waiting 15 min to generate avatars...')

    else:
        app.logger.info('/scheduler. The waking up process has been skipped.')

#########################################################################################################################
def wakeUpCluster2():

    flagWakeUp = True

    if flagWakeUp:
        app.logger.info('/scheduler/wakeUpCluster2. The scheduler has been called. Running something in Matlab to wake up the workers...')

        resWake = eng.wakeUpCluster_shell('WITCluster2')

        app.logger.info('/scheduler. Workers have been awaken, now waiting 15 min to generate avatars...')

    else:
        app.logger.info('/scheduler. The waking up process has been skipped.')

#########################################################################################################################

sched = BackgroundScheduler(timezone=utc)
#sched.add_job(sensor,'interval',seconds=60,args=None)
#sched.add_job(sensor1,'interval',seconds=60,args=None)
# sched.add_job(wakeUpCluster,'cron', hour=15, minute=45)
# sched.add_job(fd_ag,'cron', hour=16, minute=0)
# sched.add_job(BasalOptimizer,'cron', hour=12, minute=0)

trigger_fetch = OrTrigger([ # This is local time
   CronTrigger(hour=0, minute=0),
   CronTrigger(hour=6, minute=0),
   CronTrigger(hour=12, minute=0),
   CronTrigger(hour=18, minute=0)
])

#sched.add_job(sensor, trigger_fetch)
sched.add_job(sensor, 'cron',hour = 13, minute = 58) # This is UTC time
sched.add_job(sensor1, 'cron',hour = 13, minute = 58) # This is UTC time
#sched.add_job(estimateA1c_wrapper, 'cron',hour = 6, minute = 0) # This is UTC time
#sched.add_job(weeklyOptimizer, 'cron', day_of_week='tue', hour='16', minute='52') # This is UTC time


sched.start()

#########################################################################################################################
# App

app = Flask(__name__)

# Configuration
app.config.from_pyfile('config.py')

if __name__ == '__main__':
    app.logger = logging.getLogger(__name__)
    app.logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
    stream_handler.setFormatter(formatter)
    app.logger.addHandler(stream_handler)

#########################################################################################################################
# Bootstrap

try:
    Bootstrap(app)

    app.logger.info('Bootstrap has been initialized successfully')
except:
    app.logger.error('An error has been occurred when initializing Bootstrap')

#########################################################################################################################
# Matlab engine

try:
    eng = matlab.engine.start_matlab()

    app.logger.info('The Matlab engine has been initiated successfully')
except:
    app.logger.error('An error has occurred when initiating the Matlab engine')

#########################################################################################################################
# Email

try:
    mail = Mail(app)

    app.logger.info('The mail server parameters has been set up successfully')
except:
    app.logger.error('An error has occurred when setting up the mail server parameters')

#########################################################################################################################
# DB connection

try:
    db = SQLAlchemy(app)
    app.logger.info('The connection to the DB has been successful')
except:
    app.logger.error('An error has occurred when connecting to the DB')

#########################################################################################################################
# DB mapping

try:
    Base = automap_base() # Automap

    class Subject(Base,UserMixin):
        __tablename__ = 'subject'

    Base.prepare(db.engine, reflect=True)

    # Classes

    BasalProfile = Base.classes.basal_profile
    CFProfile = Base.classes.CF_profile
    CRProfile = Base.classes.CR_profile
    CGM = Base.classes.cgm
    CGMDevice = Base.classes.cgm_device
    Insulin = Base.classes.insulin
    Meal = Base.classes.meal
    ModelParameters = Base.classes.model_parameters
    PumpDevice = Base.classes.pump_device
    ControlIQ = Base.classes.controlIQ
    BasalIQ = Base.classes.basalIQ
    EA1c = Base.classes.eA1c
    CRCFOpt = Base.classes.CRCFOpt
    BasalRateOpt = Base.classes.BasalRateOpt

    app.logger.info('Mapped classes have been successfully generated')
except:
    app.logger.error('An error has occurred when mapping the DB classes')

#########################################################################################################################
# Login

try:
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    app.logger.info('The session management has been successfully created')
except:
    app.logger.error('An error has occurred when creating the session management')

#########################################################################################################################
# Shutdown your cron thread if the web process is stopped

try:
    atexit.register(lambda: sched.shutdown(wait=False))

    app.logger.info('The cron thread has been successfully configured to be shutdown if the web process is stopped')
except:
    app.logger.error("An error has occurred when configuring the crod thread to shutdown when the web process is stopped")

#########################################################################################################################
# Functions to handle a reset password request
#########################################################################################################################

# Function to generate the token
def get_reset_token(subject,expires_sec=600):
    s = Serializer(app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'user_id': subject.id}).decode('utf-8')

#########################################################################################################################

# Function to verify the token
def verify_reset_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token)['user_id']
    except:
        return None
    return db.session.query(Subject).get(int(user_id))

#########################################################################################################################

# Function to send an email with instructions to reset the password
def send_reset_email(subject):
    token = get_reset_token(subject)
    msg = Message('Password Reset Request', 
                    recipients=[subject.email])
    msg.html = f'''To reset your password, visit the following link within the next 10 minutes: 
{url_for('reset_token',token=token,_external=True)}
    
If you did not make this request then simply ignore this email and no changes will be made
'''
    try:
        mail.send(msg)

        app.logger.info('/send_reset_email: The message has been successfully sent')
    except Exception:
        error_message = traceback.format_exc()
        app.logger.error('/send_reset_email: An error has occurred when delivering the email. Error_message = ' + error_message)

#########################################################################################################################
#########################################################################################################################
# Decorators
#########################################################################################################################

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.query(Subject).get(int(user_id))
    except:
        app.logger.error('load_user: An error has occurred when querying the user object')

#########################################################################################################################

@app.route('/')
def main_route():
    if current_user.is_authenticated:
        app.logger.info('/(' + current_user.username + '. User authenticated. Redirecting to Dashboard')
        return redirect(url_for('glucMetrics1'))
    app.logger.info('/: User not authenticated. Redirecting to Login')
    return redirect(url_for('login'))

#########################################################################################################################

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            subject = db.session.query(Subject).filter_by(
                username=form.username.data).first()
        except:
            app.logger.error('/login: An error has occurred when querying the user object')

        if subject:
            if subject.active==1:
                if check_password_hash(subject.password, form.password.data):
                    try:
                        login_user(subject, remember=form.remember.data)
                    except:
                        app.logger.error('/login. Username: ' + subject.username + '. An error has occurred when logging in')
                    app.logger.info('/login. Username: ' + subject.username + '. Redirecting to Dashboard')
                    return redirect(url_for('glucMetrics1'))
            app.logger.info('/login. Username: ' + subject.username +'. User tried to log in but it is not active.')
                
        flash('Invalid username or password','warning')
        app.logger.info('/login: Invalid username or password')
    return render_template('login.html', form=form)

#########################################################################################################################

@app.route('/glucMetrics1', methods=['GET', 'POST'])
@login_required
def glucMetrics1():

    app.logger.info('/dashboard/glucMetrics1. Username: ' + current_user.username + '. eA1c routine')

    subject = db.session.query(Subject).filter_by(username=current_user.username).first() # Gets user

    # Get tz from insulin pump
    ins_device        = db.session.query(PumpDevice).filter_by(subject_id=subject.id).order_by(PumpDevice.id.desc()).first()
    ins_device_tz_str = ins_device.tz
    ins_device_tz     = gettz(ins_device_tz_str)

    local_time_now = datetime.datetime.now()

    t0_utc   = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc).timestamp())
    t0_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
    utcOffset = t0_utc - t0_local

    eA1c_records = db.session.query(EA1c).filter(EA1c.time == t0_local,EA1c.subject_id == subject.id)

    eA1c_record = eA1c_records.order_by(EA1c.id.desc()).first()

    if eA1c_record is None:
        eA1c_message = '-'
        arrow_index = -1
    else:
        eA1c_message = round(getattr(eA1c_record,'eA1c'),1)
        arrow_index = getattr(eA1c_record,'arrow')

    # PLACE eA1C CODE HERE
    
    arrowLib = ["&#8594","&#8599","&#8593","&#8598","&#8592","&#8601","&#8595","&#8600"]
    # R-NE-N-NW-W-SW-S-SE
    if arrow_index!=-1:
        arrow = arrowLib[arrow_index]
    else:
        arrow = ''

    return render_template('abc1.html',eA1c_message=eA1c_message,arrow=arrow, name=current_user.username)

#########################################################################################################################

@app.route('/glucMetrics1/gauge1-changed', methods=['POST'])
@login_required
def gauge1_changed():

    app.logger.info('/glucMetrics1/gauge1-changed. Username: ' + current_user.username + '. GV routine')

    subject = db.session.query(Subject).filter_by(username=current_user.username).first() # Gets user

    ins_device        = db.session.query(PumpDevice).filter_by(subject_id=subject.id).order_by(PumpDevice.id.desc()).first()
    ins_device_tz_str = ins_device.tz
    ins_device_tz     = gettz(ins_device_tz_str)

    local_time_now = datetime.datetime.now()
    today_utc = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc)
    t0_utc   = int((today_utc).timestamp())
    t0_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
    utcOffset = t0_utc - t0_local

    date_file = str(today_utc.year)+'-'+str(today_utc.month)+'-'+str(today_utc.day)
    fileName = 'backendFiles/'+subject.username+'_'+date_file
    fileName = fileName+'/'+subject.username+'.json'

    try:
        data = read_jsonFile(fileName)
        timeStampIni = t0_local-18*60*60 # 
        timeStampEnd = t0_local+6*60*60-1 #
        sfData = sort_filter_data(data,timeStampIni,timeStampEnd,utcOffset)
    except:
        sfData = np.array([])

    glucoseData = extract_glucoseData(sfData,utcOffset)

    timestamps = [datetime.datetime.fromtimestamp(ti+utcOffset,tz=datetime.timezone.utc).strftime('%x %H:%M:%S') for ti in glucoseData[0]]
    BG_values = glucoseData[1]
    current_date = pd.to_datetime(str(today_utc.month)+'/'+str(today_utc.day)+'/'+str(today_utc.year))

    print(timestamps)
    
    BAMp = {'RT_image_path': 'BAM_testing',
        'STS_LBGI_breakpoints': [4, 7],
        'STS_LBGI_interpretations': ['Low', 'Medium', 'High'],
        'STS_HBGI_breakpoints': [4, 7],
        'STS_HBGI_interpretations': ['Low', 'Medium', 'High'],
        'LBGI_bounds': [0, 2.94],
        'HBGI_bounds': [0, 23.01],
        'ADRR_bounds': [0, 78.24],
        'RT_num_days': 3,  # Number of days to plot on the risk trace image
       }

    #data = read_jsonFile('data/T-1.json')
    # current_date = data['Current_Date']
    # timestamps = data['Timestamps']
    # BG_values = data['BG_Values']

    BG_df, flag_1 = process_CGM_data(current_date, 
                                     timestamps, 
                                     BG_values,
                                     BAMp)
    GV = variability_index(BG_df, flag_1, BAMp)[0]

    print(GV)
    if np.isnan(GV):
        GV = 0
        gauge1_title = 'Not enough data'
    else:
        gauge1_title = 'Glucose Variability'

    data = jsonify({
        'gauge1_value': GV,
        'gauge1_title': gauge1_title
        })

    res = make_response(data,200)

    return res

#########################################################################################################################

@app.route('/glucMetrics2', methods=['GET', 'POST'])
@login_required
def glucMetrics2():

    return render_template('abc2.html', name=current_user.username)

#########################################################################################################################

@app.route('/glucMetrics2/gauge2-changed', methods=['POST'])
@login_required
def gauge2_changed():

    app.logger.info('/glucMetrics1/gauge2-changed. Username: ' + current_user.username + '. Risk index routine')

    subject = db.session.query(Subject).filter_by(username=current_user.username).first() # Gets user

    ins_device        = db.session.query(PumpDevice).filter_by(subject_id=subject.id).order_by(PumpDevice.id.desc()).first()
    ins_device_tz_str = ins_device.tz
    ins_device_tz     = gettz(ins_device_tz_str)

    local_time_now = datetime.datetime.now()
    today_utc = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc)
    t0_utc   = int((today_utc).timestamp())
    t0_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
    utcOffset = t0_utc - t0_local

    date_file = str(today_utc.year)+'-'+str(today_utc.month)+'-'+str(today_utc.day)
    fileName = 'backendFiles/'+subject.username+'_'+date_file
    fileName = fileName+'/'+subject.username+'.json'
    
    try:
        data = read_jsonFile(fileName)
        timeStampIni = t0_local-18*60*60 # 
        timeStampEnd = t0_local+6*60*60-1 #
        sfData = sort_filter_data(data,timeStampIni,timeStampEnd,utcOffset)
    except:
        sfData = np.array([])

    glucoseData = extract_glucoseData(sfData,utcOffset)

    timestamps = [datetime.datetime.fromtimestamp(ti+utcOffset,tz=datetime.timezone.utc).strftime('%x %H:%M:%S') for ti in glucoseData[0]]
    BG_values = glucoseData[1]
    current_date = pd.to_datetime(str(today_utc.month)+'/'+str(today_utc.day)+'/'+str(today_utc.year))

    print(timestamps)
    
    BAMp = {'RT_image_path': 'BAM_testing',
        'STS_LBGI_breakpoints': [4, 7],
        'STS_LBGI_interpretations': ['Low', 'Medium', 'High'],
        'STS_HBGI_breakpoints': [4, 7],
        'STS_HBGI_interpretations': ['Low', 'Medium', 'High'],
        'LBGI_bounds': [0, 2.94],
        'HBGI_bounds': [0, 23.01],
        'ADRR_bounds': [0, 78.24],
        'RT_num_days': 3,  # Number of days to plot on the risk trace image
       }

    #data = read_jsonFile('data/T-1.json')
    # current_date = data['Current_Date']
    # timestamps = data['Timestamps']
    # BG_values = data['BG_Values']

    BG_df, flag_1 = process_CGM_data(current_date, 
                                     timestamps, 
                                     BG_values,
                                     BAMp)
    LBGI_vals = BG_df.groupby('Date')['BG'] \
                        .apply(lambda BG_s: LBGI(BG_s)) \
                        .sort_index()
    HBGI_vals = BG_df.groupby('Date')['BG'] \
                        .apply(lambda BG_s: HBGI(BG_s)) \
                        .sort_index()

    both_risk_indices = risk_indices(LBGI_vals, HBGI_vals, flag_1, BAMp)

    hypoRisk = both_risk_indices[0][0]
    hyperRisk = both_risk_indices[1][0]
    hypoInd = both_risk_indices[0][1]
    hyperInd = both_risk_indices[1][1]

    print(both_risk_indices)

    if np.isnan(both_risk_indices[0][0]):
        hypoRisk = 0
        hyperRisk = 0
        hypoInd = '-'
        hyperInd = '-'
        gauge2_title = 'Not enough data'
    else:
        gauge2_title = 'Risk'

    data = jsonify({
        'gauge2_value1': hypoRisk,
        'gauge2_value2': hyperRisk,
        'hypoInd': hypoInd,
        'hyperInd': hyperInd,
        'gauge2_title': gauge2_title
        })

    res = make_response(data,200)

    return res

#########################################################################################################################

@app.route('/glucRTrace', methods=['GET', 'POST'])
def glucRTrace():
    
    app.logger.info('/glucMetrics1/gauge2-changed. Username: ' + current_user.username + '. Risk index routine')

    subject = db.session.query(Subject).filter_by(username=current_user.username).first() # Gets user

    ins_device        = db.session.query(PumpDevice).filter_by(subject_id=subject.id).order_by(PumpDevice.id.desc()).first()
    ins_device_tz_str = ins_device.tz
    ins_device_tz     = gettz(ins_device_tz_str)

    local_time_now = datetime.datetime.now()
    today_utc = datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=datetime.timezone.utc)
    t0_utc   = int((today_utc).timestamp())
    t0_local = int(datetime.datetime(local_time_now.year,local_time_now.month,local_time_now.day,tzinfo=ins_device_tz).timestamp())
    utcOffset = t0_utc - t0_local

    sfData = np.array([])

    for ii in range(2,-1,-1):
        odf_utc = today_utc-datetime.timedelta(days=ii)
        date_file = str(odf_utc.year)+'-'+str(odf_utc.month)+'-'+str(odf_utc.day)
        t0_local = int(datetime.datetime(odf_utc.year,odf_utc.month,odf_utc.day,tzinfo=ins_device_tz).timestamp())
        fileName = 'backendFiles/'+subject.username+'_'+date_file
        fileName = fileName+'/'+subject.username+'.json'
        
        try:
            data = read_jsonFile(fileName)
            timeStampIni = t0_local-18*60*60 # 
            timeStampEnd = t0_local+6*60*60-1 #
            sfData_aux = sort_filter_data(data,timeStampIni,timeStampEnd,utcOffset)
        except:
            sfData_aux = np.array([])
        
        sfData = np.append(sfData,sfData_aux)

    glucoseData = extract_glucoseData(sfData,utcOffset)

    timestamps = [datetime.datetime.fromtimestamp(ti+utcOffset,tz=datetime.timezone.utc).strftime('%x %H:%M:%S') for ti in glucoseData[0]]
    BG_values = glucoseData[1]
    current_date = pd.to_datetime(str(today_utc.month)+'/'+str(today_utc.day)+'/'+str(today_utc.year))
    
    BAMp = {'RT_image_path': 'BAM_testing',
        'STS_LBGI_breakpoints': [4, 7],
        'STS_LBGI_interpretations': ['Low', 'Medium', 'High'],
        'STS_HBGI_breakpoints': [4, 7],
        'STS_HBGI_interpretations': ['Low', 'Medium', 'High'],
        'LBGI_bounds': [0, 2.94],
        'HBGI_bounds': [0, 23.01],
        'ADRR_bounds': [0, 78.24],
        'RT_num_days': 3,  # Number of days to plot on the risk trace image
       }
    
    current_date = pd.to_datetime(current_date)        
    BG_df, flag_1 = process_CGM_data(current_date, 
                                     timestamps, 
                                     BG_values,
                                     BAMp)
    LBGI_vals = BG_df.groupby('Date')['BG'] \
                        .apply(lambda BG_s: LBGI(BG_s)) \
                        .sort_index()
    HBGI_vals = BG_df.groupby('Date')['BG'] \
                        .apply(lambda BG_s: HBGI(BG_s)) \
                        .sort_index()

    the_risk_trace = risk_trace(current_date, LBGI_vals, HBGI_vals, BAMp)

    RT_plot(the_risk_trace[0], the_risk_trace[1], 'risk_trace', 'static/img')

    risk_title = ' '
    if np.isnan(the_risk_trace[0]).all():
        if np.isnan(the_risk_trace[0][0]):
            risk_title = 'Not enough data'

    print(the_risk_trace)

    strFile = 'static/img/risk_trace.png'
    with open(strFile, 'rb') as f:
        grid=base64.b64encode(f.read()).decode()

    return render_template('abc3.html',grid=grid, risk_title=risk_title,name=current_user.username)

#########################################################################################################################

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def Index():
    if request.method == 'POST':
        return render_template('index.html', name=current_user.username, flagFirstTUser=0, flagTutorial=1)
    else:
        try:
            subject = db.session.query(Subject).filter_by(
                username=current_user.username).first() # Gets user
        except:
            app.logger.error('/dashboard. Username: ' + current_user.username + '. An error has occurred when querying the user object')

        flagFirstTUser = subject.first_time_user
        if flagFirstTUser:    
            app.logger.info('/dashboard. Username: ' + current_user.username + '. First time login')
            try:
                db.session.query(Subject).filter(Subject.username==subject.username).update({Subject.first_time_user: 0},synchronize_session=False)
                db.session.commit()
            except:
                app.logger.error('/dashboard. Username: ' + current_user.username + '. An error has occurred when updating the FirstTimeUser field')
        return render_template('index.html', name=current_user.username, flagFirstTUser=flagFirstTUser, flagTutorial=0)

#########################################################################################################################

@app.route('/dashboard/calendar-changed', methods=['POST'])
@login_required
def calendar_changed():

    app.logger.info('/dashboard/calendar-changed. Username: ' + current_user.username + '. Calendar routine')

    req = request.get_json()

    # Timestamps from the UI come in UTC 
    d1_utc = req['d1'] # startDay
    d2_utc = req['d2'] # endDay

    app.logger.info('/dashboard/calendar-changed. Username: ' + current_user.username + '. d1_utc = ' + str(d1_utc) + '; d2_utc = ' + str(d2_utc))
    app.logger.info('/dashboard/calendar-changed. Username: ' + current_user.username + '. d1 = ' + datetime.datetime.utcfromtimestamp(d1_utc).strftime("%m/%d/%y") + 
        '; d2 = ' + datetime.datetime.utcfromtimestamp(d2_utc).strftime("%m/%d/%y"))

    try:

        # Get user
        try:
            subject = db.session.query(Subject).filter_by(
                username=current_user.username).first() 
        except:
            app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username + '. An error has occurred when querying the subject table')
        
        # Get utc offset    
        try:
            cgmTOff_d1 = db.session.query(CGM).filter(CGM.time >= d1_utc-60*60*12, CGM.time <= d2_utc,
                                CGM.cgm_device_subject_id == subject.id).first() # Get Toff
            d1_utcOffset = cgmTOff_d1.utcOffset
            cgmTOff_d2 = db.session.query(CGM).filter(CGM.time >= d1_utc-60*60*12, CGM.time <= d2_utc,
                                CGM.cgm_device_subject_id == subject.id).order_by(CGM.id.desc()).first() # Get Toff
            d2_utcOffset = cgmTOff_d2.utcOffset
            if d1_utcOffset!=d2_utcOffset:
                if d2_utc-d1_utc < 86400:
                    d1_utcOffset=d2_utcOffset
        except:
            app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username + '. An error has occurred when querying the cgm table - tz. '
            'Probably no data available in the selected date range. Setting offsets to zero.')    
            d1_utcOffset = 0
            d2_utcOffset = 0
        
        app.logger.info('/dashboard/calendar-changed. Username: ' + current_user.username + '. d1_utcOffset = ' + str(d1_utcOffset) + '; d2_utcOffset = ' + str(d2_utcOffset))

        # Adjust time using utc offset 
        d1 = d1_utc - d1_utcOffset
        d2 = d2_utc - d2_utcOffset  

        app.logger.info('/dashboard/calendar-changed. Username: ' + current_user.username + '. d1 = ' + str(d1) + '; d2 = ' + str(d2))
        
        ###########################################################################
        # Display panel
        ###########################################################################

        # Get cgm records
        try:
            cgm = db.session.query(CGM).filter(CGM.time >= d1, CGM.time <= d2,
                                CGM.cgm_device_subject_id == subject.id)
        except:
            app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username + '. An error has occurred when querying the cgm table')
        
        # Generate cgm arrays for processing and visualization 
        cgmValueArray = [] 
        cgmTimeArray = []
        cgmToffArray = []

        for cgmS in cgm.all():
            cgmValueArray.append(float(cgmS.value)) # numpy doesn't understand decimal
            cgmTimeArray.append(cgmS.time)
            cgmToffArray.append(cgmS.utcOffset)
        
        # Compute cgm metrics
        try:
            metrics = compute_metrics_array(cgmValueArray,cgmTimeArray,cgmToffArray,d1_utc,d2_utc) # Computes all metrics, e.g., TIR, VAR, etc
            
            app.logger.info('/dashboard/calendar-changed[compute_metrics_array]. Username: ' + current_user.username + '. ' + str(metrics))
        except:
            app.logger.error('/dashboard/calendar-changed[compute_metrics_array]. Username: ' + current_user.username + '. An error has occurred when computing the CGM metrics')
        
        # Get model parameters
        try:
            modelPar = db.session.query(ModelParameters).filter(ModelParameters.timeini >= d1, ModelParameters.timeini <= d2,
                                                                ModelParameters.subject_id == subject.id)
        except:
            app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username +
                             '. An error has occurred when querying the model_parameters table')

        # Generate array of column names for ModelParameters
        xV = [a for a in dir(ModelParameters) if a.startswith('x')]
        xV.sort(key=len)

        # Generate array of model parameters
        try:
            modelPars, tOffV = generate_parArray(xV, modelPar.all(), True)

            app.logger.info('/dashboard/calendar-changed[generate_parArray]. Username: ' +
                            current_user.username + '. modelPars successfully generated')
        except:
            app.logger.error('/dashboard/calendar-changed[generate_parArray]. Username: ' +
                             current_user.username + '. An error has occurred when generating modelPars')

        # Computes data quality based on days with model parameters
        try:
            quality = compute_dataQuality_array(modelPars,d1_utc,d2_utc) 

            app.logger.info('/dashboard/calendar-changed[compute_dataQuality_array]. Username: ' + current_user.username + '. ' + str(quality))                                                               
        except:
            app.logger.error('/dashboard/calendar-changed[compute_dataQuality_array]. Username: ' + current_user.username + '. An error has occurred when computing the data quality')

        # Generate object used in the area chart
        try:
            glucSeries = compute_glucSeries_full(cgmTimeArray,cgmValueArray,cgmToffArray,d1_utc,d2_utc) 

            app.logger.info('/dashboard/calendar-changed[compute_glucSeries_full]. Username: ' + current_user.username + '. glucSeries successfully generated')                                                               
        except:
            app.logger.error('/dashboard/calendar-changed[compute_glucSeries_full]. Username: ' + current_user.username + '. An error has occurred when generating the object glucSeries')

        ###########################################################################
        # Replay panel
        ###########################################################################

        # Get basal patterns
        try:
            basalP = db.session.query(BasalProfile).filter(BasalProfile.timeini >= d1, BasalProfile.timeini <= d2,
                                BasalProfile.subject_id == subject.id) 
        except:
            app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username + '. An error has occurred when querying the basal_profile table')
        
        # Get CR patterns
        try:
            CRP = db.session.query(CRProfile).filter(CRProfile.timeini >= d1, CRProfile.timeini <= d2,
                                CRProfile.subject_id == subject.id) 
        except:
            app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username + '. An error has occurred when querying the CR_profile table')    

        # Get CF patterns
        try:            
            CFP = db.session.query(CFProfile).filter(CFProfile.timeini >= d1, CFProfile.timeini <= d2,
                                CFProfile.subject_id == subject.id) 
        except:
            app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username + '. An error has occurred when querying the CF_profile table')    
        
        # Get meal records
        try:
            meals = db.session.query(Meal).filter(Meal.time >= d1, Meal.time <= d2,
                                Meal.subject_id == subject.id) 
        except:
            app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username + '. An error has occurred when querying the meal table')
        
        # Get insulin records
        try:
            insulin = db.session.query(Insulin).filter(Insulin.time >= d1, Insulin.time <= d2,
                                Insulin.pump_device_subject_id == subject.id) 
        except:
            app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username + '. An error has occurred when querying the insulin table')

        # Generate meal and HT arrays
        try:
            moM, moH = generate_mArrays_5min(meals.all())

            app.logger.info('/dashboard/calendar-changed[generate_mArrays_5min]. Username: ' + current_user.username + '. meal and HT arrays successfully generated')
        except:
            app.logger.error('/dashboard/calendar-changed[generate_mArrays_5min]. Username: ' + current_user.username + '. An error has occurred when generating the meal and HT arrays')

        # Compute number of hypo-treatments
        try:
            nHT = compute_nHT(moH,d1_utc,d2_utc)
            
            app.logger.info('/dashboard/calendar-changed[compute_nHT]. Username: ' + current_user.username + '. ' + str(nHT))
        except:
            app.logger.error('/dashboard/calendar-changed[compute_nHT]. Username: ' + current_user.username + '. An error has occurred when computing nHT')

        # Generate arrays of insulin boluses (basal, corr, meal)
        try:
            basalV = generate_iArray_5min(insulin.all(),'basal')
            corrV = generate_iArray_5min(insulin.all(),'corr')
            mealV = generate_iArray_5min(insulin.all(),'meal')

            app.logger.info('/dashboard/calendar-changed[generate_iArray_5min]. Username: ' + current_user.username + '. basalV, corrV, and mealV arrays successfully generated')
        except:
            app.logger.error('/dashboard/calendar-changed[generate_iArray_5min]. Username: ' + current_user.username + '. An error has occurred when generating the basalV, corrV, and mealV arrays')

        # Compute total daily basal and total daily insulin
        try:
            tdb,tdi = compute_td(basalV,corrV,mealV,d1_utc,d2_utc)

            app.logger.info('/dashboard/calendar-changed[compute_td]. Username: ' + current_user.username + '. tdb and tdi arrays successfully generated')
        except:
            app.logger.error('/dashboard/calendar-changed[compute_td]. Username: ' + current_user.username + '. An error has occurred when generating the tdb and tdi arrays')

        # Generate array of column names (same structure for all Basal, CF and CR)        
        tmtiV = [a for a in dir(BasalProfile) if a.startswith('tmti')] 
        tmtiV.sort(key=len)

        # Generate arrays of basal patterns and capture different profiles
        try:
            basals = generate_parArray(tmtiV,basalP.all(),False)
            bProfiles = extractProfiles(basals)

            app.logger.info('/dashboard/calendar-changed[generate_parArray & extractProfiles]. Username: ' + current_user.username + '. basal profiles successfully extracted')
        except:
            app.logger.error('/dashboard/calendar-changed[generate_parArray & extractProfiles]. Username: ' + current_user.username + '. An error has occurred when extracting the basal profiles')            

        # Generate arrays of CR patterns and capture different profiles
        try:
            crs = generate_parArray(tmtiV,CRP.all(),False)
            crProfiles = extractProfiles(crs)
            
            app.logger.info('/dashboard/calendar-changed[generate_parArray & extractProfiles]. Username: ' + current_user.username + '. CR profiles successfully extracted')
        except:
            app.logger.error('/dashboard/calendar-changed[generate_parArray & extractProfiles]. Username: ' + current_user.username + '. An error has occurred when extracting the CR profiles')                        

        # Generate arrays of CF patterns and capture different profiles
        try:
            cfs = generate_parArray(tmtiV,CFP.all(),False)
            cfProfiles = extractProfiles(cfs)
            
            app.logger.info('/dashboard/calendar-changed[generate_parArray & extractProfiles]. Username: ' + current_user.username + '. CF profiles successfully extracted')
        except:
            app.logger.error('/dashboard/calendar-changed[generate_parArray & extractProfiles]. Username: ' + current_user.username + '. An error has occurred when extracting the CF profiles')            

        # Create a response with the JSON representation of the given arguments
        apSystem = subject.apSystem
        try:
            data = jsonify({
                'metrics': metrics,
                'quality': quality,
                'glucSeries': glucSeries,
                'bProfiles': bProfiles,
                'crProfiles': crProfiles,
                'cfProfiles': cfProfiles,
                'moM': moM,
                'moH': moH,
                'nHT': nHT,
                'tdb': tdb,
                'tdi': tdi,
                'apSystem': apSystem
                })

            res = make_response(data,200)

            app.logger.info('/dashboard/calendar-changed[make_response]. Username: ' + current_user.username + '. JSON response successfully generated')
        except:
            app.logger.error('/dashboard/calendar-changed[make_response]. Username: ' + current_user.username + '. An error has occurred when generating the JSON response')            

    except exc.SQLAlchemyError as e:

        error = str(e.__dict__['orig'])
        res = make_response(jsonify({'error': error}), 204)

        app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username + '. 204')            
    except:
        
        res = make_response(jsonify({'error': 'Unexpected error!'}), 500) # who knows...
        app.logger.error('/dashboard/calendar-changed. Username: ' + current_user.username + '. 500')

    return res

#########################################################################################################################

@app.route('/dashboard/run-replay', methods=['POST'])
@login_required
def run_replay():

    app.logger.info('/dashboard/run-replay. Username: ' + current_user.username + '. Replay routine')

    req = request.get_json()

    # Timestamps from the UI come in UTC 
    d1_utc = req['d1']  # startDay
    d2_utc = req['d2']  # endDay

    app.logger.info('/dashboard/run-replay. Username: ' + current_user.username + '. d1_utc = ' + str(d1_utc) + '; d2_utc = ' + str(d2_utc))
    app.logger.info('/dashboard/run-replay. Username: ' + current_user.username + '. d1 = ' + datetime.datetime.utcfromtimestamp(d1_utc).strftime("%m/%d/%y") + 
        '; d2 = ' + datetime.datetime.utcfromtimestamp(d2_utc).strftime("%m/%d/%y"))

    # Data from UI
    bProfiles_full = req['bProfiles'] # Modified basal profiles from UI
    crProfiles_full = req['crProfiles'] # Modified CR profiles from UI
    cfProfiles_full = req['cfProfiles'] # Modified CF profiles from UI
    moM = req['moM'] # Modified meals from UI
    moH = req['moH'] # Hypo-treatments (cannot be modified)
    apSel = req['apSel'] # 0 - OL; 1 - Basal-IQ; 2 - Control-IQ
    adjIns = req['adjIns'] # 0 - Do not adjust overwritten insulin doses; 1 - Adjust them
    genIns = req['genIns'] # 0 - Do not generate new insulin doses; 1 - Generate them (if no under Control-IQ)
    adjHTs = req['adjHTs'] # 0 - Do not adjust detected hypo-treatments; 1 - Adjust them
    genHTs = req['genHTs'] # 0 - Do not generate new hypo-treatments; 1 - Generate them

    try:

        ###########################################################################
        # Adjust timestamps
        ###########################################################################

        # Get user
        try:
            subject = db.session.query(Subject).filter_by(
                username=current_user.username).first()
        except:
            app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                             '. An error has occurred when querying the subject table')

        # Get insulin duration
        ins_device = db.session.query(PumpDevice).filter_by(subject_id=subject.id).order_by(PumpDevice.id.desc()).first()
        insDur     = ins_device.ins_dur

        # Get utc offset 
        try:
            cgmTOff = db.session.query(CGM).filter(CGM.time >= d1_utc-60*60*12, CGM.time <= d2_utc,
                                                   CGM.cgm_device_subject_id == subject.id).first()  # Get Toff
            d1_utcOffset = cgmTOff.utcOffset
            cgmTOff = db.session.query(CGM).filter(CGM.time >= d1_utc-60*60*12, CGM.time <= d2_utc,
                                                   CGM.cgm_device_subject_id == subject.id).order_by(CGM.id.desc()).first()  # Get Toff
            d2_utcOffset = cgmTOff.utcOffset
            if d1_utcOffset!=d2_utcOffset:
                if d2_utc-d1_utc < 86400:
                    d1_utcOffset=d2_utcOffset
        except:
            app.logger.error('/dashboard/run-replay. Username: ' + current_user.username + '. An error has occurred when querying the cgm table - tz. '
            'Setting offsets to zero.')    
            d1_utcOffset = 0
            d2_utcOffset = 0
            
        app.logger.info('/dashboard/run-replay. Username: ' + current_user.username + '. d1_utcOffset = ' + str(d1_utcOffset) + '; d2_utcOffset = ' + str(d2_utcOffset))

        # Adjust time using utc offset 
        d1 = d1_utc - d1_utcOffset
        d2 = d2_utc - d2_utcOffset  

        app.logger.info('/dashboard/run-replay. Username: ' + current_user.username + '. d1 = ' + str(d1) + '; d2 = ' + str(d2))

        ###########################################################################
        # Generate blocks of days
        ###########################################################################

        # Generate array of column names for ModelParameters
        xV = [a for a in dir(ModelParameters) if a.startswith('x')]
        xV.sort(key=len)

        # Get model parameters
        try:
            modelPar = db.session.query(ModelParameters).filter(ModelParameters.timeini >= d1, ModelParameters.timeini <= d2,
                                                                ModelParameters.subject_id == subject.id)
        except:
            app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                             '. An error has occurred when querying the model_parameters table')

        # Generate array of model parameters
        try:
            modelPars, tOffV = generate_parArray(xV, modelPar.all(), True)

            app.logger.info('/dashboard/run-replay[generate_parArray]. Username: ' +
                            current_user.username + '. modelPars successfully generated')
        except:
            app.logger.error('/dashboard/run-replay[generate_parArray]. Username: ' +
                             current_user.username + '. An error has occurred when generating modelPars')

        # Timestamps for full date range
        d1_full = d1
        d2_full = d2

        d1_utc_full = d1_utc
        d2_utc_full = d2_utc

        # Generate blocks of days based on existence of avatars
        d1_block = [d1]
        d2_block = [d2]

        d1_utc_block = [d1_utc]
        d2_utc_block = [d2_utc]

        if len(modelPars) > 1:
            d1_block_h = d1
            d1_utc_block_h = d1_utc
            for i in range(0, len(modelPars)-1):
               if (modelPars[i+1][0] - modelPars[i][0] > 86400):
                   d2_block.append(modelPars[i][0]-tOffV[i]+86399)
                   d2_utc_block.append(modelPars[i][0]+86399)
                   d1_block_h = d2_block[-1]+1
                   d1_block.append(d1_block_h)
                   d1_utc_block_h = d2_utc_block[-1]+1
                   d1_utc_block.append(d1_utc_block_h)
                   
        d2_block_aux = np.copy(d2_block)
        d2_block.sort()
        sortInd_aux = np.argsort(np.array(d2_block_aux))
        d2_utc_block = np.array(d2_utc_block)[sortInd_aux].tolist()

        # Create answer variables
        replayGlucSeries_full = []
        replayTDB_full = []
        replayTDI_full = []
        replaynHT_full = []
        replayMetrics_full = {
            'cv': [],
            'lbgi': [],
            'hbgi': [],
            'percentR1': [],
            'percentR2': [],
            'percentR3': [],
            'percentR4': []
        }

        SumBolusMem = []
        J24h = []

        ###########################################################################
        # Block iteration
        ###########################################################################

        # Iterate over the detected blocks
        for i in range(0, len(d1_block)):

            d1 = d1_block[i]
            d2 = d2_block[i]
            d1_utc = d1_utc_block[i]
            d2_utc = d2_utc_block[i]

            app.logger.info('/dashboard/run-replay. Username: ' + current_user.username + '. Block num: ' + str(i+1) + '/' + str(len(d1_block)) + '. d1 = ' + str(d1) + '; d2 = ' + str(d2))

            ###########################################################################
            # Data within the active block of days
            ###########################################################################
           
            # Get model parameters
            try:
                modelPar = db.session.query(ModelParameters).filter(ModelParameters.timeini >= d1, ModelParameters.timeini <= d2,
                                                                    ModelParameters.subject_id == subject.id)  
            except:
                app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                 '. An error has occurred when querying the model_parameters table')
            
            # Generate array of model parameters
            try:
                modelPars, tOffV = generate_parArray(xV, modelPar.all(), True)

                app.logger.info(
                    '/dashboard/run-replay[generate_parArray]. Username: ' + current_user.username + '. modelPars successfully generated')
            except:
                app.logger.error(
                    '/dashboard/run-replay[generate_parArray]. Username: ' + current_user.username + '. An error has occurred when generating modelPars')

            mPar_tini_utc = modelPars[0][0]
            mPar_tini = mPar_tini_utc-tOffV[0]
            mPar_tend_utc = modelPars[-1][0]
            mPar_tend = mPar_tend_utc-tOffV[-1]

            g = db.session.query(CGM).filter(CGM.time >= mPar_tini-12*60*60, CGM.time < mPar_tini,
                                                   CGM.cgm_device_subject_id == subject.id).order_by(CGM.id.desc()).first()
            
            if g is not None:
                utcOffsetPrev = g.utcOffset
            else:
                utcOffsetPrev = tOffV[0]
            
            utcOffsetDiff = tOffV[0]-utcOffsetPrev
            
            bProfiles = extract_blockProfiles(
                bProfiles_full, d1_utc_full, mPar_tini_utc, mPar_tend_utc+86399)
            crProfiles = extract_blockProfiles(
                crProfiles_full, d1_utc_full, mPar_tini_utc, mPar_tend_utc+86399)
            cfProfiles = extract_blockProfiles(
                cfProfiles_full, d1_utc_full, mPar_tini_utc, mPar_tend_utc+86399)

            # Get cgm records
            try:
                cgm = db.session.query(CGM).filter(CGM.time >= mPar_tini, CGM.time <= mPar_tend+86399,
                                                   CGM.cgm_device_subject_id == subject.id)                                                   
            except:
                app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                 '. An error has occurred when querying the cgm table')

            # Number of days of the block of days
            ndays = len(modelPars)

            # Generate cgm arrays for processing and visualization
            cgmValueArray = []
            cgmTimeArray = []

            for cgmS in cgm.all():
                cgmValueArray.append(float(cgmS.value)) # numpy doesn't understand decimal
                cgmTimeArray.append(cgmS.time)          

            moM_block = extract_blockMeals(
                moM, mPar_tini_utc, mPar_tend_utc+86399)  

            # Get meal records
            try:
                meals = db.session.query(Meal).filter(Meal.time >= mPar_tini, Meal.time <= mPar_tend+86399,
                                    Meal.subject_id == subject.id)                                     
            except:
                app.logger.error('/dashboard/run-replay. Username: ' + current_user.username + '. An error has occurred when querying the meal table')

            # Generate meal and HT arrays
            try:
                moMorig, moH_block = generate_mArrays_5min(meals.all())

                app.logger.info('/dashboard/run-replay[generate_mArrays_5min]. Username: ' + current_user.username + '. meal and HT arrays successfully generated')
            except:
                app.logger.error('/dashboard/run-replay[generate_mArrays_5min]. Username: ' + current_user.username + '. An error has occurred when generating the meal and HT arrays')
            
            ###########################################################################
            # Data from previous day(s) necessary to run the simulation
            ###########################################################################

            # Get model parameters from previous day (if there are)
            try:
                modelPar_previousD = db.session.query(ModelParameters).filter(ModelParameters.timeini >= mPar_tini+utcOffsetDiff-60*60*24, ModelParameters.timeini < mPar_tini,
                                                                              ModelParameters.subject_id == subject.id)                                                             
            except:
                app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                 '. An error has occurred when querying the model_parameters table - Previous day')

            # Generate array of previous day's model parameters
            try:
                modelPars_previousD = generate_parArray(
                    xV, modelPar_previousD.all(), False)

                app.logger.info('/dashboard/run-replay[generate_parArray]. Username: ' +
                                current_user.username + '. modelPars_previousD successfully generated')
            except:
                app.logger.error('/dashboard/run-replay[generate_parArray]. Username: ' + current_user.username +
                                 '. An error has occurred when generating modelPars_previousD')

            # Get previous day's basal profile
            try:
                basalP_6 = db.session.query(BasalProfile).filter(BasalProfile.timeini >= mPar_tini+utcOffsetDiff-24*60*60, BasalProfile.timeini <mPar_tini,
                                                                 BasalProfile.subject_id == subject.id)
            except:
                app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                 '. An error has occurred when querying the basal_profile table')

            # If there is no previous day's basal profile, get some previous one.
            if len(basalP_6.all()) == 0:
                try:
                    basalP_6_aux = db.session.query(BasalProfile).filter(BasalProfile.timeini >= d1, BasalProfile.timeini <= d2,
                                                                         BasalProfile.subject_id == subject.id)
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                     '. An error has occurred when querying the basal_profile table - basalP_6')

            # Generate array of column names
            tmtiV = [a for a in dir(BasalProfile) if a.startswith('tmti')]
            tmtiV.sort(key=len)

            # Generate previous day's basal profiles (6 h & 24 h)
            try:
                # If there is no previous day's profile, get the last one available within the active block
                if len(basalP_6.all()) == 0:
                    bProfiles_6 = generate_xhparArray(
                        tmtiV, basalP_6_aux.order_by(BasalProfile.id.desc()).first() , 6)
                    bProfiles_24 = generate_xhparArray(
                        tmtiV, basalP_6_aux.order_by(BasalProfile.id.desc()).first(), 24)
                # Otherwise, use it
                else:
                    bProfiles_6 = generate_xhparArray(
                        tmtiV, basalP_6.first(), 6)
                    bProfiles_24 = generate_xhparArray(
                        tmtiV, basalP_6.first(), 24)
                app.logger.info('/dashboard/run-replay[generate_xhparArray]. Username: ' +
                                current_user.username + '. bProfiles_6 and _24 profiles successfully extracted')
            except:
                app.logger.error('/dashboard/run-replay[generate_xhparArray]. Username: ' + current_user.username +
                                 '. An error has occurred when extracting the basal_6 and _24 profiles')

            # Get last 6 hour insulin records
            try:
                insulin_6 = db.session.query(Insulin).filter(Insulin.time >= mPar_tini+utcOffsetDiff-6*60*60, Insulin.time < mPar_tini,
                                                             Insulin.pump_device_subject_id == subject.id) 
            except:
                app.logger.error('/dashboard/run-replay(' + current_user.username +
                                 '. An error has occurred when querying the insulin table - insulin_6')

            # Generate array of last 6 hour insulin records
            try:
                insulinV_6 = generate_xh_InsArray_5min(insulin_6.all(), 6)

                app.logger.info('/dashboard/run-replay[generate_xh_InsArray_5min]. Username: ' +
                                current_user.username + '. insulinV_6 array successfully generated')
            except:
                app.logger.error('/dashboard/run-replay[generate_xh_InsArray_5min]. Username: ' +
                                 current_user.username + '. An error has occurred when generating the insulinV_6 array. '
                                 'Probably no data available. Setting insulinV_6 to empty list')
                insulinV_6 = []

            # If insulinV_6 is empty, set it using basal rate pattern
            if len(insulinV_6) == 0:
                insulinV_6 = np.array(bProfiles_6)/12.0

            # Generate array of last 6 hour temp basal rate
            try:
                tempRV_6 = generate_xh_Ins_Attr_5min(
                    insulin_6.all(), 'temp_rate', 6)

                app.logger.info('/dashboard/run-replay[generate_xh_Ins_Attr_5min]. Username: ' +
                                current_user.username + '. tempRV_6 array successfully generated')
            except:
                app.logger.error('/dashboard/run-replay[generate_xh_Ins_Attr_5min]. Username: ' +
                                 current_user.username + '. An error has occurred when generating the tempRV_6 array')

            # If tempRV_6 is empty, set it to 100%
            if len(tempRV_6) == 0:
                tempRV_6 = [100.0]*72

            # Modify original basal profile using temp rate
            bProfilesM_6 = np.multiply(
                np.array(bProfiles_6), 0.01*np.array(tempRV_6))

            # Generate INSdif_6 array
            INSdif_6 = np.subtract(insulinV_6, bProfilesM_6/12.0)
            
            # Get insulin records within the active block of days
            try: 
                insulin = db.session.query(Insulin).filter(Insulin.time >= mPar_tini+utcOffsetDiff, Insulin.time <= mPar_tend+86399,
                                                           Insulin.pump_device_subject_id == subject.id)                                                             
            except:
                app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                 '. An error has occurred when querying the insulin table')

            # Generate arrays of insulin fields 
            try:
                bBolusV = generate_iArray_5min(insulin.all(), 'basal')
                cBolusV = generate_iArray_5min(insulin.all(), 'corr')
                mBolusV = generate_iArray_5min(insulin.all(), 'meal')
                choV = generate_iArray_5min(insulin.all(), 'cho')
                BT = generate_iArray_5min(insulin.all(), 'bolusType')
                corrDecl = generate_iArray_5min(insulin.all(), 'corrDeclined')
                lagB = generate_iArray_5min(insulin.all(), 'lagB')
                target = generate_iArray_5min(insulin.all(), 'target')
                userOv = generate_iArray_5min(insulin.all(), 'userOverW')
                tempR = generate_iArray_5min(insulin.all(), 'temp_rate')
                extB = generate_iArray_5min(insulin.all(), 'extended_bolus')
                extB_per = generate_iArray_5min(insulin.all(), 'extended_bolus_per')
                extB_dur = generate_iArray_5min(insulin.all(), 'extended_bolus_dur')

                app.logger.info('/dashboard/run-replay[generate_iArray_5min]. Username: ' + current_user.username +
                                '. basalV, cBolusV, mBolusV, choV, BT, userOv, and tempR arrays successfully generated')
            except:
                app.logger.error('/dashboard/run-replay[generate_iArray_5min]. Username: ' + current_user.username +
                                 '. An error has occurred when generating the basalV, cBolusV, mBolusV, choV, BT, userOv, and tempR arrays')

            ###########################################################################
            # OL; Basal-IQ; Control-IQ
            ###########################################################################

            ###########################################################################
            # Basal IQ activated
            if apSel == '1':

                # Get last 30 min cgm records
                try:
                    gVPred = db.session.query(CGM).filter(CGM.time > mPar_tini+utcOffsetDiff-60*20, CGM.time <= mPar_tini,
                                                             CGM.cgm_device_subject_id == subject.id)  
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                     '. An error has occurred when querying the cgm table')

                # Generate last 30 min glucose array
                try:
                    gVPred_20m = generate_xh_glucoseArray_5min(
                        gVPred.all(), 4, cgmValueArray[0])

                    app.logger.info('/dashboard/run-replay[generate_xh_glucoseArray_5min]. Username: ' +
                                    current_user.username + '. gVPred_20m array successfully generated')
                except:
                    app.logger.error('/dashboard/run-replay[generate_xh_glucoseArray_5min]. Username: ' +
                                     current_user.username + '. An error has occurred when generating the gVPred_20m array.'
                                     'Setting all samples to first cgm record.')
                    gVPred_20m = [cgmValueArray[0]]*4
                
                # Compute time of insulin suspension
                try:
                    rollWin = db.session.query(BasalIQ).filter(BasalIQ.time > mPar_tini+utcOffsetDiff-60*60*2.5, BasalIQ.time <= mPar_tini,
                                                             BasalIQ.subject_id == subject.id)
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                     '. An error has occurred when querying the basalIQ table')
                    rollWin = []
                
                try:
                    tInsSusp = compute_time_insSusp(rollWin.all())
                except:
                    tInsSusp = 0
                
                # Check if last record indicates current suspension
                try:
                    rollWin_last = rollWin.order_by(rollWin.id.desc()).first()
                    flagInsSusp = int(rollWin_last.insSusp)
                except:
                    flagInsSusp = 0

                # Generate dictionary with data for Basal-IQ to run
                apData = {
                    'flagInsSusp': flagInsSusp,
                    'tInsSusp': tInsSusp,
                    'gTPred': np.array([-15, -10, -5, 0]),
                    'gVPred': np.array(gVPred_20m)
                }

            ###########################################################################
            # Control IQ activated
            elif apSel == '2':
                
                flagDefCIQ = False
                # Get Control-IQ parameters within the active block of days
                try:
                    controlIQPar = db.session.query(ControlIQ).filter(ControlIQ.time >= mPar_tini+utcOffsetDiff, ControlIQ.time <= mPar_tend+86399,
                                                                      ControlIQ.subject_id == subject.id)  
                    
                    # Generate arrays of Control-IQ parameters
                    try:
                        EX, TDIpop, sleep, tgt = generate_controlIQPar_5min(controlIQPar.all())

                        app.logger.info('/dashboard/run-replay[generate_controlIQPar_5min]. Username: ' +
                                        current_user.username + '. controlIQ par arrays successfully generated')
                    except:
                        app.logger.error('/dashboard/run-replay[generate_controlIQPar_5min]. Username: ' + current_user.username +
                                         '. An error has occurred when generating the controlIQ par arrays')
                    
                    if len(controlIQPar.all())==0:
                        flagDefCIQ = True

                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                     '. An error has occurred when querying the controlIQ table')
                    flagDefCIQ = True

                if flagDefCIQ:
                    app.logger.info('/dashboard/run-replay[generate_controlIQPar_5min]. Username: ' +
                                        current_user.username + '. Error or no data -> Setting default CIQ parameters')

                    # Define default parameters
                    EX     = np.zeros((ndays, 288))
                    TDIpop = float(subject.TDIpop)*np.ones((ndays, 288))

                    tgt_aux = np.array([[159.2057, 158.5634, 157.5503, 156.0492, 153.9663, 151.2723, 148.0383, 144.4422, 140.7324, 137.1615, 
                                133.9247, 131.1315, 128.8104, 126.9339, 125.4450, 124.2775, 123.3679, 122.6612, 122.1121, 121.6846, 
                                121.3507, 121.0888, 120.8823, 120.7188, 120.5887, 120.4845, 120.4007, 120.3330, 120.2779, 120.2329, 
                                120.1961, 120.1657, 120.1405, 120.1196, 120.1022, 120.0876, 120.0753, 120.0649, 120.0561, 120.0487, 
                                120.0423, 120.0369, 120.0322, 120.0282, 120.0247, 120.0218, 120.0192, 120.0169, 120.0149, 120.0132, 
                                120.0117, 120.0104, 120.0093, 120.0082, 120.0073, 120.0065, 120.0058, 120.0052, 120.0047, 120.0042, 
                                120.0037, 120.0033, 120.0030, 120.0027, 120.0024, 120.0021, 120.0019, 120.0017, 120.0015, 120.0013, 
                                120.0012, 120.0010, 120.0009, 120.0008, 120.0007, 120.0006, 120.0005, 120.0004, 120.0004, 120.0003, 
                                120.0002, 120.0002, 120.0001, 120.0001, 120.0000, 120.0000, 120.0004, 120.0013, 120.0033, 120.0082, 
                                120.0218, 120.0649, 120.2329, 121.0888, 126.9339, 151.2723, 159.9130, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 160.0000, 
                                159.9999, 159.9993, 159.9968, 159.9884, 159.9658, 159.9130, 159.8021, 159.5884]])
                    tgt = np.copy(tgt_aux)
                    sleep_aux = np.ones((1,288))
                    sleep_aux[0][86:277] = 0
                    sleep = np.copy(sleep_aux)

                    for hh in range(0,ndays-1):
                        tgt   = np.vstack((tgt,tgt_aux))
                        sleep = np.vstack((sleep,sleep_aux))

                    EX     = EX.tolist()
                    TDIpop = TDIpop.tolist()
                    tgt    = tgt.tolist()
                    sleep  = sleep.tolist()
                # Get last 24 hour insulin records
                try:
                    insulin_24 = db.session.query(Insulin).filter(Insulin.time >= mPar_tini+utcOffsetDiff-24*60*60, Insulin.time < mPar_tini,
                                                                  Insulin.pump_device_subject_id == subject.id)  
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                     '. An error has occurred when querying the insulin table - insulin_24')

                # Generate array of last 24 hour insulin records
                try:
                    insulinV_24 = generate_xh_InsArray_5min(
                        insulin_24.all(), 24)

                    app.logger.info('/dashboard/run-replay[generate_xh_InsArray_5min]. Username: ' +
                                    current_user.username + '. insulinV_24 array successfully generated')
                except:
                    app.logger.error('/dashboard/run-replay[generate_xh_InsArray_5min]. Username: ' +
                                     current_user.username + '. An error has occurred when generating the insulinV_24 array')
                    insulinV_24 = []

                # If there is no data, use the basal rate
                #if len(insulinV_24) == 0:
                    #insulinV_24 = np.array(bProfiles_24)/12.0

                # On the first day of the first block go back 6 days
                if i == 0:
                    d2_prev = mPar_tini-86400*6

                # Compute the difference between the first day of the active block with the last day of the previous one
                dDiff = max(min(6, int(np.floor((mPar_tini-d2_prev)/86400))),0)

                # Get previous insulin records
                try:
                    insulin_Froll = db.session.query(Insulin).filter(Insulin.time >= mPar_tini-7*24*60*60+(144-24*dDiff)*60*60, Insulin.time < mPar_tini,
                                                                        Insulin.pump_device_subject_id == subject.id) 
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                        '. An error has occurred when querying the insulin table - insulin_Froll')
                    insulin_Froll = []

                # Get previous TDIpop records
                try:
                    TDIpop_Froll = db.session.query(ControlIQ).filter(ControlIQ.time >= mPar_tini-7*24*60*60+(144-24*dDiff)*60*60, ControlIQ.time < mPar_tini,
                                                                        ControlIQ.subject_id == subject.id)
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                        '. An error has occurred when querying the controlIQ table - TDIpop_Froll')
                    TDIpop_Froll = []
                
                if len(SumBolusMem)>0:
                    SumBolusMem_aux = SumBolusMem.tolist()
                else:
                    SumBolusMem_aux = []
                if len(J24h)>0:
                    J24h_aux = J24h.tolist()
                else:
                    J24h_aux = []

                # Generate SumBolusMem variable
                SumBolusMem = gen_SumBolusMem(SumBolusMem_aux,insulin_Froll,TDIpop_Froll,TDIpop[0][0],mPar_tini,dDiff,J24h_aux)

                # Get last 6 hour meal records (as informed)
                try:
                    meals_6 = db.session.query(Insulin).filter(Insulin.time >= mPar_tini+utcOffsetDiff-6*60*60, Insulin.time < mPar_tini,
                                                            Insulin.pump_device_subject_id == subject.id)
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                     '. An error has occurred when querying the meal table - meals_6')                                     

                # Generate array of last 6 hour meal records (as informed)
                try:
                    mealsV_6 = generate_xh_mealArray_Ins_5min(meals_6.all(), 6)

                    app.logger.info('/dashboard/run-replay[generate_xh_mealArray_Ins_5min]. Username: ' +
                                    current_user.username + '. mealsV_6 array successfully generated')
                except:
                    app.logger.error('/dashboard/run-replay[generate_xh_mealArray_Ins_5min]. Username: ' +
                                     current_user.username + '. An error has occurred when generating the mealsV_6 array')
                    mealsV_6 = [0.0]*72

                # Get last 6 hour cgm records
                try:
                    glucose_6 = db.session.query(CGM).filter(CGM.time >= mPar_tini+utcOffsetDiff-6*60*60, CGM.time < mPar_tini,
                                                             CGM.cgm_device_subject_id == subject.id)
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                     '. An error has occurred when querying the cgm table - glucose_6')

                # Generate array of last 6 hour cgm records
                try:
                    glucoseV_6 = generate_xh_glucoseArray_5min(
                        glucose_6.all(), 72, cgmValueArray[0])

                    app.logger.info('/dashboard/run-replay[generate_xh_glucoseArray_5min]. Username: ' +
                                    current_user.username + '. glucoseV_6 array successfully generated')
                except:
                    app.logger.error('/dashboard/run-replay[generate_xh_glucoseArray_5min]. Username: ' +
                                     current_user.username + '. An error has occurred when generating the glucoseV_6 array.'
                                     'Probably no available data. Setting all samples to first cgm record.')                 
                    glucoseV_6 = [cgmValueArray[0]]*72

                # Generate dictionary with data for Control-IQ to run
                apData = {
                    'EX': EX,
                    'tgt': tgt,
                    'sleep': sleep,
                    'TDIpop': TDIpop,
                    'SumBolusMem': SumBolusMem,
                    'mealsV_6': mealsV_6,
                    'glucoseV_6': glucoseV_6,
                    'insulinV_6': insulinV_6,
                    'insulinV_24': insulinV_24
                }

            # If no APS is selected, set apData to an empty list
            else:
                apData = []

            if len(crProfiles)>len(bBolusV):
                crProfiles_aux = crProfiles[-len(bBolusV):]
            else:
                crProfiles_aux = crProfiles
            
            if len(cfProfiles)>len(bBolusV):
                cfProfiles_aux = cfProfiles[-len(bBolusV):]
            else:
                cfProfiles_aux = cfProfiles

            crProfiles = crProfiles_aux
            cfProfiles = cfProfiles_aux

            # Generate dictionary with data to run the replay simulation
            try:
                dataSim = {
                    'tOffV': tOffV,
                    'bProfiles': bProfiles,
                    'crProfiles': crProfiles,
                    'cfProfiles': cfProfiles,
                    'bBolusV': bBolusV,
                    'cBolusV': cBolusV,
                    'mBolusV': mBolusV,
                    'choV': choV,
                    'BT': BT,
                    'lagB': lagB,
                    'corrDecl': corrDecl,
                    'target': target,
                    'userOv': userOv,
                    'tempR': tempR,
                    'extB': extB,
                    'extB_per': extB_per,
                    'extB_dur': extB_dur,
                    'moM': moM_block,
                    'moH': moH_block,
                    'INSdif_6': INSdif_6,
                    'bProfiles_6': bProfiles_6,
                    'insulinV_6': insulinV_6,
                    'modelPars_previousD': modelPars_previousD,
                    'cgmValueArray': cgmValueArray,
                    'apSel': apSel,
                    'adjIns': adjIns,
                    'genIns': genIns,
                    'adjHTs': adjHTs,
                    'genHTs': genHTs,
                    'apData': apData,
                    'BW': float(subject.weight),
                    'insDur': insDur
                }

                app.logger.info(
                    '/dashboard/run-replay. Username: ' + current_user.username + '. dataSim successfully generated')
            except:
                app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                 '. An error has occurred when generating dataSim')

            # Run the replay simulation
            try:
                resSim = replaySim_preProc_v2(modelPars, dataSim)
                replayGlucSeries = resSim['glucReplayPack']
                htReplayPack = resSim['htReplayPack']
                basalReplayPack = resSim['basalReplayPack']
                cBolusReplayPack = resSim['cBolusReplayPack']
                mBolusReplayPack = resSim['mBolusReplayPack']
                SumBolusMem = resSim['SumBolusMem']
                J24h = resSim['J24h']
                
                lastBasalReplay_f = resSim['lastBasalReplay_f']
                lastCBolusReplay_f = resSim['lastCBolusReplay_f']
                lastMBolusReplay_f = resSim['lastMBolusReplay_f']
                lastCBolusReplay = resSim['lastCBolusReplay']
                lastMBolusReplay = resSim['lastMBolusReplay']
                lastBTReplay_f = resSim['lastBTReplay_f']

                app.logger.info(
                    '/dashboard/run-replay[replaySim_preProc]. Username: ' + current_user.username + '. Replay sim successfully executed')
            except:
                app.logger.error(
                    '/dashboard/run-replay[replaySim_preProc]. Username: ' + current_user.username + '. An error has occurred when executing the replay sim')

            cgmValueArray_sim = []
            cgmTimeArray_sim = []
            cgmToffArray_sim = []

            # Generate replayed cgm list
            for ii in range(0, len(replayGlucSeries)):
                cgmValueArray_sim.extend(replayGlucSeries[ii][1])
                cgmTimeArray_sim.append(modelPars[ii][0]-tOffV[ii])
                cgmToffArray_sim.append(tOffV[ii])
                for jj in range(1, 288):
                    cgmTimeArray_sim.append(modelPars[ii][0]-tOffV[ii]+300*jj)
                    cgmToffArray_sim.append(tOffV[ii])
            
            # Capture non-playable data
            # Get cgm records
            try:
                cgm = db.session.query(CGM).filter(CGM.time >= d1, CGM.time < mPar_tini,
                                                   CGM.cgm_device_subject_id == subject.id)                                                   
            except:
                app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                 '. An error has occurred when querying the cgm table')

            cgmValueArray_fixed_pre = []
            cgmTimeArray_fixed_pre = []
            cgmToffArray_fixed_pre = []

            # Generate fixed cgm list
            for cgmS in cgm.all():
                cgmValueArray_fixed_pre.append(float(cgmS.value)) # numpy doesn't understand decimal
                cgmTimeArray_fixed_pre.append(cgmS.time)
                cgmToffArray_fixed_pre.append(cgmS.utcOffset)

            cgmValueArray_fixed_post = []
            cgmTimeArray_fixed_post = []
            cgmToffArray_fixed_post = []

            # Get fixed insulin records
            bBolusV_fixed_pre = []
            cBolusV_fixed_pre = []
            mBolusV_fixed_pre = []
            bBolusV_fixed_post = []
            cBolusV_fixed_post = []
            mBolusV_fixed_post = []

            try:
                insulin = db.session.query(Insulin).filter(Insulin.time >= d1, Insulin.time < mPar_tini,
                                                           Insulin.pump_device_subject_id == subject.id)                                                             
            except:
                app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                 '. An error has occurred when querying the insulin table')

            # Generate arrays of fixed insulin fields 
            try:
                bBolusV_fixed_pre = generate_iArray_5min(insulin.all(), 'basal')
                cBolusV_fixed_pre = generate_iArray_5min(insulin.all(), 'corr')
                mBolusV_fixed_pre = generate_iArray_5min(insulin.all(), 'meal')
                app.logger.info('/dashboard/run-replay[generate_iArray_5min]. Username: ' + current_user.username +
                                '. basalV_fixed_pre, cBolusV_fixed_pre, and mBolusV_fixed_pre arrays successfully generated')
            except:
                app.logger.error('/dashboard/run-replay[generate_iArray_5min]. Username: ' + current_user.username +
                                 '. An error has occurred when generating the basalV_fixed_pre, cBolusV_fixed_pre, and mBolusV_fixed_pre arrays')

            # Get fixed meal records
            moM_fixed_pre = []
            moH_fixed_pre = []
            moM_fixed_post = []
            moH_fixed_post = []

            try:
                meals = db.session.query(Meal).filter(Meal.time >= d1, Meal.time < mPar_tini,
                                    Meal.subject_id == subject.id)                                     
            except:
                app.logger.error('/dashboard/run-replay. Username: ' + current_user.username + '. An error has occurred when querying the meal table')

            # Generate fixed meal and HT arrays
            try:
                moM_fixed_pre, moH_fixed_pre = generate_mArrays_5min(meals.all())

                app.logger.info('/dashboard/run-replay[generate_mArrays_5min]. Username: ' + current_user.username + '. moM_fixed_pre and moH_fixed_pre arrays successfully generated')
            except:
                app.logger.error('/dashboard/run-replay[generate_mArrays_5min]. Username: ' + current_user.username + '. An error has occurred when generating the moM_fixed_pre and moH_fixed_pre arrays')

            if i==len(d1_block)-1:
                # Get cgm records
                try:
                    cgm = db.session.query(CGM).filter(CGM.time >= mPar_tend+86400, CGM.time <= d2,
                                                    CGM.cgm_device_subject_id == subject.id)                                                    
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                    '. An error has occurred when querying the cgm table')

                # Generate fixed cgm list
                for cgmS in cgm.all():
                    cgmValueArray_fixed_post.append(float(cgmS.value)) # numpy doesn't understand decimal
                    cgmTimeArray_fixed_post.append(cgmS.time)
                    cgmToffArray_fixed_post.append(cgmS.utcOffset)

                # Get fixed insulin records
                try: 
                    insulin = db.session.query(Insulin).filter(Insulin.time >= mPar_tend+86400, Insulin.time <= d2,
                                                            Insulin.pump_device_subject_id == subject.id)                                                              
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username +
                                    '. An error has occurred when querying the insulin table')

                # Generate arrays of fixed insulin fields 
                try:
                    bBolusV_fixed_post = generate_iArray_5min(insulin.all(), 'basal')
                    cBolusV_fixed_post = generate_iArray_5min(insulin.all(), 'corr')
                    mBolusV_fixed_post = generate_iArray_5min(insulin.all(), 'meal')
                    app.logger.info('/dashboard/run-replay[generate_iArray_5min]. Username: ' + current_user.username +
                                    '. basalV_fixed_post, cBolusV_fixed_post, and mBolusV_fixed_post arrays successfully generated')
                except:
                    app.logger.error('/dashboard/run-replay[generate_iArray_5min]. Username: ' + current_user.username +
                                    '. An error has occurred when generating the basalV_fixed_post, cBolusV_fixed_post, and mBolusV_fixed_post arrays')

                # Get fixed meal records                
                try:
                    meals = db.session.query(Meal).filter(Meal.time >= mPar_tend+86400, Meal.time <= d2,
                                        Meal.subject_id == subject.id)                                         
                except:
                    app.logger.error('/dashboard/run-replay. Username: ' + current_user.username + '. An error has occurred when querying the meal table')

                # Generate fixed meal and HT arrays
                try:
                    moM_fixed_post, moH_fixed_post = generate_mArrays_5min(meals.all())

                    app.logger.info('/dashboard/run-replay[generate_mArrays_5min]. Username: ' + current_user.username + '. moM_fixed_post and moH_fixed_post arrays successfully generated')
                except:
                    app.logger.error('/dashboard/run-replay[generate_mArrays_5min]. Username: ' + current_user.username + '. An error has occurred when generating the moM_fixed_post and moH_fixed_post arrays')

            cgmValueArray_replay = cgmValueArray_fixed_pre+cgmValueArray_sim+cgmValueArray_fixed_post
            cgmTimeArray_replay = cgmTimeArray_fixed_pre+cgmTimeArray_sim+cgmTimeArray_fixed_post
            cgmToffArray_replay = cgmToffArray_fixed_pre+cgmToffArray_sim+cgmToffArray_fixed_post            
            replayGlucSeries_block = compute_glucSeries_full(cgmTimeArray_replay,cgmValueArray_replay,cgmToffArray_replay,d1_utc,d2_utc) 
            
            replayGlucSeries_full = replayGlucSeries_full+replayGlucSeries_block

            try:
                # Compute replay metrics
                replayMetrics = compute_metrics_array(
                    cgmValueArray_replay, cgmTimeArray_replay, cgmToffArray_replay, d1_utc, d2_utc)
                
                for metric, metricList in replayMetrics_full.items():
                    replayMetrics_full[metric] = metricList+replayMetrics[metric]

                app.logger.info(
                    '/dashboard/run-replay[compute_metrics_array]. Username: ' + current_user.username + '. Replay CGM metrics: ' + str(replayMetrics))
            except:
                app.logger.error('/dashboard/run-replay[compute_metrics_array]. Username: ' + current_user.username +
                                 '. An error has occurred when computing the replay CGM metrics')

            htReplayPack = moH_fixed_pre+htReplayPack+moH_fixed_post

            try:
                replaynHT = compute_nHT(htReplayPack, d1_utc, d2_utc)

                replaynHT_full = replaynHT_full+replaynHT

                app.logger.info(
                    '/dashboard/run-replay[compute_nHT]. Username: ' + current_user.username + '. Replay nHT: ' + str(replaynHT))
            except:
                app.logger.error(
                    '/dashboard/run-replay[compute_nHT]. Username: ' + current_user.username + '. An error has occurred when computing the replay nHT')

            basalReplayPack = bBolusV_fixed_pre+basalReplayPack+bBolusV_fixed_post            
            cBolusReplayPack = cBolusV_fixed_pre+cBolusReplayPack+cBolusV_fixed_post
            mBolusReplayPack = mBolusV_fixed_pre+mBolusReplayPack+mBolusV_fixed_post

            try:
                replayTDB, replayTDI = compute_td(
                    basalReplayPack, cBolusReplayPack, mBolusReplayPack, d1_utc, d2_utc)

                replayTDB_full = replayTDB_full+replayTDB
                replayTDI_full = replayTDI_full+replayTDI

                app.logger.info('/dashboard/run-replay[compute_td]. Username: ' + current_user.username +
                                '. Replay tdb and tdi arrays successfully generated. replayTDB: ' + str(replayTDB) + '. replayTDI: ' + str(replayTDI))
            except:
                app.logger.error('/dashboard/run-replay[compute_td]. Username: ' + current_user.username +
                                 '. An error has occurred when generating the replay tdb and tdi arrays')
            
            # Update d2_prev
            d2_prev = d2

        # Send response
        try:

            data = jsonify({
                'metrics': replayMetrics_full,
                'glucSeries': replayGlucSeries_full,
                'nHT': replaynHT_full,
                'tdi': replayTDI_full,
                'tdb': replayTDB_full
            })

            res = make_response(data, 200)

            app.logger.info(
                '/dashboard/run-replay[make_response]. Username: ' + current_user.username + '. JSON response successfully generated')
        except:
            app.logger.error('/dashboard/run-replay[make_response]. Username: ' + current_user.username +
                             '. An error has occurred when generating the JSON response')

    except exc.SQLAlchemyError as e:

        error = str(e.__dict__['orig'])
        res = make_response(jsonify({'error': error}), 204)

        app.logger.error(
            '/dashboard/run-replay[make_response]. Username: ' + current_user.username + '. 204')

    except:

        # who knows...
        res = make_response(jsonify({'error': 'Unexpected error!'}), 500)

        app.logger.error(
            '/dashboard/run-replay[make_response]. Username: ' + current_user.username + '. 500')

    return res

#########################################################################################################################

@app.route('/support')
@login_required
def support():
    app.logger.info('/support. Username: ' + current_user.username + '. Viewing the Support page')
    return render_template('support.html', name=current_user.username)

#########################################################################################################################

@app.route('/about')
@login_required
def about():
    app.logger.info('/about. Username: ' + current_user.username + '. Viewing the About page')
    return render_template('about.html', name=current_user.username)

#########################################################################################################################

@app.route('/dashboard/generate-report', methods=['POST'])
@login_required
def generate_report():
    try:

        app.logger.info('/dashboard/generate-report. Username: ' + current_user.username + '. Report routine')

        req = request.get_json()
        d1_utc = req['d1'] # startDay
        d2_utc = req['d2'] # endDay

        apSel = req['apSel']
        adjIns = req['adjIns']
        genIns = req['genIns']
        adjHTs = req['adjHTs']
        genHTs = req['genHTs']

        app.logger.info('/dashboard/generate-report. Username: ' + current_user.username + '. d1 = ' + datetime.datetime.utcfromtimestamp(d1_utc).strftime("%m/%d/%y") + 
        '; d2 = ' + datetime.datetime.utcfromtimestamp(d2_utc).strftime("%m/%d/%y"))

        if apSel == '0':
            apSel_rep = 'No APS'
        elif apSel == '1':
            apSel_rep = 'Basal-IQ'
        else:
            apSel_rep = 'Control-IQ'
        
        if adjIns:
            adjIns_rep = 'Yes'
        else:
            adjIns_rep = 'No'

        if genIns:
            genIns_rep = 'Yes'
        else:
            genIns_rep = 'No'

        if adjHTs:
            adjHTs_rep = 'Yes'
        else:
            adjHTs_rep = 'No'

        if genHTs:
            genHTs_rep = 'Yes'
        else:
            genHTs_rep = 'No'    

        # Get user
        try:
            subject = db.session.query(Subject).filter_by(
                username=current_user.username).first() 
        except:
            app.logger.error('/dashboard/generate-report. Username: ' + current_user.username + '. An error has occurred when querying the subject table')
        
        # Get utc offset    
        try:
            cgmTOff_d1 = db.session.query(CGM).filter(CGM.time >= d1_utc-60*60*12, CGM.time <= d2_utc,
                                CGM.cgm_device_subject_id == subject.id).first() # Get Toff
            d1_utcOffset = cgmTOff_d1.utcOffset
            cgmTOff_d2 = db.session.query(CGM).filter(CGM.time >= d1_utc-60*60*12, CGM.time <= d2_utc,
                                CGM.cgm_device_subject_id == subject.id).order_by(CGM.id.desc()).first() # Get Toff
            d2_utcOffset = cgmTOff_d2.utcOffset
        except:
            app.logger.error('/dashboard/generate-report. Username: ' + current_user.username + '. An error has occurred when querying the cgm table - tz. '
            'Probably no data available in the selected date range. Setting offsets to zero.')    
            d1_utcOffset = 0
            d2_utcOffset = 0
        
        app.logger.info('/dashboard/generate-report. Username: ' + current_user.username + '. d1_utcOffset = ' + str(d1_utcOffset) + '; d2_utcOffset = ' + str(d2_utcOffset))

        # Adjust time using utc offset 
        d1 = d1_utc - d1_utcOffset
        d2 = d2_utc - d2_utcOffset  

        app.logger.info('/dashboard/generate-report. Username: ' + current_user.username + '. d1 = ' + str(d1) + '; d2 = ' + str(d2))

        replay = req['replay']
        original = req['original']

        try:
            replay_profiles = {
                'bProfiles': req['bProfiles'],
                'crProfiles': req['crProfiles'],
                'cfProfiles': req['cfProfiles']
            }

            original_profiles = {
                'bProfiles': original['bProfiles'],
                'crProfiles': original['crProfiles'],
                'cfProfiles': original['cfProfiles']
            }

            app.logger.info('/dashboard/generate-report. Username: ' + current_user.username + '. replay_profiles and original_profiles successfully generated')
        except:
            app.logger.error('/dashboard/generate-report. Username: ' + current_user.username + '. An error has occurred when generating replay_profiles and original_profiles')

        if "bProfiles" in replay:
            app.logger.info('/dashboard/generate-report. Username: ' + current_user.username + '. No data from replay sim -> replay=original')
            replay = original
        else:
            app.logger.info('/dashboard/generate-report. Username: ' + current_user.username + '. There are data from replay sim')

        #path_wkthmltopdf = r'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
        path_wkthmltopdf = r'/usr/local/bin/wkhtmltopdf'
        try:
            config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)

            app.logger.info('/dashboard/generate-report. Username: ' + current_user.username + '. wkthmltopdf successfully configured')
        except:
            app.logger.error('/dashboard/generate-report. Username: ' + current_user.username + '. An error has occurred when configuring wkthmltopdf')
        
        try:
            tirs,cvs,tdis,tdbs,hypors,hypers,hts = meanMetrics(original,replay)
            
            app.logger.info('/dashboard/generate-report[meanMetrics]. Username: ' + current_user.username + '. tirs,cvs,tdis,tdbs,hypors,hypers, and hts arrays successfully computed')
        except:
            app.logger.error('/dashboard/generate-report[meanMetrics]. Username: ' + current_user.username + '. An error has occurred when computing the tirs,cvs,tdis,tdbs,hypors,hypers, and hts arrays')

        try:
            tir_string = tirChart(tirs)

            app.logger.info('/dashboard/generate-report[tirChart]. Username: ' + current_user.username + '. tirChart successfully generated')
        except:
            app.logger.error('/dashboard/generate-report[tirChart]. Username: ' + current_user.username + '. An error has occurred when generating the tirChart')

        try:
            gluc_string = glucChart(original['glucSeries'],replay['glucSeries'])

            app.logger.info('/dashboard/generate-report[glucChart]. Username: ' + current_user.username + '. glucChart successfully generated')
        except:
            app.logger.error('/dashboard/generate-report[glucChart]. Username: ' + current_user.username + '. An error has occurred when generating the glucChart')

        try:        
            logo_string = logoChart()
        
            app.logger.info('/dashboard/generate-report[logoChart]. Username: ' + current_user.username + '. logoChart successfully generated')
        except:
            app.logger.error('/dashboard/generate-report[logoChart]. Username: ' + current_user.username + '. An error has occurred when generating the logoChart')


        auxD1 = datetime.datetime.fromtimestamp(d1_utc,tz=datetime.timezone.utc)
        startD = auxD1.strftime('%d %b %Y')
        auxD2 = datetime.datetime.fromtimestamp(d2_utc,tz=datetime.timezone.utc)
        endD = auxD2.strftime('%d %b %Y')
        dateRange = startD+' - '+endD

        try:
            mProfile_string,mProfile_dates,m_orig_t,m_orig_v,m_replay_t,m_replay_v,m_diff = profileChart(original['moM'],req['moM'],'meal',d2_utc,288,'5min')
            
            app.logger.info('/dashboard/generate-report[profileChart]. Username: ' + current_user.username + '. mProfile successfully generated')
        except:
            app.logger.error('/dashboard/generate-report[profileChart]. Username: ' + current_user.username + '. An error has occurred when generating the mProfile')

        try:
            bProfile_string,bProfile_dates,bp_orig_t,bp_orig_v,bp_replay_t,bp_replay_v,bp_diff = profileChart(original_profiles['bProfiles'],replay_profiles['bProfiles'],'bp',d2_utc,48,'30min')
            
            app.logger.info('/dashboard/generate-report[profileChart]. Username: ' + current_user.username + '. bProfile successfully generated')
        except:
            app.logger.error('/dashboard/generate-report[profileChart]. Username: ' + current_user.username + '. An error has occurred when generating the bProfile')            

        try:    
            cfProfile_string,cfProfile_dates,cf_orig_t,cf_orig_v,cf_replay_t,cf_replay_v,cf_diff = profileChart(original_profiles['cfProfiles'],replay_profiles['cfProfiles'],'cfp',d2_utc,48,'30min')
            
            app.logger.info('/dashboard/generate-report[profileChart]. Username: ' + current_user.username + '. cfProfile successfully generated')
        except:
            app.logger.error('/dashboard/generate-report[profileChart]. Username: ' + current_user.username + '. An error has occurred when generating the cfProfile')
        
        try:
            crProfile_string,crProfile_dates,cr_orig_t,cr_orig_v,cr_replay_t,cr_replay_v,cr_diff = profileChart(original_profiles['crProfiles'],replay_profiles['crProfiles'],'crp',d2_utc,48,'30min')
            
            app.logger.info('/dashboard/generate-report[profileChart]. Username: ' + current_user.username + '. crProfile successfully generated')
        except:
            app.logger.error('/dashboard/generate-report[profileChart]. Username: ' + current_user.username + '. An error has occurred when generating the crProfile')
                
        try:
            rendered =  render_template('report.html',logo_string=logo_string,name=current_user.username,gluc_string=gluc_string,pie_string=tir_string,dateRange=dateRange,\
            apSel_rep=apSel_rep,adjIns_rep=adjIns_rep,genIns_rep=genIns_rep,adjHTs_rep=adjHTs_rep,genHTs_rep=genHTs_rep,\
            bProfile_string=bProfile_string,bProfile_dates=bProfile_dates,\
            crProfile_string=crProfile_string,crProfile_dates=crProfile_dates,\
            cfProfile_string=cfProfile_string,cfProfile_dates=cfProfile_dates,\
            mProfile_string=mProfile_string,mProfile_dates=mProfile_dates,\
            o_70=np.around(tirs[0,0],decimals=1),o_70180=np.around(tirs[1,0],decimals=1),o_180250=np.around(tirs[2,0],decimals=1),o_250=np.around(tirs[3,0],decimals=1),\
            r_70=np.around(tirs[0,1],decimals=1),r_70180=np.around(tirs[1,1],decimals=1),r_180250=np.around(tirs[2,1],decimals=1),r_250=np.around(tirs[3,1],decimals=1),\
            d_70=np.around(tirs[0,1]-tirs[0,0],decimals=1),d_70180=np.around(tirs[1,1]-tirs[1,0],decimals=1),d_180250=np.around(tirs[2,1]-tirs[2,0],decimals=1),d_250=np.around(tirs[3,1]-tirs[3,0],decimals=1),\
            o_tdi=np.around(tdis[0],decimals=1),o_tdb=np.around(tdbs[0],decimals=1),o_var=np.around(cvs[0],decimals=1),o_hypor=np.around(hypors[0],decimals=1),o_hyper=np.around(hypers[0],decimals=1),o_ht=np.around(hts[0],decimals=1),\
            r_tdi=np.around(tdis[1],decimals=1),r_tdb=np.around(tdbs[1],decimals=1),r_var=np.around(cvs[1],decimals=1),r_hypor=np.around(hypors[1],decimals=1),r_hyper=np.around(hypers[1],decimals=1),r_ht=np.around(hts[1],decimals=1),\
            bp_orig_t=bp_orig_t,bp_orig_v=bp_orig_v,bp_replay_v=bp_replay_v,bp_diff=bp_diff,\
            cr_orig_t=cr_orig_t,cr_orig_v=cr_orig_v,cr_replay_v=cr_replay_v,cr_diff=cr_diff,\
            cf_orig_t=cf_orig_t,cf_orig_v=cf_orig_v,cf_replay_v=cf_replay_v,cf_diff=cf_diff,\
            m_orig_t=m_orig_t,m_orig_v=m_orig_v,m_replay_t=m_replay_t,m_replay_v=m_replay_v,\
            d_tdi=np.around(tdis[1]-tdis[0],decimals=1),d_tdb=np.around(tdbs[1]-tdbs[0],decimals=1),d_var=np.around(cvs[1]-cvs[0],decimals=1),d_hypor=np.around(hypors[1]-hypors[0],decimals=1),d_hyper=np.around(hypers[1]-hypers[0],decimals=1),d_ht=np.around(hts[1]-hts[0],decimals=1))

            app.logger.info('/dashboard/generate-report[render_template]. Username: ' + current_user.username + '. template successfully rendered')
        except:
            app.logger.error('/dashboard/generate-report[render_template]. Username: ' + current_user.username + '. An error has occurred when rendering the template')

        try:
            pdf = pdfkit.from_string(rendered, False, configuration=config)

            app.logger.info('/dashboard/generate-report[pdfkit]. Username: ' + current_user.username + '. pdf successfully generated')
        except:
            app.logger.error('/dashboard/generate-report[pdfkit]. Username: ' + current_user.username + '. An error has occurred when generating the pdf')

        try:
            pdfEncode = base64.b64encode(pdf).decode()

            app.logger.info('/dashboard/generate-report[base64]. Username: ' + current_user.username + '. pdfEncode successfully generated')
        except:
            app.logger.error('/dashboard/generate-report[base64]. Username: ' + current_user.username + '. An error has occurred when generating the pdfEncode')            

        try:
            data = jsonify({
                'pdf': pdfEncode
                })

            res = make_response(data,200)
            
            app.logger.info('/dashboard/generate-report[make_response]. Username: ' + current_user.username + '. JSON response successfully generated')
        except:
            app.logger.error('/dashboard/generate-report[make_response]. Username: ' + current_user.username + '. An error has occurred when generating the JSON response')                        

    except:
        
        res = make_response(jsonify({'error': 'Unexpected error!'}), 500) # who knows...

        app.logger.error('/dashboard/generate-report[make_response]. Username: ' + current_user.username + '. 500') 

    return res

#########################################################################################################################

@app.route('/contact',methods=['GET', 'POST'])
@login_required
def contact():

    app.logger.info('/contact. Username: ' + current_user.username + '. Viewing the Contact page')

    try:
        subject = db.session.query(Subject).filter_by(
                username=current_user.username).first() # Gets user
    except:
        app.logger.error('/contact. Username: ' + current_user.username + '. An error has occurred when querying the user object')                    

    if request.method == 'POST':
        
        msgBody = request.form['msgBody']
        app.logger.info('/contact. Username: ' + current_user.username + '. Message body = ' + msgBody)
        #print(msgBody)

        if len(msgBody)>0:
            try:
                msg = Message('Inquiry on WST. Username: '+subject.username,recipients=['phcolmegna@gmail.com'])
                msg.html = msgBody

                app.logger.info('/contact. Username: ' + current_user.username + '. The message has been successfully created')
            except:
                app.logger.error('/contact. Username: ' + current_user.username + '. An error has occurred when creating the message')

            try:
                mail.send(msg)

                app.logger.info('/contact. Username: ' + current_user.username + '. The message has been successfully sent')
            except Exception:
                error_message = traceback.format_exc()
                app.logger.error('/contact. Username: ' + current_user.username + '. An error has occurred when delivering the email. Error_message = ' + error_message)

            flash('Your message has been succesfully sent! We will contact you soon!')

        else:
            app.logger.info('/contact. Username: ' + current_user.username + '. Empty message. No action taken')
            flash('No message! You should make a selection...')
        
    return render_template('contact_n.html', name=current_user.username,email=subject.email)

#########################################################################################################################

@app.route('/profile/<username>')
@login_required
def profile(username):

    app.logger.info('/profile. Username: ' + current_user.username + '. Viewing the Profile page')

    try:
        try:
            subject = db.session.query(Subject).filter_by(
                username=current_user.username).first() # Gets user
        except:
            app.logger.error('/profile. Username: ' + current_user.username + '. An error has occurred when querying the user object')  
            
    except exc.SQLAlchemyError as e:

        error = str(e.__dict__['orig'])
        app.logger.error('/profile[make_response]. Username: ' + current_user.username + '. 204') 

        return make_response(jsonify({'error': error}), 204)

    except:
        
        app.logger.error('/profile[make_response]. Username: ' + current_user.username + '. 500') 

        return make_response(jsonify({'error': 'Unexpected error!'}), 500) # who knows...

    app.logger.info('/profile[render_template]. Username: ' + current_user.username + '. Profile template successfully rendered')
    
    ins_device        = db.session.query(PumpDevice).filter_by(subject_id=current_user.id).order_by(PumpDevice.id.desc()).first()
    ins_device_tz_str = ins_device.tz
    insDur            = ins_device.ins_dur

    if subject.first_time_user == 1:
        user_ftUser = 'Yes'
    else:
        user_ftUser = 'No'
    
    if subject.active == 1:
        user_active = 'Yes'
    else:
        user_active = 'No'
    
    if subject.apSystem == 0:
        user_apSystem = 'No APS'
    elif subject.apSystem == 1:
        user_apSystem = 'Basal-IQ'
    else:
        user_apSystem = 'Control-IQ'

    return render_template('profile.html',name=subject.username, user_name=subject.username, user_email=subject.email, user_weight=np.around(float(subject.weight),decimals=1),\
         user_height=subject.height,user_age=subject.age, user_TDI=np.around(float(subject.TDIpop),decimals=1), user_apSystem = user_apSystem, user_ftUser = user_ftUser,\
             user_active = user_active, user_startDate = subject.startDate,timezone = ins_device_tz_str, insDur = insDur)

#########################################################################################################################

@app.route('/logout')
@login_required
def logout():

    app.logger.info('/logout. Username: ' + current_user.username + '. Logging the user out')

    try:
        logout_user()

        app.logger.info('/logout: User successfully logged out')
    except:
        app.logger.info('/logout: An error has occurred when logging the user out')  

    app.logger.info('/logout: Redirecting to login page')
    return redirect(url_for('login'))

#########################################################################################################################

@app.route('/reset_password',methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        app.logger.info('/reset_password. Username: ' + current_user.username + '. User authenticated. Redirecting to Dashboard')
        return redirect(url_for('Index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        subject = db.session.query(Subject).filter_by(
                email=form.email.data).first() # Gets user
        if subject is None:
            flash('There is no account with that email. You must register first','warning')
        else:
            send_reset_email(subject)
            flash('An email has been sent with instructions to reset your password','info')
        return redirect(url_for('login'))

    return render_template('reset_request.html', form=form)

#########################################################################################################################

@app.route('/reset_password/<token>',methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        app.logger.info('/reset_password. Username: ' + current_user.username + '. User authenticated. Redirecting to Dashboard')
        return redirect(url_for('Index'))
    subject = verify_reset_token(token)
    if subject is None:
        flash('That is an invalid or expired token','warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            hashed_password = generate_password_hash(form.password.data, method='sha256') # 80 characters long
            db.session.query(Subject).filter_by(id=subject.id).update({Subject.password: hashed_password},synchronize_session=False)
            db.session.commit()
            flash('Your password has been updated! You are now able to log in','info')
            app.logger.info('/reset_password. Username: ' + subject.username + '. The password has been successfully updated')
            return redirect(url_for('login'))
        except:
            flash('An error has occurred when updating your password. Try again or contact the support team','warning')
            app.logger.error('/reset_password: An error has occurred when trying to update the password')
            return redirect(url_for('login'))
    return render_template('reset_token.html',form=form,token=token)

#########################################################################################################################
@app.route('/testWakeUpCluster1', methods=['GET','POST'])
@login_required
def testWakeUpCluster1():

    if current_user.username=='fakeUser':
        wakeUpCluster1()
        rMessage = "<h1 style='color: red;'>testWakeUpCluster1 executed!</h1>"
    else:
        rMessage = "<h1 style='color: red;'>User not authorized to perform this operation!</h1>"

    return rMessage

#########################################################################################################################
@app.route('/testWakeUpCluster2', methods=['GET','POST'])
@login_required
def testWakeUpCluster2():

    if current_user.username=='fakeUser':
        wakeUpCluster2()
        rMessage = "<h1 style='color: red;'>testWakeUpCluster2 executed!</h1>"
    else:
        rMessage = "<h1 style='color: red;'>User not authorized to perform this operation!</h1>"

    return rMessage

#########################################################################################################################

@app.route('/testFetchData', methods=['GET','POST'])
@login_required
def testFetchData():

    if current_user.username=='fakeUser':
        fetchTandemData()
        rMessage = "<h1 style='color: red;'>fetchTandemData executed!</h1>"
    else:
        rMessage = "<h1 style='color: red;'>User not authorized to perform this operation!</h1>"

    return rMessage

#########################################################################################################################

@app.route('/testVIP', methods=['GET','POST'])
@login_required
def testVIP():

    if current_user.username=='fakeUser':
        VIP()
        rMessage = "<h1 style='color: red;'>VIP method executed!</h1>"
    else:
        rMessage = "<h1 style='color: red;'>User not authorized to perform this operation!</h1>"

    return rMessage

#########################################################################################################################

@app.route('/testEstimateA1c', methods=['GET','POST'])
@login_required
def testEstimateA1c():

    if current_user.username=='fakeUser':
        estimateA1c_wrapper()
        rMessage = "<h1 style='color: red;'>testEstimateA1c executed!</h1>"
    else:
        rMessage = "<h1 style='color: red;'>User not authorized to perform this operation!</h1>"

    return rMessage

#########################################################################################################################

@app.route('/testWeeklyOpt', methods=['GET','POST'])
@login_required
def testWeeklyOpt():

    if current_user.username=='fakeUser':
        weeklyOptimizer()
        rMessage = "<h1 style='color: red;'>testWeeklyOpt executed!</h1>"
    else:
        rMessage = "<h1 style='color: red;'>User not authorized to perform this operation!</h1>"

    return rMessage

#########################################################################################################################

@app.route('/testDailyOptimizer', methods=['GET','POST'])
@login_required
def testDailyOptimizer():

    if current_user.username=='fakeUser':
        dailyOptimizer()
        rMessage = "<h1 style='color: red;'>testDailyOptimizer executed!</h1>"
    else:
        rMessage = "<h1 style='color: red;'>User not authorized to perform this operation!</h1>"

    return rMessage

#########################################################################################################################

@app.route('/testFinalBasalRate', methods=['GET','POST'])
@login_required
def testFinalBasalRate():

    if current_user.username=='fakeUser':
        FinalBasalEstimation()
        rMessage = "<h1 style='color: red;'>testFinalBasalRate executed!</h1>"
    else:
        rMessage = "<h1 style='color: red;'>User not authorized to perform this operation!</h1>"

    return rMessage

#########################################################################################################################
#########################################################################################################################

# Run Forest run
if __name__ == '__main__':
    app.run(use_reloader=False,host='0.0.0.0')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)        