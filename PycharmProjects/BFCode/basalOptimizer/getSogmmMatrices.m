function matrices = getSogmmMatrices(ts,pars,nmeals,options)

nstates = 5+2*nmeals;
ninputs = 1+nmeals;

Ac = zeros(nstates,nstates);
Ac(1:2,1:5) = [-pars.SG -pars.SI*pars.Gop 0 0 0
        0 -pars.p2 0 0 pars.p2/(pars.VI*pars.BW)];
if strcmp(options.insModel,'catenary')
    Ac(3:5,1:5) = [0 0 -pars.kd 0 0
        0 0 pars.kd -pars.kd 0
        0 0 0 pars.kd -pars.kcl];
elseif strcmp(options.insModel,'triangular')
    Ac(3:5,1:5) = [0 0 -(pars.ka1+pars.kd) 0 0
        0 0 pars.kd -pars.ka2 0
        0 0 pars.ka1 pars.ka2 -pars.kcl];
end
if strcmp(options.mealModel,'catenary')
    for i = 1:nmeals
        Ac(1,5+(i-1)*2+2) = pars.f(i)*pars.k2(i)/(pars.VG*pars.BW);
        Ac(5+(i-1)*2+1,5+(i-1)*2+1) = -pars.k1(i);
        Ac(5+(i-1)*2+2,5+(i-1)*2+(1:2)) = [pars.k1(i) -pars.k2(i)];
    end
elseif strcmp(options.mealModel,'triangular')
    for i = 1:nmeals
        Ac(1,5+(i-1)*2+(1:2)) = pars.f(i)*[pars.k1(i) pars.k3(i)]./(pars.VG*pars.BW);
        Ac(5+(i-1)*2+1,5+(i-1)*2+1) = -(pars.k1(i)+pars.k2(i));
        Ac(5+(i-1)*2+2,5+(i-1)*2+(1:2)) = [pars.k2(i) -pars.k3(i)];
    end
end
Bc = zeros(nstates,ninputs);
Bc(3,1) = 1;
for i = 1:nmeals
    Bc(5+(i-1)*2+1,1+i) = 1;
end
Cc = zeros(1,nstates);
Cc(1) = 1;
Dc = zeros(1,ninputs);

sys = ss(Ac,Bc,Cc,Dc);
sysd = c2d(sys,ts,'zoh');

matrices.Ac = Ac;
matrices.Bc = Bc;
matrices.Cc = Cc;
matrices.Dc = Dc;

matrices.Ad = sysd.A;
matrices.Bd = sysd.B;
matrices.Cd = sysd.C;
matrices.Dd = sysd.D;
