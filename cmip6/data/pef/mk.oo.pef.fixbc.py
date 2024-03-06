import os
import sys
sys.path.append('../')
sys.path.append('/home/miyawaki/scripts/common')
import dask
from dask.diagnostics import ProgressBar
from dask.distributed import Client
import dask.multiprocessing
from concurrent.futures import ProcessPoolExecutor as Pool
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

bct='bcef'
varn='oopef_fixbc'
varnp='pef'
se='sc'
nt=7
p=95
doy=False
only95=True

fo0 = 'historical' # forcing (e.g., ssp245)
byr0=[1980,2000]

fo = 'ssp370' # forcing (e.g., ssp245)
byr='gwl2.0'

freq='day'

lmd=mods(fo)

def get_fn0(varn,md,fo,byr):
    idir='/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,md,varn)
    if 'gwl' in byr:
        fn='%s/lm.%s_%s.%s.nc' % (idir,varn,byr,se)
    else:
        fn='%s/lm.%s_%g-%g.%s.nc' % (idir,varn,byr[0],byr[1],se)
    return fn

def get_fn(varn,md):
    idir='/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,md,varn)
    if doy:
        px='pc.doy'
    else:
        px='pc'
    if 'gwl' in byr:
        fn='%s/%s.%s_%s.%s.nc' % (idir,px,varn,byr,se)
    else:
        fn='%s/%s.%s_%g-%g.%s.nc' % (idir,px,varn,byr[0],byr[1],se)
    return fn

def get_bc(md,fo,byr):
    idir='/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,md,bct)
    iname='%s/%s.%g-%g.%s.pickle' % (idir,bct,byr[0],byr[1],se)
    return pickle.load(open(iname,'rb'))

def eval_bc(sm,bc):
    return np.interp(sm,bc[0],bc[1])

def calc_pef(md):
    print(md)
    ens=emem(md)
    grd=grid(md)

    odir='/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,md,varn)
    if not os.path.exists(odir):
        os.makedirs(odir)

    print('\n Loading data...')
    ds=xr.open_dataset(get_fn('mrsos',md))
    pct=ds['percentile']
    gpi=ds['gpi']
    sm=ds['mrsos']
    if only95:
        pct=[95]
        sm=sm.sel(percentile=pct)
    print('\n Done.')

    print('\n Computing soil moisture anomaly...')
    sm0=xr.open_dataset(get_fn0('mrsos',md,fo0,byr0))['mrsos']
    sm=sm-sm0.mean('time')
    print('\n Done.')

    print('\n Computing ef using budyko curve...')
    ###### NEW ######
    bc=get_bc(md,fo0,byr0)

    def pefmon(mon,sm,bc):
        ssm=sm.sel(month=[mon])
        sef=ssm.copy()
        for igpi in tqdm(range(len(gpi))):
            try:
                sef.data[...,igpi]=eval_bc(ssm[...,igpi],bc[mon-1][igpi])
            except:
                sef.data[...,igpi]=np.nan
        return sef

    oopef=[]
    for ip,p in enumerate(pct):
        psm=sm.sel(percentile=[p])
        with Client(n_workers=12):
            tasks=[dask.delayed(pefmon)(mon,psm,bc) for mon in np.arange(1,13,1)]
            pef=dask.compute(*tasks)

        pef=xr.concat(pef,'month').sortby('month')
        pef=pef.rename(varnp)
        oopef.append(pef)

    oopef=xr.concat(oopef,'percentile').sortby('percentile')

    # save pef
    oname=get_fn(varn,md)
    pef.to_netcdf(oname,format='NETCDF4')

if __name__=='__main__':
    # calc_pef('TaiESM1')
    [calc_pef(md) for md in tqdm(lmd)]

# if __name__=='__main__':
#     with Pool(max_workers=len(lmd)) as p:
#         p.map(calc_pef,lmd)
