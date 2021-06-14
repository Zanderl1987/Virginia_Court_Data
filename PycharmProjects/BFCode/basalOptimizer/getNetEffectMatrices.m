function [AA,BBins,BBmeals,BBne] = getNetEffectMatrices(data,mat)

% add net effect input
mat.Bc = [mat.Bc zeros(size(mat.Bc(:,1)))];
mat.Bc(1,end) = 1;
mat.Dc = [mat.Dc 0];
sys = ss(mat.Ac,mat.Bc,mat.Cc,mat.Dc);
sysd = c2d(sys,data.ts,'zoh');
mat.Bd = sysd.B;
mat.Dd = sysd.D;
A = mat.Ad;
Bins = mat.Bd(:,1);
Bmeals = mat.Bd(:,2:end-1);
Bne = mat.Bd(:,end);
C = mat.Cd;

% build matrices
nx = size(A,1);
nu = size(Bmeals,2);
ny = 1;
ns = length(data.cgm);

AA = zeros(ny*ns,nx);
BBins = zeros(ny*ns,1*(ns-1));
BBmeals = zeros(ny*ns,nu*(ns-1));
BBne = zeros(ny*ns,1*(ns-1));
for i = 1:ns
    AA((i-1)*ny+(1:ny),:) = C*A^(i-1);
    if i>1
        BBins((i-1)*ny+(1:ny),1:(i-1)*1) = [C*A^(i-2)*Bins BBins((i-2)*ny+(1:ny),1:(i-2)*1)];
        BBmeals((i-1)*ny+(1:ny),1:(i-1)*nu) = [C*A^(i-2)*Bmeals BBmeals((i-2)*ny+(1:ny),1:(i-2)*nu)];
        BBne((i-1)*ny+(1:ny),1:(i-1)*1) = [C*A^(i-2)*Bne BBne((i-2)*ny+(1:ny),1:(i-2)*1)];
    end
end
