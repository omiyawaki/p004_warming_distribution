import os
import sys
sys.path.append('../../data/')
sys.path.append('/home/miyawaki/scripts/common')
import dask
from dask.diagnostics import ProgressBar
import dask.multiprocessing
import pickle
import pwlf
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.stats import gaussian_kde
from tqdm import tqdm
from util import mods
from utils import corr,corr2d,monname,varnlb,unitlb
from regions import pointlocs,masklev0,settype,retname,regionsets
from CASutils import shapefile_utils as shp

# relb='fourcorners'
# re=['Utah','Colorado','Arizona','New Mexico']

lrelb=['ic']

pct=np.linspace(1,99,101)
varn1='hfls'
varn2='mrsos'
varn3='pr'
vr=[0,15]
bvn2=np.arange(10,50+2,2)
varn='%s+%s'%(varn1,varn2)
ise='sc'
ose='ann'

fo1='historical' # forcings 
yr1='1980-2000'

fo2='ssp370' # forcings 
yr2='2080-2100'

fo='%s+%s'%(fo1,fo2)
fod='%s-%s'%(fo2,fo1)

lmd=mods(fo1)

def set_clim(relb):
    clim={  
            'ic':   [0,15],
            'fc':   [0,8],
            }
    return clim[relb]

# load ocean indices
_,omi=pickle.load(open('/project/amp/miyawaki/data/share/lomask/cesm2/lomi.pickle','rb'))

# grid
rgdir='/project/amp/miyawaki/data/share/regrid'
# open CESM data to get output grid
cfil='%s/f.e11.F1850C5CNTVSST.f09_f09.002.cam.h0.PHIS.040101-050012.nc'%rgdir
cdat=xr.open_dataset(cfil)
gr=xr.Dataset({'lat': (['lat'], cdat['lat'].data)}, {'lon': (['lon'], cdat['lon'].data)})

def load_data(md,fo,varn,mask,yr):
    idir = '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (ise,fo,md,varn)
    ds=xr.open_dataset('%s/lm.%s_%s.%s.nc' % (idir,varn,yr,ise))
    vn=ds[varn]
    gpi=ds['gpi']
    # extract data for season
    if ose!='ann':
        vn=vn.sel(time=vn['time.season']==ose.upper())
    # delete data outside masked region
    vn=np.delete(vn.data,np.nonzero(np.isnan(mask)),axis=1)
    vn=vn.flatten()
    if varn=='pr':
        vn=86400*vn
    return vn

def bindata(fo,yr,mask):
    print('Loading %s...'%varn1)
    vn1=load_data(md,fo,varn1,mask,yr)
    print('Loading %s...'%varn2)
    vn2=load_data(md,fo,varn2,mask,yr)
    print('Loading %s...'%varn3)
    vn3=load_data(md,fo,varn3,mask,yr)

    # bin
    nans=np.logical_or(np.isnan(vn1),np.isnan(vn2))
    vn1=vn1[~nans]
    vn2=vn2[~nans]
    vn3=vn3[~nans]
    dg=np.digitize(vn2,bvn2)
    bvn1=np.array([vn1[dg==i].mean() for i in range(1,len(bvn2)+1)])
    svn1=np.array([vn1[dg==i].std() for i in range(1,len(bvn2)+1)])
    bvn3=np.array([vn3[dg==i].mean() for i in range(1,len(bvn2)+1)])

    # find critical soil moisture
    nans=np.logical_or(np.isnan(bvn1),np.isnan(bvn2))
    nbvn1=bvn1[~nans]
    nbvn2=bvn2[~nans]
    pa=np.polynomial.polynomial.polyfit(nbvn2,nbvn1,3) # polynomial fit
    xv1=-(2*pa[2]+np.sqrt(4*pa[2]**2-12*pa[1]*pa[3]))/(6*pa[3])
    xv2=-(2*pa[2]-np.sqrt(4*pa[2]**2-12*pa[1]*pa[3]))/(6*pa[3])
    cc1=2*pa[2]+6*pa[3]*xv1
    cc2=2*pa[2]+6*pa[3]*xv2
    if cc1<0:
        csm=xv1
    else:
        csm=xv2
    return bvn1,bvn2,bvn3,svn1,csm

def plot(relb):
    # mask
    mask=masklev0(re,gr,mtype).data
    mask=mask.flatten()
    mask=np.delete(mask,omi)
    print(mask.shape)

    hbvn1,hbvn2,hbvn3,hsvn1,hcsm=bindata(fo1,yr1,mask)
    fbvn1,fbvn2,fbvn3,fsvn1,fcsm=bindata(fo2,yr2,mask)

    print('Plotting...')
    clim=set_clim(relb)
    oname1='%s/bin.bc.%s_%s.%s' % (odir,varn,yr1,ose)
    ax[i].set_title('%s'%md.upper())
    try:
        ax[i].annotate(r'$SM_c=%0.1d$'%csm, xy=(0.05, 0.85), xycoords='axes fraction')
    except:
        print('SMc could not be solved')
    ax[i].axvline(hcsm,color='tab:blue')
    ax[i].errorbar(hbvn2,hbvn1,yerr=hsvn1,fmt='.',color='tab:blue',alpha=0.2)
    ax[i].scatter(hbvn2,hbvn1,s=3,c='tab:blue')
    ax[i].axvline(fcsm,color='tab:orange')
    ax[i].errorbar(fbvn2,fbvn1,yerr=fsvn1,fmt='.',color='tab:orange',alpha=0.2)
    ax[i].scatter(fbvn2,fbvn1,s=3,c='tab:orange')
    fig.savefig('%s.png'%oname1, format='png', dpi=600)

for relb in lrelb:
    mtype=settype(relb)
    retn=retname(relb)
    re=regionsets(relb)
    fig,ax=plt.subplots(nrows=4,ncols=4,figsize=(9,7),constrained_layout=True)
    ax=ax.flatten()
    tname=r'%s' % (retn)
    fig.suptitle(r'%s' % (tname),fontsize=16)
    fig.supxlabel('%s (%s)'%(varnlb(varn2),unitlb(varn2)))
    fig.supylabel('%s (%s)'%(varnlb(varn1),unitlb(varn1)))

    odir= '/project/amp/miyawaki/plots/p004/cmip6/%s/%s/%s/%s/%s' % (ose,fo,'mi',varn,'regions')
    if not os.path.exists(odir):
        os.makedirs(odir)

    for i,md in enumerate(tqdm(lmd)):
        plot(relb)
