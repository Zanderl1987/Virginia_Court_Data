function sim = run_nintegration(profile,struttura,ivcSig,h,model_x0,options_replay,profile_replay)
    
    n = round(struttura.tau/h); %Shift units
    
    model_x      = zeros(16,length(profile.time)+1);
    model_x(:,1) = model_x0;
    tRK          = 0;

    rqsto        = model_x0(1)+model_x0(2);
    dosekempt    = profile.dosekempt;
    lastMeal     = profile.lastMeal;
    indHTimer    = profile_replay.HTimer;
    indCorrTimer = profile_replay.corrTimer;

    insDur = profile_replay.insDur;

    Bmeal_c = [1 0 0]';
    Cmeal_c = [0 0 struttura.f*struttura.kabs/struttura.BW];

    Ains_d = expm(struttura.Ains*h);
    Bins_d = struttura.Ains\(Ains_d-eye(length(Ains_d)))*struttura.Bins;
    
    model_xIns      = zeros(4,length(profile.time)+1);
    model_xIns(:,1) = [model_x0(4:5);model_x0(8);model_x0(12)];
    model_xMeal     = zeros(3,length(profile.time)+1);
    model_xMis      = zeros(9,length(profile.time)+1);
    model_xMis(:,1) = [model_x0(6:7);model_x0(9:11);model_x0(13:end)]; 

    Uaux = zeros(7,1);
    Uaux(2) = lastMeal;
    
    INSdif_6 = profile_replay.INSdif_6;
    BP_6 = profile_replay.bProfiles_6;

    A_delay_aux  = eye(n-1);
    A_delay_aux1 = zeros(1,n);
    A_delay_aux2 = zeros(n-1,1);
    A_delay      = [A_delay_aux1;A_delay_aux A_delay_aux2];
    B_delay      = [1;zeros(n-1,1)];
    C_delay      = [zeros(1,n-1) 1];
    
    model_delay = 0.2*(6000/struttura.BW)*profile_replay.insulinV_6(end)*ones(n,1);
    
    x = length(profile.pivc_x);
    
    if sum(profile.pivc_x)==0
        ivcSig_x = ivcSig(1)*ones(1,x);
    else
        ivcSig_x = profile.pivc_x;
    end
    
    ivcSigp   = [ivcSig_x(1) ivcSig_x(1)];
    ivcSig_Fp = [ivcSig_x(end) ivcSig_x(end)];
    
    fNum = [0.003916126660547   0.007832253321095   0.003916126660547];
    fDen = [1.000000000000000  -1.815341082704568   0.831005589346757];
    
    for ii=1:x
        ivcSigF   = sum(fNum.*[ivcSig_x(ii) ivcSigp])-sum(fDen(2:end).*ivcSig_Fp);
        ivcSigp   = [ivcSig_x(ii) ivcSigp];
        ivcSigp   = ivcSigp(1:end-1);
        ivcSig_Fp = [ivcSigF ivcSig_Fp];
        ivcSig_Fp = ivcSig_Fp(1:end-1);
    end

    ivcSigF_acum = [];

    if options_replay.apSel==1
        flagInsSusp = profile_replay.ap.flagInsSusp;
        tInsSusp = profile_replay.ap.tInsSusp;
        gTPred = profile_replay.ap.gTPred;
        gVPred = profile_replay.ap.gVPred;
    elseif options_replay.apSel==2
        J24h = profile_replay.ap.J24h;
        J6 = profile_replay.ap.J6;
        M6 = profile_replay.ap.M6;
        G6 = profile_replay.ap.G6;
        sbMem = profile_replay.ap.sbMem;
        TDIest = profile_replay.ap.TDIest;
    end
    
    delayB = 0;
    indExtMBTimer = 0;
    indExtCBTimer = 0;
    rMDose = 0;
    rCDose = 0;
    rCDose_final = 0;
    rMDose_final = 0;
    flagInsSusp = 0;
    
    for ii=1:length(profile.time)

        ivcSigF   = sum(fNum.*[ivcSig(ii) ivcSigp])-sum(fDen(2:end).*ivcSig_Fp);
        ivcSigp   = [ivcSig(ii) ivcSigp];
        ivcSigp   = ivcSigp(1:end-1);
        ivcSig_Fp = [ivcSigF ivcSig_Fp];
        ivcSig_Fp = ivcSig_Fp(1:end-1);
        Uaux(4)   = ivcSigF;

        Uaux(5) = profile_replay.CR(ii);
        Uaux(6) = profile_replay.CF(ii);
        Uaux(7) = profile_replay.target(ii);

        if options_replay.apSel == 2
            TDIpop = profile_replay.ap.TDIpop(ii);
            tgt    = profile_replay.ap.tgt(ii);
            sleep  = profile_replay.ap.sleep(ii);
            ex     = profile_replay.ap.EX(ii);
        end
        
        % IOB estimation
        IOBest_BC = IOB_estimator(INSdif_6,options_replay.apSel,insDur);

        % Extended Meal bolus
        if indExtMBTimer >=1 && flagInsSusp~=1
            indExtMBTimer = indExtMBTimer-1;
            rMDose_final = rMDose;
        else
            indExtMBTimer = 0;
            rMDose = 0.0;
            rMDose_final = 0.0;
        end

        % Extended Corr bolus
        if indExtCBTimer >=1 && flagInsSusp~=1
            indExtCBTimer = indExtCBTimer-1;
            rCDose_final = rCDose;
        else
            indExtCBTimer = 0;
            rCDose = 0.0;
            rCDose_final = 0.0;
        end

        % Bolus calculator
        mBolus = 0;
        cBolus = 0;

        if profile_replay.mBolusV(ii)>0
            delayB = profile_replay.lagB(ii);
            indCorrTimer = 1;
            g = model_x(13,ii)/struttura.Vg;
            cho = profile_replay.choV(ii)/1e3;
            if profile_replay.userOv(ii) == 0
                [mBolus_f,mBolus,rMDose,indExtMBTimer] = MB_calculator(cho,g,Uaux(5),Uaux(6),Uaux(7),IOBest_BC,profile_replay.corrDecl(ii),profile_replay.extB(ii),profile_replay.extB_per(ii),profile_replay.extB_dur(ii));
            else
                [mBolus_f,mBolus,rMDose,indExtMBTimer] = FB_calculator(profile_replay.mBolusV(ii),profile_replay.extB(ii),profile_replay.extB_per(ii),profile_replay.extB_dur(ii));
            end
        end

        if profile_replay.cBolusV(ii)>0 && profile_replay.choV(ii) == 0 && profile_replay.BT(ii) == 0
            delayB = profile_replay.lagB(ii);
            indCorrTimer = 1;
            g = model_x(13,ii)/struttura.Vg;
            if profile_replay.userOv(ii) == 0
                [cBolus_f,cBolus,rCDose,indExtCBTimer] = CB_calculator(g,Uaux(6),Uaux(7),IOBest_BC,profile_replay.extB(ii),profile_replay.extB_per(ii),profile_replay.extB_dur(ii));
            else
                [cBolus_f,cBolus,rCDose,indExtCBTimer] = FB_calculator(profile_replay.cBolusV(ii),profile_replay.extB(ii),profile_replay.extB_per(ii),profile_replay.extB_dur(ii));
            end
        end
        
        basal = profile_replay.basalPM(ii)/12.0;

        % IOB re-estimation taking into account async bolus
        INSdif_6_aux = [INSdif_6(1:end-1) INSdif_6(end)+(mBolus+cBolus+rMDose_final+rCDose_final)];
        IOBest_BC = IOB_estimator(INSdif_6_aux,options_replay.apSel,insDur);

        if options_replay.apSel == 2
            J24h_aux = J24h;
            if length(J24h)==288
                J24h_aux(end) = J24h(end)+mBolus+cBolus+rMDose_final+rCDose_final;
            else
                J24h_aux = [J24h_aux  mBolus+cBolus+rMDose_final+rCDose_final];
            end
            J6_aux = J6;
            J6_aux(end) = J6(end)+mBolus+cBolus+rMDose_final+rCDose_final;

            M6_aux = M6;
            M6_aux(end) = M6(end)+profile_replay.choV(ii)/1e3;
        end

        if options_replay.apSel == 0
            apDose = basal;
        elseif options_replay.apSel == 1
            [apDose,tInsSusp,flagInsSusp] = basalIQ(gTPred,gVPred,tInsSusp,basal,flagInsSusp);
        else
            tod = (ii-1)*5.0/60.0;
            [TDIest,sbMem,apBDose,apCDose,indCorrTimer,GP30] = controlIQ(J24h_aux,J6_aux,G6,M6_aux,tod,BP_6,profile_replay.basalPM(ii),Uaux(6),ex,indCorrTimer,sbMem,TDIpop,sleep,tgt,struttura.BW,TDIest);
            apDose = apBDose+apCDose;
        end

        if indCorrTimer == 0
            delayB = 0;
        end

        % Correction bolus
        if indCorrTimer>=12+delayB
            indCorrTimer = 0;
        elseif indCorrTimer>=1
            indCorrTimer = indCorrTimer+1;
        end

        % Final insulin dose
        Uaux(3) = 6000*(mBolus+cBolus+apDose+rMDose_final+rCDose_final)/5/struttura.BW;
        
        % Update 6h insulin vector
        INSdif_6 = [INSdif_6(2:end) mBolus+cBolus+rMDose_final+rCDose_final+apDose-profile_replay.basalPM(ii)/12.0];
        BP_6 = [BP_6(2:end) profile_replay.basalPM(ii)];

        if options_replay.apSel == 2
            if length(J24h)==288
                J24h = [J24h(2:end) mBolus+cBolus+rMDose_final+rCDose_final+apDose];
            else
                J24h = [J24h mBolus+cBolus+rMDose_final+rCDose_final+apDose];
            end
            J6 = [J6(2:end) mBolus+cBolus+rMDose_final+rCDose_final+apDose];
            M6 = [M6(2:end) profile_replay.choV(ii)/1e3];
        end

        Uaux(1) = profile.meal.values(ii);

        % Meals        
        if profile.meal.values(ii)>0.0
            rqsto = model_xMeal(1,ii)+model_xMeal(2,ii);
            lastMeal  = profile.meal.values(ii)*h;
            Uaux(2)   = lastMeal;
            dosekempt = Uaux(2)+rqsto;
        end
        
        struttura.dosekempt = dosekempt;
        struttura.rqsto     = rqsto;
        
        if struttura.dosekempt>0.0
            aa=5/2/(1-struttura.b)/struttura.dosekempt;
            cc=5/2/struttura.d/struttura.dosekempt;
            if struttura.dosekempt<=16000
                struttura.kgut=struttura.kmax;
            else
                struttura.kgut=struttura.kmin+(struttura.kmax-struttura.kmin)/2*(tanh(aa*(model_xMeal(1,ii)+model_xMeal(2,ii)-struttura.b*struttura.dosekempt))-tanh(cc*(model_xMeal(1,ii)+model_xMeal(2,ii)-struttura.d*struttura.dosekempt))+2);
            end
        else
            struttura.kgut=struttura.kmax;
        end
        
        if lastMeal<=20000
            mF = 5;
            Ameal_c = [-mF*struttura.kmax 0 0;mF*struttura.kmax -mF*struttura.kgut 0;0 mF*struttura.kgut -struttura.kabs];
        else
            Ameal_c = [-struttura.kmax 0 0;struttura.kmax -struttura.kgut 0;0 struttura.kgut -struttura.kabs];
        end
                
        Ameal_d = expm(Ameal_c*h);
        Bmeal_d = Ameal_c\(Ameal_d-eye(length(Ameal_c)))*Bmeal_c;
        
        model_xMeal(:,ii+1) = Ameal_d*model_xMeal(:,ii)+Bmeal_d*Uaux(1);
        Rat = Cmeal_c*model_xMeal(:,ii);
        
        % Ins
        model_delay(:,ii+1) = A_delay*model_delay(:,ii)+B_delay*Uaux(3);
        model_xIns(:,ii+1)  = Ains_d*model_xIns(:,ii)+Bins_d*C_delay*model_delay(:,ii);
        
        It = model_xIns(3,ii)/struttura.Vi;
        In = It*Uaux(4);
        
        % Mis
        k1 = model_equations(model_xMis(:,ii),struttura,[It;In;Rat]); 
        k2 = model_equations(model_xMis(:,ii)+h*k1/2,struttura,[It;In;Rat]); 
        k3 = model_equations(model_xMis(:,ii)+h*k2/2,struttura,[It;In;Rat]); 
        k4 = model_equations(model_xMis(:,ii)+h*k3,struttura,[It;In;Rat]); 

        model_xMis(:,ii+1) = model_xMis(:,ii) + h*(k1+2*k2+2*k3+k4)/6;
        model_xMis([1 2 4 5 6],ii+1)   = max(model_xMis([1 2 4 5 6],ii+1),zeros(5,1)); 
        model_x([1:3],ii+1)            = model_xMeal(:,ii+1);
        model_x([4:5 8 12],ii+1)       = model_xIns(:,ii+1);
        model_x([6:7 9:11 13:16],ii+1) = model_xMis(:,ii+1);

        if options_replay.apSel == 1
            gVPred = [gVPred(2:end) model_x(13,ii)/struttura.Vg];
        end

        if options_replay.apSel == 2
            G6 = [G6(2:end) model_x(13,ii)/struttura.Vg];
        end

        tRK = tRK + h; 
        
        ivcSigF_acum = [ivcSigF_acum ivcSigF];
    end
    
    sim.simGlucose = (model_x(13,1:end-1)/struttura.Vg).*(model_x(13,1:end-1)/struttura.Vg>=20 & model_x(13,1:end-1)/struttura.Vg<=400)+20.*(model_x(13,1:end-1)/struttura.Vg<20)+400.*(model_x(13,1:end-1)/struttura.Vg>400);
    sim.model_xf = model_x(:,end-1);
    sim.dosekempt = dosekempt;
    sim.lastMeal = lastMeal;
    sim.ivcSigF = ivcSigF_acum;

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function IOBest = IOB_estimator(INSdif,apSel,insDur)

        IOB_curve_6h = [0.0041;0.0046;0.0050;0.0055;0.0061;0.0067;0.0073;0.0081;0.0089;0.0098;0.0107;0.0118;
                    0.0129;0.0142;0.0156;0.0171;0.0188;0.0206;0.0226;0.0248;0.0272;0.0298;0.0327;0.0358;
                    0.0392;0.0429;0.0469;0.0513;0.0561;0.0613;0.0670;0.0732;0.0799;0.0872;0.0951;0.1036;
                    0.1129;0.1230;0.1339;0.1456;0.1583;0.1720;0.1867;0.2025;0.2196;0.2378;0.2574;0.2784;
                    0.3007;0.3246;0.3499;0.3768;0.4053;0.4353;0.4670;0.5001;0.5348;0.5708;0.6080;0.6463;
                    0.6854;0.7250;0.7647;0.8040;0.8422;0.8787;0.9125;0.9426;0.9676;0.9860;0.9959;0.9953];

        IOB_curve_2h_mud = [0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 
                    0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0;0.0018;0.0057;0.0106;0.0166;
                    0.0240;0.0330;0.0437;0.0565;0.0716;0.0891;0.1095;0.1329;0.1597;0.1900;0.2242;0.2623;0.3046;
                    0.3510;0.4015;0.4559;0.5139;0.5748;0.6380;0.7021;0.7658;0.8270;0.8834;0.9317;0.9682;0.9884;0.9866];

        IOB_curve_3h_mud = [0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0.0007;0.0019;
                    0.0034;0.0052;0.0073;0.0099;0.0129;0.0164;0.0205;0.0253;0.0308;0.0371;0.0444;0.0527;0.0621;0.0727;0.0846;
                    0.0981;0.1131;0.1298;0.1484;0.1690;0.1917;0.2166;0.2438;0.2734;0.3055;0.3402;0.3773;0.4170;0.4592;0.5035;
                    0.5500;0.5981;0.6475;0.6976;0.7477;0.7969;0.8441;0.8878;0.9266;0.9583;0.9808;0.9913;0.9866];

        IOB_curve_4h_mud = [0.0000;0.0001;0.0001;0.0002;0.0003;0.0004;0.0005;0.0007;0.0009;0.0011;
                    0.0013;0.0016;0.0020;0.0024;0.0029;0.0034;0.0040;0.0047;0.0056;0.0065;0.0076;0.0088;0.0102;0.0117;0.0135;
                    0.0155;0.0178;0.0204;0.0233;0.0265;0.0302;0.0343;0.0388;0.0439;0.0496;0.0560;0.0630;0.0708;0.0795;0.0890;
                    0.0996;0.1112;0.1240;0.1381;0.1535;0.1703;0.1887;0.2087;0.2304;0.2539;0.2793;0.3066;0.3360;0.3674;0.4008;
                    0.4363;0.4738;0.5133;0.5544;0.5971;0.6411;0.6860;0.7312;0.7761;0.8201;0.8620;0.9008;0.9350;0.9629;0.9825;0.9913;0.9866];

        IOB_curve_5h_mud = [0.0027;0.0030;0.0033;0.0037;0.0041;0.0045;0.0050;0.0055;0.0061;0.0068;0.0076;
                    0.0084;0.0093;0.0103;0.0114;0.0126;0.0139;0.0154;0.0170;0.0188;0.0207;0.0229;0.0253;0.0279;0.0308;0.0340;0.0374;
                    0.0413;0.0454;0.0500;0.0550;0.0605;0.0665;0.0731;0.0803;0.0881;0.0967;0.1060;0.1161;0.1271;0.1391;0.1521;0.1661;
                    0.1814;0.1978;0.2156;0.2348;0.2554;0.2775;0.3012;0.3265;0.3536;0.3823;0.4129;0.4451;0.4791;0.5148;0.5520;0.5907;
                    0.6306;0.6715;0.7130;0.7547;0.7960;0.8362;0.8745;0.9098;0.9408;0.9660;0.9836;0.9913;0.9866];

        IOB_curve_6h_mud = [0.0082;0.0090;0.0098;0.0106;0.0116;0.0126;0.0137;0.0149;0.0162;0.0176;0.0191;0.0208;
                    0.0226;0.0245;0.0267;0.0289;0.0314;0.0341;0.0370;0.0401;0.0435;0.0472;0.0511;0.0554;0.0600;0.0649;0.0703;0.0760;0.0822;
                    0.0889;0.0961;0.1038;0.1120;0.1209;0.1304;0.1407;0.1516;0.1633;0.1758;0.1892;0.2034;0.2186;0.2348;0.2520;0.2703;0.2897;
                    0.3102;0.3319;0.3548;0.3789;0.4043;0.4309;0.4587;0.4878;0.5180;0.5493;0.5816;0.6149;0.6489;0.6834;0.7184;0.7533;0.7880;
                    0.8220;0.8549;0.8859;0.9145;0.9397;0.9608;0.9765;0.9856;0.9866];
        
        IOB_curve_7h_mud = [0.0193;0.0208;0.0223;0.0240;0.0258;0.0277;0.0297;0.0319;0.0342;0.0367;0.0394;0.0423;0.0453;
                    0.0486;0.0521;0.0558;0.0598;0.0641;0.0686;0.0734;0.0786;0.0841;0.0899;0.0962;0.1028;0.1099;0.1174;0.1253;0.1338;0.1428;0.1523;
                    0.1624;0.1732;0.1845;0.1965;0.2092;0.2225;0.2367;0.2516;0.2673;0.2838;0.3011;0.3194;0.3385;0.3585;0.3794;0.4013;0.4240;0.4477;
                    0.4723;0.4978;0.5242;0.5513;0.5793;0.6079;0.6371;0.6667;0.6968;0.7270;0.7572;0.7872;0.8167;0.8454;0.8729;0.8989;0.9228;0.9441;
                    0.9622;0.9764;0.9858;0.9896;0.9866];

        IOB_curve_8h_mud = [0.0343;0.0365;0.0389;0.0414;0.0441;0.0469;0.0499;0.0531;0.0564;0.0600;0.0638;0.0678;0.0720;0.0765;
                    0.0813;0.0863;0.0916;0.0972;0.1032;0.1094;0.1161;0.1231;0.1304;0.1382;0.1464;0.1551;0.1642;0.1738;0.1838;0.1944;0.2056;0.2173;0.2295;
                    0.2424;0.2558;0.2700;0.2847;0.3001;0.3162;0.3330;0.3505;0.3688;0.3877;0.4074;0.4278;0.4489;0.4708;0.4933;0.5165;0.5404;0.5649;0.5900;
                    0.6156;0.6416;0.6680;0.6947;0.7215;0.7483;0.7751;0.8015;0.8274;0.8526;0.8769;0.8998;0.9211;0.9405;0.9574;0.9714;0.9819;0.9885;0.9903;
                    0.9866];

        if apSel == 2
            IOB_curve = IOB_curve_6h;
        else
            if insDur == 2
                IOB_curve = IOB_curve_2h_mud;
            elseif insDur == 3
                IOB_curve = IOB_curve_3h_mud;
            elseif insDur == 4
                IOB_curve = IOB_curve_4h_mud;
            elseif insDur == 5
                IOB_curve = IOB_curve_6h;
            elseif insDur == 6
                IOB_curve = IOB_curve_6h_mud;
            elseif insDur == 7
                IOB_curve = IOB_curve_7h_mud;
            elseif insDur == 8
                IOB_curve = IOB_curve_8h_mud;
            else
                IOB_curve = IOB_curve_5h_mud;
            end
        end

        IOBest = INSdif*IOB_curve;
        IOBest = IOBest.*(IOBest>=0);

    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function [tBolus_f,tBolus,rDose,indExtBTimer] = MB_calculator(cho,g,CR,CF,target,IOBest,corrDecl,extB,extB_per,extB_dur)
        
        mDose = cho/CR;
        cDose = (g-target)/CF;
        
        tBolus = 0;
        tBolus_f = 0;
        indExtBTimer = 0;
        rDose = 0;

        if mDose>0
            tBolus_f = mDose;
            if extB>0
                indExtBTimer = fix(extB_dur/5);
                rDose = ((100.0-extB_per)*mDose/100.0)/indExtBTimer;
                mDose = extB_per*mDose/100.0;
            end
            if corrDecl==1 && g>70.0
                tBolus = mDose;
            else
                if cDose>=0
                    if cDose-IOBest<0
                        tBolus = mDose;
                    else
                        tBolus = mDose+cDose-IOBest;
                        tBolus_f = tBolus_f+cDose-IOBest;
                    end
                else
                    if mDose+cDose-IOBest>0
                        tBolus = mDose+cDose-IOBest;
                        tBolus_f = tBolus_f+cDose-IOBest;
                    else
                        tBolus = mDose;
                    end
                end
            end
        end

    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function [tBolus_f,tBolus,rDose,indExtBTimer] = CB_calculator(g,CF,target,IOBest,extB,extB_per,extB_dur)

        cDose = (g-target)/CF;
        
        tBolus = 0.0;
        indExtBTimer = 0;
        rDose = 0.0;
        tBolus_f = 0.0;

        if cDose>=0
            if cDose-IOBest<0
                tBolus = 0.0;
            else
                cBolus = cDose-IOBest;
                tBolus_f = cDose-IOBest;
                if extB>0
                    indExtBTimer = fix(extB_dur/5);
                    rDose = ((100.0-extB_per)*cBolus/100.0)/indExtBTimer;
                    tBolus = extB_per*cBolus/100.0;
                else
                    tBolus = cBolus;
                end
            end
        end

    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function [tBolus_f,tBolus,rDose,indExtBTimer] = FB_calculator(dose,extB,extB_per,extB_dur)  

        tBolus = 0.0;
        indExtBTimer = 0;
        rDose = 0.0;
        tBolus_f = 0.0;

        if dose>=0
            tBolus_f = dose;
            if extB>0
                indExtBTimer = fix(extB_dur/5);
                rDose = ((100.0-extB_per)*dose/100.0)/indExtBTimer;
                tBolus = extB_per*dose/100.0;
            else
                tBolus = dose;
            end
        end
    
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function [apDose,tInsSusp,flagInsSusp] = basalIQ(gTPred,gVPred,tInsSusp,basal,flagInsSusp)
        
        gPredModel = polyfit(gTPred,gVPred,1);
        g30min = polyval(gPredModel,30);

        preFlagInsSusp = 0;
        preFlagInsRes = 0;

        if gVPred(end)<70 || g30min<80
            preFlagInsSusp = 1;
        end

        if flagInsSusp==1 && ((gVPred(end)>gVPred(end-1)) || g30min>=80 || tInsSusp>120)
            preFlagInsRes = 1;
        end

        if preFlagInsSusp==1 && preFlagInsRes==0
            flagInsSusp = 1;
        elseif preFlagInsRes == 1
            flagInsSusp = 0;
        end

        if flagInsSusp == 1
            apDose = 0;
            tInsSusp = tInsSusp+5;
        else
            apDose = basal;
            tInsSusp = min(tInsSusp-5,0);
        end

    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function [TDIest,sbMem,apBDose,apCDose,indCorrTimer,GP30] = controlIQ(J24r,J6,G6,M6,tod,bh6,basal,CF,EX,indCorrTimer,sbMem,TDIpop,sleep,tgt,BW,TDIest)
    
        INSdif = J6-bh6/12; % U every 5 min
        
        % 1- Estimate TDI 
        if mod(round(60*tod),20)<=1 % Update TDIest and sbMem every 20 min
            [TDIest,sbMem] = controlIQ_TDI(J24r,sbMem,TDIpop);
        end

        % 2- Estimate IOB -> It is relative to basal rate
        
        IOBest = controlIQ_IOB(INSdif);
        
        % 3 - Predict glucose
        
        [GP30,GPL,Gest] = controlIQ_USSPred(INSdif,G6,M6,basal,BW);
        
        % 4 - Run HMS
        
        [corrBol,indCorrTimer] = controlIQ_BOP(CF,indCorrTimer,sleep,IOBest,GP30);
        
        % 5 - Run BRM
        
        [du,a,gt] = controlIQ_BRM(CF,EX,tgt,TDIest,IOBest,Gest,GP30);
        
        % 6 - Apply brakes
        
        [usugg,apBDose,apCDose] = controlIQ_FC(basal,EX,GPL,corrBol,du,a);

    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function [TDIest,SumBolusMEM]=controlIQ_TDI(INS,SumBolusMEM,TDIpop)
        
        B = [1.17E-04;1.90E-04;3.11E-04;5.07E-04;8.28E-04;1.35E-03;2.20E-03;3.60E-03;5.87E-03;
            9.58E-03;1.56E-02;2.55E-02;1.21E-04;1.98E-04;3.24E-04;5.28E-04;8.62E-04;1.41E-03;
            2.30E-03;3.75E-03;6.12E-03;9.98E-03;1.63E-02;2.66E-02;1.27E-04;2.07E-04;3.37E-04;
            5.50E-04;8.98E-04;1.47E-03;2.39E-03;3.90E-03;6.37E-03;1.04E-02;1.70E-02;2.77E-02;
            1.32E-04;2.15E-04;3.51E-04;5.73E-04;9.35E-04;1.53E-03;2.49E-03;4.07E-03;6.64E-03;
            1.08E-02;1.77E-02;2.89E-02;1.37E-04;2.24E-04;3.66E-04;5.97E-04;9.74E-04;1.59E-03;
            2.60E-03;4.24E-03;6.91E-03;1.13E-02;1.84E-02;3.01E-02;1.43E-04;2.33E-04;3.81E-04;
            6.22E-04;1.02E-03;1.66E-03;2.70E-03;4.41E-03;7.20E-03;1.18E-02;1.92E-02;3.13E-02;
            1.49E-04;2.43E-04;3.97E-04;6.48E-04;1.06E-03;1.73E-03;2.82E-03;4.60E-03;7.50E-03;
            1.22E-02;2.00E-02;3.26E-02;1.55E-04;2.53E-04;4.13E-04;6.75E-04;1.10E-03;1.80E-03;
            2.93E-03;4.79E-03;7.81E-03;1.28E-02;2.08E-02;3.40E-02;1.62E-04;2.64E-04;4.31E-04;
            7.03E-04;1.15E-03;1.87E-03;3.06E-03;4.99E-03;8.14E-03;1.33E-02;2.17E-02;3.54E-02;
            1.68E-04;2.75E-04;4.49E-04;7.32E-04;1.20E-03;1.95E-03;3.18E-03;5.20E-03;8.48E-03;
            1.38E-02;2.26E-02;3.69E-02;1.75E-04;2.86E-04;4.67E-04;7.63E-04;1.24E-03;2.03E-03;
            3.32E-03;5.41E-03;8.83E-03;1.44E-02;2.35E-02;3.84E-02;1.83E-04;2.98E-04;4.87E-04;
            7.95E-04;1.30E-03;2.12E-03;3.45E-03;5.64E-03;9.20E-03;1.50E-02;2.45E-02;4.00E-02];
        
        B = reshape(B,144,1);
        AX0 = 2.691e-3;
        SumBolusAux = [TDIpop*ones(1,143-length(SumBolusMEM)) SumBolusMEM(max(1,end-142):end)];
        
        if length(INS)<(0.85*288)
            SumBolus = TDIpop;
        else
            SumBolus = sum(INS(max(1,end-287):end));
        end

        TDIest = AX0*TDIpop+[SumBolusAux SumBolus]*B;
        
        if TDIest>2*TDIpop
            TDIest = 2*TDIpop;
        elseif TDIest<0.5*TDIpop
            TDIest = 0.5*TDIpop;
        end

        SumBolusMEM = [SumBolusMEM(2:end) SumBolus];

    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function IOBest = controlIQ_IOB(INSdif)
        
        IOB_curve_4h = [0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;
            0;0;0;0;0;0;0.0013;0.0028;0.0045;0.0064;0.0085;
            0.0108;0.0135;0.0164;0.0196;0.0233;0.0273;0.0318;
            0.0369;0.0425;0.0487;0.0556;0.0633;0.0719;0.0813;
            0.0918;0.1034;0.1162;0.1304;0.1460;0.1632;0.1822;
            0.2029;0.2257;0.2506;0.2777;0.3072;0.3393;0.3739;
            0.4111;0.4510;0.4936;0.5387;0.5861;0.6355;0.6865;
            0.7383;0.7901;0.8407;0.8884;0.9312;0.9664;0.9908];
        
        IOBest = INSdif*IOB_curve_4h;
        IOBest = IOBest.*(IOBest>=0);

    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function [GP30,GPL,Gest] = controlIQ_USSPred(INSdif,G6,M6,basal,BW)
        
        Gop = 90; % [mg/dl]
        
        INS_A = [0.9048 6.256e-6 2.996e-6/BW 1.551e-6/BW;
                0 0.4107 0.5301/BW 0.28/BW;
                0 0 0.9048 0.0452;
                0 0 0 0.9048];

        INS_B = [2.792e-6/BW;0.8035/BW;0.117;4.758];

        INS_C = [1 0 0 0
                0 1 0 0
                0 0 1 0
                0 0 0 1];

        INS_D = [0;0;0;0];

        MEAL_A = [0.9512 0.06959;
                0 0.9048];

        MEAL_B = [0.1784;4.758];

        MEAL_C = [0.01 0.005;
                1 0;
                0 1];

        MEAL_D = [0;0;0];

        CORE_pred_A = [0.7408 -2296 -1728 0.117/BW 0.0744/BW -0.0169 -0.0203/BW -0.0347/BW
                    0 0.9704 0 0 0 0 0 0
                    0 0 0.5488 0 0 6.89e-6 1.75e-5/BW 2.794e-5/BW
                    0 0 0 0.7408 0.2880 0 0 0
                    0 0 0 0 0.5488 0 0 0
                    0 0 0 0 0 0.0048 0.4315/BW 0.5836/BW
                    0 0 0 0 0 0 0.5488 0
                    0 0 0 0 0 0 0.1646 0.5488];

        CORE_pred_C = [1 0 0 0 0 0 0 0];

        LIGHT_pred_A = [0.8607 -1244 -1079 0.068/BW 0.0388/BW -8.29e-3 -4.34e-3/BW -8.034e-3/BW;
                        0 0.9851 0 0 0 0 0 0
                        0 0 0.7408 0 0 8.5e-06 8.217e-6/BW 1.472e-5/BW
                        0 0 0 0.8607 0.1798 0 0 0
                        0 0 0 0 0.7408 0 0 0
                        0 0 0 0 0 0.0693 0.4338/BW 0.7204/BW
                        0 0 0 0 0 0 0.7408 0
                        0 0 0 0 0 0 0.1111 0.7408];

        LIGHT_pred_B = [0.2936/BW -0.0186/BW;
                        0 0;
                        0 9.726e-05/BW;
                        1.4552 0;
                        12.9591 0;
                        0 4.6119/BW;
                        0 12.9591;
                        0 0.9234];

        LIGHT_pred_C = [1 0 0 0 0 0 0 0];

        KF_A = [6.486e-3 -417.53;
                7.136e-4 0.9048];

        KF_B = [-2.14e-3 2.5669/BW 0.9447;
                9.5163e-6 0 -7.136e-4];

        KF_C = [0.353 0;
                7.887e-4 1];

        KF_D = [0 0 0.647;
                0 0 -7.887e-4];

        BUFF_MEAL_A = [0.6065 0.3033;
                    0 0.6065];

        BUFF_MEAL_B = [0.0902;0.3935]; 

        BUFF_MEAL_C = [1 0];

        BUFF_INS_A = [0.6065 0.3033;
                    0 0.6065];

        BUFF_INS_B = [0.0902;0.3935];

        BUFF_INS_C = [1 0];

        %KF loop
        
        MB      = zeros(2,length(G6));
        MX      = zeros(2,length(G6)+1);
        Mout    = zeros(3,length(G6));
        IB      = zeros(2,length(G6));
        IX      = zeros(4,length(G6)+1);
        Iout    = zeros(4,length(G6));
        KFout   = zeros(2,length(G6));
        KFstate = zeros(2,length(G6)+1);

        for k=1:length(G6)
            
            MB(:,k+1) = BUFF_MEAL_A*MB(:,k)+BUFF_MEAL_B*1000*M6(k)/5; % ts = 5 min; input in mg / 5 min
            MX(:,k+1) = MEAL_A*MX(:,k)+MEAL_B*BUFF_MEAL_C*MB(:,k);
            Mout(:,k) = MEAL_C*MX(:,k)+MEAL_D*BUFF_MEAL_C*MB(:,k);

            IB(:,k+1) = BUFF_INS_A*IB(:,k)+BUFF_INS_B*6000*INSdif(k)/5; % ts = 5 min; input in pmol / 5 min
            IX(:,k+1) = INS_A*IX(:,k)+INS_B*BUFF_INS_C*IB(:,k);
            Iout(:,k) = INS_C*IX(:,k)+INS_D*BUFF_INS_C*IB(:,k);

            KFout(:,k)     = KF_C*KFstate(:,k)+KF_D*[Iout(2,k);Mout(1,k);G6(k)-Gop];
            KFstate(:,k+1) = KF_A*KFstate(:,k)+KF_B*[Iout(2,k);Mout(1,k);G6(k)-Gop];
            
        end

        XI   = [KFout(1,end);KFout(2,end)-Iout(1,end);Iout(1,end);Mout(2:3,end);Iout(2:4,end)];
        Gest = XI(1)+Gop;
        
        GP30 = CORE_pred_C*CORE_pred_A*XI+Gop;
        GPL = LIGHT_pred_C*(LIGHT_pred_A*XI+LIGHT_pred_B*[-6000*basal/60;0])+Gop;

    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function [Corr,indCorrTimer] = controlIQ_BOP(CF,indCorrTimer,sleep,IOBest,GP30) 
        
        if GP30>=180 && indCorrTimer == 0
            if (sleep==0)
                Corr = min(6,max(0,0.6*((GP30-110)/CF-max(0,IOBest))));
            else
                Corr = 0;
            end
        else
            Corr = 0;
        end
        
        if Corr>0
            indCorrTimer = 1;
        end
        
    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function [du,a,tgt] = controlIQ_BRM(CF,EX,tgt,TDIest,IOBest,Gest,GP30)
    
        T2tgt = 30; % [min]
            
        CFactive = min(max(1500/TDIest,CF),1800/TDIest); % [mg/dl/U]

        INSTarget_predicted = (min(90,GP30-tgt))/CFactive; % [U]

        Rate = max(0,(INSTarget_predicted-IOBest)/T2tgt); % [U/min]

        if Gest>=180
            du = min(Rate,3*TDIest/(48*60)); % [U/min]
        else
            du = min(Rate,2*TDIest/(48*60)); % [U/min]
        end
        
        a = controlIQ_brakes(GP30,EX);
        
    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    function a = controlIQ_brakes(GP30,EX)
        
        Kbrakes = 2.5;
        risk    = 10*(GP30<=112.5)*scaledBG(GP30)^2;
        riskEX  = 10*(GP30<=140)*EXscaledBG(GP30)^2;
        
        if EX>0
            a = 1/(1+Kbrakes*riskEX);
            if GP30<80
                a = 0;
            end
        else
            a = 1/(1+Kbrakes*risk);
            if GP30<70
                a = 0;
            end
        end
        
        function res = EXscaledBG(bg)

            bg(bg<=20)  = 20;
            bg(bg>=600) = 600;

            res = 0.9283*(exp(1.8115*log(log(bg)))-18.0696);
            
        end

        function res = scaledBG(bg)

            bg(bg<=20)  = 20;
            bg(bg>=600) = 600;

            res = 1.509*(exp(1.084*log(log(bg)))-5.381);
            
        end

    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function [usugg,apBDose,apCDose] = controlIQ_FC(basal,EX,GPL,corrBol,du,a)
        
        if a<1
            usugg = a*basal/12; 
            apBDose = a*basal/12;
            apCDose = 0;
        else
            usugg   = (corrBol+5*du+basal/12);
            apBDose = 5*du+basal/12;
            apCDose = corrBol;
        end
                
        Hlo = controlIQ_hypoLight(a,GPL,EX);
        
        if Hlo==2
            usugg = 0; %red hypo light
            apBDose = 0;
            apCDose = 0;
        end
        
    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    function H = controlIQ_hypoLight(a,GPL,EX)

        if EX==1 && GPL<80
            H = 2;
        elseif EX==0 && GPL<70
            H = 2;
        elseif a<1
            H = 1;
        else
            H = 0;
        end
        
    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

end