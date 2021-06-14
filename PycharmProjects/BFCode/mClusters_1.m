function res = mClusters_1(profile)
    c1 = parcluster(profile);
    j1 = createJob(c1);
    t1 = createTask(j1,@rand,1,{8,4});
    submit(j1);
    wait(j1);
    res = fetchOutputs(j1);
    delete(j1);