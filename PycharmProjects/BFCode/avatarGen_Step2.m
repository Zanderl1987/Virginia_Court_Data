function res = avatarGen_Step2(sim_dist,ivc,struttura,profile,sim_set,ivc_dist,opt,options_replay,profile_replay)

    %parfor (base=opt.baseV)
    parfor ii=1:numel(opt.baseV)
        base = opt.baseV(ii)

        % Initial condition
        
        x0_ident = sim_dist.data_var(base,:)';
        x0_ne    = [1;zeros(2*ivc.fourierOrder,1)];
        x0       = [x0_ident;x0_ne];
        
        % f
        f = @(x)eval_opt_v1(x,struttura,profile,sim_set,sim_dist,ivc_dist,ivc,options_replay,profile_replay);

        [x,fval,exitflag,output,lambda,grad,hessian] = fmincon(f, x0, opt.const.A, opt.const.b, opt.const.Aeq, opt.const.beq, opt.const.lb, opt.const.ub, opt.const.nonlcon, opt.options);

        [score,wRes,simGlucose,ivcSig,ivcSigF,strutturaF] = eval_opt_res_v1(x,struttura,profile,sim_set,sim_dist,ivc_dist,ivc,options_replay,profile_replay);

        x_ident = x(1:length(x0_ident));
        x_ivc   = x(length(x0_ident)+1:end);

        devX_ident = (x_ident-sim_dist.mup)'/sim_dist.sigmap*(x_ident-sim_dist.mup);
        devX_ivc   = (x_ivc-ivc_dist.mu)'/ivc_dist.sigma*(x_ivc-ivc_dist.mu);

        res{ii} = struct();

        res{ii}.x0         = x0;
        res{ii}.x          = x;
        res{ii}.opt.fval   = score;
        res{ii}.opt.exitF  = exitflag;
        res{ii}.opt.output = output;
        res{ii}.opt.lambda = lambda;
        res{ii}.opt.grad   = grad;
        res{ii}.opt.hess   = hessian;
        res{ii}.wRes       = wRes;
        res{ii}.simGlucose = simGlucose;
        res{ii}.base       = base;
        res{ii}.cons.A     = opt.const.A;
        res{ii}.cons.b     = opt.const.b;
        res{ii}.cons.Aeq   = opt.const.Aeq;
        res{ii}.cons.beq   = opt.const.beq;
        res{ii}.cons.lb    = opt.const.lb;
        res{ii}.cons.ub    = opt.const.ub;
        res{ii}.cons.nonl  = opt.const.nonlcon;
        res{ii}.options    = opt.options;
        res{ii}.ivc        = ivc;
        res{ii}.ivcSig     = ivcSig;
        res{ii}.ivcSigF    = ivcSigF;
        res{ii}.profile    = profile;
        res{ii}.sim_set    = sim_set;
        res{ii}.sim_dist   = sim_dist;
        res{ii}.devX_ident = devX_ident;
        res{ii}.devX_ne    = devX_ivc;
        res{ii}.struttura  = strutturaF;
                
    end
    
end