'''
	Translated in Python by Biman Chakraborty, April 2022.
	Originally written in Matlab by Thomas J. Aubry, June 2019.
	Department of Geography, University of Cambridge
   E-mail: ta460@cam.ac.uk
	Please cite the corresponding paper if you use this script


Note: the structure and indices of model boxes to which we refer in this
script are defined in the companion paper. Boxes are indexed from 1 to 8,
from South to North and from top to bottom. 

Given the boundaries of the boxes of our model (defined by h1lim, h2lim
and latlim) and a path to an excel file containing a list of volcanic SO2
emission parameters, this function returns the mass of sulfur injected in
each box of the model and the time of injection.
'''

#Import a few packages and define basic functions

import os
import numpy as np
from numpy.matlib import repmat
import scipy.io as io
from scipy.integrate import quad
import pandas as pd

def cosd(x):
    I = x/180.
    y = np.cos(I * np.pi)
    mask = (I == np.trunc(I)) & np.isfinite(I)
    y[mask] = 0
    return y

#This is where things get done...
def so2injection_8boxes(eva_h_dir,h1lim,h2lim,latlim,user_params):
    # injec will be a N x 8 matrix containing the mass of sulfur to be injected
    # in each box in Tg S (N=number of eruptive events).
    # timelist will contain the time of injection, in months after Jan 1st 1979
    # filepath must be a relative path to a .xlsx file where column and units
    # are the same as the two example files provided (singleinjection.xlsx and
    # volSO2_Carn2016.xlsx)

# ==========================================================================
# Load data for tropopause height from NCEP/NCAR reanalysis
# ==========================================================================

    tropo_mat = os.sep.join([eva_h_dir, 'ncep_tropo.mat'])
    tropo = io.loadmat(tropo_mat) # zonal mean tropopause height for 1979-2016 
    tropoheight = tropo['tropoheight']
    
    # Define and time corresponding to NCEP tropopause
    lat = np.arange(-90,92.5, 2.5)
    tropotime = np.arange(0.5,455.5,1) #time in month since 1979
    # Define average tropopause height in latitudinal band of the model
    ntl = np.argmin(np.abs(lat-latlim))
    stl = np.argmin(np.abs(lat+latlim))
    climtropoheight=np.ones((tropoheight.shape[1],3))*np.nan
    climtropoheight[:,0] = np.sum(tropoheight[:(stl-1),:].transpose() * (repmat(cosd(lat[:(stl-1)]), tropoheight.shape[1], 1)/np.sum(cosd(lat[:(stl-1)]))),axis=1)
    climtropoheight[:,1] = np.sum(tropoheight[(stl-1):ntl,:].transpose() * (repmat(cosd(lat[(stl-1):ntl]), tropoheight.shape[1], 1)/np.sum(cosd(lat[(stl-1):ntl]))),axis=1)
    climtropoheight[:,2] = np.sum(tropoheight[ntl:,:].transpose() * (repmat(cosd(lat[ntl:]), tropoheight.shape[1],1)/np.sum(cosd(lat[ntl:]))),axis=1)

    # ==========================================================================
    # Load SO2 injection parameters
    # ==========================================================================
    
    erulat = user_params['lat']
    erudate = user_params['month']
    timelist = erudate
    so2mass = user_params['so2_mass']
    # convert mass from Tg to kt:
    so2mass *= 1e3
    eruheight = user_params['so2_height']
    erutropo = user_params['tropo_height']
    eruhstar = eruheight / erutropo
    # convert mass from kt so2 to tg of S:
    so2mass = (10**(-3)) * (0.50052) * so2mass

    # ==========================================================================
    # Main loop
    # ==========================================================================
    
    # Pre-allocate memory for list of mass injected in each box
    injec=np.zeros((len(erudate),8))

    # Loop through all eruptions
    for i in range(len(erudate)):

        # ==========================================================================
        # Define parameters and distribution function for SO2 injection #i
        # ==========================================================================  
        h0 = eruheight[i] #height
        l0 = erulat[i] #latitude
        dh = 1.2  # vertical thickness of the eruption cloud, in km
        dl = 7  # latitudinal extent of the eruption cloud, in degree
        
        def so2latdist(l):
            return np.exp(-((l-l0)/dl)**2) #vertical distribution function (gaussian)
        
        def so2hgtdist(h):
            return np.exp(-((h-h0)/dh)**2) #latitudinal distribution function  (gaussian)
        
        # Find height of tropopause in latitudinal band
        ert = np.argmin(abs(erudate[i] - tropotime))
        SHtrop = climtropoheight[ert,0]
        Ttrop=climtropoheight[ert,1]
        NHtrop=climtropoheight[ert,2]

        # For the band where the eruption occur, use local tropopause height at
        # volcano location
        if erulat[i] < -latlim:
            SHtrop = erutropo[i]
        elif erulat[i] > latlim:
            NHtrop = erutropo[i]
        else:
            Ttrop=erutropo[i];   


        
        #==========================================================================
        #For each box, calculate the mass injected by eruption #i
        #========================================================================== 
        
    

        # Box 1

        # 1) set integration limits for the box

        lmin = -np.inf 
        lmax = -latlim #latitudinal limits; box 1 comprise latitudes south of -latlim
        hmin = h2lim 
        hmax = h0+100*dh #vertical limits; box one is above h2lim

        # 2) Calculate injected mass in this box by multiplying the mass injected by
        # the eruption by the product of the distribution functions integrated over the box
        # limit, and normalized by their quads over the entire domain.
        # Essentially, this is calculating the fraction of mass injected in a box
        # and multiplying by the mass injected by the eruption.
        injec[i,0] = so2mass[i] * (quad(so2latdist,lmin,lmax, epsabs=1.0e-10)[0] *
                                   quad(so2hgtdist,hmin,hmax,epsabs=1.0e-10)[0]) / (quad(so2hgtdist,h0-100*dh,h0+100*dh, epsabs=1.0e-10)[0]*
                                                                      quad(so2latdist,l0-100*dl,l0+100*dl, epsabs=1.0e-10)[0])


        # Box 2
        lmin = -latlim 
        lmax = latlim
        hmin = h2lim 
        hmax = h0+100*dh
        injec[i,1] = so2mass[i] * (quad(so2latdist,lmin,lmax, epsabs=1.0e-10)[0] * 
                                   quad(so2hgtdist,hmin,hmax, epsabs=1.0e-10)[0])/(quad(so2hgtdist,h0-100*dh,h0+100*dh, epsabs=1.0e-10)[0]*
                                                                    quad(so2latdist,l0-100*dl,l0+100*dl, epsabs=1.0e-10)[0])

        # Box 3
        lmin = latlim 
        lmax = l0+100*dl
        hmin = h2lim 
        hmax = h0+100*dh
        injec[i,2] = so2mass[i] * (quad(so2latdist,lmin,lmax, epsabs=1.0e-10)[0] * 
                                   quad(so2hgtdist,hmin,hmax, epsabs=1.0e-10)[0])/(quad(so2hgtdist,h0-100*dh,h0+100*dh, epsabs=1.0e-10)[0]*
                                                                    quad(so2latdist,l0-100*dl,l0+100*dl, epsabs=1.0e-10)[0])


        # Box 4
        lmin = l0-100*dl 
        lmax = -latlim
        hmin = Ttrop 
        hmax = h2lim # the bottom of boxes 4-6 is the tropical tropopause height
        injec[i,3] = so2mass[i] * (quad(so2latdist,lmin,lmax, epsabs=1.0e-10)[0] * 
                                   quad(so2hgtdist,hmin,hmax, epsabs=1.0e-10)[0])/(quad(so2hgtdist,h0-100*dh,h0+100*dh, epsabs=1.0e-10)[0]*
                                                                    quad(so2latdist,l0-100*dl,l0+100*dl, epsabs=1.0e-10)[0])

        # Box 5
        lmin = -latlim 
        lmax = +latlim
        hmin = Ttrop 
        hmax=h2lim
        injec[i,4] = so2mass[i] * (quad(so2latdist,lmin,lmax, epsabs=1.0e-10)[0] * 
                                   quad(so2hgtdist,hmin,hmax, epsabs=1.0e-10)[0])/(quad(so2hgtdist,h0-100*dh,h0+100*dh, epsabs=1.0e-10)[0]*
                                                                    quad(so2latdist,l0-100*dl,l0+100*dl, epsabs=1.0e-10)[0])

        # Box 6
        lmin = latlim  
        lmax = l0+100*dl
        hmin = Ttrop 
        hmax = h2lim
        injec[i,5] = so2mass[i] * (quad(so2latdist,lmin,lmax, epsabs=1.0e-10)[0] * 
                                   quad(so2hgtdist,hmin,hmax, epsabs=1.0e-10)[0])/(quad(so2hgtdist,h0-100*dh,h0+100*dh, epsabs=1.0e-10)[0]*
                                                                    quad(so2latdist,l0-100*dl,l0+100*dl, epsabs=1.0e-10)[0])

        # Box 7
        lmin = -l0-100*dl 
        lmax = -latlim
        hmin = SHtrop 
        hmax = Ttrop #the bottom of box 7 is the SH tropopause height
        injec[i,6] = so2mass[i] * (quad(so2latdist,lmin,lmax, epsabs=1.0e-10)[0] * 
                                   quad(so2hgtdist,hmin,hmax, epsabs=1.0e-10)[0])/(quad(so2hgtdist,h0-100*dh,h0+100*dh, epsabs=1.0e-10)[0]*
                                                                    quad(so2latdist,l0-100*dl,l0+100*dl, epsabs=1.0e-10)[0])


        # Box 8
        lmin = latlim 
        lmax = l0+100*dl
        hmin = NHtrop 
        hmax = Ttrop  #the bottom of box 8 is the NH tropopause height
        injec[i,7] = so2mass[i] * (quad(so2latdist,lmin,lmax, epsabs=1.0e-10)[0] * 
                                   quad(so2hgtdist,hmin,hmax, epsabs=1.0e-10)[0])/(quad(so2hgtdist,h0-100*dh,h0+100*dh, epsabs=1.0e-10)[0]*
                                                                    quad(so2latdist,l0-100*dl,l0+100*dl, epsabs=1.0e-10)[0])


    injec = injec.transpose()

    return injec, timelist
