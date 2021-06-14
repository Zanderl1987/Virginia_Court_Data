function pars = getSogmmPars(data,options)

% meal model parameters
pars.k1 = 0.01;
pars.k2 = 0.01;
if strcmp(options.mealModel,'triangular')
    pars.k3 = 0.01;
end

% Dalla Man et al., JDST, 2007
pars.kd = 0.0164;
pars.ka1 = 0.0018;
pars.ka2 = 0.0182;

% estimated from simulation
pars.p2 = 0.0449; % [avg 0.0517]
pars.SG = 0.0046; % [avg 0.0051]
pars.VG = 1.8366; % [avg 1.8377]
pars.f = 0.9;

% Campioni et al., AJPEM, 2009
if isfield(data,'BH') && isfield(data,'age')
    BSA = 0.007184*data.BW^0.425*data.BH^0.725;
    pars.VI = exp(0.814+0.754*BSA-0.000908*data.age);
    pars.CL = exp(-0.0402+0.372*BSA-0.00313*data.age);
else
    pars.VI = 9.31;
    pars.CL = 1.7;
end
pars.kcl = pars.CL/pars.VI;
pars.VI = pars.VI/data.BW;

% set population prior on meal parameters
if strcmp(options.mealModel,'catenary')
    pars.allMealPars = {'k1','k2','f'};
elseif strcmp(options.mealModel,'triangular')
    pars.allMealPars = {'k1','k2','k3','f'};
end
for i = 1:length(pars.allMealPars)
    pars.prior.(pars.allMealPars{i}) = pars.(pars.allMealPars{i});
end
