#!/glade/work/miyawaki/conda-envs/g/bin/python
#PBS -l select=1:ncpus=1:mpiprocs=1
#PBS -l walltime=06:00:00
#PBS -q casper
#PBS -A P54048000
#PBS -N xaaer-loop

import os
import sys
sys.path.append('../')
sys.path.append('/home/miyawaki/scripts/common')
sys.path.append('/project2/tas1/miyawaki/common')
import pickle
import numpy as np
import xarray as xr
from scipy.interpolate import interp1d
from tqdm import tqdm
from cmip6util import mods,emem,simu,year
from glade_utils import grid
from regions import rinfo

# this script creates a histogram of daily temperature for a given year
# at each gridir point. 

realm='atmos' # data realm e.g., atmos, ocean, seaIce, etc
freq='day' # data frequency e.g., day, mon
varn='tas' # variable name

lre=['swus','sea']
lfo = ['historical'] # data to use from 2015 onward (e.g., ssp245)
lse = ['jja'] # season (ann, djf, mam, jja, son)
# lse = ['jja','mam','son','djf'] # season (ann, djf, mam, jja, son)
lcl = ['his']
byr=[1980,2000] # output year bounds
# byr=[2080,2100] # output year bounds
lyr=np.arange(byr[0],byr[1]+1)

# percentiles to compute (follows Byrne [2021])
# pc = [1e-3,1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,82,85,87,90,92,95,97,99] 
pc = [1,5,50,95,99] 

for re in lre:
    # file where selected region is provided
    rloc,rlat,rlon=rinfo(re)

    for se in lse:
        for fo in lfo:
            for cl in lcl:
                # list of models
                lmd=mods(fo)

                # years and simulation names
                for imd in tqdm(range(len(lmd))):
                    md=lmd[imd]
                    ens=emem(md)
                    sim=simu(fo,cl,None)
                    grd=grid(fo,cl,md)
                    if sim=='ssp245':
                        lyr=['208001-210012']
                    elif sim=='historical':
                        lyr=['198001-200012']

                    idir='/project/amp/miyawaki/temp/cmip6/%s/%s/%s/%s/%s/%s' % (sim,freq,varn,md,ens,grd)
                    odir='/project/amp/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl,fo,md,varn)

                    if not os.path.exists(odir):
                        os.makedirs(odir)

                    c=0 # counter
                    fnt = '%s/%s_%s_%s_%s_%s_%s_*.nc' % (idir,varn,freq,md,sim,ens,grd)
                    ds = xr.open_mfdataset(fnt)
                    t2m = ds[varn]

                    # for yr in lyr:
                    #     if se=='ann':
                    #         fn = '%s/%s_%s_%s_%s_%s_%s_%s.nc' % (idir,varn,freq,md,sim,ens,grd,yr)
                    #     else:
                    #         fn = '%s/%s_%s_%s_%s_%s_%s_%s.%s.nc' % (idir,varn,freq,md,sim,ens,grd,yr,se)

                    #     ds = xr.open_dataset(fn)
                    #     if c==0:
                    #         t2m = ds[varn]
                    #     else:
                    #         t2m = xr.concat((t2m,ds[varn]),'time')
                    #     c=c+1
                        
                    # save grid info
                    gr = {}
                    gr['lon'] = ds['lon']
                    gr['lat'] = ds['lat']
                    ds.close()
                    t2m.load()

                    # initialize array to store histogram data
                    rt2m = np.empty([t2m.shape[0], len(rloc[0])])
                    # loop through time to aggregate data in selected region
                    for it in tqdm(range(t2m.shape[0])):
                        lt=t2m[it,...].data
                        # regrid 
                        if len(gr['lon'])!=len(rlon):
                            fint=interp1d(gr['lon'],lt,axis=1,fill_value='extrapolate')
                            lt=fint(rlon)
                        if len(gr['lat'])!=len(rlat):
                            fint=interp1d(gr['lat'],lt,axis=0,fill_value='extrapolate')
                            lt=fint(rlat)
                        rt2m[it,:]=lt[rloc]
                    rt2m=rt2m.flatten()
                    ht2m=np.percentile(rt2m,pc)	

                    pickle.dump([ht2m, pc], open('%s/ht2m_%g-%g.%s.%s.pickle' % (odir,byr[0],byr[1],re,se), 'wb'), protocol=5)	
