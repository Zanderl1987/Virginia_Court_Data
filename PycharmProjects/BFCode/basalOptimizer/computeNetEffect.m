function [x0,ne,matNe] = computeNetEffect(data,identRes)

[AA,BBins,BBmeals,BBne] = getNetEffectMatrices(data,identRes.matrices);

%nx = size(AA,2);
ns = length(data.cgm);

% weight on data fit
lambdaFit = eye(ns);

% input regularization
%gamma1 = diag([1/50^2; 1/0.001^2; 1/10^2; 1/10^2; 1/10^2; 1/10^2*ones(nx-5,1)]);
gamma1 = [];
gamma2 = 1000.0;
F = eye(ns-1)-tril(ones(ns-1),-1)+tril(ones(ns-1),-2);
lambdaReg = blkdiag(gamma1,gamma2*(F'*F));

% extract estimates of x0 and net effect
%Mfit = [AA BBne];
Mfit = BBne;
pars = identRes.parameters;
dy = (data.cgm-pars.Gop)-AA*(data.x0-pars.xop)-BBins*(data.u(1:end-1,1)-pars.uop(1))-BBmeals*(reshape(data.u(1:end-1,2:end)',size(BBmeals,2),1));

uest = (Mfit'*lambdaFit*Mfit+lambdaReg)\(Mfit'*lambdaFit)*dy;
%x0 = uest(1:nx,1);
%ne = uest(nx+1:end,1);
x0 = [];
ne = uest;

matNe.AA = AA;
matNe.BBins = BBins;
matNe.BBmeals = BBmeals;
matNe.BBne = BBne;
