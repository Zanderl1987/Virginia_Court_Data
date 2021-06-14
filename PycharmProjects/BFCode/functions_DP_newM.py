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

def preProcessData(rawData,timeZone,utcOffset,endDateTime,requestLength,requestInterval,Gb=120,display=False,rawCGM=False):
    # fetch data from database for a given interval
    # fetch_result is a list containing, in this order: subject_info, br_profiles, cr_profiles, cf_profiles, cgm_data, basal_data, insulin_data, meal_data, daily_recBasal_value
    # if no data is available for the queried interval, fetch_result is assigned -1
    
    if rawData['cgm_data']==0:
        procData={}
    else:
        est=pytz.timezone(timeZone)
        utc=pytz.utc
        fmt='%Y-%m-%d %H:%M:%S'
        # translate every time into utc when running
        endDateTime_t = endDateTime.timestamp()
        print(endDateTime)
        print(endDateTime_t)
        print(utcOffset)
        utc_time = datetime.fromtimestamp(endDateTime_t,tz=timezone.utc).strftime(fmt)
        print(datetime.fromtimestamp(endDateTime_t,tz=timezone.utc).timestamp())
        #utc_time=datetime.strptime(endDateTime,fmt).astimezone(utc).strftime(fmt)

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

        raw_cgm=rawData['raw_cgm']
        selected_br_profiles=rawData['selected_br_profiles']
        selected_cr_profiles=rawData['selected_cr_profiles']
        selected_cf_profiles=rawData['selected_cf_profiles']

        ######################################  CGM Preprocessing  #################################################
        
        selected_cgm=rawData['raw_cgm']

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
        
        selected_basal_profile=rawData['selected_br_profiles']

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
        
        selected_basal=rawData['basal_data']
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
        
        selected_insulin=rawData['insulin_data']
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
        
        selected_meal=rawData['meal_data']
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
    
    return procData

# Helper functions 
def genTvector(start_time,end_time,interval):
    tvector=[]
    current_time=copy.deepcopy(start_time)
    while current_time<end_time:
        tvector.append([current_time.timestamp(),None])
        current_time=current_time+timedelta(minutes=interval)
    return tvector

def profileTime(profile_dict,profile_name):
    one_profile=[]    
    for i in profile_dict[profile_name]:
        one_profile.append([int(i['time']),float(i['value'])])
    one_profile=sorted(one_profile, key=lambda x: x[0])
    return one_profile 