function [tMins,nSteps,cgm,basal,bolus,meal] = createUnivTimeVec(tStart,tEnd,ts,original)

% create time vector
tStart = datenum(dateshift(datetime(datevec(tStart)),'start','minute'));
tEnd = datenum(dateshift(datetime(datevec(tEnd)),'start','minute'));
tLength = round((tEnd-tStart)*24*60);
if mod(tLength,ts)==0
    nSteps = tLength/ts;
else
    nSteps = floor(tLength/ts)+1;
end
tMins = zeros(nSteps,1);
tMins(1) = tStart;
for i = 2:nSteps
    tMins(i) = tMins(i-1)+ts/60/24;
end
tMins = round(tMins*24*60)/(24*60);

% select data between tStart and tEnd
cgmt = original.cgm.time(original.cgm.time>tStart-1e-6 & original.cgm.time<tEnd);
cgmv = original.cgm.value(original.cgm.time>tStart-1e-6 & original.cgm.time<tEnd);
basalt = original.basal.time(original.basal.time>tStart-1e-6 & original.basal.time<tEnd);
basalv = original.basal.value(original.basal.time>tStart-1e-6 & original.basal.time<tEnd);
bolust = original.bolus.time(original.bolus.time>tStart-1e-6 & original.bolus.time<tEnd);
bolusv = original.bolus.value(original.bolus.time>tStart-1e-6 & original.bolus.time<tEnd);
mealt = original.meal.time(original.meal.time>tStart-1e-6 & original.meal.time<tEnd);
mealv = original.meal.value(original.meal.time>tStart-1e-6 & original.meal.time<tEnd);

% store data
cgm.time = cgmt;
cgm.value = cgmv;
basal.time = basalt;
basal.value = basalv;
bolus.time = bolust;
bolus.value = bolusv;
meal.time = mealt;
meal.value = mealv;
