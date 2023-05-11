import os
import sys
sys.path.append('../../data/')
sys.path.append('/home/miyawaki/scripts/common')
import pickle
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.stats import linregress
from tqdm import tqdm
from cmip6util import mods
from utils import monname

nt=7 # window size in days
pref1='ddp'
varn1='hfls'
pref2='ddp'
varn2='mrsos'
varn='%s%s+%s%s'%(pref1,varn1,pref2,varn2)
se = 'sc' # season (ann, djf, mam, jja, son)
fo1='historical' # forcings 
fo2='ssp370' # forcings 
fo='%s-%s'%(fo2,fo1)
his='1980-2000'
fut='2080-2100'
skip5075=True

md='mi'

idir = '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl,fo,md,varn)
idir1 = '/project/amp02/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl,fo,'mmm','tas')
odir = '/project/amp/miyawaki/plots/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl,fo,md,varn)

if not os.path.exists(odir):
    os.makedirs(odir)

# correlation
_,_,gr=pickle.load(open('%s/d%s_%s_%s.%s.pickle' % (idir1,'tas',his,fut,se), 'rb'))	
r=pickle.load(open('%s/rsq.%s_%s_%s.%s.pickle' % (idir,varn,his,fut,se), 'rb'))	

r=np.nanmean(r,0) # MMM
# repeat 0 deg lon info to 360 deg to prevent a blank line in contour
gr['lon'] = np.append(gr['lon'].data,360)
r=np.append(r,r[...,0][...,None],axis=2)

[mlat,mlon] = np.meshgrid(gr['lat'], gr['lon'], indexing='ij')

# plot r (pct warming - mean warming)
for i,p in enumerate(gr['pct']):
    if p==95:
        fig,ax=plt.subplots(subplot_kw={'projection': ccrs.Robinson(central_longitude=240)},figsize=(5,4),constrained_layout=True)
        ax.set_title(r'%s %s' % ('MMM',fo.upper()),fontsize=16)
        clf=ax.contourf(mlon, mlat, r[i,...], np.arange(-1,1+0.1,0.1), vmax=1, vmin=-1, transform=ccrs.PlateCarree(),cmap='RdBu_r')
        ax.coastlines()
        cb=fig.colorbar(clf,location='bottom',aspect=50)
        cb.set_label(label=r'$R(\Delta \delta LH^{%02d},\Delta\delta SM^{%02d})$'%(p,p))
        fig.savefig('%s/sc.r%02d%s.%s.pdf' % (odir,p,varn,fo), format='pdf', dpi=300)
