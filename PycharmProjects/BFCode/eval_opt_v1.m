function fval = eval_opt_v1(x,struttura,profile,sim_set,sim_dist,ivc_dist,ivc,options_replay,profile_replay)
    
    %% Sampling time
    
    h = sim_set.ts;
    
    %% Design variables
    
    x_ident = x(1:length(sim_dist.mu1));
    x_ne    = x(length(sim_dist.mu1)+1:end);
        
    %% Transform x_ident to original space
        
    for ii = 1:length(sim_dist.invf1)
       struttura.(sim_dist.vpar.name{ii}) = sim_dist.invf1{ii}(x_ident(ii)); 
    end
    
    %% Define parameters that depend on design variables
    
    struttura.Gb  = profile.Gb;
    struttura.BW  = profile.weight;
    struttura.Gpb = struttura.Gb*struttura.Vg;
    struttura.r2  = log(struttura.Gb).^struttura.r1;
    struttura.Gth = struttura.Gb;
    
    if struttura.Gpb<=struttura.ke2
        struttura.Gtb = (struttura.Fsnc-struttura.EGPb+struttura.k1*struttura.Gpb)/struttura.k2; %mg/kg
        struttura.Vm0 = (struttura.EGPb-struttura.Fsnc)*(struttura.Km0+struttura.Gtb)/struttura.Gtb; %mg/kg/min
    else
        struttura.Gtb = ((struttura.Fsnc-struttura.EGPb+struttura.ke1*(struttura.Gpb-struttura.ke2))/struttura.Vg+struttura.k1*struttura.Gpb)/struttura.k2;%mg/kg
        struttura.Vm0 = (struttura.EGPb-struttura.Fsnc-struttura.ke1*(struttura.Gpb-struttura.ke2))*(struttura.Km0+struttura.Gtb)/struttura.Gtb; %mg/kg/min
    end

    struttura.m2  = 3/5*struttura.CL/struttura.HEb/(struttura.Vi*struttura.BW);  %min^-1
    struttura.m4  = 2/5*struttura.CL/(struttura.Vi*struttura.BW);  %min^-1
    struttura.m30 = struttura.HEb*struttura.m1/(1-struttura.HEb); %min^-1

    %% Update variables than depend on Ib

    Ains = [-(struttura.ka1+struttura.kd) 0 0 0; 
            struttura.kd -struttura.ka2 0 0; 
            struttura.ka1 struttura.ka2 -(struttura.m2+struttura.m4) struttura.m1; 
            0 0 struttura.m2 -(struttura.m1+struttura.m30)];
    Bins = [1 0 0 0]';
    Cins = [0 0 1/struttura.Vi 0];

    struttura.Ib  = -Cins*(Ains\Bins)*(profile.aBasal*6000/struttura.BW);
    struttura.Ipb = struttura.Ib*struttura.Vi;
    struttura.Ilb = struttura.Ib*struttura.Vi*struttura.m2/(struttura.m1+struttura.m30);
    struttura.Ith = struttura.Ib;
    struttura.kp1 = struttura.EGPb+struttura.kp2*struttura.Gb*struttura.Vg+struttura.kp3*struttura.Ib; %mg/kg/min
    
    struttura.Ains = Ains;
    struttura.Bins = Bins;
    struttura.Cins = Cins;
    
    %% Simulation's initial conditions
    
    if isempty(sim_set.model_x0)
        struttura = mt_sub_t1_ss_cf(struttura,sim_set.BGinit,0); % Steady-state considering new parameters    
        ins_x0    = [struttura.u2ss/(struttura.kd+struttura.ka1)+sim_set.init_isc1 struttura.u2ss*struttura.kd/(struttura.ka2*(struttura.kd+struttura.ka1))];
        model_x0  = [zeros(3,1);ins_x0';struttura.x0'];
    else
        model_x0 = sim_set.model_x0;
    end
      
    %% IVC signal
    
    ivcSig = x_ne(1)*ones(1,length(profile.insulin.values));
    
    for jj=1:length(profile.insulin.values)
        for ii=1:ivc.fourierOrder
            ivcSig(jj) = ivcSig(jj) + x_ne(2*ii)*cos((h*(jj-1))*ii*ivc.wFreq)+ ...
                        x_ne(2*ii+1)*sin((h*(jj-1))*ii*ivc.wFreq);
        end
    end
    
    %% Numerical integration
    
    sim = run_nintegration(profile,struttura,ivcSig,h,model_x0,options_replay,profile_replay);
    
    simGlucose = sim.simGlucose;
    
    %% Cost function
    
    fval = sum(((simGlucose'-profile.glucose.values)./(profile.glucose.values*0.125)).^2) + ...
           (x_ident-sim_dist.mup)'/sim_dist.sigmap*(x_ident-sim_dist.mup) + ...
           (x_ne-ivc_dist.mu)'/ivc_dist.sigma*(x_ne-ivc_dist.mu);
    
end