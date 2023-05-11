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
# from metpy.calc import saturation_mixing_ratio,specific_humidity_from_mixing_ratio
# from metpy.units import units

# collect warmings across the ensembles

varn='shuss'

# fo = 'historical' # forcing (e.g., ssp245)
# byr=[1980,2000]

fo = 'ssp370' # forcing (e.g., ssp245)
byr=[2080,2100]

freq='day'

lmd=mods(fo) # create list of ensemble members

def saturation_mixing_ratio(p,t):
    # p in pa, T in K
    t=t-273.15
    es=1e2*6.112*np.exp(17.67*t/(t+243.5)) # *100 for Pa
    rs=c.ep*es/(p-es)
    return rs/(1+rs)

def calc_shuss(md):
    ens=emem(md)
    grd=grid(fo,cl,md)

    odir='/project/amp02/miyawaki/data/share/cmip6/%s/%s/%s/%s/%s/%s' % (fo,freq,varn,md,ens,grd)
    if not os.path.exists(odir):
        os.makedirs(odir)

    idir0='/project/mojave/cmip6/%s/%s/%s/%s/%s/%s' % (fo,'Amon','ps',md,ens,grd)
    ds = xr.open_mfdataset('%s/*.nc'%idir0)
    ps = ds['ps'].load()
    ps=ps.resample(time='1D').interpolate('linear')
    ps=ps.groupby('time.dayofyear').mean('time')

    chk=0
    idir='/project/mojave/cmip6/%s/%s/%s/%s/%s/%s' % (fo,freq,'tas',md,ens,grd)
    for _,_,files in os.walk(idir):
        for fn in files:
            ofn='%s/%s'%(odir,fn.replace('tas',varn,1))
            if os.path.isfile(ofn):
                continue
            fn1='%s/%s'%(idir,fn)
            ds = xr.open_dataset(fn1)
            tas=ds['tas']
            dr=tas['time']
            doy=tas['time.dayofyear']
            sel=xr.DataArray(doy, dims=["time"], coords=[dr])
            extps=ps.sel(dayofyear=sel)
            # compute saturation sp humidity
            shuss=tas.copy()
            shuss.data=saturation_mixing_ratio(extps.data,tas.data)
            shuss=shuss.rename(varn)
            shuss.to_netcdf(ofn)

# calc_shuss('CanESM5')

if __name__ == '__main__':
    with ProgressBar():
        tasks=[dask.delayed(calc_shuss)(md) for md in lmd]
        dask.compute(*tasks,scheduler='processes')
        # dask.compute(*tasks,scheduler='single-threaded')
