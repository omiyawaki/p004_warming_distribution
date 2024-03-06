import os
import sys
sys.path.append('../')
sys.path.append('/home/miyawaki/scripts/common')
from concurrent.futures import ProcessPoolExecutor as Pool
import numpy as np
import xarray as xr
import constants as c
from tqdm import tqdm
from util import mods,simu,emem
from glade_utils import grid
from scipy.interpolate import interp1d

# collect warmings across the ensembles

slev=850 # in hPa
ivar='advm'
varn='%s%g'%(ivar,slev)

fo = 'historical' # forcing (e.g., ssp245)
# fo = 'ssp370' # forcing (e.g., ssp245)

checkexist=False
freq='Eday'

lmd=mods(fo) # create list of ensemble members

def calc_advm(md):
    ens=emem(md)
    grd=grid(md)

    odir='/project/amp02/miyawaki/data/share/cmip6/%s/%s/%s/%s/%s/%s' % (fo,freq,varn,md,ens,grd)
    if not os.path.exists(odir):
        os.makedirs(odir)

    chk=0
    idir='/project/amp02/miyawaki/data/share/cmip6/%s/%s/%s/%s/%s/%s' % (fo,freq,'ua850',md,ens,grd)
    for _,_,files in os.walk(idir):
        for fn in files:
            ofn='%s/%s'%(odir,fn.replace('ua850',varn))
            if checkexist and os.path.isfile(ofn):
                continue
            try:
                fn1='%s/%s'%(idir,fn)
                ds = xr.open_dataset(fn1)
                ua850=ds['ua850']
                fn1=fn1.replace('ua850','va850')
                ds = xr.open_dataset(fn1)
                va850=ds['va850']
                fn1=fn1.replace('va850','ta850')
                ds = xr.open_dataset(fn1)
                ta850=ds['ta850']
                fn1=fn1.replace('ta850','hus850')
                ds = xr.open_dataset(fn1)
                hus850=ds['hus850']
                try:
                    fn1=fn1.replace('hus850','zg850')
                    ds = xr.open_dataset(fn1)
                    zg850=ds['zg850']
                except:
                    fn1=fn1.replace('hus850','zg850').replace('day','Eday')
                    ds = xr.open_dataset(fn1)
                    zg850=ds['zg850']
                lat=np.deg2rad(ds['lat'].data)
                lon=np.deg2rad(ds['lon'].data)

                # compute mse flux divergence
                advm=ua850.copy()
                # compute mse
                mse=c.cpd*ta850.data+c.g*zg850.data+c.Lv*hus850.data
                clat=np.transpose(np.tile(np.cos(lat),(1,1,1)),[0,2,1])
                cmse=clat*mse
                # zonal gradient 
                advmx=1/(c.a*clat)*(mse[...,2:]-mse[...,:-2])/(lon[2:]-lon[:-2])
                advmx=np.concatenate((1/(c.a*clat)*(mse[...,[1]]-mse[...,[0]])/(lon[1]-lon[0]),advmx),axis=-1)
                advmx=np.concatenate((advmx,1/(c.a*clat)*(mse[...,[-1]]-mse[...,[-2]])/(lon[-1]-lon[-2])),axis=-1)
                # meridional gradient
                advmy=1/(c.a*clat[:,1:-1,:])*(cmse[:,2:,:]-cmse[:,:-2,:])/(lat[2:]-lat[:-2]).reshape([1,len(lat)-2,1])
                advmy=np.concatenate((1/(c.a*clat[:,0,:])*(cmse[:,[1],:]-cmse[:,[0],:])/(lat[1]-lat[0]),advmy),axis=1)
                advmy=np.concatenate((advmy,1/(c.a*clat[:,-1,:])*(cmse[:,[-1],:]-cmse[:,[-2],:])/(lat[-1]-lat[-2])),axis=1)

                # total horizontal divergence
                advm.data=ua850.data*advmx+va850.data*advmy

                advm=advm.rename(varn)
                advm.to_netcdf(ofn)

            except Exception as e:
                print(e)

calc_advm('UKESM1-0-LL')

# if __name__=='__main__':
#     with Pool(max_workers=len(lmd)) as p:
#         p.map(calc_advm,lmd)
