function [xop,uop] = getSogmmOpPoint(pars,nmeals,options)

uop = zeros(1,nmeals+1);
uop(1) = pars.Jop;
if strcmp(options.insModel,'catenary')
    xop = [pars.Gop; 0; pars.Jop/pars.kd; pars.Jop/pars.kd; pars.Jop/pars.kcl; zeros(nmeals*2,1)];
elseif strcmp(options.insModel,'triangular')
    xop = [pars.Gop; 0; pars.Jop/(pars.kd+pars.ka1); (pars.kd/pars.ka2)*pars.Jop/(pars.kd+pars.ka1); pars.Jop/pars.kcl; zeros(nmeals*2,1)];
end
