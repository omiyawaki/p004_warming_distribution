import os
import sys
sys.path.append('../')
sys.path.append('/home/miyawaki/scripts/common')
import pickle
import numpy as np
import xarray as xr
from tqdm import tqdm
from metpy.units import units
from metpy.calc import specific_humidity_from_dewpoint as td2q
from scipy.stats import gaussian_kde
from scipy.interpolate import interp1d
from regions import rinfo
from glade_utils import grid
from cmip6util import mods,emem,simu,year

# this script aggregates the histogram of daily temperature for a given region on interest

# index for location to make plot
iloc=[110,85] # SEA
# iloc=[135,200] # SWUS

fo1='historical'
yr1='1980-2000'

fo2='ssp370'
yr2='2080-2100'

fo=fo2

lse = ['jja'] # season (ann, djf, mam, jja, son)
# lse = ['ann','djf','mam','jja','son'] # season (ann, djf, mam, jja, son)

realm='atmos'
freq='day'
varn='mrsos'

for se in lse:
    # list of models
    lmd=mods(fo)

    odir='/project/amp/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl,fo,'mmm',varn)

    if not os.path.exists(odir):
        os.makedirs(odir)

    for imd in tqdm(range(len(lmd))):
        md=lmd[imd]

        # >95th and mean sm data
        idir1 = '/project/amp/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl1,fo1,md,varn)
        idir2 = '/project/amp/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl2,fo2,md,varn)
        [vn1, _] = pickle.load(open('%s/c%s_%s.%s.rg.pickle' % (idir1,varn,yr1,se), 'rb'))
        [vn2, _] = pickle.load(open('%s/c%s_%s.%s.rg.pickle' % (idir2,varn,yr2,se), 'rb'))
        ism1=vn1[:,iloc[0],iloc[1]]
        ism2=vn2[:,iloc[0],iloc[1]]
        
        if imd==0:
            esm=np.empty([len(lmd),len(ism1)])

        esm[imd,:]=ism2-ism1

    dsm=np.nanmean(esm,axis=0)

    pickle.dump([dsm,esm], open('%s/dpc%s_%s.%s.%g.%g.%s.pickle' % (odir,varn,yr1,yr2,iloc[0],iloc[1],se), 'wb'), protocol=5)	
