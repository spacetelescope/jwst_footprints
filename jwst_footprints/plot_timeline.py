#! /usr/bin/env python
from __future__ import absolute_import, division, print_function

import datetime
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord

from astropy.io import ascii
from astropy.time import Time
from .find_tgt_info import *


def plottimeline(ra_msa='202.47',
                 dec_msa='47.2',
                 theta_msa=0.0,
                 outdir='/Users/myname/Desktop/'):

  
  #--------------------------------------------------------------------------  
  #  here i need to transform ra dec to float      06JUN2017    LEONARDO
    
    print('using NIRSpec RA  :',ra_msa)
    print('using NIRSpec DEC :',dec_msa)

    if (' ' in ra_msa) and (' ' in dec_msa) == True:   
       # it recognizes that the string has the format   hh mm ss.sss
       b = ra_msa+' '+dec_msa
       c = SkyCoord(b,unit=(u.hourangle, u.deg))
       #   transform to degrees to be used in the rest of the code
       ra = c.ra.deg 
       dec = c.dec.deg
       ra_msa = np.array(ra, np.float_)
       dec_msa = np.array(dec, np.float_)

    
    else:                          #   string is in units of degrees
       ra_msa = np.array(ra_msa, np.float_)
       dec_msa = np.array(dec_msa, np.float_)
#----------------------------------------------------------------------------  


    # here we use Wayne's code to calculate the rollangle for NIRCam and
    # NIRSpec
    rollangle(float(ra_msa), float(dec_msa),outdir)
    # output goes to screen and to a text file with the name v3pa_nircam_nirspec.txt

    # read v3pa_nircam_nirspec.txt
    data = ascii.read(outdir+'/v3pa_nircam_nirspec.txt')
    # time expressed in JDTDB Julian Day Number, Barycentric Dynamical Time
    x = np.array(data['col1']) + 2400000.5
    t = Time(x, format='jd')
    ti = t.datetime
    timeplot = np.array(t.datetime)

    # we read the values to plot
    minv2v3 = np.array(data['col2'])  #minimum possible value for v2v3
    maxv2v3 = np.array(data['col3'])  #maximum possible value for v2v3 
    minnircam = np.array(data['col4'])  # minimum possible value for nircam
    maxnircam = np.array(data['col5'])  # maximum possible value for nircam
    minnirspec = np.array(data['col6'])  # minimum possible value for nirspec
    maxnirspec = np.array(data['col7'])  # maximum possible value for nirspec

    fig = plt.figure(
        figsize=(
            10,
            5),
        dpi=120,
        edgecolor=None,
        facecolor='white')
    plt.grid(True)

    launch = datetime.date(2019, 3, 1)

    numdays = 90 + 365 * 4

    plt.plot_date(timeplot,minv2v3,color='yellow', marker='o',markersize=5)
    plt.plot_date(timeplot,maxv2v3,color='yellow', marker='o',markersize=5)

    plt.plot_date(timeplot,minnircam,color='blue', marker='s',markersize=1)
    plt.plot_date(timeplot,maxnircam,color='blue', marker='s',markersize=1)

    plt.plot_date(timeplot,maxnirspec,color='firebrick',  marker='.',markersize=2)
    plt.plot_date(timeplot,minnirspec,color='firebrick' , marker='.',markersize=2)

    red_patch = mpatches.Patch(color='blue', label='NIRCam')
    gre_patch = mpatches.Patch(color='firebrick', label='NIRSPec')
    bla_patch = mpatches.Patch(color='yellow', label='V3PA')


    plt.legend(handles=[red_patch,gre_patch,bla_patch])
    plt.gcf().autofmt_xdate()
   # plt.title('Aperture Position Angle')

    commissioning_start = datetime.date(2019, 3, 1)
    commissioning_end = datetime.date(2019, 8, 31)
    #plt.axvspan(
    #    commissioning_start,
    #    commissioning_end,
    #    ymin=0.0,
    #    ymax=360,
    #    alpha=0.99,
    #    color='steelblue')
    #plt.text(commissioning_start, 378, 'JWST')
    
    '''
    plt.text(commissioning_start, 365, 'commissioning')

    cycle1_start = datetime.date(2019, 9, 1)
    cycle1_end = datetime.date(2020, 8, 31)
    plt.axvspan(
        cycle1_start,
        cycle1_end,
        ymin=0.0,
        ymax=360,
        alpha=0.2,
        color='grey')
    plt.text(datetime.date(2019, 9, 1), 370, 'science cycle 1')

    cycle2_start = datetime.date(2020, 9, 1)
    cycle2_end = datetime.date(2021, 8, 31)
    plt.axvspan(
        cycle2_start,
        cycle2_end,
        ymin=0.0,
        ymax=360,
        alpha=1.0,
        color='white')
    plt.text(datetime.date(2020, 9, 1), 370, 'science cycle 2')
    '''
    cycle3_start = datetime.date(2021, 9, 1)
    cycle3_end = datetime.date(2022, 8, 31)
    #plt.axvspan(
    #    cycle3_start,
    #    cycle3_end,
    #    ymin=0.0,
    #    ymax=360,
    #    alpha=0.2,
    #    color='grey')
    #plt.text(datetime.date(2021, 8, 1), 370, 'cycle 3 science')
    


    plt.text(commissioning_start, 399, 'RA  : ' + str(ra_msa))
    plt.text(commissioning_start, 385, 'DEC : ' + str(dec_msa))

    plt.xlim([commissioning_start, cycle3_start])
    plt.ylim([0, 360])
    plt.ylabel('Aperture PA')
    plt.show()
