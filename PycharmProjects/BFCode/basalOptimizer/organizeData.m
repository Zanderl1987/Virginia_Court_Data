function data = organizeData(subjData,neOptions)

disp('Organizing data...')

%% SAMPLING TIME
ts = round(neOptions.ts);

%% NET EFFECT SETTING
hoursHead = neOptions.hoursHead;
hoursTail = neOptions.hoursTail;
if hoursHead<6
    hoursHead = 6;
    warning('hoursHead has to be at least 6h: value was reset')
end
if hoursTail<2
    hoursTail = 2;
    warning('hoursTail has to be at least 2h: value was reset')
end

%% FETCH DATA FROM DATABASE
% FETCH THERAPY PROFILES
% store original data
original.basalRate = subjData.basalRate;
original.carbRatio = subjData.carbRatio;
original.corrFactor = subjData.corrFactor;

% FETCH AND CLEAN OTHER DATA
cgmt = subjData.cgm.time;
cgmv = subjData.cgm.value; % [mg/dl]
bolust = subjData.bolus.time;
bolusv = subjData.bolus.value; % [U]
basalt = subjData.basal.time;
basalv = subjData.basal.value; % [U/hr]
mealt = subjData.meal.time;
mealv = subjData.meal.value; % [gr]
% remove NaNs and sort data
cgm = cleanData(cgmt,cgmv,'cgm');
basal = cleanData(basalt,basalv,'basal');
bolus = cleanData(bolust,bolusv,'bolus');
meal = cleanData(mealt,mealv,'meal');
% store original data
original.cgm = cgm;
original.basal = basal;
original.bolus = bolus;
original.meal = meal;

% PREPROCESS DATA
data = preProcessData(original,ts,hoursHead,hoursTail);

%% GATHER SUBJECT'S DEMOGRAPHIC INFO
data.demographics.BW = subjData.BW;
data.demographics.BH = subjData.BH;
data.demographics.age = subjData.age;

%% CALCULATE SIest, Gb, AND Jb
tMins = data.tMins;
tDays = unique(data.tDays);
vDays = data.vDays;
idx = ismember(floor(tMins),tDays(vDays==1));
idx2 = ismember(floor(tMins),tDays(vDays==1)) & hour(tMins)>=1 & hour(tMins)<6;
data.parameters.TDIest = (1440/1000)*(sum(data.bolus(idx))+sum(data.basal(idx)))/length(find(idx));
data.parameters.TDBest = (1440/1000)*sum(data.basal(idx))/length(find(idx));
data.parameters.SIest = max(exp(-6.4417-0.063546*data.parameters.TDIest+0.057944*data.parameters.TDBest),2.5e-04);
data.parameters.Gb = mean(data.cgm(idx2));
data.parameters.Jb = mean(data.basalRate(idx));
data.parameters.hoursHead = hoursHead;
data.parameters.hoursTail = hoursTail;
data.parameters.ts = ts;

