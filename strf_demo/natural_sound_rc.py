# Python class -- WEEK 5
#
# Processing spiking data recorded during presentation of temporally
# orthogonal ripple combinations (TORCs). TORCs are stimulus designed
# for efficient white noise analysis of the auditory system. The basic
# idea is to play a lot of complex random sounds while recording the
# activity of an auditory neuron. You then find the average sound that
# evokes an increase in spiking activity
#
# Goals: 
# 1. Deal with some very practical resampling and reshaping problems. 
# 2. Visualize TORC stimulus spectrograms
# 3. Plot spike raster, showing the time of spike events aligned in
#    time to the spectrogram
# 4. Plot peristimulus time histogram (PSTH) response to the TORCs,
#    i.e., the time-varying firing rate averaged across presentations
#    of the TORC stimulus.

import numpy as np
import pylab as plt

import scipy.io
import scipy.signal

import strflib

# The data: 

# Spike data were recorded from a single neuron in primary auditory
# cortex during 2 repetitions of 30 different TORC stimuli, each 2
# seconds long and with 0.5 sec of silence before and after the
# sound. These TORCs consist of the same spectro-temporal pattern
# repeated 4 times a second. So each 2-sec stimulus effectively
# contains cycles of the same sound. The first cycle drives onset
# transients, so usually it is discarded, leaving 7 cycles of
# "steady-state" stimuluation on each trial.

# load contents of Matlab data file

# IC cell, easy
#filepath="data/bbl031f-a1_b291_ozgf_c18_fs100.mat"

# A1 cell, harder
filepath="data/gus025b-c1_b271_ozgf_c18_fs100.mat"

data = strflib.load_baphy_data(filepath)


# parse into relevant variables
# spectrogram of TORC stimuli. 15 frequency bins X 300 time samples X 30 different TORCs
stim=data['stim']
stimFs=data['stimFs']

# response matrix. spikes per bin, sampled at 100 Hz [400 time bins X 3 or 24
# repetitions X 30 different TORCs]

resp=data['resp']

# each trial is (PreStimSilence + Duration + PostStimSilence) sec long
Duration=data['Duration']
PreStimSilence=data['PreStimSilence']
respFs=data['respFs']
PostStimSilence=data['PostStimSilence']

# first three stimuli were repeated many (24) times and are reserved for
# validation (model testing)
validx=np.array([0,1,2])

# majority of stimuli (4-93) were repeated 3 times and are used for estimateion
estidx=np.setdiff1d(np.arange(0,93),validx)

stimest=data['stim'][:,:,estidx]
stimval=data['stim'][:,:,validx]

respest=np.nanmean(data['resp'][:,:,estidx],axis=1)
respval=np.nanmean(data['resp'][:,:,validx],axis=1)

X=np.reshape(stimest,[stimest.shape[0],-1],order='F')
Y=np.reshape(respest,[1,-1],order='F')
mY=np.mean(Y)
Y=Y-mY

(Hsta,Hsta0)=strflib.sta(X,Y,10)
(Hnrc,Hnrc0)=strflib.norm_reverse_correlation(X,Y,10)
(Hcd,Hcd0)=strflib.coordinate_descent(X,Y,10)

# display results
plt.figure()

plt.subplot(2,2,1)
mm=np.max(np.abs(Hsta))
plt.imshow(Hsta, origin='lower', aspect='auto', clim=(-mm,mm))
plt.colorbar()
plt.title('Spike-triggered average')

plt.subplot(2,2,2)
mm=np.max(np.abs(Hnrc))
plt.imshow(Hnrc, origin='lower', aspect='auto', clim=(-mm,mm))
plt.colorbar()
plt.title('Normalized reverse correlation')

plt.subplot(2,2,3)
mm=np.max(np.abs(Hcd))
plt.imshow(Hcd, origin='lower', aspect='auto', clim=(-mm,mm))
plt.colorbar()
plt.title('Coordinate descent')

#plt.tight_layout()


# test prediction accuracy
s=stimval.shape
Xval=np.reshape(stimval,[s[0],-1],order='F')
Yval=np.reshape(respval,[1,-1],order='F')

Ypred_cd=np.reshape(strflib.predict(Xval,Hcd)+mY,[s[1],s[2]],order='F')
Ypred_sta=np.reshape(strflib.predict(Xval,Hsta)+mY,[s[1],s[2]],order='F')
Ypred_nrc=np.reshape(strflib.predict(Xval,Hnrc)+mY,[s[1],s[2]],order='F')

r_cd=np.corrcoef(Ypred_cd.flatten('F'),Yval)[0,1]
r_sta=np.corrcoef(Ypred_sta.flatten('F'),Yval)[0,1]
r_nrc=np.corrcoef(Ypred_nrc.flatten('F'),Yval)[0,1]

plt.figure()

data_stimidx=0
tt=np.arange(0,s[1])/stimFs

plt.subplot(2,1,1)
plt.imshow(stimval[:,:,data_stimidx], origin='lower', aspect='auto')
plt.axis('off')

plt.subplot(2,1,2)
fresp,=plt.plot(tt,respval[:,data_stimidx].T,label='Actual r(t)')
fnrc,=plt.plot(tt,Ypred_nrc[:,data_stimidx].T,label="NRC (cc={0:.3f})".format(r_nrc))
fcd,=plt.plot(tt,Ypred_cd[:,data_stimidx].T,label="CD (cc={0:.3f})".format(r_cd))

plt.legend(handles=[fresp,fnrc,fcd])
#plt.tight_layout()

plt.show()
