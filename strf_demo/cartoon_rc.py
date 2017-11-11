# -*- coding: utf-8 -*-
"""
simple_rc_demo.py

author: SVD

Demonstrate basic methodologies for estimation of encoding models using a "toy",
two-dimensional input space

Input is Gaussian white noise, which can contain correlations between channels,
mimicking the correlations that occur in natural sounds. (set CORR_INPUTS=True)

The output can pass through a static nonlinearity, illustrating limitations of
a completely linear model, especially in generalizing to stimuli outside of the
space used for fitting. (set NONLIN=True)

"""


# load relevant libraries analysis and plotting
import numpy as np
import matplotlib.pyplot as plt
import strflib

# define filter
h1=np.array([[.5], [0]])
dimcount=h1.shape[0]
h0=np.zeros([1,1])

CORR_INPUTS=True   # should input channels be correlated?
NONLIN=True   # static nonlinearity at output?

# parameters of static NL (if used)
sigmoid_parms=np.array([-1, 2, 0.75, 0.08])

if CORR_INPUTS:
    # gaussian noise stimulus covariance matrix has non-zero off-diagonal terms
    s=np.array([[1.0, 0.7], [0.7, 1.0]])
    sout=np.array([[0.2, 0.1], [0.1, 0.2]])
else:
    # gaussian noise stimulus covariance matrix has zero off-diagonal terms
    s=np.array([[1.0, 0], [0, 1.0]])
    sout=np.array([[1.0,0],[0,1.0]])
    
# mean of output -- shifted for the "out of class" test set
m=np.zeros([dimcount,1])
mout=np.matrix([[2],[2]])

# gaussian additive noise
noiseamp=0.05

# number of samples for estimation/testing
T=dimcount*100

# generate inputs
xfit=strflib.gnoise(m,s,T)
xval=strflib.gnoise(m,s,T)
xoutval=strflib.gnoise(mout,sout,T)

# linear filter
yfit=np.matmul(h1.T,xfit)
yval=np.matmul(h1.T,xval)
youtval=np.matmul(h1.T,xoutval)

if NONLIN:
    # pass output of filter through sigmoid (if specified)
    yfit=strflib.logsig_fn(sigmoid_parms,yfit)
    yval=strflib.logsig_fn(sigmoid_parms,yval)
    youtval=strflib.logsig_fn(sigmoid_parms,youtval)
    

if noiseamp>0:
    # add noise (if specified)
    yfit=yfit+strflib.gnoise(np.zeros([1,1]),np.matrix([[noiseamp]]),T)
    yval=yval+strflib.gnoise(np.zeros([1,1]),np.matrix([[noiseamp]]),T)
    youtval=youtval+strflib.gnoise(np.zeros([1,1]),np.matrix([[noiseamp]]),T)


# fit the models

# subtract mean from stimulus and response to make them well-behaved
mx=np.mean(xfit,axis=1)
my=np.mean(yfit,axis=1)
xx=xfit-np.repeat(np.transpose(np.matrix(mx)),T,axis=1)
yy=yfit-my

# stimulus-response correlation  STA = S * r
SR= np.matmul(xx, yy.T) / T

# stimulus autocorrelation
C= np.matmul(xx, xx.T) / T

# sta is normalized by stimulus variance
hsta= ((1/np.diag(C)) * np.array(SR.T)).T

# estimate filter using normalized reverse correlation (aka linear regression)
Cinv=np.linalg.inv(C)
hnrc= np.matmul(Cinv, hsta)

# estimate filter using coordinate descent (aka boosting)
(hcd,hcd0)=strflib.coordinate_descent(xfit,yfit,0)

plt.close('all')
fig=plt.figure()

# slope of true underlying system
xr=np.array([[np.min(xval[0,:])],[np.max(xval[0,:])]])
yr0=xr * h1[0,0] + h0
yr1=xr * h1[1,0] + h0

# STA results
plt.subplot(3,3,1)
plt.plot(xval[0,:],yval[0,:],'k.')
xr=np.array([[np.min(xval[0,:])],[np.max(xval[0,:])]])
yr=xr * hsta[0,0] + my
plt.plot(xr,yr,'-')
yr0=xr * h1[0,0] + h0
plt.plot(xr,yr0,'r-')
plt.title('STA')
plt.xlabel('X0')
plt.ylabel('Y')

plt.subplot(3,3,2)
plt.plot(xval[1,:],yval[0,:],'k.')
xr=np.array([[np.min(xval[1,:])],[np.max(xval[1,:])]])
yr=xr * hsta[1,0] + my
plt.plot(xr,yr,'-')
plt.plot(xr,yr1,'r-')
plt.xlabel('X1')
plt.ylabel('Y')

# plot X0 vs. X1 to illustrate stimulus autocorrelation (if specified)
plt.subplot(3,3,3)
plt.plot(xoutval[0,:],xoutval[1,:],'b.')
plt.plot(xval[0,:],xval[1,:],'k.')
plt.xlabel('X0')
plt.ylabel('X1')
plt.title('Input correlation')

plt.subplot(3,3,4)
plt.plot(xval[0,:],yval[0,:],'k.')
xr=np.array([[np.min(xval[0,:])],[np.max(xval[0,:])]])
yr=xr * hnrc[0,0] + my
plt.plot(xr,yr,'-')
plt.plot(xr,yr0,'r-')
plt.title('NRC')

plt.subplot(3,3,5)
plt.plot(xval[1,:],yval[0,:],'k.')
xr=np.array([[np.min(xval[1,:])],[np.max(xval[1,:])]])
yr=xr * hnrc[1,0] + my
plt.plot(xr,yr,'-')
plt.plot(xr,yr1,'r-')

plt.subplot(3,3,7)
yr=xr * hcd[0,0] + hcd0
plt.plot(xval[0,:],yval[0,:],'k.')
#if NONLIN:
plt.plot(xoutval[0,:],youtval[0,:],'b.')

plt.plot(xr,yr0,'r-')
plt.plot(xr,yr,'-')
plt.title('CD')

plt.subplot(3,3,8)
yr=xr * hcd[1,0] + hcd0
plt.plot(xval[1,:],yval[0,:],'k.')
#if NONLIN:
plt.plot(xoutval[1,:],youtval[0,:],'b.')

plt.plot(xr,yr1,'r-')
plt.plot(xr,yr,'-')

#plt.tight_layout()

plt.show()




