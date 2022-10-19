import os
import sys
import pickle
import numpy as np
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.stats import linregress
from tqdm import tqdm

varn='m2m'
lse = ['ann','jja'] # season (ann, djf, mam, jja, son)
# lse = ['jja','ann','djf','mam','son'] # season (ann, djf, mam, jja, son)
lpc = [1,5,50,95,99] # percentile (choose from lpc below)

for se in lse:
    print(se.upper())
    idir = '/project/amp/miyawaki/data/p004/hist_hotdays/era5/%s/%s' % (se,varn)
    odir = '/project/amp/miyawaki/plots/p004/hist_hotdays/era5/%s/%s' % (se,varn)

    if not os.path.exists(odir):
        os.makedirs(odir)

    c = 0
    clima={}
    for ipc in range(len(lpc)):
        pc = lpc[ipc]
        [mm2m, gr] = pickle.load(open('%s/clmean_m2m_%02d.%s.pickle' % (idir,pc,se), 'rb'))
        # repeat 0 deg lon info to 360 deg to prevent a blank line in contour
        gr['lon'] = np.append(gr['lon'].data,360)
        mm2m = np.append(mm2m, mm2m[:,0][:,None],axis=1)

        clima[str(pc)] = 1e-3*mm2m # convert MSE from J/kg to J/g

    [mlat,mlon] = np.meshgrid(gr['lat'], gr['lon'], indexing='ij')

    # plot skewness (ratio of hot to cold diff) in climatology
    ax = plt.axes(projection=ccrs.Robinson(central_longitude=240))
    vmin=-1
    vmax=1
    # transparent colormap
    colors = [(0.5,0.5,0.5,c) for c in np.linspace(0,1,100)]
    clf=ax.contourf(mlon, mlat, (clima['95']+clima['5']-2*clima['50'])/(clima['95']-clima['5']), np.arange(vmin,vmax+0.1,0.1),extend='both', vmax=vmax, vmin=vmin, transform=ccrs.PlateCarree(), cmap='RdBu_r')
    ax.coastlines()
    ax.set_title(r'%s ERA5 ($1950-2020$)' % (se.upper()))
    cb=plt.colorbar(clf,location='bottom')
    cb.set_label(r'$\frac{MSE^{95}_\mathrm{2\,m}+MSE^{5}_\mathrm{2\,m}-2MSE^{50}_\mathrm{2\,m}}{MSE^{95}_\mathrm{2\,m}-MSE^{5}_\mathrm{2\,m}}$ (unitless)')
    plt.savefig('%s/skewness_clima.%s.pdf' % (odir,se), format='pdf', dpi=300)
    plt.close()

    # plot climatological m2m
    for pc in tqdm(lpc):
        ax = plt.axes(projection=ccrs.Robinson(central_longitude=240))
        # vmax=np.max(slope[str(pc)])
        vmin=200
        vmax=370
        # clf=ax.contourf(mlon, mlat, clima[str(pc)], np.arange(vmin,vmax,5),extend='both', vmax=vmax, vmin=vmin, transform=ccrs.PlateCarree(), cmap='RdBu_r')
        clf=ax.contourf(mlon, mlat, clima[str(pc)], np.arange(vmin,vmax,5), vmax=vmax, vmin=vmin, transform=ccrs.PlateCarree(), cmap='RdBu_r')
        # ax.contour(mlon, mlat, clima[str(pc)], 273.15,colors='gray', transform=ccrs.PlateCarree())
        ax.coastlines()
        ax.set_title(r'%s ERA5 ($1950-2020$)' % (se.upper()))
        cb=plt.colorbar(clf,location='bottom')
        cb.set_label(r'Climatological $MSE^{%s}_\mathrm{2\,m}$ (J g$^{-1}$)' % pc)
        plt.savefig('%s/clima_m%02d.%s.pdf' % (odir,pc,se), format='pdf', dpi=300)
        plt.close()

    # plot ratios of hot to average day in climatology
    for pc in tqdm(lpc):
        if pc == 50:
            continue
        ax = plt.axes(projection=ccrs.Robinson(central_longitude=240))
        # transparent colormap
        if se=='ann':
            vmin=0.8
            vmax=1.2
            if pc>50:
                lvs=np.arange(1,vmax+0.01,0.01)
            else:
                lvs=np.arange(vmin,1.01,0.01)
        else:
            vmin=0.95
            vmax=1.05
            if pc>50:
                lvs=np.arange(1,vmax+1e-3,1e-3)
            else:
                lvs=np.arange(vmin,1.01,1e-3)
        colors = [(0.5,0.5,0.5,c) for c in np.linspace(0,1,100)]
        clf=ax.contourf(mlon, mlat, clima[str(pc)]/clima['50'], lvs,extend='both', vmax=vmax, vmin=vmin, transform=ccrs.PlateCarree(), cmap='RdBu_r')
        ax.coastlines()
        ax.set_title(r'%s ERA5 ($1950-2020$)' % (se.upper()))
        cb=plt.colorbar(clf,location='bottom')
        cb.set_label(r'$\frac{MSE^{%s}_\mathrm{2\,m}}{MSE^{50}_\mathrm{2\,m}}$ (unitless)' % pc)
        plt.savefig('%s/ratioM50_clima_m%02d.%s.pdf' % (odir,pc,se), format='pdf', dpi=300)
        plt.close()

    # plot diff of hot to average day in climatology
    for pc in tqdm(lpc):
        if pc == 50:
            continue
        ax = plt.axes(projection=ccrs.Robinson(central_longitude=240))
        # transparent colormap
        if se=='ann':
            vmin=-50
            vmax=50
            if pc>50:
                lvs=np.arange(0,vmax+5,5)
            else:
                lvs=np.arange(vmin,5,5)
        else:
            vmin=-40
            vmax=40
            if pc>50:
                lvs=np.arange(0,vmax+5,5)
            else:
                lvs=np.arange(vmin,5,5)
        colors = [(0.5,0.5,0.5,c) for c in np.linspace(0,1,100)]
        clf=ax.contourf(mlon, mlat, clima[str(pc)]-clima['50'], lvs,extend='both', vmax=vmax, vmin=vmin, transform=ccrs.PlateCarree(), cmap='RdBu_r')
        ax.coastlines()
        ax.set_title(r'%s ERA5 ($1950-2020$)' % (se.upper()))
        cb=plt.colorbar(clf,location='bottom')
        cb.set_label(r'$MSE^{%s}_\mathrm{2\,m}-MSE^{50}_\mathrm{2\,m}$ (J g$^{-1}$)' % pc)
        plt.savefig('%s/diffM50_clima_m%02d.%s.pdf' % (odir,pc,se), format='pdf', dpi=300)
        plt.close()

