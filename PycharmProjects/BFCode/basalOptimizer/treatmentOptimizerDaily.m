close all
clear
clc

subjNumber = [];

%% net effect setting
neOptions.ts = 5;
neOptions.hoursHead = 6;
neOptions.hoursTail = 2;

%% organize data and parse into extended days
allData = organizeData(subjNumber,neOptions);
allDataEx = parseExtendedDays(allData.data,allData.parameters.ts,allData.parameters.hoursHead,allData.parameters.hoursTail);
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
%disp(' ')
nDays = size(allDataEx.cgmExtended,2);
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
