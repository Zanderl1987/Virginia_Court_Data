function identRes = identifySogmm(data,day,pars,options)

disp(['Identify SOGMM for extended day #' num2str(day) '...'])

if options.modelIdent
    
    data = collapseMeals(data);
    
    meals = find(data.mealFlag>0);
    nmeals = length(meals);
    
    mealParsIdent = options.mealParsIdent;
    mealParsMultiTh = options.mealParsMultiTh;
    mealParsNotMultiTh = mealParsIdent(~contains(mealParsIdent,mealParsMultiTh));
    nparsMultiTh = length(mealParsMultiTh);
    nparsNotMultiTh = length(mealParsNotMultiTh);
    
    mup = zeros(nparsMultiTh*nmeals+nparsNotMultiTh*(nmeals>0)+1,1);
    cvp = ones(nparsMultiTh*nmeals+nparsNotMultiTh*(nmeals>0)+1,1);
    for i = 1:nmeals
        for j = 1:nparsMultiTh
            mup((i-1)*nparsMultiTh+j) = pars.prior.(mealParsMultiTh{j});
            if strcmp(mealParsMultiTh{j},'f')
                cvp((i-1)*nparsMultiTh+j) = 0.5;
            end
        end
    end
    for i = 1:nparsNotMultiTh
        mup(nparsMultiTh*nmeals+i) = pars.prior.(mealParsNotMultiTh{i});
        if strcmp(mealParsNotMultiTh{i},'f')
            cvp(nparsMultiTh*nmeals+i) = 0.5;
        end
    end
    mup(end) = pars.SIest;
    cvp(end) = 1.5;
    
    pars.cv = 0.125;
    pars.w = ones(size(data.cgm));
    pars.w(1:data.hoursHead*60/data.ts) = flip(exp(-(data.ts:data.ts:data.hoursHead*60)/90));
    pars.w((data.hoursHead+24)*60/data.ts+1:(data.hoursHead+24+data.hoursTail)*60/data.ts) = exp(-(data.ts:data.ts:data.hoursTail*60)/90);
    pars.alfa = 1;
    pars.beta = 1;
    
    data.u = getSogmmInputs(data);
    data.x0 = getSogmmInitCond(pars,nmeals,options);
    [pars.xop,pars.uop] = getSogmmOpPoint(pars,nmeals,options);
    
    pest = lsqnonlin(@(p) sogmmOptimFun(p,mup,cvp,data,pars,options),mup,mup/1000,mup*1000,optimset('Display','iter','MaxFunEval',length(mup)*150));
    identRes = sogmmOptimFun(pest,[],[],data,pars,options);

else
    
    data = collapseMeals(data);
    
    meals = find(data.mealFlag>0);
    nmeals = length(meals);
    
    data.u = getSogmmInputs(data);
    data.x0 = getSogmmInitCond(pars,nmeals,options);
    [pars.xop,pars.uop] = getSogmmOpPoint(pars,nmeals,options);
    
    identRes = sogmmOptimFun([],[],[],data,pars,options);

end
