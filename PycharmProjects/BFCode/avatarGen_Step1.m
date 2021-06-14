function res = avatarGen_Step1(clusterName,baseV,glucose,meal,insulin,basal,BW,iCond,pivc_x,options_replay,profile_replay)
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Inputs
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % clusterName: Name of the Matlab cluster profile [string]. E.g., 'local'.
    % baseV: Vector of virtual subjects' IDs used as initial conditions. E.g., if baseV = 1:10, the first 10 adult subjects of the simulator are used as initial conditions.
    % glucose: Vector of daily glucose values every 5 min in mg/dL [1x288 double]
    % insulin: Vector of daily insulin rates (basal+bolus) every 5 min in U/min [1x288 double]. Original bolus should be divided by 5 to convert them to rates.
    % basal: Vector of daily basal rates every 5 min in U/min [1x288 double]
    % BW: Subject's body weight in kg [double]
    % iCond: Vector of initial conditions [1x18] -> 1:16 = model's states; 17: dosekempt; 18 = lastMeal. If iCond is empty, the function assumes steady-state conditions given by the initial glucose value
    % pivc_x: Previous x hour ivcSig
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Outputs
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % res: Structure that contains all the results. 
    % Important fields:
    % res.struttura = The well known struttura variable; and res.ivcSig = Vector of the daily ivc signal every 5 min [1x288]
    
    %% General settings

    ts = 5;
    ivc.wFreq = 2*pi*(1/1440);
    ivc.fourierOrder = 12;
    flagSensSet = 1;

    if flagSensSet
        n1 = 8;
    else
        n1 = 33;
    end

    n2 = 33;
    gamma = 1;

    %% Simulator's distribution

    warning('off', 'MATLAB:dispatcher:UnresolvedFunctionHandle');
    load('./sim_distribution.mat')

    sim_dist.vpar.name        = sim_dist.variables(1:n1);
    sim_dist.ppar.name        = sim_dist.variables(n1+1:n2);
    sim_dist.ppar.mean.orig   = mean(sim_dist.data.orig(:,n1+1:n2));
    sim_dist.ppar.mean.transf = mean(sim_dist.data.transf(:,n1+1:n2));

    sim_dist.sigma11 = sim_dist.sigma(1:n1,1:n1);
    sim_dist.sigma12 = sim_dist.sigma(1:n1,n1+1:end);
    sim_dist.sigma21 = sim_dist.sigma(n1+1:end,1:n1);
    sim_dist.sigma22 = sim_dist.sigma(n1+1:end,n1+1:end);

    sim_dist.mu1 = sim_dist.mu(1:n1);
    sim_dist.mu2 = sim_dist.mu(n1+1:end);

    sim_dist.sigmap = sim_dist.sigma11 - sim_dist.sigma12/sim_dist.sigma22*sim_dist.sigma21;

    sim_dist.min1 = sim_dist.min(1:n1);
    sim_dist.max1 = sim_dist.max(1:n1);

    sim_dist.data_var = sim_dist.data.transf(:,1:n1);

    sim_dist.invf1 = sim_dist.invf(1:n1);
    
    %% IVC distribution
    
    ivc_dist.mu         = zeros(2*ivc.fourierOrder+1,1);
    ivc_dist.mu(1)      = 1;
    ivc_dist.sigma      = 2*diag(ones(1,2*ivc.fourierOrder+1));
    ivc_dist.sigma(1,1) = 1;
    ivc_dist.sigma      = ivc_dist.sigma/gamma;
    
    %% Profile

    profile.glucose.values = glucose';
    profile.meal.values    = meal';
    profile.insulin.values = insulin';
    profile.time           = 0:ts:1440-ts;
    profile.weight = BW;
    profile.aBasal = mean(basal);
    profile.basal.values = basal';
    
    Gb = mean(glucose(1:300/ts+1));
    profile.Gb = Gb;
    
    profile.pivc_x = pivc_x;
    
    %% Simulator's distribution
        
    x2 = [sim_dist.ppar.mean.transf';log(profile.weight);profile.Gb];
    sim_dist.mup = sim_dist.mu1 + sim_dist.sigma12/sim_dist.sigma22*(x2-sim_dist.mu2);

    %% Set up simulation conditions
    
    if isempty(iCond)
        sim_set.BGinit = glucose(1); 
        sim_set.model_x0 = [];
        profile.dosekempt = 0;
        profile.lastMeal  = 0;
    else
        sim_set.BGinit = [];
        sim_set.model_x0 = iCond(1:16)';
        profile.dosekempt = iCond(17);
        profile.lastMeal  = iCond(18);
    end
    
    sim_set.u_ini     = 0; % Added bolus in U
    sim_set.init_isc1 = sim_set.u_ini*6000/profile.weight;  % Added bolus in pmol/kg
    sim_set.simToD    = length(profile.glucose.values)-1; % Model run time in ts minutes
    sim_set.ts        = ts;

    %% Struttura - Fixed parameters

    for ii = 1:length(sim_dist.ppar.mean.orig)
       struttura.(sim_dist.ppar.name{ii}) = sim_dist.ppar.mean.orig(ii); 
    end

    struttura.ke1    = 0.0005; %min^-1
    struttura.ke2    = 339; %mg/kg
    struttura.Fsnc   = 1; %mg/kg/min
    struttura.HEb    = 0.6;  %dimensionless
    struttura.f      = 0.9;
    struttura.kGSRs2 = 0;
    
    if ~isempty(iCond)
        struttura.dosekempt = iCond(17);
    else
        struttura.dosekempt = 0;
    end
    
    %% Opt options

    opt.options = optimoptions('fmincon','Display','iter','UseParallel',false,'MaxFunEvals',5000,'Algorithm','interior-point');
        
    % Constraints

    % Defines linear inequalities
    A_ident = zeros(n1);
    b_ident = zeros(n1,1);

    A_ne = zeros(1440/ts,2*ivc.fourierOrder+1);
    b_ne = -.2*ones(1440/ts,1);

    A_ne(:,1) = 1;

    for pp=0:1440/ts-1
        for tt=1:ivc.fourierOrder
            A_ne(pp+1,2*tt)   = cos(tt*ivc.wFreq*ts*pp);
            A_ne(pp+1,2*tt+1) = sin(tt*ivc.wFreq*ts*pp);
        end
    end

    A_ne = -A_ne;

    A = blkdiag(A_ident,A_ne);
    b = [b_ident;b_ne];

    % Defines linear equalities 
    flagCont=1;
    if flagCont==1
        Aeq_ident = zeros(2,n1);
        Aeq_ne = zeros(2,2*ivc.fourierOrder+1);
        Aeq_ne(1,1) = 1;
        Aeq_ne(1,2:2:end) = 1;
        Aeq_ne(2,3:2:end) = ivc.wFreq*ts;
        Aeq = [Aeq_ident Aeq_ne]; 
        beq = [1;0];
    else
        Aeq = [];
        beq = [];
    end
    
    % Defines lower and upper bounds on the design variables
    lb = [sim_dist.min1'-0.001*sim_dist.min1' 0.5 -inf*ones(1,2*ivc.fourierOrder)];
    ub = [sim_dist.max1'+0.001*sim_dist.max1' 1.5 inf*ones(1,2*ivc.fourierOrder)];

    % Defines nonlinear inequalities
    nonlcon = [];
    
    opt.const.A       = A;
    opt.const.b       = b;
    opt.const.Aeq     = Aeq;
    opt.const.beq     = beq;
    opt.const.lb      = lb;
    opt.const.ub      = ub;
    opt.const.nonlcon = nonlcon;
    opt.baseV         = baseV;
    
    %% Opt problem

    tStartW = tic;

    %% Matlab cluster

    nT = 3;
    flagExit = 0;

    while nT>0 && flagExit == 0
        cluster = parcluster(clusterName);

        job = batch(cluster,'avatarGen_Step2',1,{sim_dist,ivc,struttura,profile,sim_set,ivc_dist,opt,options_replay,profile_replay},'Pool',cluster.NumWorkers-1);
        wait(job)
        %resAll = avatarGen_Step2(sim_dist,ivc,struttura,profile,sim_set,ivc_dist,opt,options_replay,profile_replay);

        tEnd = toc(tStartW);
        try
            resAllAux = fetchOutputs(job);
            flagExit = 1;
        catch
            nT=nT-1;
        end
    end

    resAll = resAllAux{1};
    resAll = resAll(~cellfun('isempty',resAll));
    %resAll = resAll(~cellfun('isempty',resAll));
        
    %% Select the minimum

    fvalV = zeros(1,length(resAll));

    for ii=1:length(resAll)
        fvalV(ii) = resAll{ii}.opt.fval;
    end

    [minFval,ind] = min(fvalV);

    %%

    res = resAll{ind};

    modelPar = zeros(1,11+2*ivc.fourierOrder+18+3);

    neCoeff  = res.x(9:end)';
    parIdent = [res.struttura.Gb, res.struttura.Ib, res.struttura.EGPb, res.struttura.Vmx, ...
                res.struttura.Km0, res.struttura.k1, res.struttura.k2, res.struttura.CL, ...
                res.struttura.kp2, res.struttura.kmax];

    modelPar(1,1:10)  = parIdent;
    modelPar(1,11:11+2*ivc.fourierOrder) = neCoeff;  
    modelPar(1,11+2*ivc.fourierOrder+1:11+2*ivc.fourierOrder+18) = [res.struttura.model_xf' res.struttura.dosekempt res.struttura.lastMeal];

    res.modelPar = modelPar;
    res.tEnd = tEnd;
    
end