function n = mClusters(profile)
c = parcluster(profile);
n = c.NumWorkers;