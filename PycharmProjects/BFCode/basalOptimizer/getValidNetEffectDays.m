function vDays = getValidNetEffectDays(time,cgm,bolus,meal)

days = unique(floor(time));
nDays = length(days);
vDays = zeros(nDays,1);
for i = 1:nDays
    cday = days(i);
    idxCgm = find(cgm.time>cday-1e-6 & cgm.time<cday+1);
    idxBolus = find(bolus.time>cday-1e-6 & bolus.time<cday+1);
    idxMeal = find(meal.time>cday-1e-6 & meal.time<cday+1);
    % cgm gaps not larger than 3 hours in an regular day
    % at least 2 meals and 2 boluses in a regular day    
    if max(diff([cday; cgm.time(idxCgm); cday+1]))<=3/24 && length(idxCgm)>=288*3/4 ...
        && length(idxBolus)>=2 && length(idxMeal)>=2
        vDays(i) = 1;
    end
end
