function outputData = parseExtendedDays(inputData,ts,hoursHead,hoursTail)

disp('Parsing extended days...')

allData = inputData;

% select valid days for the net effect computation
validDays = allData.vDays;
startDay = allData.tDays(1);
nValidDays = sum(validDays);
indDay = zeros(nValidDays,24*60/ts);
ind2 = 1;
for i = 1:length(validDays)
    if validDays(i)==1
        currDay = startDay+i-1;
        ind1 = find(allData.tMins>currDay-1e-6,1,'first');
        if allData.tMins(ind1+24*60/ts)-(currDay+1)>1e-6
            error('wrong extended day timestamp')
        end
        indDay(ind2,:) = (ind1:ind1+24*60/ts-1);
        ind2 = ind2+1;
    end
end

% add buffer and tail
minutesBefore = hoursHead*60/ts;
minutesAfter = hoursTail*60/ts;

% create extended days
indExtendedDay = [];
for i = 1:nValidDays
    indExtendedDay = [indExtendedDay; [indDay(i,1)-minutesBefore:indDay(i,1)-1 indDay(i,:) indDay(i,end)+1:indDay(i,end)+minutesAfter]];
end

% organize data
allData.cgmExtended = [];
allData.basalExtended = [];
allData.bolusExtended = [];
allData.mealExtended = [];
allData.basalRateExtended = [];
allData.carbRatioExtended = [];
allData.corrFactorExtended = [];
allData.tMinsExtended = [];
allData.tDaysExtended = [];

for i = 1:nValidDays
    % extract
    cgmExtended = allData.cgm(indExtendedDay(i,:));
    basalExtended = allData.basal(indExtendedDay(i,:));
    bolusExtended = allData.bolus(indExtendedDay(i,:));
    mealExtended = allData.meal(indExtendedDay(i,:));
    basalRateExtended = allData.basalRate(indExtendedDay(i,:));
    carbRatioExtended = allData.carbRatio(indExtendedDay(i,:));
    corrFactorExtended = allData.corrFactor(indExtendedDay(i,:));
    tMinsExtended = allData.tMins(indExtendedDay(i,:));
    tDaysExtended = allData.tDays(indExtendedDay(i,:));
    
    % add to the record
    allData.cgmExtended = [allData.cgmExtended cgmExtended];
    allData.basalExtended = [allData.basalExtended basalExtended];
    allData.bolusExtended = [allData.bolusExtended bolusExtended];
    allData.mealExtended = [allData.mealExtended mealExtended];
    allData.basalRateExtended = [allData.basalRateExtended basalRateExtended];
    allData.carbRatioExtended = [allData.carbRatioExtended carbRatioExtended];
    allData.corrFactorExtended = [allData.corrFactorExtended corrFactorExtended];
    allData.tMinsExtended = [allData.tMinsExtended tMinsExtended];
    allData.tDaysExtended = [allData.tDaysExtended tDaysExtended];
end

outputData = allData;
