function x0 = getSogmmInitCond(pars,nmeals,options)

if strcmp(options.insModel,'catenary')
    x0 = [pars.Gop; 0; pars.Jop/pars.kd; pars.Jop/pars.kd; pars.Jop/pars.kcl; zeros(nmeals*2,1)];
elseif strcmp(options.insModel,'triangular')
    x0 = [pars.Gop; 0; pars.Jop/(pars.kd+pars.ka1); (pars.kd/pars.ka2)*pars.Jop/(pars.kd+pars.ka1); pars.Jop/pars.kcl; zeros(nmeals*2,1)];
end
