function data = cleanData(time,value,dataType)

% remove NaNs and zeros
if strcmp(dataType,'basal')
    data.time = time(time>0 & ~isnan(value));
    data.value = value(time>0 & ~isnan(value));
else
    data.time = time(time>0 & value>0);
    data.value = value(time>0 & value>0);
end
% remove duplicates and sort data
if strcmp(dataType,'cgm') || strcmp(dataType,'basal')
    [data.time,ind] = unique(data.time);
    data.value = data.value(ind);
else
    [data.time,ind] = sort(data.time);
    data.value = data.value(ind);
end
