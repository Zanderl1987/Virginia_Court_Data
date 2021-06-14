from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from werkzeug.security import check_password_hash
from forms import LoginForm, InsForm
from flask_login import login_user, login_required, logout_user, current_user
from sandbox import app, db, login_manager, mail
from models import Subject, CGMDevice, CGM, BasalProfile, CFProfile, CRProfile, Meal, ModelParameters, Insulin, PumpDevice
import simplejson as json
from sqlalchemy import exc
from functions import *
import pdfkit
import datetime
import numpy as np
from flask_mail import Message
import logging
import traceback

#########################################################################################################################
#########################################################################################################################
# Decorators
#########################################################################################################################
#########################################################################################################################

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Subject).get(int(user_id))

#########################################################################################################################

@app.route('/')
def main_route():
    if current_user.is_authenticated:
        return redirect(url_for('Index'))
    return redirect(url_for('login'))

#########################################################################################################################

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    print(form.username.data)
    if form.validate_on_submit():
        subject = db.session.query(Subject).filter_by(
            username=form.username.data).first()
        if subject:
            if check_password_hash(subject.password, form.password.data):
                login_user(subject, remember=form.remember.data)
                return redirect(url_for('Index'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

#########################################################################################################################

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def Index():
    insForm = InsForm()
    if request.method == 'POST':
        return render_template('index.html', name=current_user.username, insForm=insForm, flagFirstTUser=0, flagTutorial=1)
    else:
        subject = db.session.query(Subject).filter_by(
            username=current_user.username).first() # Gets user
        flagFirstTUser = subject.first_time_user
        if flagFirstTUser:    
            db.session.query(Subject).filter(Subject.username==subject.username).update({Subject.first_time_user: 0},synchronize_session=False)
            db.session.commit()
        return render_template('index.html', name=current_user.username, insForm=insForm, flagFirstTUser=flagFirstTUser, flagTutorial=0)

#########################################################################################################################

@app.route('/dashboard/calendar-changed', methods=['POST'])
@login_required
def calendar_changed():
    req = request.get_json()
    d1 = req['d1'] # startDay
    d2 = req['d2'] # endDay
    try:
        ###########################################################################
        # Display panel
        subject = db.session.query(Subject).filter_by(
            username=current_user.username).first() # Gets user
        # cgm_device = db.session.query(CGMDevice).filter_by(
        #     subject_id=subject.id).first() # Gets cgm_device
        # cgm = db.session.query(CGM).filter(CGM.time >= d1, CGM.time <= d2,
        #                     CGM.cgm_device_id == cgm_device.id, CGM.cgm_device_subject_id == subject.id) # Get cgm records
        cgm = db.session.query(CGM).filter(CGM.time >= d1, CGM.time <= d2,
                            CGM.cgm_device_subject_id == subject.id) # Get cgm records

        # Generates cgm arrays for processing and visualization 
        cgmValueArray = [] 
        cgmTimeArray = []

        for cgmS in cgm.all():
            cgmValueArray.append(float(cgmS.value)) # numpy doesn't understand decimal
            cgmTimeArray.append(cgmS.time)

        #print(cgmTimeArray)
        metrics = compute_metrics_array(cgmValueArray,cgmTimeArray,d1,d2) # Computes all metrics, e.g., TIR, VAR, etc
        quality = compute_dataQuality_array(cgmTimeArray,d1,d2) # Computes data quality. At this point, it is defined as the amount of data
                                                           # that is associated with the selected date range.
        print(metrics)
        #glucSeries = compute_glucSeries(cgmTimeArray,cgmValueArray,d1,d2) # Generates object used in the area chart.
        glucSeries = compute_glucSeries_full(cgmTimeArray,cgmValueArray,d1,d2) # Generates object used in the area chart.
        #print(glucSeries)

        ###########################################################################
        # Replay panel
        basalP = db.session.query(BasalProfile).filter(BasalProfile.timeini >= d1, BasalProfile.timeini <= d2,
                            BasalProfile.subject_id == subject.id) # Gets basals
        CRP = db.session.query(CRProfile).filter(CRProfile.timeini >= d1, CRProfile.timeini <= d2,
                            CRProfile.subject_id == subject.id) # Gets CRs
        CFP = db.session.query(CFProfile).filter(CFProfile.timeini >= d1, CFProfile.timeini <= d2,
                            CFProfile.subject_id == subject.id) # Gets CFs
        meals = db.session.query(Meal).filter(Meal.time >= d1, Meal.time <= d2,
                            Meal.subject_id == subject.id) # Gets meal records
        insulin = db.session.query(Insulin).filter(Insulin.time >= d1, Insulin.time <= d2,
                            Insulin.pump_device_subject_id == subject.id) # Gets insulin records

        # Generates meal and HT arrays
        moM, moH = generate_mArrays_5min(meals.all())
        #print(moM)
        #print(moH)
        
        nHT = compute_nHT(moH,d1,d2)
        #print(nHT)

        basalV,corrV,mealV = generate_iArrays_5min(insulin.all())
        #print(basalV)
        #print(corrV)
        #print(mealV)

        tdb,tdi = compute_td(basalV,corrV,mealV,d1,d2)
        #print(tdb,tdi)

        def myFunc(e):
            return len(e)
                
        tmtiV = [a for a in dir(BasalProfile) if a.startswith('tmti')] # Same structure for all Basal, CF and CR
        tmtiV.sort(key=myFunc)

        # Captures basals and generates profiles
        basals = generate_parArray(tmtiV,basalP.all())
        bProfiles = extractProfiles(basals)
        #print('Basal profiles: ',len(bProfiles))
        print(bProfiles)

        # Captures crs and generates profiles
        crs = generate_parArray(tmtiV,CRP.all())
        crProfiles = extractProfiles(crs)
        #print('CR profiles: ',len(crProfiles))
        #print(crProfiles)

        # Captures cfs and generates profiles
        cfs = generate_parArray(tmtiV,CFP.all())
        cfProfiles = extractProfiles(cfs)
        #print('CF profiles: ',len(cfProfiles))
        #print(cfProfiles)

        ###########################################################################
        # Creates a response with the JSON representation of the given arguments
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
            'tdi': tdi
            })

        res = make_response(data,200)

    except exc.SQLAlchemyError as e:

        error = str(e.__dict__['orig'])
        res = make_response(jsonify({'error': error}), 204)

    except:
        
        res = make_response(jsonify({'error': 'Unexpected error!'}), 500) # who knows...

    return res

#########################################################################################################################

@app.route('/dashboard/run-replay', methods=['POST'])
@login_required
def run_replay():
    req = request.get_json()
    d1 = req['d1'] # startDay
    d2 = req['d2'] # endDay
    bProfiles = req['bProfiles']
    crProfiles = req['crProfiles']
    cfProfiles = req['cfProfiles']
    moM = req['moM']
    moH = req['moH']
    #print(bProfiles)
    try:
        subject = db.session.query(Subject).filter_by(
            username=current_user.username).first() # Gets user
        
        modelPar = db.session.query(ModelParameters).filter(ModelParameters.timeini >= d1, ModelParameters.timeini <= d2,
                                ModelParameters.subject_id == subject.id) # Get model parameters
        
        meals = db.session.query(Meal).filter(Meal.time >= d1, Meal.time <= d2,
                            Meal.subject_id == subject.id) # Gets meal records
        
        # Generates meal and HT arrays
        moMorig, moH = generate_mArrays_5min(meals.all())
        #print(moH)

        def myFunc(e):
            return len(e)

        xV = [a for a in dir(ModelParameters) if a.startswith('x')] # Same structure for all Basal, CF and CR
        xV.sort(key=myFunc)

        modelPars = generate_parArray(xV,modelPar.all())

        dataSim = {
            'bProfiles': bProfiles,
            'crProfiles': crProfiles,
            'cfProfiles': cfProfiles,
            'moM': moM,
            'moH': moH,
            'BW': float(subject.weight)
        }

        replayGlucSeries,htReplayPack,basalReplayPack,cBolusReplayPack,mBolusReplayPack = replaySim_preProc(modelPars,dataSim)
        #print(replayGlucSeries)
        
        cgmValueArray = []
        cgmTimeArray = []

        for ii in range(0,len(replayGlucSeries)):
            cgmValueArray.extend(replayGlucSeries[ii][1])
            cgmTimeArray.append(modelPars[ii][0])
            for jj in range(1,288):
                cgmTimeArray.append(modelPars[ii][0]+300*jj)
        
        replayMetrics = compute_metrics_array(cgmValueArray,cgmTimeArray,d1,d2)
        #print(replayMetrics)

        replaynHT = compute_nHT(htReplayPack,d1,d2)
        #print(replaynHT)

        replayTDB,replayTDI = compute_td(basalReplayPack,cBolusReplayPack,mBolusReplayPack,d1,d2)
        #print(replayTDB,replayTDI)

        data = jsonify({
            'metrics': replayMetrics,
            'glucSeries': replayGlucSeries,
            'nHT': replaynHT,
            'tdi': replayTDI,
            'tdb': replayTDB
            })

        res = make_response(data,200)

    except exc.SQLAlchemyError as e:

        error = str(e.__dict__['orig'])
        res = make_response(jsonify({'error': error}), 204)

    except:
        
        res = make_response(jsonify({'error': 'Unexpected error!'}), 500) # who knows...

    return res

#########################################################################################################################


@app.route('/support')
@login_required
def support():
    return render_template('support.html', name=current_user.username)

#########################################################################################################################

@app.route('/about')
@login_required
def about():
    return render_template('about.html', name=current_user.username)

#########################################################################################################################

@app.route('/dashboard/generate-report', methods=['POST'])
@login_required
def generate_report():
    try:
        req = request.get_json()
        d1 = req['d1'] # startDay
        d2 = req['d2'] # endDay
        replay = req['replay']
        original = req['original']
        #print(replay)
        #print(original)

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

        print('pepe')
        print(replay)
        print(replay_profiles)
        # if len(replay_profiles['bProfiles'])==0:
        #     print('pepe')
        #     replay = original
        # else:
        #     print('pepe1')

        if "bProfiles" in replay:
            print('case1')
            replay = original
        else:
            print('case2')

        #path_wkthmltopdf = r'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
        path_wkthmltopdf = r'/usr/local/bin/wkhtmltopdf'
        config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
        #print(np.nanmean(np.array(original['metrics']['percentR1'],dtype=np.float)))
        tirs,cvs,tdis,tdbs,hypors,hypers,hts = meanMetrics(original,replay)

        tir_string = tirChart(tirs)
        gluc_string = glucChart(original['glucSeries'],replay['glucSeries'])
        logo_string = logoChart()

        auxD1 = datetime.datetime.fromtimestamp(d1)
        startD = auxD1.strftime('%d %b %Y')
        auxD2 = datetime.datetime.fromtimestamp(d2)
        endD = auxD2.strftime('%d %b %Y')
        dateRange = startD+' - '+endD


        mProfile_string,mProfile_dates = profileChart(original['moM'],req['moM'],'meal',d2,288,'5min')

        bProfile_string,bProfile_dates = profileChart(original_profiles['bProfiles'],replay_profiles['bProfiles'],'bp',d2,48,'30min')
        cfProfile_string,cfProfile_dates = profileChart(original_profiles['cfProfiles'],replay_profiles['cfProfiles'],'cfp',d2,48,'30min')
        crProfile_string,crProfile_dates = profileChart(original_profiles['crProfiles'],replay_profiles['crProfiles'],'crp',d2,48,'30min')

        #print(mProfile_dates)
        #print(original['moM'])
        # print(req['moM'])

        rendered =  render_template('report.html',logo_string=logo_string,name=current_user.username,gluc_string=gluc_string,pie_string=tir_string,dateRange=dateRange,\
        bProfile_string=bProfile_string,bProfile_dates=bProfile_dates,\
        crProfile_string=crProfile_string,crProfile_dates=crProfile_dates,\
        cfProfile_string=cfProfile_string,cfProfile_dates=cfProfile_dates,\
        mProfile_string=mProfile_string,mProfile_dates=mProfile_dates,\
        o_70=np.around(tirs[0,0],decimals=1),o_70180=np.around(tirs[1,0],decimals=1),o_180250=np.around(tirs[2,0],decimals=1),o_250=np.around(tirs[3,0],decimals=1),\
        r_70=np.around(tirs[0,1],decimals=1),r_70180=np.around(tirs[1,1],decimals=1),r_180250=np.around(tirs[2,1],decimals=1),r_250=np.around(tirs[3,1],decimals=1),\
        d_70=np.around(tirs[0,1]-tirs[0,0],decimals=1),d_70180=np.around(tirs[1,1]-tirs[1,0],decimals=1),d_180250=np.around(tirs[2,1]-tirs[2,0],decimals=1),d_250=np.around(tirs[3,1]-tirs[3,0],decimals=1),\
        o_tdi=np.around(tdis[0],decimals=1),o_tdb=np.around(tdbs[0],decimals=1),o_var=np.around(cvs[0],decimals=1),o_hypor=np.around(hypors[0],decimals=1),o_hyper=np.around(hypers[0],decimals=1),o_ht=np.around(hts[0],decimals=1),\
        r_tdi=np.around(tdis[1],decimals=1),r_tdb=np.around(tdbs[1],decimals=1),r_var=np.around(cvs[1],decimals=1),r_hypor=np.around(hypors[1],decimals=1),r_hyper=np.around(hypers[1],decimals=1),r_ht=np.around(hts[1],decimals=1),\
        d_tdi=np.around(tdis[1]-tdis[0],decimals=1),d_tdb=np.around(tdbs[1]-tdbs[0],decimals=1),d_var=np.around(cvs[1]-cvs[0],decimals=1),d_hypor=np.around(hypors[1]-hypors[0],decimals=1),d_hyper=np.around(hypers[1]-hypers[0],decimals=1),d_ht=np.around(hts[1]-hts[0],decimals=1))

        pdf = pdfkit.from_string(rendered, False, configuration=config)
        pdfEncode = base64.b64encode(pdf).decode()
        data = jsonify({
            'pdf': pdfEncode
            })

        res = make_response(data,200)

    except:
        
        res = make_response(jsonify({'error': 'Unexpected error!'}), 500) # who knows...

    return res

#########################################################################################################################

@app.route('/contact',methods=['GET', 'POST'])
@login_required
def contact():
    subject = db.session.query(Subject).filter_by(
            username=current_user.username).first() # Gets user

    app.logger.info('You have accessed /contact')

    if request.method == 'POST':
        msgBody = request.form['msgBody']
        
        app.logger.info('Message body: ' + msgBody)
        #print(msgBody)

        if len(msgBody)>0:
            app.logger.info('non-empty message')
            #print('non-empty message')
            msg = Message('Inquiry on WST. Username: '+subject.username,recipients=['phcolmegna@gmail.com'])
            msg.html = msgBody
            app.logger.info('The message has been successfully created!')
            try:
                mail.send(msg)
                app.logger.info('The message has been successfully sent!')
            except Exception:
                error_message = traceback.format_exc()
                app.logger.info('There was an error while trying to deliver the email!')
                app.logger.info(error_message)
            # msg = Message('Hey there',recipients=['phcolmegna@gmail.com'])
            # msg.html = "<b>This is a testing email from WST to the world!</b>"
            # mail.send(msg)
            flash('Your message has been succesfully sent! We will contact you soon!')
        else:
            app.logger.info('empty message')
            #print('empty message')
            flash('No message! You should write something...')
        
        
    return render_template('contact_n.html', name=current_user.username,email=subject.email)

#########################################################################################################################

@app.route('/profile/<username>')
@login_required
def profile(username):
    try:
        subject = db.session.query(Subject).filter_by(
            username=current_user.username).first() # Gets user
        cgm = db.session.query(CGMDevice).filter_by(
            subject_id=subject.id).first() # Gets cgm_device
        pump = db.session.query(PumpDevice).filter_by(
            subject_id=subject.id).first() # Gets pump_device    
            
    except exc.SQLAlchemyError as e:

        error = str(e.__dict__['orig'])
        return make_response(jsonify({'error': error}), 204)

    except:
        
        return make_response(jsonify({'error': 'Unexpected error!'}), 500) # who knows...

    print('Subject: '+subject.username, subject.email, np.around(float(subject.weight),decimals=1), subject.height, subject.age)
    print('CGM device: '+cgm.device, np.around(float(cgm.min_cgm),decimals=1), np.around(float(cgm.max_cgm),decimals=1))
    print('Pump device:'+pump.device, np.around(float(pump.reservoir_size),decimals=1), np.around(float(pump.max_bolus),decimals=1),\
        np.around(float(pump.min_bolus),decimals=1), np.around(float(pump.bolus_quanta),decimals=4), np.around(float(pump.max_basal),decimals=1),\
            np.around(float(pump.min_basal),decimals=1), np.around(float(pump.basal_quanta),decimals=4))
    return render_template('profile.html',name=subject.username, user_name=subject.username, user_email=subject.email, user_weight=np.around(float(subject.weight),decimals=1),\
         user_height=subject.height,user_age=subject.age, cgm_device=cgm.device, cgm_min=np.around(float(cgm.min_cgm),decimals=1), cgm_max=np.around(float(cgm.max_cgm),decimals=1), \
         pump_device=pump.device, pump_res=np.around(float(pump.reservoir_size),decimals=1), pump_maxBolus=np.around(float(pump.max_bolus),decimals=1), pump_minBolus=np.around(float(pump.min_bolus),decimals=1),\
         pump_quantaBolus=np.around(float(pump.bolus_quanta),decimals=4), pump_maxBasal=np.around(float(pump.max_basal),decimals=1), pump_minBasal= np.around(float(pump.min_basal),decimals=1), pump_quantaBasal=np.around(float(pump.basal_quanta),decimals=4))
    # return render_template('profile.html', user_name=subject.username, user_email=subject.email, user_weight=subject.weight,\
    #     user_height=subject.height,user_age=subject.age, cgm_device=cgm.device, cgm_min=cgm.min_cgm, cgm_max=cgm.max_cgm,
    #     pump_device=pump.device, pump_res=pump.reservoir_size, pump_maxBolus=pump.max_bolus, pump_minBolus=pump.min_bolus,\
    #     pump_quantaBolus=pump.bolus_quanta, pump_maxBasal=pump.max_basal, pump_minBasal=pump.min_basal, pump_quantaBasal=pump.basal_quanta)

#########################################################################################################################

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
