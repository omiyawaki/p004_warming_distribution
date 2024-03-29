import os
import sys
sys.path.append('../')
sys.path.append('/home/miyawaki/scripts/common')
import dask
from dask.diagnostics import ProgressBar
import dask.multiprocessing
import pickle
import numpy as np
import xesmf as xe
import xarray as xr
import constants as c
from tqdm import tqdm
from cmip6util import mods,simu,emem
from glade_utils import grid
from metpy.calc import saturation_mixing_ratio,specific_humidity_from_mixing_ratio
from metpy.units import units

# collect warmings across the ensembles

slev=500 # in hPa
ivar='zg'
varn='%s%g'%(ivar,slev)

fo = 'historical' # forcing (e.g., ssp245)
byr=[1980,2000]

# fo = 'ssp370' # forcing (e.g., ssp245)
# byr=[2080,2100]

# freq='day'

lmd=mods(fo) # create list of ensemble members

def calc_zg500(md):
    if md=='MIROC-ES2L':
        freq='Eday'
    else:
        freq='day'
    ens=emem(md)
    grd=grid(fo,cl,md)

    odir='/project/amp02/miyawaki/data/share/cmip6/%s/%s/%s/%s/%s/%s' % (fo,freq,varn,md,ens,grd)
    if not os.path.exists(odir):
        os.makedirs(odir)

    idir='/project/mojave/cmip6/%s/%s/%s/%s/%s/%s' % (fo,freq,ivar,md,ens,grd)
    for _,_,files in os.walk(idir):
        for fn in files:
            if '.sh' in fn:
                continue
            ds = xr.open_dataset('%s/%s'%(idir,fn))
            # select data at desired level
            zg=ds[ivar]
            zglev=zg.sel(plev=100*slev,method='nearest')
            zglev=zglev.rename(varn)
            zglev.to_netcdf('%s/%s'%(odir,fn.replace(ivar,varn,1)))

calc_zg500('MIROC-ES2L')

# if __name__ == '__main__':
#     with ProgressBar():
#         tasks=[dask.delayed(calc_zg500)(md) for md in lmd]
#         dask.compute(*tasks,scheduler='processes')
