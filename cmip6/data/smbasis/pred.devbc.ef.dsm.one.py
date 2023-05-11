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

fo='historical'
yr='1980-2000'

# fo='ssp370'
# yr='2080-2100'

lse = ['jja'] # season (ann, djf, mam, jja, son)
# lse = ['ann','djf','mam','jja','son'] # season (ann, djf, mam, jja, son)

realm='atmos'
freq='day'
varn1='ef' # y axis var
varn2='dmrsos'# x axis var
varn='%s+%s'%(varn1,varn2)

for se in lse:
    # list of models
    lmd=mods(fo)

    for imd in tqdm(range(len(lmd))):
        md=lmd[imd]

        idir='/project/amp/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl,fo,md,varn)
        idirm='/project/amp/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl,fo,'mmm',varn)
        odir='/project/amp/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl,fo,md,varn1)

        # load budyko
        if cl=='his':
            fn = '%s/b%s_%s.%g.%g.%s.dev.pickle' % (idir,varn,yr,iloc[0],iloc[1],se)
            [ef,arr2] = pickle.load(open(fn,'rb'))
            # extrapolate ef
            fint=interp1d(arr2[~np.isnan(ef)],ef[~np.isnan(ef)],bounds_error=False,fill_value='extrapolate')
            ef=fint(arr2)
        elif cl=='fut':
            idir0='/project/amp/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,'his','historical',md,varn)
            fn0 = '%s/b%s_%s.%g.%g.%s.dev.pickle' % (idir0,varn,'1980-2000',iloc[0],iloc[1],se)
            [ef0,arr2] = pickle.load(open(fn0,'rb'))
            # load change in bc
            idir1='/project/amp/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,'fut-his',fo,'mmm',varn)
            [delef,_]=pickle.load(open('%s/db%s_%s.%s.%g.%g.%s.dev.pickle' % (idir1,varn,'1980-2000',yr,iloc[0],iloc[1],se), 'rb'))
            # extrapolate ef0
            fint=interp1d(arr2[~np.isnan(ef0)],ef0[~np.isnan(ef0)],bounds_error=False,fill_value='extrapolate')
            ef0=fint(arr2)
            ef=ef0+delef

        # >95th and mean sm data
        idir = '/project/amp/miyawaki/data/p004/cmip6/%s/%s/%s/%s/%s' % (se,cl,fo,'mmm',varn2)
        l = pickle.load(open('%s/pcm%s_%s.%g.%g.%s.dev.pickle' % (idir,varn2,yr,iloc[0],iloc[1],se), 'rb'))
        fint=interp1d(arr2,ef)
        pef=fint(l)

        pickle.dump(pef, open('%s/pc.devbc%s_%s.%g.%g.%s.dev.pickle' % (odir,varn1,yr,iloc[0],iloc[1],se), 'wb'), protocol=5)	
