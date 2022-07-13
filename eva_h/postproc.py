'''
	Translated in Python by Biman Chakraborty, April 2022.
	Originally written in Matlab by Thomas J. Aubry, June 2019.
	Department of Geography, University of Cambridge
    E-mail: ta460@cam.ac.uk
	Please cite the corresponding paper if you use this script
'''

#import some packages and define basic functions

import os
import numpy as np
from numpy.matlib import repmat
from scipy.interpolate import interp2d, RectBivariateSpline
import scipy.io as io
import netCDF4 as nc

def cosd(x):
    I = x/180.
    y = np.cos(I * np.pi)
    mask = (I == np.trunc(I)) & np.isfinite(I)
    y[mask] = 0
    return y

#This is where the job gets done...
def postproc(eva_h_dir,SO4mass,modelpara,mstar,R_reff,wl_req):


    # ==========================================================================
    # 1) Calculate global mean SAOD and area-weighted AOD at 525nm, and
    # aerosol effective radius
    # ==========================================================================

    totmass = np.sum(SO4mass,axis=1) #total mass of sulfate in the stratosphere
    gmsaod525_lin = modelpara.A * totmass # global mean SAOD at 525nm calculated
                                          # using the linear scaling

    gmsaod525 = gmsaod525_lin.copy()
    gmsaod525[totmass>mstar] = modelpara.A * (mstar**(1.0/3)) * totmass[totmass>mstar]**(2.0/3)

    # global mean SAOD at 525nm with 2/3 scaling applied for sulfate mass larger
    # than the critical mass mstar.

    waod = modelpara.A*SO4mass*repmat(np.reshape(gmsaod525/gmsaod525_lin,(gmsaod525.shape[0],1)),1, 8)
    
    # area-weighted AOD at 525nm in each box, calculated as the mass of sulfate
    # in each box multiplied by the SAOD-sulfate mass scaling factor, and
    # corrected by the ratio of the actual global mean SAOD at 525nm and the
    # obtained from a linear scaling. This correction insures that the sum of
    # area-weighted AOD in all boxes is equal to the global mean SAOD.

    gmreff = R_reff*totmass**(1.0/3)
    
    # Calculate global mean mass-weighted effective radius in um from the
    # scaling described in the companion paper.



    # ==========================================================================
    # 2) Calculate altitude and latitude dependent extinction at 525nm and
    # effective radius
    # ==========================================================================

    shape_func_mat = os.sep.join([eva_h_dir, 'shapefunctions.mat'])
    shapemat = io.loadmat(shape_func_mat) #load shape functions
    shapefunctions = shapemat['shapefunctions']
    
    # define latitude/altitude grid of the shape functions
    lat = np.arange(-87.5,88, 5)
    alt = np.arange(5, 40, 0.5)
 
    ext525 = np.ones((len(totmass),36,70))*np.nan #pre-allocate space for extinction at 525nm
    massdist = np.ones((len(totmass),36,70))*np.nan #pre-allocate space for sulfate mass
    for i in range(len(totmass)):
        # %At each timestep, calculate the extinction at 525nm as the sum, over the
        # %8 boxes, of the product of the area-weighted AOD in the box by the shape
        # %function of the same box (cf. companion paper for more details on these
        # %shape functions and how they were derived). The shape functions return
        # %extinction in /km
        ext525[i,:,:] = np.squeeze(np.nansum(np.transpose(np.tile(np.reshape(waod[i,:],(8,1)),(36, 1, 70)),axes=(0,2,1))*shapefunctions,axis=2))
    
        # Assume that spatial distribution of sulfate mass is the same as that
        # of extinction
        massdist[i,:,:] = np.squeeze(np.nansum(np.transpose(np.tile(np.reshape(SO4mass[i,:], (8,1)), (36, 1, 70)), axes=(0,2,1))*shapefunctions,axis=2))



    # Calculate weight (cos(latitude)*mass) to calculate global mean
    # mass-weighted average
    latweight = np.transpose(np.tile(np.reshape(cosd(lat),(lat.shape[0],1)),( 70, 1, len(totmass))), axes=(2,1,0))
    latweight = latweight*massdist/np.transpose(np.tile(np.reshape(np.sum(np.sum(latweight*massdist,axis=1),axis=1), (latweight.shape[0],1)), (massdist.shape[1],1,massdist.shape[2])),axes=(1,0,2))

    # Assume that local effective radius follows the same spatial distribution
    # as sulfate mass, raised to power 1/3.
    reff = massdist**(1.0/3)


    # Re-scale the effective radius so that the global mean average follows the
    # scaling introduced in the paper, with a minimum value of 0.1um for local
    # effective radius
    gmreff_scale = np.squeeze(np.nansum(np.nansum(reff*latweight,axis=1),axis=1))
    reff = 0.101+reff*np.transpose(np.tile(np.reshape((gmreff-0.101)/gmreff_scale,(gmreff_scale.shape[0],1)),(36,1, 70)), axes=(1,0,2))



    # ==========================================================================
    # 3) Calculate time, altitude, latitude and wavelength dependent extinction,
    # stratospheric aerosol optical depth, single scattering albedo and
    # scattering asymmetry factor
    # ==========================================================================

    #Read Mie look-up tables:
    lookup_nc = os.sep.join([eva_h_dir, 'eva_Mie_lookuptables.nc'])
    ncid = nc.Dataset(lookup_nc)

    # a) Read effective radius and wavelength grid, and reformat them for
    # use as input for the 2D interpolation function later
    reffgrid_mie = ncid['reff'][:]
    wlgrid_mie = ncid['wl'][:]
    #[Xwl,Yreff] = np.meshgrid(wlgrid_mie,reffgrid_mie);
    
    # b) Read calculated parameters, which are 2D array, with one dimension for
    # effective radius and the other one for wavelength.
    
    extrat_mie = ncid['extrat'][:] #ratio of extinction to extinction at 550nm (EXT)
    ssa_mie = ncid['ssa'][:] #single scattering albedo (SSA)
    asy_mie = ncid['asy'][:] #scattering asymmetry factor (ASY)
    
    # preallocate memory for calculating EXT, SSA and ASY
    ext=np.ones((ext525.shape[0],ext525.shape[1],ext525.shape[2],len(wl_req)))*np.nan
    ssa=np.ones(ext.shape)*np.nan
    asy=np.ones(ext.shape)*np.nan

    # c) Loop through latitude, altitude and wavelength to calculate them. All
    # calculations are done by linearly interpolating the Mie lookup tables at
    # the requested wavelength and the effective radius outputted by the model.
    extint = RectBivariateSpline(wlgrid_mie,reffgrid_mie,extrat_mie, kx=1, ky=1)
    ssaint = RectBivariateSpline(wlgrid_mie,reffgrid_mie,ssa_mie, kx=1, ky=1)
    asyint = RectBivariateSpline(wlgrid_mie,reffgrid_mie,asy_mie, kx=1, ky=1)
    
    for ilat in range(len(lat)):
        for ialt in range(len(alt)):
            for iwl in range(len(wl_req)):
                # ignore points in time where the extinction at 525nm or
                # effective radius are NaNs
                mask = (~np.isnan(np.squeeze(ext525[:,ilat,ialt]))) & (~ np.isnan(np.squeeze(reff[:,ilat,ialt])))
                # Calculate the raio of extinction at desired wavelength to
                # extinction at 525nm
                temp = np.minimum(reff[mask,ilat,ialt],1.29)               
                ratio525 = np.squeeze(extint.ev(wl_req[iwl],temp))/np.squeeze(extint.ev(0.525, temp))
                # multiple above ratio by extinction at 525nm
                ext[mask,ilat,ialt,iwl] = ext525[mask,ilat,ialt] * ratio525
                # calculate SSA and ASY
                ssa[mask,ilat,ialt,iwl] = np.squeeze(ssaint.ev(wl_req[iwl], temp))
                asy[mask,ilat,ialt,iwl] = np.squeeze(asyint.ev(wl_req[iwl], temp))
            
            
    ssa = np.minimum(ssa, 1.0)

    # Calculate stratospheric aerosol optical depth. These are simply the sum of
    # extinction along vertical dimension, multiplied by 0.5 because the
    # vertical grid is regurlarly spaced by 0.5km. All tropospheric values are
    # NaNs in the shape functions and thus in ext.
    saod = np.nansum(ext,axis=2)*0.5

    # Calculate weights (cosinus(latitude)) for calculating global mean 
    latweight = np.transpose(np.tile(np.reshape(cosd(lat),(lat.shape[0],1)),(len(wl_req), 1, len(totmass))),axes=(2,1,0))
    latweight = latweight/np.squeeze(np.sum(latweight[0,:,0],axis=0))
    # Calculate global mean SAOD
    gmsaod = np.nansum(saod*latweight,axis=1)


    return gmsaod, saod, reff, ext, ssa, asy, lat, alt
