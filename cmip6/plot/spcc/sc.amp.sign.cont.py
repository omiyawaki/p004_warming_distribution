import os
import sys
sys.path.append('../../data/')
sys.path.append('/home/miyawaki/scripts/common')
import pickle
import numpy as np
import xarray as xr
from concurrent.futures import ProcessPoolExecutor as Pool
import cartopy.crs as ccrs
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import MultipleLocator
from scipy import ndimage
from scipy.stats import ttest_1samp as tt1
from sklearn.utils import resample
from tqdm import tqdm
from util import mods
from utils import monname,varnlb,unitlb
from mpl_toolkits.axes_grid1 import Divider,Size
from regions import masklev0,retname

nbs=int(1e2) # number of bootstrap resamples
lre=['tr','ml','hl'] # tr=tropics, ml=midlatitudes, hl=high lat, et=extratropics
mtype='continent'
lct=[['af'],['as'],['au'],['eu'],['na'],['oc'],['sa']]
tlat=30 # latitude bound for tropics
plat=50 # midlatitude bound
alc=0.05 # significance level (that mmm is different from 0)
cval=0.4 # threshold DdT value for drawing contour line
npamp=20 # number of bins for AI percentiles
dpamp=100/npamp
lpamp=np.arange(0,100+dpamp,dpamp)
mppamp=1/2*(lpamp[1:]+lpamp[:-1])
filt=False # only look at gridpoints with max exceeding value below
fmax=0.5
debug=False
title=True
xlb=True
ylboverride=True
cboverride=True
titleoverride=True
fs=(3.5,3)
pds=(1,0.5)
axs=(1.5,2)
h=[Size.Fixed(pds[0]), Size.Fixed(axs[0])]
v=[Size.Fixed(pds[1]), Size.Fixed(axs[1])]

p=95 # percentile
px0='ddpc'
varn='tas'
px1='d'
varn1='hfls'
varnp='hfls'
se = 'sc' # season (ann, djf, mam, jja, son)
fo1='historical' # forcings 
fo2='ssp370' # forcings 
fo='%s-%s'%(fo2,fo1)
his='1980-2000'
# fut='2080-2100'
fut='gwl2.0'
skip507599=True

lmd=mods(fo1)
md='mmm'

def ctitle(vn):
    d={ 
        'ooplh_msm':    'blue',
        'ooplh_fixmsm': 'orange',
        'ooplh_fixasm': 'blue',
        'ooplh_fixbc':  'blue',
        'ooplh_dbc':    'blue',
        'ooplh_rbcsm':  'blue',
        'ooplh_rddsm':  'green',
        'ooplh_mtr':    'blue',
            }
    try:
        color=d[vn]
    except:
        color='black'
    return color

def cmap(vn):
    d={ 'hfls':         'RdBu_r',
        'hfss':         'RdBu_r',
        'rsfc':         'RdBu_r',
        'ooplh':        'RdBu_r',
        'ooplh_msm':    'RdBu_r',
        'ooplh_fixmsm': 'RdBu_r',
        'ooplh_fixasm': 'RdBu_r',
        'ooplh_fixbc':  'RdBu_r',
        'ooplh_dbc':    'RdBu_r',
        'ooplh_rbcsm':  'RdBu_r',
        'ooplh_rddsm':  'RdBu_r',
        'ooplh_mtr':    'RdBu_r',
        'tas':          'RdBu_r',
        'pr':           'BrBG',
        'mrsos':        'BrBG',
        'td_mrsos':     'BrBG',
        'ti_pr':        'BrBG',
        'ti_ev':        'BrBG',
        'ef':           'RdBu_r',
        'ef2':          'RdBu_r',
        'ef3':          'RdBu_r',
        'ooef':         'RdBu_r',
        'oopef':        'RdBu_r',
        'oopef_fixbc':  'RdBu_r',
            }
    return d[vn]

def vmax(vn):
    d={ 'hfls':         10,
        'hfss':         10,
        'rsfc':         10,
        'ooplh':        10,
        'ooplh_msm':    10,
        'ooplh_fixmsm': 10,
        'ooplh_fixasm': 10,
        'ooplh_fixbc':  10,
        'ooplh_dbc':    10,
        'ooplh_rbcsm':  10,
        'ooplh_rddsm':  10,
        'ooplh_mtr':    10,
        'tas':          1,
        'pr':           1,
        'mrsos':        1,
        'td_mrsos':     1,
        'ti_pr':        1,
        'ti_ev':        1,
        'ef':           0.05,
        'ef2':          0.05,
        'ef3':          0.05,
        'ooef':         0.05,
        'oopef':        0.05,
        'oopef_fixbc':  0.05,
            }
    return d[vn]

def vstr(vn):
    d={ 'ooplh':        r'$BC_{all}$',
        'ooplh_fixbc':  r'$BC_{hist}$',
        'ooplh_dbc':    r'$SM_{hist}$',
        'ooplh_rbcsm':  r'Residual',
        'ooplh_rddsm':  r'(b)$-$(c)',
        'ooplh_fixmsm': r'$BC_{hist}$, $\Delta\delta SM=0$',
        'ooplh_fixasm': r'$BC_{hist}$, $\Delta\delta SM=0$',
        'ooplh_mtr':    r'$\frac{\mathrm{d}LH}{\mathrm{d}SM}_{hist}\Delta SM$',
        'oopef':        r'$BC_{all}$',
        'oopef_fixbc':  r'$BC_{hist}$',
        'mrsos':        r'$SM$',
        'td_mrsos':     r'$SM_{\mathrm{30\,d}}$',
        'ti_pr':        r'$P_{\mathrm{30\,d}}$',
        'ti_ev':        r'$-E_{\mathrm{30\,d}}$',
        'pr':           r'$P$',
            }
    return d[vn]

def pxlb(px):
    if px=='d':
        return 'Mean'
    elif px=='dpc':
        return 'Hot'
    elif px=='ddpc':
        return '\Delta\delta'

def plot(re):
    if ylboverride:
        ylb=True
    else:
        ylb=True if re=='tr' else False
    if cboverride:
        showcb=True
    else:
        showcb=True if re=='hl' else False
    # plot strings
    if titleoverride:
        tstr='$%s$'%varnlb(varn1)
    else:
        if 'ooplh' in varn1 or 'oopef' in varn1:
            tstr=vstr(varn1)
        elif 'mrsos' in varn1 or 'pr' in varn1:
            tstr=vstr(varn1)
        else:
            if re=='tr':
                tstr='Tropics'
            elif re=='ml':
                tstr='Midlatitudes'
            elif re=='hl':
                tstr='High latitudes'
            elif re=='et':
                tstr='Extratropics'
    fstr='.filt' if filt else ''

    # load land indices
    lmi,_=pickle.load(open('/project/amp/miyawaki/data/share/lomask/cesm2/lomi.pickle','rb'))

    # grid
    rgdir='/project/amp/miyawaki/data/share/regrid'
    # open CESM data to get output grid
    cfil='%s/f.e11.F1850C5CNTVSST.f09_f09.002.cam.h0.PHIS.040101-050012.nc'%rgdir
    cdat=xr.open_dataset(cfil)
    gr=xr.Dataset({'lat': (['lat'], cdat['lat'].data)}, {'lon': (['lon'], cdat['lon'].data)})

    def remap(v,gr):
        llv=np.nan*np.ones([12,gr['lat'].size*gr['lon'].size])
        llv[:,lmi]=v.data
        llv=np.reshape(llv,(12,gr['lat'].size,gr['lon'].size))
        return llv

    def eremap(v,gr):
        llv=np.nan*np.ones([v.shape[0],12,gr['lat'].size*gr['lon'].size])
        llv[:,:,lmi]=v.data
        llv=np.reshape(llv,(v.shape[0],12,gr['lat'].size,gr['lon'].size))
        return llv

    def regsl(v,ma):
        v=v*ma
        v=np.reshape(v,[v.shape[0],v.shape[1]*v.shape[2]])
        kidx=~np.isnan(v).any(axis=0)
        return v[:,kidx],kidx

    def regsla(v,gr,ma):
        sv=np.roll(v,6,axis=0) # seasonality shifted by 6 months
        v[:,gr['lat']<0,:]=sv[:,gr['lat']<0,:]
        return regsl(v,ma)

    def eregsl(v,ma,kidx):
        v=v*np.moveaxis(ma[...,None],-1,0)
        v=np.reshape(v,[v.shape[0],v.shape[1],v.shape[2]*v.shape[3]])
        return v[:,:,kidx]

    def eregsla(v,gr,ma,kidx):
        sv=np.roll(v,6,axis=1) # seasonality shifted by 6 months
        v[:,:,gr['lat']<0,:]=sv[:,:,gr['lat']<0,:]
        return eregsl(v,ma,kidx)

    def mregsl(v,ma,kidx):
        v=v*ma
        v=np.reshape(v,[v.shape[0],v.shape[1]*v.shape[2]])
        return v[:,kidx]

    def mregsla(v,gr,ma,kidx):
        sv=np.roll(v,6,axis=0) # seasonality shifted by 6 months
        v[:,gr['lat']<0,:]=sv[:,gr['lat']<0,:]
        return mregsl(v,ma,kidx)

    def regsl2d(v,ma,kidx):
        v=v*ma
        v=np.reshape(v,[v.shape[0]*v.shape[1]])
        return v[kidx]

    def sortai(v):
        idx=np.argsort(v)
        return v[idx],idx

    odir = '/project/amp/miyawaki/plots/p004/cmip6/%s/%s/%s/%s' % (se,fo,md,varn)
    if not os.path.exists(odir):
        os.makedirs(odir)

    def load_vn(varn,fo,byr,px='m'):
        idir = '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,md,varn)
        return xr.open_dataarray('%s/%s.%s_%s.%s.nc' % (idir,px,varn,byr,se))

    def load_mmm(varn,varnp,px):
        idir = '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,md,varn)
        ddpvn=xr.open_dataarray('%s/%s.%s_%s_%s.%s.nc' % (idir,px,varn,his,fut,se))
        try:
            pct=ddpvn['percentile']
            gpi=ddpvn['gpi']
            return ddpvn.sel(percentile=pct==p).squeeze()
        except:
            gpi=ddpvn['gpi']
            return ddpvn

    ddpvn=load_mmm(varn,varn,px0)
    ddpvn1=load_mmm(varn1,varnp,px1)
    if varn1=='ti_ev':
        ddpvn1=-ddpvn1

    # variable of interest
    odir1 = '/project/amp/miyawaki/plots/p004/cmip6/%s/%s/%s/%s%s' % (se,fo,md,px1,varn1)
    if not os.path.exists(odir1):
        os.makedirs(odir1)

    def load_vn(idir0):
        ddpvne=xr.open_dataarray('%s/ddpc.%s_%s_%s.%s.nc' % (idir0,varn1,his,fut,se))
        if varn1=='pr': ddpvne=86400*ddpvne
        return ddpvne.sel(percentile=p).squeeze()

    # load data for each model
    def load_idir(md):
        return '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s' % (se,fo,md,varn1)
    idirs=[load_idir(md0) for md0 in lmd]
    ddpvne=[load_vn(idir0) for idir0 in tqdm(idirs)]
    ddpvne=xr.concat(ddpvne,'model')

    # remap to lat x lon
    ddpvn=remap(ddpvn,gr)
    ddpvn1=remap(ddpvn1,gr)
    ddpvne=eremap(ddpvne,gr)

    # mask greenland and antarctica
    aagl=pickle.load(open('/project/amp/miyawaki/data/share/aa_gl/cesm2/aa_gl.pickle','rb'))
    ai=ai*aagl
    ddpvn1=ddpvn1*aagl
    ddpvne=ddpvne*aagl

    amp=np.nanmax(ddpvn,axis=0)-np.nanmin(ddpvn,axis=0)

    [mlat,mlon] = np.meshgrid(gr['lat'], gr['lon'], indexing='ij')
    awgt=np.cos(np.deg2rad(mlat)) # area weight

    # make sure nans are consistent
    nidx=np.isnan(ddpvn1)
    for imd in range(ddpvne.shape[0]):
        nidx=np.logical_or(np.isnan(nidx),np.isnan(ddpvne[imd,...]))
    ddpvn1[nidx]=np.nan
    ddpvne[:,nidx]=np.nan

    ah=np.ones_like(mlat)
    if re=='tr':
        ah[np.abs(gr['lat'])>tlat]=np.nan
    elif re=='ml':
        ah[np.logical_or(np.abs(gr['lat'])<=tlat,np.abs(gr['lat'])>plat)]=np.nan
    elif re=='hl':
        ah[np.abs(gr['lat'])<=plat]=np.nan
    elif re=='et':
        ah[np.abs(gr['lat'])<=tlat]=np.nan

    # select region
    ahddp1,kidx=regsla(ddpvn1,gr,ah)
    ahddpe=eregsla(ddpvne,gr,ah,kidx)
    amp=regsl2d(amp,ah,kidx)
    # weights
    ahw=regsl2d(awgt,ah,kidx)

    # bin DdT
    def binned(vn,w,idx):
        nb=idx.max()-1
        bvn=np.empty([12,nb])
        for im in range(12):
            bvn[im,:]=[np.nansum(w[idx==i]*vn[im,idx==i])/np.nansum(w[idx==i]) for i in 1+np.arange(nb)]
        return bvn

    # bin into 12
    def ebinned(vn,w,idx):
        nb=idx.max()-1 # number of bins
        bvn=np.empty([vn.shape[0],12,nb])
        for imd in range(vn.shape[0]):
            for im in range(12):
                bvn[imd,im,:]=[np.nansum(w[idx==i]*vn[imd,im,idx==i])/np.nansum(w[idx==i]) for i in range(nb)]
        return bvn

    # loop over continents
    for ct in lct:
        try:
            mask=masklev0(ct,gr,mtype).data
            mask2d=regsl2d(mask,ah,kidx)
            mask=np.tile(mask,(12,1,1))
            mask=mregsla(mask,gr,ah,kidx)
            camp=mask2d*amp
            cahddp1=mask*ahddp1
            cahddpe=np.tile(mask,(ahddpe.shape[0],1,1))*ahddpe
            pamp=np.nanpercentile(camp,lpamp)
            iamp=np.digitize(camp,pamp)
            cahddp1=binned(cahddp1,ahw,iamp)
            cahddpe=ebinned(cahddpe,ahw,iamp)

            # bootstrap
            s=cahddpe.shape
            cahddpe=np.reshape(cahddpe,(s[0],s[1]*s[2]))
            al=np.ones(cahddpe.shape[1])
            for ig in tqdm(range(cahddpe.shape[1])):
                sa=cahddpe[:,ig]
                bs=[np.nanmean(resample(sa)) for _ in range(nbs)]
                bs=np.array(bs)
                pl,pu=np.percentile(bs,100*np.array([alc/2,1-alc/2]))
                if pl<0 and pu>0: al[ig]=0  # 0 is inside confidence interval
            al=np.reshape(al,(s[1],s[2]))

            mon=range(12)
            [cahmmon,cahmbin] = np.meshgrid(mon,mppamp, indexing='ij')

            # plot gp vs seasonal cycle of varn1 PCOLORMESH
            fig=plt.figure(figsize=fs)
            divider=Divider(fig, (0, 0, 1, 1), h, v, aspect=False)
            ax=fig.add_axes(divider.get_position(),axes_locator=divider.new_locator(nx=1, ny=1))
            clf=ax.pcolormesh(cahmmon,cahmbin,cahddp1,vmin=-vmax(varn1),vmax=vmax(varn1),cmap=cmap(varn1))
            hatch=plt.fill_between([-0.5,11.5],0,100,hatch='///////',color='none',edgecolor='gray',linewidths=0.3)
            ax.pcolormesh(cahmmon,cahmbin,np.ma.masked_where(al==0,cahddp1),vmin=-vmax(varn1),vmax=vmax(varn1),cmap=cmap(varn1))
            # ax.set_title()
            ax.text(0.5,1.05,retname(ct[0]),c=ctitle(varn1),ha='center',va='center',transform=ax.transAxes)
            ax.xaxis.set_minor_locator(MultipleLocator(1))
            ax.set_xticks(np.arange(1,11+2,2))
            ax.set_xticklabels(np.arange(2,12+2,2))
            ax.set_yticks(100*np.arange(0,1+0.2,0.2))
            # ax.set_xticklabels(np.arange(2,12+2,2))
            if ylb:
                ax.set_ylabel('Amplitude Percentile')
            else:
                ax.set_yticklabels([])
            if not xlb:
                ax.set_xticklabels([])
            ax.set_xlim([-0.5,11.5])
            ax.set_ylim([0,100])
            if showcb:
                cb=plt.colorbar(clf,cax=fig.add_axes([(pds[0]+axs[0]+0.15)/fs[0],pds[1]/fs[1],0.1/fs[0],axs[1]/fs[1]]))
                if titleoverride:
                    cb.set_label('%s'%(unitlb(varn1)))
                else:
                    cb.set_label('$%s %s^{%02d}$ (%s)'%(pxlb(px1),varnlb(varn1),p,unitlb(varn1)))
            fig.savefig('%s/sc.%s.%s.%s%s.ah.amp.sign.%s.%s.png' % (odir1,px1,varn1,fo,fstr,re,ct[0]), format='png', dpi=600,backend='pgf')
            fig.savefig('%s/sc.%s.%s.%s%s.ah.amp.sign.%s.%s.pdf' % (odir1,px1,varn1,fo,fstr,re,ct[0]), format='pdf', dpi=600,backend='pgf')
        except Exception as e:
            if debug:
                print(e)
                sys.exit()
            else:
                print('Skipping %s for %s'%(ct[0],re))

[plot(re) for re in tqdm(lre)]

# if __name__=='__main__':
#     with Pool(max_workers=len(lre)) as p:
#         p.map(plot,lre)
