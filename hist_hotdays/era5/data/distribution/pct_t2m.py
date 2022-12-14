import os
import sys
import pickle
import numpy as np
import xarray as xr
from tqdm import tqdm

# this script creates a histogram of daily temperature for a given year
# at each gridir point. 

varn='t2m'
lse = ['ann','djf','mam','jja','son'] # season (ann, djf, mam, jja, son)

y0=1950 # first year
y1=2021 # last year+1

lyr=[str(y) for y in np.arange(y0,y1)]

pc = [1e-3,1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,82,85,87,90,92,95,97,99] # percentiles to compute

for se in lse:
    idir = '/project/mojave/observations/ERA5_daily/T2m'
    odir = '/project/amp/miyawaki/data/p004/hist_hotdays/era5/%s/%s' % (se,varn)

    if not os.path.exists(odir):
        os.makedirs(odir)

    for yr in lyr:
        fn = '%s/t2m_%s.nc' % (idir,yr)
        ds = xr.open_dataset(fn)
        t2m = ds['t2m']
        if se != 'ann':
            t2m=t2m.sel(time=t2m['time.season']==se.upper())
        gr = {}
        gr['lon'] = ds['lon']
        gr['lat'] = ds['lat']

        # initialize array to store data
        ht2m = np.empty([len(pc), gr['lat'].size, gr['lon'].size])

        # loop through gridir points to compute percentiles
        for ln in tqdm(range(gr['lon'].size)):
            for la in range(gr['lat'].size):
                lt = t2m[:,la,ln]
                ht2m[:,la,ln]=np.percentile(lt,pc)	

        pickle.dump([ht2m, gr], open('%s/h%s_%s.%s.pickle' % (odir,varn,yr,se), 'wb'), protocol=5)	
