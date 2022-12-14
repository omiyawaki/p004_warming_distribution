#!/glade/work/miyawaki/conda-envs/g/bin/python
#PBS -l select=1:ncpus=1:mpiprocs=1
#PBS -l walltime=06:00:00
#PBS -q casper
#PBS -A P54048000
#PBS -N xaaer-loop

import os
import sys
sys.path.append('../')
sys.path.append('/project2/tas1/miyawaki/common')
import pickle
import numpy as np
import xarray as xr
from tqdm import tqdm
from cmip6util import mods,emem,simu,year
from glade_utils import grid

# this script creates a histogram of daily temperature for a given year
# at each gridir point. 

realm='atmos' # data realm e.g., atmos, ocean, seaIce, etc
freq='day' # data frequency e.g., day, mon
varn='tas' # variable name

lfo = ['ssp245'] # forcing (e.g., ssp245)
# lse = ['ann'] # season (ann, djf, mam, jja, son)
lse = ['jja','mam','son','djf'] # season (ann, djf, mam, jja, son)
lcl = ['his'] # climatology (fut=future [2030-2050], his=historical [1920-1940])
# lcl = ['fut','his'] # climatology (fut=future [2030-2050], his=historical [1920-1940])
byr_his=[1980,2000] # output year bounds
byr_fut=[2080,2100]

# percentiles to compute (follows Byrne [2021])
pc = [1e-3,1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,82,85,87,90,92,95,97,99] 

for se in lse:
    for fo in lfo:
        for cl in lcl:
            # list of models
            lmd=mods(fo)

            # years and simulation names
            if cl == 'fut':
                byr=byr_fut
            elif cl == 'his':
                byr=byr_his

            for imd in tqdm(range(len(lmd))):
                md=lmd[imd]
                ens=emem(md)
                sim=simu(fo,cl)
                grd=grid(fo,cl,md)
                if sim=='ssp245':
                    lyr=['208001-210012']
                elif sim=='historical':
                    lyr=['198001-200012']

                idir='/project2/tas1/miyawaki/projects/000_hotdays/data/raw/%s/%s' % (sim,md)
                odir='/project2/tas1/miyawaki/projects/000_hotdays/data/cmip6/%s/%s/%s/%s' % (se,cl,sim,md)

                if not os.path.exists(odir):
                    os.makedirs(odir)

                c=0 # counter
                for yr in lyr:
                    if se=='ann':
                        fn = '%s/%s_%s_%s_%s_%s_%s_%s.nc' % (idir,varn,freq,md,sim,ens,grd,yr)
                    else:
                        fn = '%s/%s_%s_%s_%s_%s_%s_%s.%s.nc' % (idir,varn,freq,md,sim,ens,grd,yr,se)

                    ds = xr.open_dataset(fn)
                    if c==0:
                        t2m = ds[varn]
                    else:
                        t2m = xr.concat((t2m,ds[varn]),'time')
                    c=c+1
                    
                # save grid info
                gr = {}
                gr['lon'] = ds['lon']
                gr['lat'] = ds['lat']
                ds.close()
                t2m.load()

                # initialize array to store histogram data
                ht2m = np.empty([len(pc), gr['lat'].size, gr['lon'].size])

                # loop through gridir points to compute percentiles
                for ln in tqdm(range(gr['lon'].size)):
                    for la in range(gr['lat'].size):
                        lt = t2m[:,la,ln]
                        ht2m[:,la,ln]=np.percentile(lt,pc)	

                pickle.dump([ht2m, gr], open('%s/ht2m_%g-%g.%s.pickle' % (odir,byr[0],byr[1],se), 'wb'), protocol=5)	
