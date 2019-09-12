#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 11:16:59 2017

@author: svd
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy
import scipy.linalg

""" Some helper functions """

def gnoise(m,s,N):
    """
    generate N samples of Gaussian random noise with mean m and covariance s
    """
    dimcount=len(m)

    x=np.random.normal(size=(dimcount,N))
    x=np.matmul(scipy.linalg.sqrtm(s),x)

    for dimidx in range(0,dimcount):
        x[dimidx,:]=x[dimidx,:]+m[dimidx]

    return x

def logsig_fn(phi,X):
    """
    sigmoid function
    static nonlinearity from Rabinowitz et al 2011
    """
    a=phi[0]   # baseline
    b=phi[1]   # asymptote
    c=phi[2]   # inflection point
    d=phi[3]   # slope
    Y=a+b/(1+np.exp(-(X-c)/d))
    return(Y)

def mse(X1,X2,norm=True):
    """
    normalized mean-square error (ie, normalized to fall between 0 and 1, 
    respectively perfect to completely random)
    """
    
    #print(X1.shape)
    #print(X2.shape)
    E=np.var(X1-X2)
    # normalize by X2 power
    if norm:
        P=np.var(X2)
        E=E/P
    #print("E={0}".format(E))
    return E
    
""" Model fitting functions """

# delay line
def delay_line(X,maxlag=10,timeaxis=1,spaceaxis=0):
    
    Xout=X
    for ii in range(1,maxlag+1):
        Xout=np.concatenate((Xout,np.roll(X,ii,timeaxis)),axis=spaceaxis)
    return Xout

        
# sta function
def sta(X,Y,maxlag=10):
    
    Xdl=delay_line(X,maxlag)
    T=X.shape[1]
    mx=np.mean(Xdl,axis=1)
    xx=Xdl-np.repeat(np.transpose(np.matrix(mx)),T,axis=1)
    H0=np.mean(Y,axis=1)
    yy=Y-H0

    STA=np.matmul(Xdl,yy.T)/X.shape[1]/X.shape[1]
    STA=np.reshape(STA,[-1,maxlag+1],order='F')
    
    return (STA,H0)

# norm rc function
def norm_reverse_correlation(X,Y,maxlag=10):
    
    Xdl=delay_line(X,maxlag)
    H0=np.mean(Y,axis=1)
    yy=Y-H0
    STA=np.matmul(Xdl,yy.T)
    C=np.matmul(Xdl,Xdl.T)
    Cinv=np.linalg.inv(C)
    H=np.matmul(Cinv,STA)
    H=np.reshape(H,[-1,maxlag+1],order='F')
    
    return (H,H0)
    
# predict function
def predict(X,H):
    
    maxlag=H.shape[1]-1
    Xdl=delay_line(X,maxlag)
    Hdl=np.reshape(H,[1,-1],order='F')
    Ypred=np.matmul(Hdl,Xdl)
    
    return Ypred
    


def coordinate_descent(Xin,Y,maxlag=10,h0=None):
    """
    coordinate descent - step one parameter at a time
    """

    # add delay line to X matrix
    X=delay_line(Xin,maxlag)
    H0=np.mean(Y,axis=1)
    yy=Y-H0  # force output to have mean 0
    
    maxit=1000
    tolerance=0.0001
    step_init=0.1
    step_change=0.5
    step_min=1e-7
    verbose=True
    
    n_params=X.shape[0]
    
    if h0 is None:
        h0=np.zeros([1,n_params])
    
    n = 1   # step counter
    h = h0 # current phi
    h_save = h.copy()     # last updated phi
    ypred=np.matmul(h,X)
    s = mse(ypred,Y)   # current score
    s_new = np.zeros([n_params,2])     # Improvement of score over the previous step
    s_delta = np.inf     # Improvement of score over the previous step
    step_size = step_init;  # Starting step size.
    print("starting CD: n_params={0}, step size: {1:.6f} tolerance: {2:.6f}".format(n_params,step_size, tolerance))

    while (s_delta<0 or s_delta>tolerance) and n<maxit and step_size>step_min:
        for ii in range(0,n_params):
            for ss in [0,1]:
                h[:]=h_save[:]
                if ss==0:
                    h[0,ii]+=step_size
                else:
                    h[0,ii]-=step_size
                ypred=np.matmul(h,X)
                s_new[ii,ss] = mse(ypred,yy)   # current score
                
                
        x_opt=np.unravel_index(s_new.argmin(),(n_params,2))
        popt,sopt=x_opt
        s_delta=s-s_new[x_opt]
        
        if s_delta<0:
            step_size=step_size*step_change
            #if verbose is True:
            print("{0}: Backwards (delta={1}), adjusting step size to {2}".format(n,s_delta,step_size))
            
        elif s_delta<tolerance:
            if verbose is True:
                print("{0}: Error improvement too small (delta={1}). Iteration complete.".format(n,s_delta))
            
        elif sopt:
            h_save[0,popt]-=step_size
            if verbose is True:
                print("{0}: best step={1},{2} error={3}, delta={4}".format(n,popt,sopt,s_new[x_opt],s_delta))
        else:
            h_save[0,popt]+=step_size
            if verbose is True:
                print("{0}: best step={1},{2} error={3}, delta={4}".format(n,popt,sopt,s_new[x_opt],s_delta))
        
        h=h_save.copy()
        n+=1
        s=s_new[x_opt]
        
    # save final parameters back to model
    print("done CD: step size: {0:.6f} steps: {1}".format(step_size, n))
        
    print("Final MSE: {0}".format(s))
    H=np.reshape(h,[-1,maxlag+1],order='F')
    return(H,H0)


""" Plot routines """

def plot_lin_pred(X,Y,h,h0):
    
    p=np.matmul(h.T,X)+h0
    plt.plot(p,Y,'k.')
    


""" Data file IO routines """

def load_torc_data(filepath):
    """
    This function loads data from a TORC experiment, exported from BAPHY.
    """
   
    matdata = scipy.io.loadmat(filepath,chars_as_strings=True)
    
    # parse into relevant variables
    data={}
    
    # spectrogram of TORC stimuli. 15 frequency bins X 300 time samples X 30 different TORCs
    data['stim']=matdata['stim']
    data['FrequencyBins']=matdata['FrequencyBins'][0,:]
    data['stimFs']=matdata['stimFs'][0,0]
    try:
        data['StimCyclesPerSec']=np.float(matdata['StimCyclesPerSec'][0,0])
    except:
        data['StimCyclesPerSec']=4
        
    # response matrix. sampled at 1kHz. value of 1 means a spike occured
    # in a particular time bin. 0 means no spike. shape: [3000 time bins X 2
    # repetitions X 30 different TORCs]    
    data['resp']=matdata['resp']
    data['respFs']=matdata['respFs'][0,0]
    
    # each trial is (PreStimSilence + Duration + PostStimSilence) sec long
    data['Duration']=matdata['Duration'][0,0] # Duration of TORC sounds
    data['PreStimSilence']=matdata['PreStimSilence'][0,0]
    data['PostStimSilence']=matdata['PostStimSilence'][0,0]

    return data
    

def load_baphy_data(filepath,level=0):
    """
    This function loads data from a BAPHY .mat file located at 'filepath'. 
    It returns two dictionaries contining the file data and metadata,
    'data' and 'meta', respectively. 'data' contains:
        {'stim':stimulus,'resp':response raster,'pupil':pupil diameters}
    Note that if there is no pupil data in the BAPHY file, 'pup' will return 
    None. 'meta' contains:
        {'stimf':stimulus frequency,'respf':response frequency,'iso':isolation,
             'tags':stimulus tags,'tagidx':tag idx, 'ff':frequency channel bins,
             'prestim':prestim silence,'duration':stimulus duration,'poststim':
             poststim silence}
    """
    matdata=scipy.io.loadmat(filepath,chars_as_strings=True)
    s=matdata['data'][0][level]
    
    data={}
    data['resp']=s['resp_raster']
    data['stim']=s['stim']
    data['respFs']=s['respfs'][0][0]
    data['stimFs']=s['stimfs'][0][0]
    data['stimparam']=[str(''.join(letter)) for letter in s['fn_param']]
    data['isolation']=s['isolation']
    data['PreStimSilence']=s['tags'][0]['PreStimSilence'][0][0][0]
    data['PostStimSilence']=s['tags'][0]['PostStimSilence'][0][0][0]
    data['Duration']=s['tags'][0]['Duration'][0][0][0] 
    try:
        data['pupil']=s['pupil']
    except:
        data['pupil']=None
    return(data)

# define some global variables for the simulated data

# filter linear gain 
h1=np.array([[.5], [0]])
dimcount=len(h1)  # ie, two input channels
h0=np.zeros([1,1])

# parameters of static NL (if used)
sigmoid_parms=np.array([-1, 2.5, 0.5, 0.2])

# number of samples for estimation/testing
T=dimcount*100

def simulate_simple_data(correlated_inputs=False, output_nonlinearity=False, noise_amplitude=0.5,shifted_mean=False):

    if shifted_mean:
        # mean of input -- shifted for the "out of class" test set
        m=np.matrix([[3],[3]])
        if correlated_inputs:
            s=np.array([[0.4, 0.1], [0.1, 0.4]])
        else:
            s=np.array([[1.0,0],[0,1.0]])
    else:
        # mean of input
        m=np.zeros([dimcount,1])
        
        if correlated_inputs:
            # gaussian noise stimulus covariance matrix has non-zero off-diagonal terms
            s=np.array([[1.0, 0.7], [0.7, 1.0]])
        else:
            # gaussian noise stimulus covariance matrix has zero off-diagonal terms
            s=np.array([[1.0, 0], [0, 1.0]])
    
    # Generate the input and pass it through the linear filter based on above parameters
    x=gnoise(m,s,T)

    # linear filter
    y=np.matmul(h1.T,x)

    if output_nonlinearity:
        # pass output of filter through sigmoid (if specified)
        y=logsig_fn(sigmoid_parms,y)

    if noise_amplitude:
        # add noise (if specified)
        # gaussian additive noise
        y=y+gnoise(np.zeros([1,1]),np.matrix([[noise_amplitude]]),T)

    return x,y

