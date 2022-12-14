import os
import sys
sys.path.append('/home/miyawaki/scripts/common')
import pickle
import numpy as np
import xarray as xr
from tqdm import tqdm
from regions import rinfo

# this script creates a histogram of daily temperature for a given year
# at each gridir point. 

varn='t2m'
lre=['swus','sea']
# lse = ['jja'] # season (ann, djf, mam, jja, son)
lse = ['ann','djf','mam','jja','son'] # season (ann, djf, mam, jja, son)

y0=1950 # first year
y1=2020 # last year+1

lyr=[str(y) for y in np.arange(y0,y1+1)]

pc = [1e-3,1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,82,85,87,90,92,95,97,99] # percentiles to compute

for re in lre:
    # file where selected region is provided
    rloc,rlat,rlon=rinfo(re)

    for se in lse:
        idir = '/project/mojave/observations/ERA5_daily/T2m'
        odir = '/project/amp/miyawaki/data/p004/hist_hotdays/era5/%s/%s' % (se,varn)

        if not os.path.exists(odir):
            os.makedirs(odir)

        for yr in lyr:
            fn = '%s/t2m_%s.nc' % (idir,yr)
            ds = xr.open_dataset(fn)
            t2m = ds['t2m'].load()
            if se != 'ann':
                t2m=t2m.sel(time=t2m['time.season']==se.upper())
            gr = {}
            gr['lon'] = ds['lon']
            gr['lat'] = ds['lat']

            rt2m=np.empty([t2m.shape[0],len(rloc[0])])
            # loop through time to aggregate all data in selected region
            for it in tqdm(range(t2m.shape[0])):
                lt=t2m[it,...].data
                # aggregate all data in selected region
                rt2m[it,:]=lt[rloc]
            rt2m=rt2m.flatten()
            ht2m=np.percentile(rt2m,pc)	

            pickle.dump([ht2m,pc], open('%s/h%s_%s.%s.%s.pickle' % (odir,varn,yr,re,se), 'wb'), protocol=5)	
