function wakeUpCluster(nTimes)
    ltiSys = tf(1,conv([1 2 1],[1 2 1]));
    t = 0:0.001:1000;
    u = ones(size(t));
    parfor ii=1:nTimes
        y{ii} = lsim(ltiSys,u,t);
    end

end