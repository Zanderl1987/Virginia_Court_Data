function data = preProcessData(original,ts,hoursHead,hoursTail)

% CREATE UNIVERSAL TIME VECTOR
tStart = floor(original.cgm.time(1))+1-hoursHead/24;
tEnd = ceil(original.cgm.time(end))-1+hoursTail/24;
[tMins,nSteps,cgm,basal,bolus,meal] = createUnivTimeVec(tStart,tEnd,ts,original);
% store data
original.cgm = cgm;
original.basal = basal;
original.bolus = bolus;
original.meal = meal;

% DETERMINE NUMBER OF VALID NE DAYS
vDays = getValidNetEffectDays(tMins,original.cgm,original.bolus,original.meal);

disp('check')
disp(vDays)

if vDays(1)==1 || vDays(end)==1
    error('wrong valid NE days assessment')
end

% ALIGN DATA TO UNIVERSAL TIME VECTOR
% organize profiles
basalRate = zeros(nSteps,1);
carbRatio = zeros(nSteps,1);
corrFactor = zeros(nSteps,1);
for i = 1:nSteps
    currTime = hour(tMins(i))/24+minute(tMins(i))/60/24;
    basalRate(i) = original.basalRate.value(find(original.basalRate.time<currTime+1e-6,1,'last'))*1000/60;
    carbRatio(i) = original.carbRatio.value(find(original.carbRatio.time<currTime+1e-6,1,'last'));
    corrFactor(i) = original.corrFactor.value(find(original.corrFactor.time<currTime+1e-6,1,'last'));
end
% organize CGM data
cgm = zeros(nSteps,1);
iStart = find(tMins>original.cgm.time(1)-1e-6,1,'first')-1;
iEnd = find(tMins<original.cgm.time(end)+1e-6,1,'last')+1;
if iStart>=1
    cgm(1:iStart) = original.cgm.value(1);
end
if iEnd<=nSteps
    cgm(iEnd:end) = original.cgm.value(end);
end
cgm(iStart+1:iEnd-1) = interp1(original.cgm.time,original.cgm.value,tMins(iStart+1:iEnd-1),'linear','extrap');
% organize basal data
basal = zeros(nSteps,1);
iStart = find(tMins>original.basal.time(1)-1e-6,1,'first');
iEnd = find(tMins<original.basal.time(end)+1e-6,1,'last');
basal(iStart:iEnd) = assignToNext(original.basal.time,original.basal.value,tMins(iStart:iEnd))*1000/60;
for i = [1:iStart-1,iEnd+1:nSteps]
    basal(i) = basalRate(i);
end
% organize bolus data
bolus = zeros(nSteps,1);
iStart = max(1,find(tMins>original.bolus.time(1)-1e-6,1,'first')-1);
iEnd = min(find(tMins<original.bolus.time(end)+1e-6,1,'last')+1,nSteps);
for i = iStart+1:iEnd
    bolus(i) = sum(original.bolus.value(original.bolus.time>tMins(i-1) & original.bolus.time<tMins(i)+1e-6));
end
if iStart==1 && abs(tMins(1)-original.bolus.time(1))<1e-6
    bolus(1) = original.bolus.value(1);
end
bolus = bolus*1000/ts;
bolus1 = assignToNearest(original.bolus.time,original.bolus.value,tMins)*1000/ts;
if abs(sum(bolus)-sum(bolus1))>1e-6
    disp('possible python-matlab mismatch if assignToNearest is used for boluses')
end

% organize meal data
meal = zeros(nSteps,1);
iStart = max(1,find(tMins>original.meal.time(1)-1e-6,1,'first')-1);
iEnd = min(find(tMins<original.meal.time(end)+1e-6,1,'last')+1,nSteps);
for i = iStart+1:iEnd
    meal(i) = sum(original.meal.value(original.meal.time>tMins(i-1) & original.meal.time<tMins(i)+1e-6));
end
if iStart==1 && abs(tMins(1)-original.meal.time(1))<1e-6
    meal(1) = original.meal.value(1);
end
meal = meal*1000/ts;
meal1 = assignToNearest(original.meal.time,original.meal.value,tMins)*1000/ts;
if abs(sum(meal)-sum(meal1))>1e-6
    disp('possible python-matlab mismatch if assignToNearest is used for meals')
end

% STORE AND RETURN FINAL DATA
data.vDays = vDays;
data.tMins = tMins;
data.tDays = floor(tMins);
data.cgm = cgm;
data.basal = basal; % [mU/min]
data.bolus = bolus; % [mU/min]
data.meal = meal; % [mg/min]
data.basalRate = basalRate; % [mU/min]
data.carbRatio = carbRatio; % [gr/U]
data.corrFactor = corrFactor; % [mg/dl/U]
