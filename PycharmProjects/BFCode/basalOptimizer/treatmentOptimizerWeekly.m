close all
clear
clc

subjNumber = [];

%% fetch result from daily computations
allOptimBas = [];

%% net effect setting
ts = 5;
hoursHead = 6;
hoursTail = 2;

%% compute optimal basal rate profile
idxDay = hoursHead*60/ts+1:(hoursHead+24)*60/ts;
% compute median profile
disp('Compute median BR profile...')
optimBas = median(allOptimBas)';
% level profile
disp('Level median BR profile...')
basRes = 0.01;
maxBasalDev = 0.1;
nBreakpoints = 6;
[optimBasLev,optimizedBasalProfile,originalBasalProfile]= levelBasalProfile(origBas(idxDay),optimBas(idxDay),basRes,maxBasalDev,nBreakpoints);
