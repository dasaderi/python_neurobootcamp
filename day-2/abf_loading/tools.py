#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 12:30:21 2017

@author: charlie
"""

import numpy as np
from neo.io import AxonIO
import pandas as pd

import sys
sys.path.append('charlie/Desktop/python_bootcamp/Tims_stuff')

def abf_to_csv(filename='PVcell3.abf'):
    
    '''
    Writes data for given abf file into a csv format. Two .csv files will be created in 
    working directory. One will be meta_data, one will be time series data.
    
    These sheets are also returned as pandas data frames by this function    
    '''
    
    r = AxonIO(filename='PVcell3.abf')
    r = r.read_block()
    
    # For now, hardcode the date and the cell type (based on this filename format)
    # you could change this by getting rid of this line of code and nameing your file accordingly
    filename="PV_1_10_03_2014.abf"
        
    # Define number of sweeps in this protocol (.abf file)
    n_sweeps = len(r.segments)
    n_channels = len(r.segments[0].analogsignals)
    # Name sweeps 
    sweep_ids= []
    for i in range(0,n_sweeps):
        sweep_ids.append('sweep'+str(i+1))
        
    # List the traits to hold in meta data
    meta_traits = ['fs', 'celltype', 'date']
    for i in range(0, n_channels):
        meta_traits.append('ch'+str(i+1)+'_units')
    
    # create empty data frame for meta data
    meta_data = pd.DataFrame(columns=meta_traits,index=sweep_ids)
    
    for i, seg in enumerate(r.segments):
        for ch in range(0, n_channels):
            meta_data['ch'+str(ch+1)+'_units'][sweep_ids[i]]=str(seg.analogsignals[ch].units)[4:]
            meta_data['fs'][sweep_ids[i]]=float(seg.analogsignals[0].sampling_rate)
            meta_data['date']=filename[5:-4]
            meta_data['celltype']=str.split(filename,'_')[0]  # example of using string split to get information
    # create empty data frame to hold data
    data_cols = []
    for i in range(0, n_sweeps):
        for ch in range(0, n_channels):
            data_cols.append('ch'+str(ch+1)+'_sweep'+str(i+1))
    
    import warnings
    
    warnings.warn('If fs is same for all sweeps, hard coding time series to be the same for all sweeps within an .abf file')
    if len(meta_data['fs'].unique())==1:
        time = np.linspace(0,len(r.segments[0].analogsignals[0])/float(meta_data['fs'].unique()), len(r.segments[0].analogsignals[0]))
    else:
        sys.exit('sampling rates are different - need to figure out what to do in this case')
        
    data = pd.DataFrame(index = time, columns=data_cols)
    
    for s_index, seg in enumerate(r.segments):
        for ch_index, ch in enumerate(seg.analogsignals):
            data['ch'+str(ch_index+1)+'_sweep'+str(s_index+1)] = ch
    
    meta_data.to_csv('meta_data_'+str(filename)+'.csv')
    data.to_csv('data_'+str(filename)+'.csv')
    return meta_data, data