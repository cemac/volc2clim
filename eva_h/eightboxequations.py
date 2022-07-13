'''
 	Translated in Python by Biman Chakraborty, April 2022.
 	Originally written in Matlab by Thomas J. Aubry, June 2019.
 	Department of Geography, University of Cambridge
    E-mail: ta460@cam.ac.uk
 	Please cite the corresponding paper if you use this script
'''

'''
This functions calculate the time derivative of the mass of sulfate in
each of the 8 boxes of the model (dydt) given the mass of sulfate y at the
time t, the volcanic SO2 injections (inmass and intime),and the model
parameters (coef and backinj)
'''

import numpy as np
from numpy.matlib import repmat

def eightboxequations(t,y,inmass,intime,coef,backinj):

    '''
    t is the time (real number) in month after January 1st of a user-chosen
    year
    dydt is the 8x1 vector containing the time derivative of the sulfate mass 
    in each box (in Tg S/month)
    y is the 8x1 vector containing the sulfate mass in each box (in Tg S)
    inmass is a 8xNeru matrix containing the SO2 mass injected in the 8 boxes by
    the Neru eruptions (in Tg S)
    intime is a 1xNeru matrix containing the corresponding times of injections
    (same unit as t)
    coef is a 53x1 vector containing values for all model parameters (cf
    parameterfile.m for units)
    backinj is a 8x1 vector containing background injections in each box (in
    Tg S/month)
    '''

    # ==========================================================================
    # 1) "unwrap" vector containing model parameters
    # ==========================================================================
    # Separate model parameters into different, more explicit variables. See
    # parameterfile.m for details on each parameters and how they were combined
    # into a single vector.

    A = coef.A              # SAOD - sulfate burden scaling factor
    tauprod = coef.tauprod  # production timescales
    tauloss = coef.tauloss  # loss timescales
    taumixm = coef.taumixm  # average value of mixing timescales
    amix = coef.amix        # amplitude of mixing seasonal cycle
    smix = coef.smix        # peak mixing season
    tauowmm = coef.tauowmm  # average value of one-way mixing (OWM) timescales
    aowm = coef.aowm        # OWM seasonal cycle amplitude
    sowm =coef.sowm         # OWM peak mixing season

    # coef=[A;tauprod;tauloss;taumixm;amix;smix;tauowmm;aowm;sowm;backinj];

    # Calculate value of mixing timescales given the month of the year and
    # parameters defining seasonal cycles
    
    taumix = taumixm * (1+amix * np.cos((t-smix)*np.pi/6))
    tauowm = tauowmm * (1+aowm * np.cos((t-sowm)*np.pi/6))

    #  ==========================================================================
    #  2) Calculate the time derivative of sulfate mass
    #  ==========================================================================

    # This time derivative is calculated as dydt=C * y+ production + background
    # The matrix C and term C*y encompasse all transport terms
    # The term production correspond to new sulfate producted from SO2
    # injections
    # The term background correspond to background sulfate injections


    # ==========================================================================
    # 2.a) Build the matrix C
    # ==========================================================================
    
    # Initiate the matrix with all terms being 0. We will specify non-zero terms
    # hereafter.

    C = np.zeros((8,8))

    # Non zero coefficient are specified row by row, i.e. box by box. Detailed
    #%explainations are provided for select examples

    # BOX 1
    i = 0  #number of the matrix row corresponding to box number

    C[i,0] = -(1/tauloss[i])-(1/taumix[0])
    
    # All boxes have a loss term equal to their mass divided by the loss
    # timescale of the box, so that C(i,i) have a term -(1/tauloss(i)) as in
    # line above

    C[i,1] =  (1/tauowm[0])+(1/taumix[0]) 

    # Flux related to mixing is related to mass difference between two boxes. In
    # the case of box 1, mixing result in a mass flux (y(2)-y(1))/taumix(1)
    # explaining terms -(1/taumix(1)) in C(1,1) and +(1/taumix(1)) in C(1,2).

    # BOX 2
    i = 1
    C[i,0] =  1/taumix[0]
    C[i,1] = - (1/tauloss[i])-(1/taumix[0]+1/taumix[1]+1/tauowm[0]+1/tauowm[1])
     
    # In addition to mixing, one-way mixing terms transport mass from tropical
    # to extratropical box, with the flux being proportional to the mass of the
    # tropical box. Thus, box 2, which is tropical, lose a flux -y(2)/tauowm(1) to
    # box 1 and y(2)/tauowm(2) to box 3. This explains terms
    # -1/tauowm(1)-1/tauowm(2) for C(2,2) and, for example, the term
    # +(1/tauowm(1)) for C(1,2)

    C[i,2] =  1/taumix[1]

    # BOX 3
    i = 2
    C[i,1] = 1/taumix[1]+1/tauowm[1]  
    C[i,2] = - (1/tauloss[i])-1/taumix[1]

    # BOX 4
    i = 3
    C[i,0] = 1/tauloss[0]
    
    # The mass of aerosol lost by a box by settling (loss flux) correspond to a
    # mass gain for the model box immediatly below. Thus, the term -1/tauloss(1)
    # for C(1,1) correspond to a term +1/tauloss(1) for C(4,1) as box 4 is below
    # box 1.

    C[i,3] =- (1/tauloss[i])-1/taumix[2]
    C[i,4] = 1/taumix[2]+1/tauowm[2]

    # BOX 5
    i = 4
    C[i,1] = 1/tauloss[1]
    C[i,3] = 1/taumix[2]
    C[i,4] = -(1/tauloss[i])-(np.sum(1/taumix[2:6])+np.sum(1/tauowm[2:6]))
    
    # Mixing fluxes are only between boxes that are neighbour and at the same
    # altitude, except for box 5 (tropical lower stratosphere) for which we
    # allow mixing with boxes 7 and 8 (lowermost extratropical stratosphere.
    # This explains, for example, the terms -1/taumix(5) in C(5,5) and
    # +1/taumix(5) in C(5,7)
    
    C[i,5] = 1/taumix[3]
    C[i,6] = 1/taumix[4]
    C[i,7] = 1/taumix[5]

    # BOX 6
    i = 5
    C[i,2] = 1/tauloss[2]
    C[i,4] = 1/taumix[3] + 1/tauowm[3]
    C[i,5] = -(1/tauloss[i])-1/taumix[3]

    # BOX 7
    i = 6 

    C[i,3] = 1/tauloss[3]
    C[i,4] = 1/taumix[4] + 1/tauowm[4]
    C[i,6] = -(1/tauloss[i])-1/taumix[4]

    # BOX 8
    i = 7
    C[i,5] = 1/tauloss[5]
    C[i,4] = 1/taumix[5]+1/tauowm[5]
    C[i,7] = -(1/tauloss[i])-1/taumix[5]



    # ==========================================================================
    # 2.b) Calculate the mass of SO2 in each box
    # ==========================================================================

    # filter out all eruptions which occured after the current timestep as these
    # do not matter to calculate the mass of SO2 at current timestep.

    mask = (intime<=t)
    inmassint = inmass[:,mask]
    intimeint = intime[mask]

    # if no eruption has occured yet, the SO2 mass in all boxes is 0
    if sum(mask) == 0:
        so2mass = 0
    else:
        #  Else, the SO2 mass is calculated by assuming that the mass of SO2
        #  declines exponentially after each eruption, with an e-folding time equal
        #  to the production timescale for each box
        
        so2mass = np.sum(inmassint*np.exp(-repmat(t-intimeint,8, 1)/repmat(np.reshape(tauprod, (tauprod.shape[0],1)),1, inmassint.shape[1])),axis=1)

    '''
    Note that there is no SO2 transport in our model. Some of the transport
    that would occur is accounted for by the latitudinal distribution of the
    mass of SO2 injected by an eruption (cf. so2injection_8boxes.m and
    companion paper).
    '''

    # ==========================================================================
    # 2.c) Calculate the time derivative of sulfate mass by summing the 3
    # components
    # ==========================================================================

    
    dydt = backinj+np.matmul(C,y)+so2mass/tauprod
    #  Background injections backinj are directly specified in Tg S/ month
    #  Sulfate production from volcanic SO2 is simply the SO2 mass calculated in
    #  2.b divided by sulfate production timescales, so2mass./tauprod
    #  Transport terms are the only ones dependent on sulfate mass at current
    #  timestep, and are the product of the matrix C calculated in 2.a with the
    #  mass of sulfate in the 8 boxes.

    return dydt
