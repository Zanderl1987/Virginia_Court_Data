function [optimizedBasalLev,optimizedBasalRate,originalBasalRate] = levelBasalProfile(originalBasal,optimizedBasal,basalRes,maxBasalDev,nBreakpoints)

ts = 24*60/length(originalBasal);

origBas = zeros(48,1);
optimBas = zeros(48,1);
for i = 1:48
    origBas(i) = mean(originalBasal((i-1)*30/ts+1:i*30/ts));
    optimBas(i) = max(min(mean(optimizedBasal((i-1)*30/ts+1:i*30/ts)),origBas(i)*(1+maxBasalDev)),origBas(i)*(1-maxBasalDev));
end
origBas = origBas*60/1000;
optimBas = optimBas*60/1000;

maxBasal = max(optimBas*1.1);
minBasal = min(optimBas*.9);
minLevel = basalRes*floor(minBasal/basalRes);
maxLevel = basalRes*ceil(maxBasal/basalRes);
levels = (minLevel:basalRes:maxLevel)';

nTimes = length(origBas);
nLevels = length(levels);

J = zeros(nTimes,nLevels,nBreakpoints);
mu1 = J;
mu2 = J;

% compute cumulative costs for each time and basal level
for t = 1:nTimes
    for b = 1:nLevels
        dum = 0;
        for s = t:nTimes
            cost = abs(optimBas(s)-levels(b))^2;
            dum = dum+cost;
        end
        J(t,b,nBreakpoints) = dum;
    end
end

% assign cumulative costs obtained by minimizing the total cost
for used = nBreakpoints-1:-1:1
    for t = 1:nTimes
        for b = 1:nLevels          
            bestDum = J(t,b,nBreakpoints);
            bestTime = -1;
            bestLevel = -1;
            for s = t:nTimes                
                transitioncost = J(t,b,nBreakpoints)-J(s,b,nBreakpoints);
                for c = 1:nLevels
                    dum = transitioncost + J(s,c,used+1);
                    if dum<bestDum
                        bestDum = dum;
                        bestTime = s;
                        bestLevel = c;
                    end
                end
            end
            J(t,b,used) = bestDum;
            mu1(t,b,used) = bestTime;
            mu2(t,b,used) = bestLevel;
        end
    end
end

% reconstruct profile
appTimes = zeros(nBreakpoints,1);
appIndices = zeros(nBreakpoints,1);
appLevels = zeros(nBreakpoints,1);
appTimes(1) = 1;
[~,appIndices(1)] = min(J(appTimes(1),:,1));
appLevels(1) = levels(appIndices(1));
for i = 2:nBreakpoints
    appTimes(i) = mu1(appTimes(i-1),appIndices(i-1),i-1);
    appIndices(i) = mu2(appTimes(i-1),appIndices(i-1),i-1);
    appLevels(i) = levels(appIndices(i));
end

% construct the corresponding 48-element basal profile
appProfile = [];
for i = 1:nBreakpoints-1
    appProfile = [appProfile; appLevels(i)*ones(appTimes(i+1)-appTimes(i),1)];
end
appProfile = [appProfile; appLevels(nBreakpoints)*ones(nTimes+1-appTimes(nBreakpoints),1)];

% compute breakpoints
breakpoints = [0 appProfile(1)];
currentBasal = appProfile(1);
for i = 2:48
    if appProfile(i)~=currentBasal
        breaktime = 30*(i-1)/60/24;
        breakpoints = [breakpoints; [breaktime appProfile(i)]];
        currentBasal = appProfile(i);
    end
end

% return optimized, leveled profile
nSteps = length(optimizedBasal);
optimizedBasalLev = zeros(nSteps,1);
for i = 1:nSteps
    currTime = ts*(i-1)/60/24;
    optimizedBasalLev(i) = breakpoints(find(breakpoints(:,1)<currTime+1e-6,1,'last'),2)*1000/60;
end

% clean orginial profile
originalBasal2 = [0 originalBasal(1)*60/1000];
for i = 2:nSteps
    if abs(originalBasal(i)*60/1000-originalBasal(i-1)*60/1000)>1e-6
        originalBasal2 = [originalBasal2; ts*(i-1)/60/24 originalBasal(i)*60/1000];
    end
end

% return profiles
originalBasalRate.time = originalBasal2(:,1);
originalBasalRate.value = originalBasal2(:,2);
optimizedBasalRate.time = breakpoints(:,1);
optimizedBasalRate.value = breakpoints(:,2);
