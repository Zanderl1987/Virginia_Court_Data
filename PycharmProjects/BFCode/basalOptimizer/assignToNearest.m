function yq = assignToNearest(t,y,tq)

yq = zeros(size(tq));

for i = 1:length(t)
    [mint,ind] = min(abs(tq-t(i)));
    
    if isempty(ind)
        error('nearest position not found.')
    else
        yq(ind) = yq(ind)+y(i);
        if mint>5/60/24-1e-6
            error('nearest position farther than 5 minutes.')
        end
    end
end
