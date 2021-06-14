import math
import numpy as np
import pytz
import copy
import operator
from datetime import datetime, timedelta, timezone

# input arguments
# subjectNumber = XXXXX
# endDateTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# requestLength = (9+24+4)*60 # minutes --> will change based on the needs of the specific algorithm
# requestInterval = 5 # minutes --> sampling time of reconstructed vectors

def preProcessData(subjectNumber,endDateTime,requestLength,requestInterval,Gb=120,display=False,rawCGM=False):
    # fetch data from database for a given interval
    # fetch_result is a list containing, in this order: subject_info, br_profiles, cr_profiles, cf_profiles, cgm_data, basal_data, insulin_data, meal_data, daily_recBasal_value
    # if no data is available for the queried interval, fetch_result is assigned -1
    fetch_result=fetchData(subjectNumber,endDateTime,requestLength)
    
    if fetch_result==-1:
        procData={}
    else:
        timeZone=getSubjectTimezone(subjectNumber) # need to build this method
        est=pytz.timezone(timeZone)
        utc=pytz.utc
        fmt='%Y-%m-%d %H:%M:%S'
        # translate every time into utc when running
        utc_time=datetime.strptime(endDateTime,fmt).astimezone(utc).strftime(fmt)
        datetime_target=datetime.strptime(utc_time,fmt)
        len_hrs=math.floor((requestLength/60)/1)
        len_mins=((requestLength/60)%1)*60
        datetime_start=datetime_target-timedelta(hours=len_hrs,minutes=len_mins)
        datetime_target=datetime_target.replace(tzinfo=timezone.utc)
        print("datetime_target",datetime_target)
        datetime_start=datetime_start.replace(tzinfo=timezone.utc)
        print("datetime_start",datetime_start)
        if (requestLength%requestInterval)==0:
            steps=int(requestLength/requestInterval)
        else:
            steps=int(math.floor(requestLength/requestInterval)+1)
        
        ########################################     Store Data      ###############################################
        selected_subject_info=fetch_result[0]
        selected_br_profiles=fetch_result[1]
        selected_cr_profiles=fetch_result[2]
        selected_cf_profiles=fetch_result[3]
        raw_cgm=fetch_result[4]
        daily_recBasal=fetch_result[9] # this is the output of the daily basal optimizer

        ######################################  CGM Preprocessing  #################################################
        selected_cgm=fetch_result[4]
        cgm_return=genTvector(datetime_start,datetime_target,requestInterval)  
        if len(selected_cgm)==0:
            for i in range(len(cgm_return)):
                cgm_return[i][1]=Gb
        else:
            nCGM=len(selected_cgm)
            nbegin=0 
            nend=0
            i=0
            while selected_cgm[0][0]>cgm_return[i][0]:
                i=i+1
            nbegin=i-1
            i=steps-1
            while selected_cgm[nCGM-1][0]<cgm_return[i][0]:
                i=i-1
            nend=i+1
            #fill in gaps with the first and last available data point 
            for i in range(nbegin+1):
                cgm_return[i][1]=selected_cgm[0][1]
            for i in range(nend,steps):
                cgm_return[i][1]=selected_cgm[nCGM-1][1]
            #interpolate the indiced CGM
            if (nend-nbegin)>1:
                if len(selected_cgm)==1:
                    cgm_return[nbegin+1]=selected_cgm[0][1]
                else:
                    x=[]
                    y=[]
                    xintp=[]  
                    for i in range(nCGM):
                        x.append(selected_cgm[i][0])
                        y.append(selected_cgm[i][1])                  
                    for i in range(nbegin+1,nend):
                        xintp.append(cgm_return[i][0])
                    interpolatedCGM=np.interp(xintp,x,y)
                    for i in range(nbegin+1,nend):
                        cgm_return[i][1]=interpolatedCGM[i-(nbegin+1)]
                    
        ######################################  Basal Profile Preprocessing  #################################################
        selected_basal_profile=fetch_result[1]
        basal_profile_return=genTvector(datetime_start,datetime_target,requestInterval)  
        #if first profile is after tStart, backpropagate it until tStart
        if selected_basal_profile[0][0]>basal_profile_return[0][0]:
            selected_basal_profile[0][0]=basal_profile_return[0][0]
        #create time arrays
        nProfiles=len(selected_basal_profile)
        tProfiles=np.zeros((nProfiles,1))
        nData=len(basal_profile_return)
        tData=np.zeros((nData,1))
        for i in range(nProfiles):
            tProfiles[i,0]=selected_basal_profile[i][0]
        for i in range(nData):
            tData[i,0]=basal_profile_return[i][0]    
        #now fill-in between consecutive times
        for i in range(1,nProfiles+1):
            #current profile
            currProfile=selected_basal_profile[i-1][1]
            nBrPoints=len(currProfile)
            tPrf=np.zeros((nBrPoints,1)).astype('int')
            vPrf=np.zeros((nBrPoints,1))
            for j in range(0,nBrPoints):
                tPrf[j,0]=currProfile[j][0]
                vPrf[j,0]=currProfile[j][1]
            #current basal return   
            tStart=np.float64(tProfiles[i-1])
            if i<nProfiles:
                tEnd=np.float64(tProfiles[i])
            else:
                tEnd=np.float64(tData[-1])+60 #add 1 minute
            idx=np.array(np.asarray((tData>=tStart)&(tData<tEnd)).nonzero())[0,:]
            idx.shape=(len(idx),1)
            currBasReturn=[]
            for j in range(0,len(idx)):
                currBasReturn.append([basal_profile_return[int(idx[j])][0],basal_profile_return[int(idx[j])][1]])
            #fill current basal return
            for k in currBasReturn:
                for k1,k2 in enumerate(tPrf):
                    currMin=int(datetime.fromtimestamp(k[0]).hour*60+datetime.fromtimestamp(k[0]).minute)
                    if currMin<k2:
                        k[1]=np.float64(vPrf[k1-1])
                        break
                    elif currMin==k2:
                        k[1]=np.float64(vPrf[k1])
                        break
                    else:
                        continue 
                if k[1]==None:
                    k[1]=np.float64(vPrf[-1])
            #trace back to basal return
            for j in range(0,len(idx)):
                basal_profile_return[int(idx[j])][0]=currBasReturn[j][0]
                basal_profile_return[int(idx[j])][1]=currBasReturn[j][1]*1000/60

       ######################################  Basal Insulin Preprocessing  #################################################  
        selected_basal=fetch_result[6]  
        basal_return=genTvector(datetime_start,datetime_target,requestInterval)   
        if len(selected_basal)==0:
            for i in range(steps):
                basal_return[i][1]=basal_profile_return[i][1]
        else:
            ninsulin=len(selected_basal)
            nbegin=0
            nend=0
            i=0
            while selected_basal[0][0]>basal_return[i][0]:
                i=i+1
            nbegin=np.maximum(0,i-1)
            i=steps-1
            while selected_basal[ninsulin-1][0]<basal_return[i][0]:
                i=i-1
            nend=np.minimum(i+1,steps-1)
            for i in range(nbegin+1):
                basal_return[i][1]=basal_profile_return[i][1]
            for i in range(nbegin+1,nend+1):
                selectedBasal=[b for b in selected_basal if b[0]>basal_return[i-1][0] and b[0]<=basal_return[i][0]]
                if len(selectedBasal)!=0:
                    totalspaninterval=0
                    for j in range(len(selectedBasal)):
                        totalspaninterval=totalspaninterval+selectedBasal[j][1]
                    basal_return[i][1]=totalspaninterval*1000/5
                else:
                    basal_return[i][1]=0
            for i in range(nend+1,steps):
                    basal_return[i][1]=0
            if nbegin==0 & (basal_return[0][0]==selected_basal[0][0]):
                basal_return[0][1]=selected_basal[0][1]*1000/5
        
        ######################################  Total Insulin Preprocessing   #################################################
        selected_insulin=fetch_result[7]
        insulin_return=genTvector(datetime_start,datetime_target,requestInterval)
        if len(selected_insulin)==0:
            for i in range(steps):
                insulin_return[i][1]=basal_return[i][1]
        else:
            ninsulin=len(selected_insulin)
            nbegin=0
            nend=0
            i=0
            while selected_insulin[0][0]>insulin_return[i][0]:
                i=i+1
            nbegin=np.maximum(0,i-1)
            i=steps-1
            while selected_insulin[ninsulin-1][0]<insulin_return[i][0]:
                i=i-1
            nend=np.minimum(i+1,steps-1)
            for i in range(nbegin+1):
                insulin_return[i][1]=basal_return[i][1]     
            for i in range(nbegin+1,nend+1):         
                selectedInsulin=[insulin for insulin in selected_insulin if insulin[0]>insulin_return[i-1][0] and insulin[0]<=insulin_return[i][0]]
                if len(selectedInsulin)!=0:
                    totalspaninterval=0
                    for j in range(len(selectedInsulin)):
                        totalspaninterval=totalspaninterval+selectedInsulin[j][1]
                    insulin_return[i][1]=totalspaninterval*1000/5  
                else:
                    insulin_return[i][1]=basal_return[i][1]
            for i in range(nend+1,steps):
                insulin_return[i][1]=basal_return[i][1]
            if nbegin==0 & (insulin_return[0][0]==selected_insulin[0][0]):
                insulin_return[0][1]=selected_insulin[0][1]*1000/5
                
        ######################################  Meal Preprocessing  #################################################
        selected_meal=fetch_result[8]
        meal_return=genTvector(datetime_start,datetime_target,requestInterval)
        if len(selected_meal)==0:
            for i in range(len(meal_return)):
                meal_return[i][1]=0
        else: 
            nmeal=len(selected_meal)
            nbegin=0
            nend=0
            i=0
            while selected_meal[0][0]>meal_return[i][0]:
                i=i+1
            nbegin=np.maximum(0,i-1)
            i=steps-1
            while selected_meal[nmeal-1][0]<meal_return[i][0]:
                i=i-1
            nend=np.minimum(i+1,steps-1)
            for i in range(nbegin+1):
                meal_return[i][1]=0
            for i in range(nbegin+1,nend+1):
                selectedMeal=[m for m in selected_meal if m[0]>meal_return[i-1][0] and m[0]<=meal_return[i][0]]
                if len(selectedMeal)!=0:
                    totalspaninterval=0
                    for j in range(len(selectedMeal)):
                        totalspaninterval=totalspaninterval+selectedMeal[j][1]
                    meal_return[i][1]=totalspaninterval*1000/5
                else:
                    meal_return[i][1]=0
            for i in range(nend+1,steps):
                meal_return[i][1]=0
            if nbegin==0 & (meal_return[0][0]==selected_meal[0][0]):
                meal_return[0][1]=selected_meal[0][1]*1000/5
                
        ######################################  Final Return   #################################################
        raw_cgm_final=[]
        if display: #Est Datetime
            if rawCGM:
                raw_cgm_final=[[datetime.utcfromtimestamp(i[0]).replace(tzinfo=pytz.utc).astimezone(est).strftime(fmt),i[1]] for i in raw_cgm]
            cgm_final=[[datetime.utcfromtimestamp(i[0]).replace(tzinfo=pytz.utc).astimezone(est).strftime(fmt),i[1]] for i in cgm_return]   
            basal_final=[[datetime.utcfromtimestamp(i[0]).replace(tzinfo=pytz.utc).astimezone(est).strftime(fmt),i[1]] for i in basal_return]
            insulin_final=[[datetime.utcfromtimestamp(i[0]).replace(tzinfo=pytz.utc).astimezone(est).strftime(fmt),i[1]] for i in insulin_return]
            meal_final=[[datetime.utcfromtimestamp(i[0]).replace(tzinfo=pytz.utc).astimezone(est).strftime(fmt),i[1]] for i in meal_return]
            basal_profile_final=[[datetime.utcfromtimestamp(i[0]).replace(tzinfo=pytz.utc).astimezone(est).strftime(fmt),i[1]] for i in basal_profile_return]
        else: #Unix Timestamp
            if rawCGM:
                raw_cgm_final=raw_cgm 
            cgm_final=cgm_return
            basal_final=basal_return
            insulin_final=insulin_return
            meal_final=meal_return
            basal_profile_final=basal_profile_return   
        
        procData = {}
        procData['rawCgm']=raw_cgm_final
        procData['cgm']=cgm_final
        procData['basal']=basal_final
        procData['insulin']=insulin_final
        procData['meal']=meal_final
        procData['basalPrf']=basal_profile_final
        procData['profiles']={'brProfiles':selected_br_profiles,'crProfiles':selected_cr_profiles,'cfProfiles':selected_cf_profiles}
        procData['dailyRecBasal']=daily_recBasal.tolist()
        procData['subjInfo']=selected_subject_info
        procData['subjTZ']=getSubjectTimezone(subjectNumber)
        procData['subjID']=subjectNumber    
    
    return procData

# Helper functions 
def genTvector(start_time,end_time,interval):
    tvector=[]
    current_time=copy.deepcopy(start_time)
    while current_time<end_time:
        tvector.append([current_time.timestamp(),None])
        current_time=current_time+timedelta(minutes=interval)
    return tvector

def getData(start_time,operator1,end_time,operator2,time_array,value_array,status_array):
    ops = { ">=": operator.ge,\
           "=>": operator.ge,\
           ">":operator.gt,\
           '<=':operator.le,\
           '=<':operator.le,\
          '<':operator.lt} 
    data=[]
    for idx, val in enumerate(time_array):
        if ops[operator1](val,start_time.timestamp()) & ops[operator2](val,end_time.timestamp()):
            #if you need to filter the data based on status code you should add: 0 and 20 are the codes for status approval  
            #if status_array[idx] in [0,20]:   
            data.append([val,value_array[idx]])
    return data

def profileTime(profile_dict,profile_name):
    one_profile=[]    
    for i in profile_dict[profile_name]:
        one_profile.append([int(i['time']),float(i['value'])])
    one_profile=sorted(one_profile, key=lambda x: x[0])
    return one_profile 
        
# Data fecthing
def fetchData(subjectNumber, endDateTime, requestLength):
    est = pytz.timezone(getSubjectTimezone(subjectNumber))
    utc = pytz.utc
    fmt='%Y-%m-%d %H:%M:%S'
    #incase the transcripts got run computer not set in est. we translated every time into utc when running and tranlated utc time to est when display to users 
    utc_time_string=datetime.strptime(endDateTime,fmt).astimezone(utc).strftime(fmt)
    datetime_target= datetime.strptime(utc_time_string,fmt)
    len_hrs=math.floor((requestLength/60)/1)
    len_mins=((requestLength/60)%1)*60
    datetime_start=datetime_target-timedelta(hours=len_hrs,minutes=len_mins)
    datetime_target=datetime_target.replace(tzinfo=timezone.utc)
    datetime_start=datetime_start.replace(tzinfo=timezone.utc)
    unix_timestamp_target = int(datetime_target.timestamp())
    print("unix_timestamp_target", unix_timestamp_target)
    unix_timestamp_start = int(datetime_start.timestamp())
    print("unix_timestamp_start", unix_timestamp_start)
    print('start to work on data from {} to {}'.format(datetime_start.astimezone(est).strftime(fmt),datetime_target.astimezone(est).strftime(fmt)))
    ############################################################################
    #Fetch data using subject-number 
    ############################################################################
    cgm_response = []
    meal_response = []
    insulin_response = []
    basal_response = []
    profiles = []
    subject_info = []
    if (not subject_info) | (not cgm_response) | (not insulin_response) | (not basal_response) | (not profiles):
        raise KeyError({"subject_id":subjectNumber,"no_data":1})
        return -1
    ############################################################################
    #Create data objects for subject info
    ############################################################################
    #Get subject_info
    selected_subject_info={}
    for i in subject_info['Items']:
        selected_subject_info['Height']=int(i['height'])
        selected_subject_info['TDI']=int(i['TDI'])
        if int(i['isfemale'])==0:
            selected_subject_info['Gender']='Male'
        else:
            selected_subject_info['Gender']='Female'
        selected_subject_info['Weight']=int(i['weight'])
        selected_subject_info['Age']=int(i['age'])
    ############################################################################
    #Create data objects for basal, cr, and cf profiles  
    ############################################################################
    #Create vectors for insulin profiles 
    profile_time=[]
    br_profiles=[]
    cr_profiles=[]
    cf_profiles=[]  
    for i in profiles['Items']:
        if 'prof_set_dias_ts' in i:
            profile_time.append(int(i['prof_set_dias_ts'])) 
            br_profiles.append(profileTime(i,'br_actual'))
            cr_profiles.append(profileTime(i,'cr_actual'))
            cf_profiles.append(profileTime(i,'cf_actual'))
    selected_br_profiles=[]
    selected_cr_profiles=[]
    selected_cf_profiles=[]
    for i in range(0,len(profile_time)):
        selected_br_profiles.append([profile_time[i],br_profiles[i]])
        selected_cr_profiles.append([profile_time[i],cr_profiles[i]])
        selected_cf_profiles.append([profile_time[i],cf_profiles[i]])
    print('profile_time',profile_time)
    print('br_profiles', br_profiles)
    print('cr_profiles', cr_profiles)
    print('cf_profiles', cf_profiles)   
    ############################################################################
    #create data objects for cgm, meal, total insulin injected and basal insulin 
    ############################################################################
    #Create vectors for time/value/status 
    cgm_time=[]
    cgm_value=[]
    cgm_status=[]
    for i in cgm_response['Items']:
        cgm_time.append(i['time'])
        cgm_value.append(i['cgm'])
        cgm_status.append(i['state'])
    #convert string to int for future use 
    cgm_time=[int(i) for i in cgm_time]
    cgm_value=[int(i) for i in cgm_value]
    cgm_status=[int(i) for i in cgm_status]
    
    meal_time=[]
    meal_value=[]
    meal_status=[] 
    for i in meal_response['Items']:
        if i['status'] == str(1):     # ****** CAUTION: only approved meal will be saved 
            meal_time.append(i['time'])
            meal_value.append(i['carbs'])
            meal_status.append(i['status'])
    meal_time=[int(i) for i in meal_time]
    meal_value=[int(i) for i in meal_value]
    meal_status=[int(i) for i in meal_status]
    
    insulin_time=[]
    insulin_value=[]
    insulin_status=[] 
    insulin_issues=[]
    for i in insulin_response['Items']:
        try:
            insulin_time.append(i['deliv_time'])
            insulin_value.append(i['deliv_total'])
            insulin_status.append(i["status"]) 
        except:
            insulin_issues.append(i['status'])
    insulin_time=[int(i) for i in insulin_time]
    insulin_value=[float(i) for i in insulin_value]  #unit 
    insulin_status=[int(i) for i in insulin_status]
    
    basal_time=[]
    basal_value=[]
    basal_status=[] 
    basal_issues=[]
    for i in basal_response['Items']:
        try:
            basal_time.append(i['deliv_time'])
            basal_value.append(i['deliv_basal'])
            basal_status.append(i["status"]) 
        except:
            basal_issues.append(i['status'])
    basal_time=[int(i) for i in basal_time]
    basal_value=[float(i) for i in basal_value]  #unit
    basal_status=[int(i) for i in basal_status]
    ############################################################################
    #create data objects for daily optimal basal rate and replayed cgm
    ############################################################################
    #Create vector for date, basal value, and cgm value
    daily_recBasal_value=np.array([])
    daily_recBasal_value.shape=(1,len(daily_recBasal_value))
    for i in daily_basal_response['Items']:
        tmpRecBasal=np.array([float(j) for j in i['recBasal_list']])
        tmpRecBasal.shape=(1,len(tmpRecBasal))
        dimAll=np.shape(daily_recBasal_value)
        dimTmp=np.shape(tmpRecBasal)
        if dimTmp[1]>0:
            if dimAll[1]==0:
                daily_recBasal_value=np.append(daily_recBasal_value,tmpRecBasal)
                daily_recBasal_value.shape=(1,len(daily_recBasal_value))
            else:
                daily_recBasal_value=np.append(daily_recBasal_value,tmpRecBasal,axis=0)
    print('recBasal_dimension',np.shape(daily_recBasal_value))
    ########################################  CGM   #################################################
    cgm_data=getData(datetime_start,'>=',datetime_target,'<',cgm_time,cgm_value,cgm_status)
    #fill the latest CGM
    lastestCGM = getData(datetime_target-timedelta(minutes=4),">",datetime_target,"<=",cgm_time,cgm_value,cgm_status)
    if len(lastestCGM)==0:
        lastestCGM = None     
    ######################################  Basal   #################################################
    basal_data=getData(datetime_start,'>=',datetime_target,'<',basal_time,basal_value,basal_status)
    ######################################  Insulin   #################################################                 
    insulin_data=getData(datetime_start,'>=',datetime_target,'<',insulin_time,insulin_value,insulin_status)   
    ######################################  Meal   #################################################
    meal_data=getData(datetime_start,'>=',datetime_target,'<',meal_time,meal_value,meal_status)
    print ("Fetch Data Finished." )
    return selected_subject_info,selected_br_profiles,selected_cr_profiles,selected_cf_profiles,cgm_data,lastestCGM,basal_data,insulin_data,meal_data,daily_recBasal_value
