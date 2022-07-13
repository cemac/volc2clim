'''
	Translated in Python by Biman Chakraborty, April 2022.
	Originally written in Matlab by Thomas J. Aubry, June 2019.
	Department of Geography, University of Cambridge
	E-mail: ta460@cam.ac.uk
	Please cite the corresponding paper if you use this script


%Note: the structure and indices of model boxes to which we refer in this
%script are defined in the companion paper. Boxes are indexed from 1 to 8,
%from South to North and from top to bottom. Default model parameter 
%values proposed in this script enable to best reproduce observed (GloSSAC)
%Aerosol Optical Depth model boxes given observed SO2 injections by
%explosive volcanic eruptions (Carn et al. 2016 inventory).
'''


# Import essential libraries
import numpy as np

class ModelParams:
    # %==========================================================================
    # %Vertical and latitudinal boundaries of model boxes
    # %==========================================================================
    h1lim=16 #%in km a.s.l., upper boundary of boxes 7-8
    h2lim=20 #%in km a.s.l., upper boundary of boxes 3-6
    latlim=25 #%in degree; tropical boxes latitudinal boundaries are +/- latlim

    # %Note: all model parameters have been calibrated with above box boundaries.
    # %If you wish to change these boundaries, we strongly recommend that you
    # %recalibrate model parameters and shape functions.

    # %==========================================================================
    # %SAOD - sulfate burden scaling factor in (Tg S)^(-1)
    # %==========================================================================

    A = 0.0187 

    # %==========================================================================
    # %SULFATE PRODUCTION TIMESCALES, in month, from boxes 1 to 8
    # %==========================================================================

    tauprod = np.ones(8)*8 

    '''
    We recommend to use the same production timescale in all boxes. However,
    production timescales can be set arbitrarly for each box. For example, for
    a production timescale of 8 months in middle stratospheric boxes (#1-3), 5
    months in the lower stratospheric boxes (# 4-6), and 2 months in lowermost
    stratospheric boxes (# 7-8), uncomment the line below:
                          
    '''
    #tauprod = np.array([8,8, 8,5,5,5,2,2])   #Uncomment if needed
    

    # %==========================================================================
    # %SULFATE LOSS TIMESCALES, in month, from boxes 1 to 8 
    # %==========================================================================

    tauloss = np.array([2.3,9.1, 2.3, 2.6, 16.1, 2.6, 3.6, 3.6])

    '''
    %We recommend to use height-dependent and latitude-dependent (i.e., tropics
    %vs. extratropics) loss timescales, as specified in the line above.
    %However, loss timescales can be set arbitrarly for each box. For example,
    %for a loss timescale of 3 month in all boxes, uncomment the line below:
    '''
    #tauloss=[3;3;3;3;3;3;3;3];
  
    # %==========================================================================
    # %MIXING TIMESCALES
    # %==========================================================================
    '''
    %Mixing timescales are defined by three parameters:
    %1) The average value of mixing timescale taumixm
    %2) The amplitude of the seasonal cycle of mixing amix
    %3) The month of the year when mixing peaks smix (1=JAN, 12=DEC)
    % The mixing timescale will then be calculated by the model at each
    % timestep as:
    % taumix=taumixm.*(1+amix.*cos((t-smix)*pi/6))
    %with t the time in months after JAN XXXX
    %Each of the 3 parameters taumixm, amix and smix has 6 values corresponding
    %to box pairs 1-2, 2-3, 4-5, 5-6, 7-5 and 8-5
    '''

    taumixm = np.hstack((10.2*np.ones(4),np.array([np.inf, np.inf])))

    '''
    %We recommend to use the same mixing timescale for all box pairs, and to
    %turn off non-horizontal mixing between box 5 (lower tropical stratosphere)
    %and boxes 7-8 (lowermost tropical stratosphere), which corresponds to
    %setting mixing timescales to infinity. Similarly to previous examples for
    %sulfate and production timescales, you can arbitrarly set mixing
    %timescales.
    '''
    amix = np.zeros(6)
    smix = np.zeros(6)
    
    '''
    %Implementing a seasonal cycle for mixing does not significantly improve
    %model performance, as defined in our paper. We thus do not set the
    %amplitude of the seasonal cycle to 0. As an example, if you wish to use
    %a seasonal cycle with a 20% seasonal variation in mixing timescale, with
    %mixing in the southern hemisphere peaking in July mixing timescale, 
    %with mixing in the southern hemisphere peaking in July and in the northern
    %hemisphere peaking in January, uncomment the two lines below:
    '''
    
    # amix=np.array([0.2,0.2,0.2,0.2,0.2,0.2])
    # smix=np.array([7,1,7,1,7,1]);
    
    
    # %==========================================================================
    # %ONE-WAY MIXING TIMESCALES
    # %==========================================================================
    '''
    %These timescales are defined exactly in the same manner as
    %mixing timescales above. They correspond to a flux of sulfate from
    %tropical to extra-tropical boxes, with the flux being proportional to the
    %mass of sulfate in the tropical box.
    '''
    
    tauowmm = np.ones(6)*np.inf
    
    # %We recommend to turn off one-way mixing (owm) in the model by setting the
    # %average value of one-way mixing timescales to infinity as above
    
    aowm = np.zeros(6) # seasonal cycle amplitude for one-way mixing
    sowm = np.zeros(6) # peak mixing month for one-way mixing
    

    
    
    
    # %==========================================================================
    # %BACKGROUND SULFATE INJECTION, in Tg S/month, from boxes 1 to 8
    # %==========================================================================
    # %These correspond to stratospheric sulfate sources other than explosive
    # %volcanic injections
    
    
    backinj=np.array([0.0021, 0.0116, 0.0035, 0.0003, 0.0001, 0.0004, 0.0023, 0.0032])
    
    
    # %==========================================================================
    # %CRITICAL SULFATE MASS ABOVE WHICH TO APPLY 2/3 SAOD-MASS SCALING, in Tg S
    # %==========================================================================
    
    
    mstar = 10
    
    
    # %==========================================================================
    # %PREFACTOR FOR EFFECTIVE RADIUS - SULFATE MASS SCALING, in um/(Tg S)^(1/3)
    # %==========================================================================
    R_reff = 0.26 


