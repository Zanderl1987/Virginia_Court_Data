function optBas = optimizeBasalRate(data,pars,netEff,matNetEff)

AA = matNetEff.AA;
BBins = matNetEff.BBins;
BBmeals = matNetEff.BBmeals;
BBne = matNetEff.BBne;

ns = length(data.cgm);

% weight on data fit
lambdaFit = eye(ns);

% input regularization
gamma = 1000.0;
F = eye(ns-1)-tril(ones(ns-1),-1)+tril(ones(ns-1),-2);
lambdaReg = gamma*(F'*F);

% extract estimates of optimal basal rate
Mfit = BBins;
dy = (pars.Gtgt*ones(size(data.cgm))-pars.Gop)-AA*(data.x0-pars.xop)-BBmeals*(reshape(data.u(1:end-1,2:end)',size(BBmeals,2),1))-BBne*netEff;

uest = (Mfit'*lambdaFit*Mfit+lambdaReg)\(Mfit'*lambdaFit)*dy;
optBas = uest+pars.uop(1);
