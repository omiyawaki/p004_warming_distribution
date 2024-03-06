import os
import sys
sys.path.append('../')
sys.path.append('/home/miyawaki/scripts/common')
import dask
from dask.diagnostics import ProgressBar
import dask.multiprocessing
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
import pickle
import numpy as np
import xesmf as xe
import xarray as xr
import constants as c
from scipy.ndimage import generic_filter1d
from winpct import get_window_indices,get_our_pct
from tqdm import tqdm
from smileutil import mods
from glade_utils import grid,smile
np.set_printoptions(threshold=sys.maxsize)

# comdsect warmings across the ensembles

# lmd=mods() # list of models
lmd=['CanESM5']
lvn=['tas'] # input1
mycmip=False

# lvn=['rsfc'] # input1
# mycmip=True

ty='2d'
checkexist=False

# fo = 'historical' # forcing (e.g., ssp245)
# byr=[1980,2000]

fo = 'ssp370' # forcing (e.g., ssp245)
byr=[2080,2100]

# fo = 'ssp370' # forcing (e.g., ssp245)
# byr='gwl2.0'
# dyr=10

freq='day'
se='sc'

# load ocean indices
_,omi=pickle.load(open('/project/amp/miyawaki/data/share/lomask/cesm2/lomi.pickle','rb'))

# for regridding
rgdir='/project/amp/miyawaki/data/share/regrid'
# open CESM data to get output grid
cfil='%s/f.e11.F1850C5CNTVSST.f09_f09.002.cam.h0.PHIS.040101-050012.nc'%rgdir
cdat=xr.open_dataset(cfil)
ogr=xr.Dataset({'lat': (['lat'], cdat['lat'].data)}, {'lon': (['lon'], cdat['lon'].data)})

def calc_lm(md,ens,varn):
    print(md,ens,varn)
    grd=grid(md)

    if mycmip or (md=='IPSL-CM6A-LR' and varn=='huss'):
        idir='/project/amp02/miyawaki/data/share/cmip6/%s/%s/%s/%s/%s/%s' % (fo,freq,varn,md,ens,grd)
    else:
        idir='/project/mojave/cmip6/%s/%s/%s/%s/%s/%s' % (fo,freq,varn,md,ens,grd)

    odir='/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,md,varn)
    if not os.path.exists(odir):
        os.makedirs(odir)

    if checkexist:
        if 'gwl' in byr:
            if os.path.isfile('%s/lm.%s_%s.%s.%s.nc' % (odir,varn,byr,ens,se)):
                print('Output file already exists, skipping...')
                return
        else:
            if os.path.isfile('%s/lm.%s_%g-%g.%s.%s.nc' % (odir,varn,byr[0],byr[1],ens,se)):
                print('Output file already exists, skipping...')
                return

    # load raw data
    fn = '%s/%s_%s_%s_%s_%s_%s_*.nc' % (idir,varn,freq,md,fo,ens,grd)
    print('\n Loading data to composite...')
    ds = xr.open_mfdataset(fn)
    if md=='IITM-ESM' and varn=='mrsos':
        vn = 1e3*ds[varn] # reported soil moisture is likely g/m**3
    else:
        vn = ds[varn]
    print('\n Done.')
    # save grid info
    gr = {}
    gr['lon'] = ds['lon']
    gr['lat'] = ds['lat']
    ds=None

    # select data within time of interest
    if 'gwl' in byr:
        idirg='/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % ('ts','historical+%s'%fo,md,'tas')
        [ygwl,gwl]=pickle.load(open('%s/gwl%s.%s.pickle' % (idirg,'tas','ts'),'rb'))
        print(ygwl)
        idx=np.where(gwl==float(byr[-3:]))
        print(idx)
        if ygwl[idx]==1850:
            print('\n %s does not warm to %s K. Skipping...'%(md,byr[-3:]))
            return

        print('\n Selecting data within range of interest...')
        vn=vn.sel(time=vn['time.year']>=ygwl[idx].data-dyr)
        vn=vn.sel(time=vn['time.year']<ygwl[idx].data+dyr)
        print('\n Done.')

    else:
        if md=='IITM-ESM' and fo=='ssp370':
            yend=2098
        else:
            yend=byr[1]
        print('\n Selecting data within range of interest...')
        vn=vn.sel(time=vn['time.year']>=byr[0])
        vn=vn.sel(time=vn['time.year']<yend)
        print('\n Done.')

    # regrid data
    if md!='CESM2':
        print('\n Regridding...')
        # path to weight file
        wf='%s/wgt.cmip6.%s.%s.cesm2.nc'%(rgdir,md,ty)
        # build regridder with existing weights
        rgd = xe.Regridder(vn,ogr, 'bilinear', periodic=True, reuse_weights=True, filename=wf)
        vn=rgd(vn)
        print('\n Done.')

    # remove ocean points
    time=vn['time']
    vn=vn.data
    vn=np.reshape(vn,(vn.shape[0],vn.shape[1]*vn.shape[2]))
    vn=np.delete(vn,omi,axis=1)
    ngp=vn.shape[1]

    vn=xr.DataArray(vn,coords={'time':time,'gpi':np.arange(ngp)},dims=('time','gpi'))

    vn=vn.rename(varn)
    if 'gwl' in byr:
        vn.to_netcdf('%s/lm.%s_%s.%s.%s.nc' % (odir,varn,byr,ens,se),format='NETCDF4')
    else:
        vn.to_netcdf('%s/lm.%s_%g-%g.%s.%s.nc' % (odir,varn,byr[0],byr[1],ens,se),format='NETCDF4')


for md in tqdm(lmd):
    for varn in lvn:
        print(md)
        # lme=smile(md,fo,varn)
        lme=['r12i1p1f1']

        if __name__=='__main__':
            with ProgressBar():
                tasks=[dask.delayed(calc_lm)(md,me,varn) for me in lme]
                dask.compute(*tasks,scheduler='processes')
                # dask.compute(*tasks,scheduler='single-threaded')
