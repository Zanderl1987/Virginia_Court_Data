function data = extractExtendedDay(allData,day)

fields = fieldnames(allData);
for i = 1:length(fields)
    if contains(fields{i},'Extended') 
        idx = find(fields{i}=='E');
        label = fields{i}(1:idx-1);
        data.(label) = allData.(fields{i})(:,day);
    else
        if isscalar(allData.(fields{i})) && isnumeric(allData.(fields{i}))
            data.(fields{i}) = allData.(fields{i});
        end
    end
end
