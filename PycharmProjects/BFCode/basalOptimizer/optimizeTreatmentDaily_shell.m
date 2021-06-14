function res = optimizeTreatmentDaily_shell(clusterName,subjData)

    cluster = parcluster(clusterName);
    %job = batch(cluster,'optimizeTreatmentDaily',1,{subjData},'Pool',1);
    %wait(job)
    %res = fetchOutputs(job)
    res = optimizeTreatmentDaily(subjData);