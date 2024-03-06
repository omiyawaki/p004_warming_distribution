import os
import sys
sys.path.append('../../data/')
sys.path.append('/home/miyawaki/scripts/common')
import dask
from dask.diagnostics import ProgressBar
import dask.multiprocessing
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
import pickle
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.stats import linregress
from tqdm import tqdm
from util import mods
from utils import monname

lvn=['mrsos','tas','huss','pr','hfls','hfss']
# lvn=['pr','hfss','hfls','rsds','rsus','rlds','rlus']
se = 'sc' # season (ann, djf, mam, jja, son)
fo1='historical' # forcings 
fo2='ssp370' # forcings 
fo='%s-%s'%(fo2,fo1)
his='1980-2000'
fut='2080-2100'
# fut='gwl2.0'

lmd=mods(fo1)

def calc_mmm(varn):
    for i,md in enumerate(tqdm(lmd)):
        print(md)
        idir1 = '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo1,md,varn)
        idir2 = '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo2,md,varn)

        c = 0
        dt={}

        # prc conditioned on temp
        ds1=xr.open_dataset('%s/pc.doy.%s_%s.%s.nc' % (idir1,varn,his,se))
        try:
            pvn1=ds1[varn]
        except:
            pvn1=ds1['__xarray_dataarray_variable__']
        ds2=xr.open_dataset('%s/pc.doy.%s_%s.%s.nc' % (idir2,varn,fut,se))
        try:
            pvn2=ds2[varn]
        except:
            pvn2=ds2['__xarray_dataarray_variable__']

        pvn1=pvn1.groupby('time.dayofyear').mean(dim='time')
        pvn2=pvn2.groupby('time.dayofyear').mean(dim='time')
        if pvn1.shape[0] != 365:
            pvn1=pvn1.interp(dayofyear=np.arange(1,366,1))
            pvn2=pvn2.interp(dayofyear=np.arange(1,366,1))

        # warming
        dpvn=pvn2.data-pvn1.data

        # save individual model data
        if i==0:
            ipvn1=np.empty(np.insert(np.asarray(pvn1.shape),0,len(lmd)))
            ipvn2=np.empty(np.insert(np.asarray(pvn2.shape),0,len(lmd)))
            idpvn=np.empty(np.insert(np.asarray(dpvn.shape),0,len(lmd)))

        ipvn1[i,...]=pvn1
        ipvn2[i,...]=pvn2
        idpvn[i,...]=dpvn

    # compute mmm and std
    mpvn1=pvn1.copy()
    mpvn2=mpvn1.copy()
    mpvn1.data=np.nanmean(ipvn1,axis=0)
    mpvn2.data=np.nanmean(ipvn2,axis=0)

    mdpvn=mpvn1.copy()
    mdpvn.data=np.nanmean(idpvn,axis=0)

    spvn1=mpvn1.copy()
    spvn2=mpvn1.copy()
    spvn1.data=np.nanstd(ipvn1,axis=0)
    spvn2.data=np.nanstd(ipvn2,axis=0)

    sdpvn=mpvn1.copy()
    sdpvn.data=np.nanstd(idpvn,axis=0)

    # save mmm and std
    odir1 = '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo1,'mmm',varn)
    odir2 = '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo2,'mmm',varn)
    odir = '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,'mmm',varn)
    if not os.path.exists(odir1):
        os.makedirs(odir1)
    if not os.path.exists(odir2):
        os.makedirs(odir2)
    if not os.path.exists(odir):
        os.makedirs(odir)

    mpvn1.to_netcdf('%s/pc.doy.%s_%s.%s.nc' % (odir1,varn,his,se))
    mpvn2.to_netcdf('%s/pc.doy.%s_%s.%s.nc' % (odir2,varn,fut,se))
    spvn1.to_netcdf('%s/std.pc.doy.%s_%s.%s.nc' % (odir1,varn,his,se))
    spvn2.to_netcdf('%s/std.pc.doy.%s_%s.%s.nc' % (odir2,varn,fut,se))


    mdpvn.to_netcdf('%s/dpc.doy.%s_%s_%s.%s.nc' % (odir,varn,his,fut,se))
    sdpvn.to_netcdf('%s/std.dpc.doy.%s_%s_%s.%s.nc' % (odir,varn,his,fut,se))

if __name__=='__main__':
    with ProgressBar():
        tasks=[dask.delayed(calc_mmm)(vn) for vn in lvn]
        dask.compute(*tasks,scheduler='processes')
        # dask.compute(*tasks,scheduler='single-threaded')
