import os
import sys
sys.path.append('../')
sys.path.append('/home/miyawaki/scripts/common')
import dask
from dask.diagnostics import ProgressBar
from dask.distributed import Client
import dask.multiprocessing
import pickle
import numpy as np
import xesmf as xe
import xarray as xr
import constants as c
from tqdm import tqdm
from util import mods,simu,emem
from glade_utils import grid
from etregimes import bestfit

# collect warmings across the ensembles

varn='bc'
vn1='hfls'
vn2='mrsos'
se='sc'

# fo = 'historical' # forcing (e.g., ssp245)
# byr=[1980,2000]

fo = 'ssp370' # forcing (e.g., ssp245)
byr=[2080,2100]

freq='day'

lmd=mods(fo) # create list of ensemble members

def get_fn(varn,md):
    idir='/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,md,varn)
    if 'gwl' in byr:
        fn='%s/lm.%s_%s.%s.nc' % (idir,varn,byr,se)
    else:
        fn='%s/lm.%s_%g-%g.%s.nc' % (idir,varn,byr[0],byr[1],se)
    return fn

def load_vn(vn,md,mon,time0):
    varn=xr.open_dataset(get_fn(vn,md))[vn]
    varn=varn.interp_calendar(time0)
    varn=varn.sel(time=varn['time.month']==mon)
    return varn

def calc_bc(lmd):
    odir='/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,'mmm',varn)
    if not os.path.exists(odir):
        os.makedirs(odir)

    ds=xr.open_dataset(get_fn(vn1,'CESM2'))
    time0=ds['time']
    gpi=ds['gpi']

    print('\n Computing budyko curve...')
    # create list to store bcs
    bc = [ ([0] * len(gpi)) for im in range(12) ]

    def bcmon(mon,vn1,vn2):
        svn1=[load_vn(vn1,md,mon,time0) for md in lmd]
        svn1=xr.concat(svn1,'model')
        svn2=[load_vn(vn2,md,mon,time0) for md in lmd]
        svn2=xr.concat(svn2,'model')
        bc=[]
        for igpi in tqdm(range(len(gpi))):
            nvn1=svn1.data[...,igpi].flatten()
            nvn2=svn2.data[...,igpi].flatten()
            nans=np.logical_or(np.isnan(nvn1),np.isnan(nvn2))
            nvn1=nvn1[~nans]
            nvn2=nvn2[~nans]
            try:
                f1,f2=bestfit(nvn2,nvn1)
                bc.append(f2['line'])
            except:
                bc.append(None)
        return bc

    with Client(n_workers=12):
        tasks=[dask.delayed(bcmon)(mon,vn1,vn2) for mon in np.arange(1,13,1)]
        bc=dask.compute(*tasks)

    # save bc
    oname='%s/%s_orig.%g-%g.%s.pickle' % (odir,varn,byr[0],byr[1],se)
    pickle.dump(bc,open(oname,'wb'),protocol=5)

if __name__=='__main__':
    calc_bc(lmd)
