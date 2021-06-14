import json
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math
import datetime
from scipy.linalg import inv

#########################################################################################################################

def BAM(current_date, timestamps, BG_values, RT_filename, BAMp):
    """
    Inputs:
    1. current_date: the current date as a string (format: "MM/DD/YYYY")
    2. timestamps: a list of timestamps as strings (format: "MM/DD/YYYY HH:MM:SS")
    3. BG_values: the blood glucose value at each timestamp in timestamps
    4. RT_filename: the name of the risk trace .png file
    5. BAMp: dictionary of BAM module configurations
    Returns:
    A dictionary with the following keys:
    1. Variability_Index,
    2. Risk_Indices,
    3. Risk_Trace, and
    4. Estimated_A1c.
    """
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

    prev_date = current_date - pd.DateOffset(days=1)    
    BAM_dict = {'Variability_Index': variability_index(BG_df, flag_1, BAMp),
                'Risk_Indices': risk_indices(LBGI_vals, 
                                             HBGI_vals,
                                             flag_1,
                                             BAMp),
                'Risk_Trace': risk_trace(current_date,
                                         LBGI_vals,                       
                                         HBGI_vals,
                                         BAMp) 
               }
    RT_plot(BAM_dict['Risk_Trace'][0], 
            BAM_dict['Risk_Trace'][1], 
            RT_filename,
            BAMp['RT_image_path'])  
    
    # Add call to Chiara's code here
    BAM_dict['Estimated_A1c'] = (3, 56)  # estimated_A1c()
    
    return BAM_dict

#########################################################################################################################

def process_CGM_data(current_date, timestamps, BG_values, BAMp):
    """
    Returns a pandas DataFrame containing:
    1. The CGM blood glucose values ('BG'),
    2. The date and timestamp of the data ('Date_Time'),
    3. The date of the data ('Date').
    All timestamps are shifted back by 6 hours so that the
    24-hour prediction interval runs from 06:00 to 06:00, and 
    the most recent data belongs to the day before the 
    current_date.
    """
    cgm_df = pd.DataFrame({'BG': BG_values, 
                           'Date_Time': pd.to_datetime(timestamps, 
                                                       format='%m/%d/%Y %H:%M:%S')})    
    # Shift timestamps by 6 hours
    cgm_df['Date_Time'] = cgm_df.loc[:, 'Date_Time'] - pd.DateOffset(hours=6)
    cgm_df['Date'] = cgm_df.loc[:, 'Date_Time'].dt.normalize()
    
    # Remove sensor error values
    cgm_df = cgm_df.loc[(40 <= cgm_df['BG']) & (cgm_df['BG'] <= 400), :]
    
    # Only keep days with at least 110 data points
    num_pts_by_day = cgm_df.groupby('Date').size()
    cgm_df = cgm_df.set_index('Date') \
                    .loc[num_pts_by_day.loc[num_pts_by_day >= 110].index] \
                    .reset_index()
    
    # Remove any data from the "future"
    shifted_current_date = current_date - pd.DateOffset(days=1)
    cgm_df = cgm_df.loc[cgm_df['Date'] <= shifted_current_date, :]
    
    # Return the BG time series and a boolean flag which 
    # indicates if there is enough data from the most recent 
    # (shifted) day in the BG time series
    dates = [pd.to_datetime(dt) for dt in cgm_df['Date'].unique()]
    
    return cgm_df.sort_values('Date_Time'), \
            dates_check(dates, current_date, 1)

#########################################################################################################################

def dates_check(dates, index_date, n):
    """
    Returns True if all n dates prior to index_date
    are in the list of dates passed in.
    """
    for i in range(1, n + 1):
        if (index_date - pd.DateOffset(days=i) not in dates):
            return False
    
    return True

#########################################################################################################################

def variability_index(BG_df, flag_1, BAMp):
    """
    Returns a list containing the single ADRR value for the patient,
    scaled to the ST scale.
    Assumes the most recent date in the data is the day which 
    just finished.
    """
    if not flag_1:
        return [np.nan]
    
    BG_df = BG_df.loc[BG_df['Date'] > (BG_df['Date'].max() - pd.DateOffset(days=1))]
    
    return ST_scale([ADRR(BG_df)], BAMp['ADRR_bounds'])

#########################################################################################################################

def risk_indices(LBGI_vals, HBGI_vals, flag_1, BAMp):
    """
    Returns a list containing two tuples.
    The first tuple contains the risk index for hypoglycemia
    scaled to the ST scale and the associated string 
    interpretation, while the second tuple contains the risk 
    index for hyperglycemia scaled to the ST scale
    and the associated string interpretation.
    """
    if not flag_1:
        return [(np.nan, 'N/A'), (np.nan, 'N/A')]
       
    STS_hypo_index = ST_scale([LBGI_vals.sort_index().iloc[-1]], 
                              BAMp['LBGI_bounds'])[0]
    STS_hypo_interpretation = GI_interpretation(BAMp['STS_LBGI_breakpoints'],
                                                BAMp['STS_LBGI_interpretations'], 
                                                STS_hypo_index)
    
    STS_hyper_index = ST_scale([HBGI_vals.sort_index().iloc[-1]], 
                               BAMp['HBGI_bounds'])[0]
    STS_hyper_interpretation = GI_interpretation(BAMp['STS_HBGI_breakpoints'], 
                                                 BAMp['STS_HBGI_interpretations'], 
                                                 STS_hyper_index)    
    
    return [(STS_hypo_index, STS_hypo_interpretation), 
            (STS_hyper_index, STS_hyper_interpretation)]

#########################################################################################################################

def risk_trace(current_date, LBGI_vals, HBGI_vals, BAMp):
    """
    Returns two lists. 
    The first list contains the BAMp['RT_num_days'] most
    recent hypoglycemia risk indices if available (np.nan
    if not), while the second list contains the 
    BAMp['RT_num_days'] most recent hyperglycemia risk 
    indices if available (np.nan if not).
    Most recent is with respect to and prior to current_date.
    """
    LBGI_to_plot, HBGI_to_plot = [], []
    for i in range(BAMp['RT_num_days'], 0, -1):
        date = current_date - pd.DateOffset(days=i)
        try:
            LBGI_to_plot.append(LBGI_vals.loc[date])
        except KeyError:
            LBGI_to_plot.append(np.nan)
        try:
            HBGI_to_plot.append(HBGI_vals.loc[date])
        except KeyError:
            HBGI_to_plot.append(np.nan)
    
    return [ST_scale(LBGI_to_plot, BAMp['LBGI_bounds']), 
            ST_scale(HBGI_to_plot, BAMp['HBGI_bounds'])]

#########################################################################################################################

def convert_to_risk_space(BG_s):
    """
    Converts the passed in CGM blood glucose time series to a 
    CGM risk space time series as defined in Table 1 of:
    B. Kovatchev. Metrics for glycaemic control — from HbA1c 
    to continuous glucose monitoring. Nature Reviews Endocrinology, 
    13:425–436, 2017.
    """
    return (np.log(BG_s)**1.084) - 5.381

#########################################################################################################################

def LBGI(BG_s):
    """
    Reflection of the risk of hypoglycaemia which
    increases gradually with the extent and frequency
    of hypoglycaemic excursions as defined in Table 1 of:
    B. Kovatchev. Metrics for glycaemic control — from HbA1c 
    to continuous glucose monitoring. Nature Reviews Endocrinology, 
    13:425–436, 2017.
    Assumes the CGM time series passed in is a blood glucose
    time series measured in mg/dL.    
    """   
    return sum(r_l(BG_s)) / len(BG_s)

#########################################################################################################################    

def r_l(BG_s):
    """
    r_l as defined in Table 1 of:
    B. Kovatchev. Metrics for glycaemic control — from HbA1c 
    to continuous glucose monitoring. Nature Reviews Endocrinology, 
    13:425–436, 2017.
    Assumes the CGM time series passed in is a blood glucose
    time series measured in mg/dL.
    """
    return [(22.77 * (x**2)) if x <= 0 else 0 for x in convert_to_risk_space(BG_s)]

#########################################################################################################################

def HBGI(BG_s):
    """  
    Reflection of the risk of hyperglycaemia which
    increases gradually with the extent and frequency
    of hyperglycaemic excursions as defined in Table 1 of:
    B. Kovatchev. Metrics for glycaemic control — from HbA1c 
    to continuous glucose monitoring. Nature Reviews Endocrinology, 
    13:425–436, 2017.
    Assumes the CGM time series passed in is a blood glucose
    time series measured in mg/dL. 
    """   
    return sum(r_h(BG_s)) / len(BG_s)   

#########################################################################################################################

def r_h(BG_s):
    """
    r_h as defined in Table 1 of:
    B. Kovatchev. Metrics for glycaemic control — from HbA1c 
    to continuous glucose monitoring. Nature Reviews Endocrinology, 
    13:425–436, 2017.
    Assumes the CGM time series passed in is a blood glucose
    time series measured in mg/dL.
    """    
    return [(22.77 * (x**2)) if x > 0 else 0 for x in convert_to_risk_space(BG_s)]

#########################################################################################################################

def ADRR(BG_df):
    """
    A risk assessment of the total daily BG variation in
    risk space - the sum of the peak risks of hypoglycemia
    and hyperglycemia for the day as defined in Table 1 of:
    B. Kovatchev. Metrics for glycaemic control — from HbA1c 
    to continuous glucose monitoring. Nature Reviews Endocrinology, 
    13:425–436, 2017.
    Assumes the CGM time dataframe passed in contains blood glucose
    values measured in mg/dL. 
    """
    LR_values = BG_df.groupby('Date')['BG'].apply(LR)
    HR_values = BG_df.groupby('Date')['BG'].apply(HR)
    
    return (LR_values.sum() + HR_values.sum()) / BG_df.groupby('Date').ngroups

#########################################################################################################################

def LR(BG_s):
    """
    Returns the maximum r_l value for the time series 
    of BG values passed in.
    Used in the computation of ADRR.
    """
    return max(r_l(BG_s))

#########################################################################################################################
    
def HR(BG_s):
    """
    Returns the maximum r_h value for the time series of BG values 
    passed in.
    Used in the computation of ADRR.    
    """
    return max(r_h(BG_s))

#########################################################################################################################    

def GI_interpretation(breakpoints, interpretations, value):
    """
    Returns the string from interpretations which corresponds
    to the breakpoint in breakpoints satisfied by value.
    """
    for brkpt, interpret in zip(breakpoints, interpretations[:-1]):
        if value < brkpt:
            return interpret
        
    return interpretations[-1]
    
#########################################################################################################################

def RT_plot(LBGI_vals, HBGI_vals, RT_filename, RT_image_path):
    """
    Plots and saves the risk trace plot
    using the RT_image_path and RT_filename passed in.
    """    
    _, ax = plt.subplots(figsize=(6, 6.75))
    # Grid Squares
    ax.fill_between([0, 5.5], [0, 0], [5.5, 5.5], color='#00ff00', alpha=1, zorder=1)
    ax.fill_between([0, 5.5], [5.5, 5.5], [11, 11], color='#ffff00', alpha=1, zorder=1)
    ax.fill_between([5.5, 11], [0, 0], [5.5, 5.5], color='#ffff00', alpha=1, zorder=1)
    ax.fill_between([5.5, 11], [5.5, 5.5], [11, 11], color='#ff0000', alpha=1, zorder=1)

    # Annotations
    ax.annotate('Optimal', (0.25, 0.25), fontsize=16, color='#0a0a0a', zorder=2)
    ax.annotate('Risk for \nHighs', (0.25, 9.8), fontsize=16, color='#0a0a0a', zorder=2)
    ax.annotate('Unstable\nGlucose', (8.6, 9.8), fontsize=16, color='#0a0a0a', zorder=2)
    ax.annotate('Risk for \nLows', (8.85, 0.25), fontsize=16, color='#0a0a0a', zorder=2)

    # Points
    sizes = [200, 350, 750]
    markers = ['o', 'o', 'o']
    for LBGI_val, HBGI_val, s, marker in zip(LBGI_vals, HBGI_vals, sizes, markers):
        if not (np.isnan(LBGI_val) or np.isnan(HBGI_val)): 
            ax.scatter(LBGI_val, HBGI_val, s=s, color='#4b4b4b', zorder=5,
                       edgecolor='#ffffff', linewidths=2, marker=marker, clip_on=False)   
    
    ax.set_ylim(0, 11)
    ax.set_xlim(0, 11)
    ax.set_ylabel('Risk for Hyperglycemia', fontsize=20)
    ax.set_xlabel('Risk for Hypoglycemia', fontsize=20)
    plt.xticks(range(0, 12), fontsize=16)
    plt.yticks(range(0, 12), fontsize=16)
    
    two_days = mlines.Line2D([], [], linestyle='None', color='#4b4b4b', 
                             marker='o', markersize=12, markeredgecolor='#ffffff', 
                             label='48-72h Ago')
    yesterday = mlines.Line2D([], [], linestyle='None',color='#4b4b4b',
                              marker='o', markersize=16,markeredgecolor='#ffffff',
                              label='24-48h Ago')
    today = mlines.Line2D([], [], linestyle='None',color='#4b4b4b', 
                          marker='o', markersize=22, markeredgecolor='#ffffff',
                          label='Last 24h')
    plt.legend(handles=[two_days, yesterday, today],
               bbox_to_anchor=(-0.1, -0.25, 1.15, -0.15), 
               loc='lower left', frameon=False,
               mode='expand', ncol=3, fontsize=16, 
               markerscale=1, markerfirst=True, 
               handletextpad=-0.1)
    plt.tight_layout()
    plt.savefig(f'{RT_image_path}/{RT_filename}.png', transparent=True)
    plt.close()
    
#########################################################################################################################
    
def ST_scale(BGI_vals, bounds):
    """
    Converts the values passed in to their equivalent values
    on the ST scale ([0, 11]).
    NaN values are left alone.
    """
    l_bound, u_bound = bounds

    sts_vals = []
    for val in BGI_vals:
        if np.isnan(val):
            sts_vals.append(val)
        elif val <= l_bound:
            sts_vals.append(0)
        elif u_bound <= val:
            sts_vals.append(11)
        else:
            sts_vals.append(((val - l_bound) / (u_bound - l_bound)) * 11)
        
    return sts_vals

#########################################################################################################################

def estimateA1c(tCGM,CGM,eA1cPrev,muTIRprev,gamma,startTime,endTime):
    
    # algorithm parameters
    popTIR = 59.8894
    alfa = math.exp(-1.0/5.0)
    q = 10.1944
    m = -0.0500
    a = 0.9717
    b = 0.0283
    
    firstIter = False
    if eA1cPrev==-1.0 or muTIRprev==-1.0:
        firstIter = True
        
    if firstIter:
    	muTIRprev = popTIR
    
    enoughData = True
    if len(CGM)<288*3/4:
        enoughData = False
    
    maxGap = 0
    tCGM.shape = (len(tCGM),1)
    CGM.shape = (len(CGM),1)
    if enoughData:
        nCGM = len(CGM)
        maxGap = max(tCGM[0,0]-startTime, endTime+1-tCGM[-1,0])
        for i in range(1,nCGM):
            if tCGM[i,0]-tCGM[i-1,0] > maxGap:
                maxGap = tCGM[i,0]-tCGM[i-1,0]
    			
    if not(enoughData) or maxGap>2*60*60:
        print('CGM data requirements not met for TIR computation. Use average TIR for eA1c.')
        TIR = muTIRprev
    else:
        print('CGM data requirements met for TIR computation. Compute daily TIR for eA1c.')
        tCGMinterp = np.arange(startTime, endTime+1, 5*60)
        CGMinterp = np.interp(tCGMinterp,tCGM[:,0],CGM[:,0])
        inRangeCGM = 0
        for i in range(0,len(CGMinterp)):
            if CGMinterp[i]>=70 and CGMinterp[i]<=180:
                inRangeCGM = inRangeCGM+1
        TIR = 100 * inRangeCGM/len(CGMinterp)
    
    fTIR = gamma * (q + m*TIR)
    muTIR = alfa*muTIRprev + (1.0-alfa)*TIR 
    print('Current day time in range and driving function: TIR=', TIR, '% , fTIR=', fTIR)
    
    if (firstIter):
        eA1cPrev = fTIR
    
    eA1c = a*eA1cPrev + b*fTIR
    eA1c = round(eA1c*10)/10.0
    eA1c = max(min(eA1c,10.0),5.0)
    
    print('Previous iteration A1c estimations: muTIR=', muTIRprev, ', eA1c=', eA1cPrev, '%')
    print('Current iteration A1c estimations: muTIR=', muTIR, ', eA1c=', eA1c, '%')
    
    # update eA1cPrev_d1, ..., eA1cPrev_d6 in database with current eA1c, ..., eA1cPrev_d5
    # store eA1c in database in corresponding variable
    # store muTIR in database in corresponding variable
    return (eA1c,muTIR)

#########################################################################################################################

def estimateA1cROC(eA1cList):
    # RUNNING SCHEDULE: run every night after the computation of eA1c
    # get eA1c estimates from previous seven days (current day included)
    eA1cVec = np.array(eA1cList)
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