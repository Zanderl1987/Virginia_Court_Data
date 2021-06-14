function yq = assignToNext(t,y,tq)

yq = zeros(size(tq));

for i = 1:length(tq)
    ind = find(t<tq(i)+1e-6,1,'last');
    
    if isempty(ind)
        error('previous position not found.')
    else
        yq(i) = y(ind);
        if tq(i)-t(ind)>1-1e-6
            %disp('previous position farther than 24 hours.')
        end
    end
end
