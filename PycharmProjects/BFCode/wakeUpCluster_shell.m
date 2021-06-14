function res = wakeUpCluster_shell(clusterName)
    
    cluster = parcluster(clusterName);
    nTimes  = 1000;
    job     = batch(cluster,'wakeUpCluster',0,{nTimes},'Pool',cluster.NumWorkers-1);
    wait(job)
    delete(job);
    res = 1;
end

