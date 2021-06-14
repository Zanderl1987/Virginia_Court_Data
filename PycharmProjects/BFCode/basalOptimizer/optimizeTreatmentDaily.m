function optimBas = optimizeTreatmentDaily(subjData)

% subjData is a structure containing the following fields:
% basalRate.time: mins since midnight of breakpoint
% basalRate.value: values at breakpoints [U/hr]
% carbRatio.time: mins since midnight of breakpoint
% carbRatio.value: values at breakpoints [gr/U]
% corrFactor.time: mins since midnight of breakpoint
% corrFactor.value: values at breakpoints [mg/dl/U]
% cgm.time: datenums of CGM data
% cgm.value: CGM values [mg/dl]
% bolus.time: datenums of bolus data
% bolus.value: bolus amounts [U]
% basal.time: datenums of basal rate breakpoints;
% basal.value: basal rate values [U/hr]
% meal.time: datenums of meal data
% meal.value: meal amounts [g]
% BW, BH, age

cgmTime_datenum = datenum(datetime(subjData.cgm.time, 'ConvertFrom', 'posixtime','TimeZone',subjData.tz)); 
subjData.cgm.time = cgmTime_datenum';
subjData.cgm.value = subjData.cgm.value';

bolusTime_datenum = datenum(datetime(subjData.bolus.time, 'ConvertFrom', 'posixtime','TimeZone',subjData.tz)); 
subjData.bolus.time = bolusTime_datenum';
subjData.bolus.value = subjData.bolus.value';

basalTime_datenum = datenum(datetime(subjData.basal.time, 'ConvertFrom', 'posixtime','TimeZone',subjData.tz));
subjData.basal.time = basalTime_datenum';
subjData.basal.value = subjData.basal.value';

mealTime_datenum = datenum(datetime(subjData.meal.time, 'ConvertFrom', 'posixtime','TimeZone',subjData.tz)); 
subjData.meal.time = mealTime_datenum';
subjData.meal.value = subjData.meal.value';

%% net effect setting
neOptions.ts = 5;
neOptions.hoursHead = 6;
neOptions.hoursTail = 2;

%% organize data and parse into extended days
allData = organizeData(subjData,neOptions);
allDataEx = parseExtendedDays(allData,allData.parameters.ts,allData.parameters.hoursHead,allData.parameters.hoursTail);
fields = [fieldnames(allData.demographics); fieldnames(allData.parameters)];
for i = 1:length(fields)
    if isfield(allData.demographics,fields{i})
        allDataEx.(fields{i}) = allData.demographics.(fields{i});
    elseif isfield(allData.parameters,fields{i})
        allDataEx.(fields{i}) = allData.parameters.(fields{i});
    end
end

%% set identification options
options.insModel = 'triangular'; %catenary
options.mealModel = 'triangular'; %catenary
options.mealParsIdent = {'k1','k2','k3','f'};
options.mealParsMultiTh = {'k1','k2','k3','f'};
options.modelIdent = ~isempty(options.mealParsIdent);
options.multiThread = options.modelIdent*~isempty(options.mealParsMultiTh);

% run checks
if strcmp(options.mealModel,'catenary') && (contains('k3',options.mealParsIdent) || contains('k3',options.mealParsMultiTh))
    error('parameter k3 is not defined for catenary meal model')
end
if ~min(contains(options.mealParsMultiTh,options.mealParsIdent))
    error('mealParsMultiTh must be a subset of mealParsIdent')
end

%% get model parameters
pars = getSogmmPars(allData.demographics,options);
pars.BW = allData.demographics.BW;
pars.Gop = allData.parameters.Gb;
pars.Jop = allData.parameters.Jb;
pars.SIest = allData.parameters.SIest;
pars.Gtgt = 110;

%% identify model and compute net effect
nDays = size(allDataEx.cgmExtended,2);

if nDays>=1
    for i = 1:nDays
        % extract extended day
        data = extractExtendedDay(allDataEx,i);    
        % identify sogmm for current extended day
        identRes = identifySogmm(data,i,pars,options);
        data = identRes.data;
        pest = identRes.parameters;
        % compute net effect and replay with orginal data
        [~,netEff,matNetEff] = computeNetEffect(data,identRes);
        % optimize basal rate
        data.u(:,2:end) = 0;
        optimBas = optimizeBasalRate(data,pest,netEff,matNetEff);
        optimBas = max(optimBas,0);
    end
else
    optimBas = [];
end
