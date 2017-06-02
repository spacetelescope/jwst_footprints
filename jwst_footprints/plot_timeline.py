#! /usr/bin/env python


# load modules 
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from astropy.io import ascii
from astropy.time import Time
import numpy as np
import datetime 
from .find_tgt_info import *

def plottimeline(ra_msa=202.47,\
                 dec_msa=47.2,\
                 theta_msa=0.0):
    
    
    # here we use Wayne's code to calculate the rollangle for NIRCam and NIRSpec
    rollangle(float(ra_msa),float(dec_msa))
    # output goes to screen and to a text file with the nam nirspec_nircam.txt 

    # read nirspec_nircam.txt
    data = ascii.read('nirspec_nircam.txt')
    x = np.array(data['col1']) + 2400000.5  # time expressed in JDTDB Julian Day Number, Barycentric Dynamical Time
    t = Time(x, format='jd')
    ti = t.datetime
    timeplot= np.array(t.datetime)
     
    # we read the values to plot
    minnircam = np.array(data['col2'])  #minimum possible value for nircam
    maxnircam = np.array(data['col3'])  #maximum possible value for nircam 
    minnirspec = np.array(data['col4']) #minimum possible value for nirspec
    maxnirspec = np.array(data['col5']) #maximum possible value for nirspec

    fig = plt.figure(figsize = (10,5), dpi=120,edgecolor=None,facecolor='white')
    plt.grid(True)
      
    launch = datetime.date(2018,10,1)

    numdays = 90+365*4

    plt.plot_date(timeplot,minnircam,color='blue', marker='.')
    plt.plot_date(timeplot,maxnircam,color='blue', marker='.')
    plt.plot_date(timeplot,maxnirspec,color='firebrick',  marker='.')
    plt.plot_date(timeplot,minnirspec,color='firebrick' , marker='.')

    red_patch = mpatches.Patch(color='blue', label='NIRCam')
    gre_patch = mpatches.Patch(color='firebrick', label='NIRSPec')

    plt.legend(handles=[red_patch,gre_patch])
    plt.gcf().autofmt_xdate()
   # plt.title('Aperture Position Angle')


    commissioning_start= datetime.date(2018,10,1)
    commissioning_end= datetime.date(2019,3,31)
    plt.axvspan(commissioning_start, commissioning_end, ymin=0.0, ymax=360, alpha=0.99, color='steelblue')
    #plt.text(commissioning_start, 378, 'JWST')
    plt.text(commissioning_start, 365, 'commissioning')
  
   
    cycle1_start= datetime.date(2019,4,1)
    cycle1_end= datetime.date(2020,3,31)
    plt.axvspan(cycle1_start, cycle1_end, ymin=0.0, ymax=360, alpha=0.2, color='grey')
    plt.text(datetime.date(2019,8,1), 370, 'cycle 1 science')

    cycle2_start= datetime.date(2020,4,1)
    cycle2_end= datetime.date(2021,3,31)
    plt.axvspan(cycle2_start, cycle2_end, ymin=0.0, ymax=360, alpha=1.0, color='white')
    plt.text(datetime.date(2020,8,1), 370, 'cycle 2 science')

    cycle3_start= datetime.date(2021,4,1)
    cycle3_end= datetime.date(2022,3,31)
    plt.axvspan(cycle3_start, cycle3_end, ymin=0.0, ymax=360, alpha=0.2, color='grey')
    plt.text(datetime.date(2021,8,1), 370, 'cycle 3 science')
    

    plt.text(commissioning_start, 399, 'alpha '+str(ra_msa))
    plt.text(commissioning_start, 385, 'delta '+str(dec_msa))

    plt.xlim([commissioning_start, cycle3_end])
    plt.ylim([0, 360])
    plt.show()