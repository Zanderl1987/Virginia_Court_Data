function fun = sogmmOptimFun(p,mup,cvp,data,pars,options)

flag.optimization = 1;
if isempty(p)
    mup = [];
    cvp = [];
end
if isempty(mup) && isempty(cvp)
    flag.optimization = 0;
end

meals = find(data.mealFlag>0);
nmeals = length(meals);

mealParsIdent = options.mealParsIdent;
mealParsMultiTh = options.mealParsMultiTh;
mealParsNotMultiTh = mealParsIdent(~contains(mealParsIdent,mealParsMultiTh));
mealParsNotIdent = pars.allMealPars(~contains(pars.allMealPars,mealParsIdent));

if ~isempty(p)
    nparsMultiTh = length(mealParsMultiTh);
    for i = 1:nparsMultiTh
        pars.(mealParsMultiTh{i})(1:nmeals) = p((0:nmeals-1)*nparsMultiTh+i);
    end
    for i = 1:length(mealParsNotMultiTh)
        pars.(mealParsNotMultiTh{i})(1:nmeals) = p(nparsMultiTh*nmeals+i);
    end
    pars.SI = p(end);
    for i = 1:length(mealParsNotIdent)
        pars.(mealParsNotIdent{i})(1:nmeals) = pars.prior.(mealParsNotIdent{i});
    end
else
    for i = 1:length(pars.allMealPars)
        pars.(pars.allMealPars{i})(1:nmeals) = pars.prior.(pars.allMealPars{i});
    end
    pars.SI = pars.SIest;
end

mat = getSogmmMatrices(data.ts,pars,nmeals,options);

X = data.x0-pars.xop;
x = zeros(length(pars.xop),length(data.cgm));
y = zeros(size(data.cgm));
for i = 1:length(y)
    x(:,i) = X;
    y(i,1) = mat.Cd*X+mat.Dd*(data.u(i,:)-pars.uop)';
    X = mat.Ad*X+mat.Bd*(data.u(i,:)-pars.uop)';
end
x = x'+repmat(pars.xop',length(data.cgm),1);
y = y+pars.Gop;

if flag.optimization
    fun = [(pars.alfa.*pars.w).*(y-data.cgm)./(pars.cv.*data.cgm)
        pars.beta.*(p-mup)./(cvp.*mup)];
else
    fun.data = data;
    fun.glucose = y;
    fun.states = x;
    fun.parameters = pars;
    fun.matrices = mat;
    fun.nmeals = nmeals;
end
