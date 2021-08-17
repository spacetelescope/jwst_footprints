#!/usr/bin/env python
# encoding: utf-8

"""
Created by Leonardo Ubeda on 14JUL2016
Reads tables produced by footprints_create_apertures-00.py
and then produces region files and displays them in DS9
Based on work by Colin Cox and Wayne Kinzel
Updated by Joseph Hunkeler 
Maintained by Maria Peña Guerrero, Leonardo Ubeda, and Emily Wislowski


Version History

2.5      28JUN2021      resolved issue with NIRCam dither patterns (GitHub Issue #9)
                        added files to meet the Tier 2 community software standards


2.4      12MAR2018      changed from V3PA to aperture position angle (Help Desk INC0048565)

2.3      01JAN2018      added NIRSpec fixed slit apertures
                        added NIRCam 8NIRSPEC dither pattern
                        changed launch date and science cycles in timeline

2.2      14JUN2017      DS9 parameters in GUI
                        output directory
                        region files colours
2.0      06JUN2017      major update by Joseph Hunkeler
                        code ported to Python 3
                        compatible with Python 2.7
1.2      26MAY2017      added hhmmss format for RA 
                        added ddmmss format for DEC
                        changed the naming convention of dither patterns to FULL3 FULL3TIGHT FULL6
1.0      14JUL2016      first version

"""

from __future__ import absolute_import, division, print_function

import sys
import os
import numpy as np

from math import *
from astropy import wcs
from astropy.io import fits
from astropy.io import ascii
from astropy import units as u
from astropy.coordinates import SkyCoord
import pyds9
from . import PKG_DATA_DIR

#readfitsimage = True
#self.readfitsimageVar = StringVar()
#self.readfitsimageVar.set(self.config['readfitsimage'])
#print(readfitsimageVar)

def arcsec2deg(ra, dec, v2arcsec, v3arcsec, xr, yr):
    v2deg = ra + (v2arcsec - xr) / (3600. * cos(radians(dec)))
    v3deg = dec + ((v3arcsec - yr) / 3600.)
    return (v2deg, v3deg)


def unit(ra, dec):
    ''' Converts vector expressed in Euler angles to unit vector components.
    ra and dec in degrees
    Can be used for V2V3 after converting from arcsec to degrees)'''

    rar = radians(ra)
    decr = radians(dec)
    u = np.array([cos(rar) * cos(decr), sin(rar) * cos(decr), sin(decr)])
    return u


def radec(u):
    '''convert unit vector to Euler angles
    u is an array or list of length 3'''

    if len(u) != 3:
        print('Not a vector')
        return
    norm = sqrt(u[0]**2 + u[1]**2 + u[2]**2)  # Works for list or array
    dec = degrees(asin(u[2] / norm))
    ra = degrees(atan2(u[1], u[0]))  # atan2 puts it in the correct quadrant
    if ra < 0.0:
        ra += 360.0    # Astronomers prefer the range 0 to 360 degrees
    return (ra, dec)


def v2v3(u):
    '''Convert unit vector to v2v3'''
    if len(u) != 3:
        print('Not a vector')
        return
    norm = sqrt(u[0]**2 + u[1]**2 + u[2]**2)  # Works for list or array
    # atan2 puts it in the correct quadrant
    v2 = 3600 * degrees(atan2(u[1], u[0]))
    v3 = 3600 * degrees(asin(u[2] / norm))
    return (v2, v3)


def rotate(axis, angle):
    '''Fundamental rotation matrices.
    Rotate by angle measured in degrees, about axis 1 2 or 3'''
    if axis not in list(range(1, 4)):
        print('Axis must be in range 1 to 3')
        return
    r = np.zeros((3, 3))
    ax0 = axis - 1  # Allow for zero offset numbering
    theta = radians(angle)
    r[ax0, ax0] = 1.0
    ax1 = (ax0 + 1) % 3
    ax2 = (ax0 + 2) % 3
    r[ax1, ax1] = cos(theta)
    r[ax2, ax2] = cos(theta)
    r[ax1, ax2] = -sin(theta)
    r[ax2, ax1] = sin(theta)
    return r


def attitude(v2, v3, ra, dec, pa):
    '''This will make a rotation matrix which rotates a unit vector representing a v2,v3 position
    to a unit vector representing an RA, Dec pointing with an assigned position angle
    Described in JWST-STScI-001550, SM-12, section 6.1'''

    # v2, v3 in arcsec, ra, dec and position angle in degrees
    v2d = v2 / 3600.0
    v3d = v3 / 3600.0

    # Get separate rotation matrices
    mv2 = rotate(3, -v2d)
    mv3 = rotate(2, v3d)
    mra = rotate(3, ra)
    mdec = rotate(2, -dec)
    mpa = rotate(1, -pa)

    # Combine as mra*mdec*mpa*mv3*mv2
    m = np.dot(mv3, mv2)
    m = np.dot(mpa, m)
    m = np.dot(mdec, m)
    m = np.dot(mra, m)

    return m


def pointing(attitude, v2, v3):
    '''Using the attitude matrix to calculate where any v2v3 position points on the sky'''
    v2d = v2 / 3600.0
    v3d = v3 / 3600.0
    v = unit(v2d, v3d)
    w = np.dot(attitude, v)
    rd = radec(w)
    return rd  # tuple containing ra and dec


def linear_transformation(theta, xshift, yshift,
                          xscale, yscale, x2, x3, xr, yr):
    th = radians(theta)
    a = xshift
    d = yshift
    b = xscale * cos(th)
    c = yscale * sin(th)
    e = (-1) * xscale * sin(th)
    f = yscale * cos(th)
    v2r = a + b * (x2 - xr) + c * (x3 - yr)
    v3r = d + e * (x2 - xr) + f * (x3 - yr)
    return (v2r, v3r)


def rotate_long(x2, x3, theta):

    # search point in the center of each aperture
    xa = (x2[0] + x2[2]) / 2.0
    ya = (x3[0] + x3[2]) / 2.0
    xb = (x2[5] + x2[7]) / 2.0
    yb = (x3[5] + x3[7]) / 2.0
    # calculate center for rotation
    xr = ((xa + xb) / 2.)  # +xc
    yr = ((ya + yb) / 2.)  # +yc

    # rotate apertures according to the position angle PA
    rot = linear_transformation(theta, xr, yr, 1.0, 1.0, x2, x3, xr, yr)
    v2r = rot[0]
    v3r = rot[1]
    return (v2r, v3r, xr, yr)


def rotate_ifu(x2, x3, theta):
    # search point in the center of each aperture
    xr = (x2[0] + x2[2]) / 2.0
    yr = (x3[0] + x3[2]) / 2.0
    # rotate apertures according to the position angle PA
    rot = linear_transformation(theta, 0.0, 0.0, 1.0, 1.0, x2, x3, xr, yr)
    v2r = rot[0]
    v3r = rot[1]
    return (v2r, v3r, xr, yr)


def rotate_msa(x2, x3, theta):
    # search point in the center of each aperture
    xmsa1 = (x2[0] + x2[2]) / 2.0
    ymsa1 = (x3[0] + x3[2]) / 2.0
    xmsa2 = (x2[5] + x2[7]) / 2.0
    ymsa2 = (x3[5] + x3[7]) / 2.0
    xmsa3 = (x2[10] + x2[12]) / 2.0
    ymsa3 = (x3[10] + x3[12]) / 2.0
    xmsa4 = (x2[15] + x2[17]) / 2.0
    ymsa4 = (x3[15] + x3[17]) / 2.0

    # calculate center for rotation
    xr13 = (xmsa1 + xmsa3) / 2.0
    yr13 = (ymsa1 + ymsa3) / 2.0
    xr24 = (xmsa2 + xmsa4) / 2.0
    yr24 = (ymsa2 + ymsa4) / 2.0
    xr = (xr13 + xr24) / 2.
    yr = (yr13 + yr24) / 2.

    # rotate apertures according to the position angle PA
    rot = linear_transformation(theta, xr, yr, 1.0, 1.0, x2, x3, xr, yr)
    v2r = rot[0]
    v3r = rot[1]
    return (v2r, v3r, xr, yr)


def rotate_short(x2, x3, theta):
    # search point in the center of each aperture
    xsh1 = (x2[0] + x2[2]) / 2.0
    ysh1 = (x3[0] + x3[2]) / 2.0

    xsh2 = (x2[5] + x2[7]) / 2.0
    ysh2 = (x3[5] + x3[7]) / 2.0

    xsh3 = (x2[20] + x2[22]) / 2.0
    ysh3 = (x3[20] + x3[22]) / 2.0

    xsh4 = (x2[25] + x2[27]) / 2.0
    ysh4 = (x3[25] + x3[27]) / 2.0

    # calculate center for rotation
    xr13 = (xsh1 + xsh3) / 2.0
    yr13 = (ysh1 + ysh3) / 2.0
    xr24 = (xsh2 + xsh4) / 2.0
    yr24 = (ysh2 + ysh4) / 2.0
    xr = (xr13 + xr24) / 2.
    yr = (yr13 + yr24) / 2.

    # rotate apertures according to the position angle PA
    rot = linear_transformation(theta, xr, yr, 1.0, 1.0, x2, x3, xr, yr)
    v2r = rot[0]
    v3r = rot[1]
    return (v2r, v3r, xr, yr)

#------------------------------


def create_footprint(inputfile, ra, dec, napertures, footprintname, color):
    global w
    # input

    # ra = ra in degrees
    # dec = dec in degrees
    # footprintname is the name of the output file
    # napertures = number of apertures in footprint ( Nircam LONG = 2, NIRCam
    # short = 8, MSA = 4)

    nrows = napertures * 5
    #print(nrows)
    ra = np.array(ra, np.float_)  # np.array(ra, np.float_)
    dec = np.array(dec, np.float_)  # np.array(dec, np.float_)
    world = []
    # print ra
    #sys.exit("quitting now...")

    for i in range(0, nrows):
        #world = np.append(world,(ra[i],dec[i]))
        world.append((ra[i], dec[i]))
    pixcrd2 = w.wcs_world2pix(world, 1)
    #print(pixcrd2)
    xx = []
    yy = []
    for i in range(0, nrows):
        xx.append(pixcrd2[[i], 0])
        yy.append(pixcrd2[[i], 1])
        #xx = np.append(xx,pixcrd2[[i],0])
        #yy = np.append(yy,pixcrd2[[i],1])

    xwcs = np.array(xx, np.float_)
    ywcs = np.array(yy, np.float_)
    x = [float(i) for i in xwcs]
    y = [float(i) for i in ywcs]
    # print x
    # polygon x1 y1 x2 y2 x3 y3 ...

    outputfile = footprintname
    file = open(outputfile, "w")
    file.write(
        'global color=' +
        color +
        ' width=1 font="helvetica 15 normal roman"   select=0 highlite=1 \n')
    file.write('image\n')
    pos = 0
    for i in range(0, napertures):
        newline = 'polygon ' + str(x[pos]) + '  ' + str(y[pos]) + '  ' + str(x[pos + 1]) + '  ' + str(y[pos + 1]) + '  ' + str(x[pos + 2]) + '  ' + str(
            y[pos + 2]) + '  ' + str(x[pos + 3]) + '  ' + str(y[pos + 3]) + '  ' + str(x[pos + 4]) + '  ' + str(y[pos + 4]) + '  ' + '# text={}' + '\n'
        file.write(newline)
        pos = pos + 5
    file.close()
#------------------------------


#------------------------------
def create_footprint_center(inputfile, ra, dec, footprintname, color):
    global w

    '''
    # ra = ra in degrees
    # dec = dec in degrees
    # footprintname is the name of the output file
    # napertures = number of apertures in footprint ( Nircam LONG = 2, NIRCam
    # short = 8, MSA = 4)
    '''
    ra = np.array(ra, np.float_)
    dec = np.array(dec, np.float_)
    world = []
    world.append((ra, dec))
    pixcrd2 = w.wcs_world2pix(world, 1)
    xx = float(pixcrd2[[0], 0])
    yy = float(pixcrd2[[0], 1])
    c2 = "%10s" % str(xx)
    c3 = "%10s" % str(yy)

    # polygon x1 y1 x2 y2 x3 y3 ...

    outputfile = footprintname
    file = open(outputfile, "w")
    file.write(
        'global color=' +
        color +
        ' width=1 font="helvetica 15 normal roman"  select=0 highlite=1 \n')
    file.write('image\n')
    newline = 'point(' + c2 + ',' + c3 + ') # point=cross 20  \n'
    file.write(newline)
    file.close()

#------------------------------
def read_table(inputfile, delim=' '):
    records = []
    with open(inputfile, 'r') as fp:
        for row in fp:
            cols = [ x for x in row.strip().split(delim) if x ]
            records.append(cols)

    return list(zip(*records))


def footprints(inputfile,
               sourcelist,
               plot_long='No',
               plot_short='No',
               plot_msa='No',
               plot_sources='No',
               ra_long='202.47',
               dec_long='47.2',
               theta_long=0.0,
               dither_pattern_long='No',
               ra_msa='202.47',
               dec_msa='47.2',
               theta_msa=0.0,
               mosaic='No',
               usershiftv2=0.0,
               usershiftv3=0.0,
               colmsa='red',
               colshort='green',
               collong='blue',
               ds9cmap='grey',
               ds9limmin=0.0,
               ds9limmax=30.0,
               ds9scale='log',
               outdir='/Users/myname/Desktop/'):
               #readfitsimage=True):

    # verify that outdir exists
    if not os.path.exists(outdir):
        os.makedirs(outdir, mode=0o0755)
        print("creating directory "+ outdir )

    #print(outdir)
    global w

    usershiftv2 = np.array(usershiftv2, np.float_)
    usershiftv3 = np.array(usershiftv3, np.float_)

    # nircam long footprint
    ra_short = ra_long
    dec_short = dec_long
    theta_short = theta_long
    dither_pattern_short = dither_pattern_long

    # read image and its header
    # need to extend this to multi extension fits files
    # print(readfitsimage)
    # print('reading fits')
    hdulist = fits.open(inputfile)
    w = wcs.WCS(hdulist[0].header)    # assuming WCS is in extension 0
    '''
    if readfitsimage == True:
        print('reading fits')
        hdulist = fits.open(inputfile)
        w = wcs.WCS(hdulist[0].header)    # assuming WCS is in extension 0
        readfitsimage = False 
#        readfitsimage = False
    '''


    if plot_sources == 'Yes':
        print('creating region file from source list')
        # here we read the list ra dec and create a DS9 region file
        data = ascii.read(sourcelist)
        # this gives the number of columns in the input file
        #print(len(data.colnames))

        if len(data.colnames) == 2:
            flagsources = 2
            # in this case the user inputs ra dec
            ra = np.array(data['col1'], np.float_)
            dec = np.array(data['col2'], np.float_)
            #print(ra)
            #print(dec)
            world = []
            for i in range(len(ra)):
                world.append((ra[i], dec[i]))
            pixcrd2 = w.wcs_world2pix(world, 1)
            xx = []
            yy = []
            for i in range(len(ra)):
                xx.append(pixcrd2[[i], 0])
                yy.append(pixcrd2[[i], 1])
            xwcs = np.array(xx, np.float_)
            ywcs = np.array(yy, np.float_)
            x = [float(i) for i in xwcs]
            y = [float(i) for i in ywcs]

            outputfile = outdir+'/ds9-sources.reg'
            file = open(outputfile, "w")
            file.write(
                'global color=yellow width=1 font="helvetica 15 normal roman"   select=0 highlite=1 \n')
            file.write('image\n')
            #pos = 0
            for i in range(len(ra)):
                c2 = "%10s" % str(x[i])
                c3 = "%10s" % str(y[i])
                newline = 'circle(' + c2 + ',' + c3 + ',5) # text={}' + '\n'
                file.write(newline)
            file.close()

        if len(data.colnames) >= 3:
            flagsources = 3
            # in this case the user inputs ra dec source-type
            ra = np.array(data['col1'], np.float_)
            dec = np.array(data['col2'], np.float_)
            sourcetype = data['col3']
            #print(ra)
            #print(dec)
            #print(sourcetype.info)
            # select sources according to type
            a = np.where(sourcetype == 'F')[0]  # fillers
            rafill = ra[a]
            decfill = dec[a]
            a = np.where(sourcetype == 'P')[0]  # primary sources
            rap = ra[a]
            decp = dec[a]

            # region file of fillers
            world = []
            for i in range(len(rafill)):
                world.append((rafill[i], decfill[i]))
            pixcrd2 = w.wcs_world2pix(world, 1)
            xx = []
            yy = []
            for i in range(len(rafill)):
                xx.append(pixcrd2[[i], 0])
                yy.append(pixcrd2[[i], 1])
            xwcs = np.array(xx, np.float_)
            ywcs = np.array(yy, np.float_)
            x = [float(i) for i in xwcs]
            y = [float(i) for i in ywcs]

            outputfile = outdir+'/ds9-sources-fillers.reg'
            file = open(outputfile, "w")
            file.write(
                'global color=yellow width=1 font="helvetica 15 normal roman"   select=0 highlite=1 \n')
            file.write('image\n')
            #pos = 0
            for i in range(len(rafill)):
                c2 = "%10s" % str(x[i])
                c3 = "%10s" % str(y[i])
                newline = 'circle(' + c2 + ',' + c3 + ',5) # text={}' + '\n'
                file.write(newline)
            file.close()

            # region file of primary sources
            world = []
            for i in range(len(rap)):
                world.append((rap[i], decp[i]))
            pixcrd2 = w.wcs_world2pix(world, 1)
            xx = []
            yy = []
            for i in range(len(rap)):
                xx.append(pixcrd2[[i], 0])
                yy.append(pixcrd2[[i], 1])
            xwcs = np.array(xx, np.float_)
            ywcs = np.array(yy, np.float_)
            x = [float(i) for i in xwcs]
            y = [float(i) for i in ywcs]

            outputfile = outdir+'/ds9-sources-primary.reg'
            file = open(outputfile, "w")
            file.write(
                'global color=red width=1 font="helvetica 15 normal roman"  select=0  highlite=1 \n')
            file.write('image\n')
            #pos = 0
            for i in range(len(rap)):
                c2 = "%10s" % str(x[i])
                c3 = "%10s" % str(y[i])
                newline = 'circle(' + c2 + ',' + c3 + ',5) # text={}' + '\n'
                file.write(newline)
            file.close()
        if len(data.colnames) < 2:
            print('Invalid input file')
#-------------------------------------------------------------------
    #                                                                     nirspec msa
    #   15DEC2017  I add NIRSpec slits to be plotted with the MSA and IFU
    if plot_msa == 'Yes':
        print('processing NIRSPEC MSA')
        v2msa, v3msa, aper, v2ref, v3ref = read_table(os.path.join(PKG_DATA_DIR, 'table-nirspec-msa.txt'))
        v2msa = np.array(v2msa, np.float_)
        v3msa = np.array(v3msa, np.float_)

#---------------------------  
#  here i need to transform ra dec to float        06JUN2017  LEONARDO
    
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


        x2 = v2msa
        x3 = v3msa
        # search point in the center of each aperture
        xmsa1 = (x2[0] + x2[2]) / 2.0
        ymsa1 = (x3[0] + x3[2]) / 2.0
        xmsa2 = (x2[5] + x2[7]) / 2.0
        ymsa2 = (x3[5] + x3[7]) / 2.0
        xmsa3 = (x2[10] + x2[12]) / 2.0
        ymsa3 = (x3[10] + x3[12]) / 2.0
        xmsa4 = (x2[15] + x2[17]) / 2.0
        ymsa4 = (x3[15] + x3[17]) / 2.0

        # calculate center for rotation
        xr13 = (xmsa1 + xmsa3) / 2.0
        yr13 = (ymsa1 + ymsa3) / 2.0
        xr24 = (xmsa2 + xmsa4) / 2.0
        yr24 = (ymsa2 + ymsa4) / 2.0
        xr = (xr13 + xr24) / 2.
        yr = (yr13 + yr24) / 2.

        v2 = v2msa
        v3 = v3msa
        xr0 = xr
        yr0 = yr
        ra0 = ra_msa
        dec0 = dec_msa 
        pa = theta_msa - 137.4874   #  12MAR2018   NRS_FULL_MSA_V3IdlYang = 137.4874
        myv2 = []
        myv3 = []
        v20 = xr0
        v30 = yr0
        m = attitude(v20, v30, ra0, dec0, pa)
        for k in range(len(v2)):
            a = pointing(m, v2[k], v3[k])
            myv2 = np.append(myv2, a[0])
            myv3 = np.append(myv3, a[1])
        myv2 = np.array(myv2)
        myv3 = np.array(myv3)
        
        # create_footprint(input,myv2,myv3,5,'ds9-msa.reg','red') # 10 because
        # is includes the IFU aperture
        # 10 because it includes the IFU aperture and the slits
        create_footprint(
            input, 
            myv2, 
            myv3, 
            10,                                # here we have msa = 4 + ifu =1 + slits = 5 total =10 
            outdir+'/ds9-msa.reg', 
            colmsa)
        create_footprint_center(
            input,
            ra_msa,
            dec_msa,
            outdir+'/ds9-msa-centre.reg',
            colmsa)

    #-------------------------------------------------------------------
    # nircam long
    # print plot_long
    if plot_long == 'Yes':
        print('processing NIRCAM LWC')



#--------------------------------------------------------------------------  
#  here i need to transform ra dec to float             06JUN2017  LEONARDO
    
        print('using NIRCAm RA  :',ra_long)
        print('using NIRCam DEC :',dec_long)

        if (' ' in ra_long) and (' ' in dec_long) == True:   
           # it recognizes that the string has the format   hh mm ss.sss
           b = ra_long+' '+dec_long
           c = SkyCoord(b,unit=(u.hourangle, u.deg))
           #   transform to degrees to be used in the rest of the code
           ra = c.ra.deg 
           dec = c.dec.deg
           ra_long = np.array(ra, np.float_)
           dec_long = np.array(dec, np.float_)

        
        else:                          #   string is in units of degrees
           ra_long = np.array(ra_long, np.float_)
           dec_long = np.array(dec_long, np.float_)
#----------------------------------------------------------------------------  
        create_footprint_center(
            inputfile,
            ra_long,
            dec_long,
            outdir+'/ds9-long-centre.reg',
            collong)
        v2c, v3c, aper, v2ref, v3ref = read_table(os.path.join(PKG_DATA_DIR, 'table-nircam-long.txt'))
        v2_0 = np.array(v2c, np.float_)
        v3_0 = np.array(v3c, np.float_)

        if dither_pattern_long == 'None' and mosaic == 'No':
            #shiftv2 = [0.0, -58.0,  58.0]
            #shiftv3 = [0.0, -23.5,  23.5]
            v2 = v2_0
            v3 = v3_0
            # determine center of rotation
            xa = (v2[0] + v2[2]) / 2.0
            ya = (v3[0] + v3[2]) / 2.0
            xb = (v2[5] + v2[7]) / 2.0
            yb = (v3[5] + v3[7]) / 2.0
            xr = ((xa + xb) / 2.)
            yr = ((ya + yb) / 2.)
            xr0 = xr
            yr0 = yr
            ra0 = ra_long
            dec0 = dec_long
            pa = theta_long + 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            # for shft in (0,1,2):
            v20 = xr0
            v30 = yr0
            m = attitude(v20, v30, ra0, dec0, pa)
            for k in range(len(v2)):
                a = pointing(m, v2[k], v3[k])
                myv2 = np.append(myv2, a[0])
                myv3 = np.append(myv3, a[1])
            myv2 = np.array(myv2)
            myv3 = np.array(myv3)
            create_footprint(inputfile, 
               myv2,
               myv3, 
               2, 
               outdir+'/ds9-long-no.reg', 
               collong)

        #                                                                          8NIRSPEC  29NOV2017
        if dither_pattern_long == '8NIRSPEC':
            mosaic == 'No'
            shiftv2 = [-24.6, -24.4, 24.6, 24.4, 24.6, 24.4, -24.6, -24.4]
            shiftv3 = [-64.1, -89.0, -88.8, -63.9, 64.1, 89.0, 88.8, 63.9 ]
            v2 = v2_0
            v3 = v3_0
            # determine center of rotation
            xa = (v2[0] + v2[2]) / 2.0
            ya = (v3[0] + v3[2]) / 2.0
            xb = (v2[5] + v2[7]) / 2.0
            yb = (v3[5] + v3[7]) / 2.0
            xr = ((xa + xb) / 2.)
            yr = ((ya + yb) / 2.)
            xr0 = xr
            yr0 = yr
            ra0 = ra_long
            dec0 = dec_long
            pa =  (theta_long+ 0.0265)    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            #for shft in (0, 1, 2, 4, 5, 6, 7):
            for shft in range(len(shiftv2)):
                v20 = xr0 - (shiftv2[shft])  # here we shift
                v30 = yr0 + (shiftv3[shft])  # here we shift
                m = attitude(v20, v30, ra0, dec0, pa)
                for k in range(len(v2)):
                    a = pointing(m, v2[k], v3[k])
                    myv2 = np.append(myv2, a[0])
                    myv3 = np.append(myv3, a[1])
                myv2 = np.array(myv2)
                myv3 = np.array(myv3)
            #print(len(myv2))    
            create_footprint(
                inputfile,
                myv2,
                myv3,
                16,
                outdir+'/ds9-long-8nirspec.reg',
                collong)


        if dither_pattern_long == 'FULL3' and mosaic == 'No':
            shiftv2 = [0.0, -58.0, 58.0]
            shiftv3 = [0.0, -23.5, 23.5]
            v2 = v2_0
            v3 = v3_0
            # determine center of rotation
            xa = (v2[0] + v2[2]) / 2.0
            ya = (v3[0] + v3[2]) / 2.0
            xb = (v2[5] + v2[7]) / 2.0
            yb = (v3[5] + v3[7]) / 2.0
            xr = ((xa + xb) / 2.)
            yr = ((ya + yb) / 2.)
            xr0 = xr
            yr0 = yr
            ra0 = ra_long
            dec0 = dec_long
            pa = theta_long+ 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            for shft in (0, 1, 2):
                v20 = xr0 - (shiftv2[shft])  # here we shift
                v30 = yr0 + (shiftv3[shft])  # here we shift
                m = attitude(v20, v30, ra0, dec0, pa)
                for k in range(len(v2)):
                    a = pointing(m, v2[k], v3[k])
                    myv2 = np.append(myv2, a[0])
                    myv3 = np.append(myv3, a[1])
                myv2 = np.array(myv2)
                myv3 = np.array(myv3)
            create_footprint(
                inputfile,
                myv2,
                myv3,
                6,
                outdir+'/ds9-long-three.reg',
                collong)

        if dither_pattern_long == 'FULL3TIGHT' and mosaic == 'No':
            shiftv2 = [0.0, -58.0, 58.0]
            shiftv3 = [0.0, -7.5, 7.5]
            v2 = v2_0
            v3 = v3_0
            # determine center of rotation
            xa = (v2[0] + v2[2]) / 2.0
            ya = (v3[0] + v3[2]) / 2.0
            xb = (v2[5] + v2[7]) / 2.0
            yb = (v3[5] + v3[7]) / 2.0
            xr = ((xa + xb) / 2.)
            yr = ((ya + yb) / 2.)
            xr0 = xr
            yr0 = yr
            ra0 = ra_long
            dec0 = dec_long
            pa = theta_long+ 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            for shft in (0, 1, 2):
                v20 = xr0 - (shiftv2[shft])  # here we shift
                v30 = yr0 + (shiftv3[shft])  # here we shift
                m = attitude(v20, v30, ra0, dec0, pa)
                for k in range(len(v2)):
                    a = pointing(m, v2[k], v3[k])
                    myv2 = np.append(myv2, a[0])
                    myv3 = np.append(myv3, a[1])
                myv2 = np.array(myv2)
                myv3 = np.array(myv3)
            create_footprint(
                inputfile,
                myv2,
                myv3,
                6,
                outdir+'/ds9-long-threetight.reg',
                collong)

        if dither_pattern_long == 'FULL6' and mosaic == 'No':
            shiftv2 = [-72.0, -43.0, -14.0, 15.0, 44.0, 73.0]
            shiftv3 = [-30.0, -18.0, -6.0, 6.0, 18.0, 30.0]
            # determine center of rotation
            v2 = v2_0 + 73.0
            v3 = v3_0 + 30.0
            xa = (v2[0] + v2[2]) / 2.0
            ya = (v3[0] + v3[2]) / 2.0
            v2 = v2_0 - 72.0
            v3 = v3_0 - 30.0
            xb = (v2[5] + v2[7]) / 2.0
            yb = (v3[5] + v3[7]) / 2.0
            xr = ((xa + xb) / 2.)
            yr = ((ya + yb) / 2.)

            v2 = v2_0
            v3 = v3_0

            xr0 = xr
            yr0 = yr
            ra0 = ra_long
            dec0 = dec_long
            pa = theta_long+ 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            for shft in (0, 1, 2, 3, 4, 5):
                v20 = xr0 - (shiftv2[shft])  # here we shift
                v30 = yr0 + (shiftv3[shft])  # here we shift
                m = attitude(v20, v30, ra0, dec0, pa)
                for k in range(len(v2)):
                    a = pointing(m, v2[k], v3[k])
                    myv2 = np.append(myv2, a[0])
                    myv3 = np.append(myv3, a[1])
                myv2 = np.array(myv2)
                myv3 = np.array(myv3)
            create_footprint(
                inputfile,
                myv2,
                myv3,
                12,
                outdir+'/ds9-long-six.reg',
                collong)


        if (dither_pattern_long == 'FULL3' or dither_pattern_long ==
                'FULL3TIGHT' or dither_pattern_long == 'None') and mosaic == 'Yes':
            if dither_pattern_long == 'FULL3':
                shiftv3 = [0.0, -23.5, 23.5, usershiftv3 + 0.0,
                           usershiftv3 - 23.5, usershiftv3 + 23.5]
            if dither_pattern_long == 'FULL3TIGHT':
                shiftv3 = [0.0, -7.5, 7.5, usershiftv3 + 0.0,
                           usershiftv3 - 7.5, usershiftv3 + 7.5]

            shiftv2 = [0.0, -58.0, 58.0, usershiftv2 + 0.0,
                       usershiftv2 - 58.0, usershiftv2 + 58.0]
            if (dither_pattern_long == 'None'):
                shiftv3 = [0.0, usershiftv3 + 0.0]
                shiftv2 = [0.0, usershiftv2 + 0.0]

            v2 = v2_0
            v3 = v3_0
            # determine center of rotation
            v2 = np.append(v2, v2 + usershiftv2)
            v3 = np.append(v3, v3 + usershiftv3)
            ascii.write([v2, v3], 'values.dat')

            xa = (v2[0] + v2[2]) / 2.0
            ya = (v3[0] + v3[2]) / 2.0
            xb = (v2[5] + v2[7]) / 2.0
            yb = (v3[5] + v3[7]) / 2.0
            xr1 = ((xa + xb) / 2.)
            yr1 = ((ya + yb) / 2.)
            xa = (v2[10] + v2[12]) / 2.0
            ya = (v3[10] + v3[12]) / 2.0
            xb = (v2[15] + v2[17]) / 2.0
            yb = (v3[15] + v3[17]) / 2.0
            xr2 = ((xa + xb) / 2.)
            yr2 = ((ya + yb) / 2.)

            xr = ((xr1 + xr2) / 2.)
            yr = ((yr1 + yr2) / 2.)

            xr0 = xr
            yr0 = yr
            ra0 = ra_long
            dec0 = dec_long
            pa = theta_long+ 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            for shft in range(len(shiftv2)):
                v20 = xr0 - (shiftv2[shft])  # here we shift
                v30 = yr0 + (shiftv3[shft])  # here we shift
                #print(v20, v30)
                m = attitude(v20, v30, ra0, dec0, pa)
                for k in range(len(v2)):
                    a = pointing(m, v2[k], v3[k])
                    myv2 = np.append(myv2, a[0])
                    myv3 = np.append(myv3, a[1])
                myv2 = np.array(myv2)
                myv3 = np.array(myv3)
            if (dither_pattern_long == 'None'):
                napertures = 4
            if (dither_pattern_long ==
                    'FULL3' or dither_pattern_long == 'FULL3TIGHT'):
                napertures = 12
            create_footprint(
                inputfile,
                myv2,
                myv3,
                napertures,
                outdir+'/ds9-long-mosaic.reg',
                collong)


#-------------------------------------------------------------------
# nircam short
    if plot_short == 'Yes':
        print('processing NIRCAM SWC')
       
        v2sh, v3sh, aper, v2ref, v3ref = read_table(os.path.join(PKG_DATA_DIR, 'table-nircam-short.txt'))
        v2sh = np.array(v2sh, np.float_)
        v3sh = np.array(v3sh, np.float_)

#--------------------------------------------------------------------------  
#  here i need to transform ra dec to float          06JUN2017    LEONARDO
    
        print('using NIRCAm RA  :',ra_long)
        print('using NIRCam DEC :',dec_long)
        ra_short = ra_long
        dec_short = dec_long

        if (' ' in ra_long) and (' ' in dec_long) == True:   
           # it recognizes that the string has the format   hh mm ss.sss
           b = ra_long+' '+dec_long
           c = SkyCoord(b,unit=(u.hourangle, u.deg))
           #   transform to degrees to be used in the rest of the code
           ra = c.ra.deg 
           dec = c.dec.deg
           ra_short = np.array(ra, np.float_)
           dec_short = np.array(dec, np.float_)

        
        else:                          #   string is in units of degrees
           ra_short = np.array(ra_short, np.float_)
           dec_short = np.array(dec_short, np.float_)
#----------------------------------------------------------------------------          

        create_footprint_center(
            inputfile,
            ra_short,
            dec_short,
            outdir+'/ds9-short-centre.reg',
            colshort)

        if dither_pattern_short == 'None':
            x2 = v2sh
            x3 = v3sh
            v2 = v2sh
            v3 = v3sh
            # determine center of rotation
            # search point in the center of each aperture
            xsh1 = (x2[0] + x2[2]) / 2.0
            ysh1 = (x3[0] + x3[2]) / 2.0
            xsh2 = (x2[5] + x2[7]) / 2.0
            ysh2 = (x3[5] + x3[7]) / 2.0
            xsh3 = (x2[20] + x2[22]) / 2.0
            ysh3 = (x3[20] + x3[22]) / 2.0
            xsh4 = (x2[25] + x2[27]) / 2.0
            ysh4 = (x3[25] + x3[27]) / 2.0

            # calculate center for rotation
            xr13 = (xsh1 + xsh3) / 2.0
            yr13 = (ysh1 + ysh3) / 2.0
            xr24 = (xsh2 + xsh4) / 2.0
            yr24 = (ysh2 + ysh4) / 2.0
            xr = (xr13 + xr24) / 2.
            yr = (yr13 + yr24) / 2.

            xr0 = xr
            yr0 = yr
            ra0 = ra_short
            dec0 = dec_short
            pa = theta_short+ 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            v20 = xr0
            v30 = yr0
            m = attitude(v20, v30, ra0, dec0, pa)
            for k in range(len(v2)):
                a = pointing(m, v2[k], v3[k])
                myv2 = np.append(myv2, a[0])
                myv3 = np.append(myv3, a[1])
            myv2 = np.array(myv2)
            myv3 = np.array(myv3)
            #print(myv2)
            create_footprint(
                inputfile,
                myv2,
                myv3,
                8,
                outdir+'/ds9-short-no.reg',
                colshort)


        #                                                                          8NIRSPEC  15DEC2017
        if dither_pattern_short == '8NIRSPEC' :
            mosaic == 'No'
            shiftv2 = [-24.6, -24.4, 24.6, 24.4, 24.6, 24.4, -24.6, -24.4]
            shiftv3 = [-64.1, -89.0, -88.8, -63.9, 64.1, 89.0, 88.8, 63.9 ]
            x2 = v2sh
            x3 = v3sh
            v2 = v2sh
            v3 = v3sh
            # determine center of rotation
            # search point in the center of each aperture
            xsh1 = (x2[0] + x2[2]) / 2.0
            ysh1 = (x3[0] + x3[2]) / 2.0
            xsh2 = (x2[5] + x2[7]) / 2.0
            ysh2 = (x3[5] + x3[7]) / 2.0
            xsh3 = (x2[20] + x2[22]) / 2.0
            ysh3 = (x3[20] + x3[22]) / 2.0
            xsh4 = (x2[25] + x2[27]) / 2.0
            ysh4 = (x3[25] + x3[27]) / 2.0
            # calculate center for rotation
            xr13 = (xsh1 + xsh3) / 2.0
            yr13 = (ysh1 + ysh3) / 2.0
            xr24 = (xsh2 + xsh4) / 2.0
            yr24 = (ysh2 + ysh4) / 2.0
            xr = (xr13 + xr24) / 2.
            yr = (yr13 + yr24) / 2.
            xr0 = xr
            yr0 = yr
            ra0 = ra_short
            dec0 = dec_short
            pa = theta_short+ 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            for shft in range(len(shiftv2)):
                v20 = xr0 - (shiftv2[shft])  # here we shift
                v30 = yr0 + (shiftv3[shft])  # here we shift
                m = attitude(v20, v30, ra0, dec0, pa)
                for k in range(len(v2)):
                    a = pointing(m, v2[k], v3[k])
                    myv2 = np.append(myv2, a[0])
                    myv3 = np.append(myv3, a[1])
                myv2 = np.array(myv2)
                myv3 = np.array(myv3)
            #print(len(myv2))    
            create_footprint(
                inputfile,
                myv2,
                myv3,
                64,
                outdir+'/ds9-short-8nirspec.reg',
                colshort)



        if dither_pattern_short == 'FULL3':
            shiftv2 = [0.0, -58.0, 58.0]
            shiftv3 = [0.0, -23.5, 23.5]
            x2 = v2sh
            x3 = v3sh
            v2 = v2sh
            v3 = v3sh
            # determine center of rotation
            # search point in the center of each aperture
            xsh1 = (x2[0] + x2[2]) / 2.0
            ysh1 = (x3[0] + x3[2]) / 2.0
            xsh2 = (x2[5] + x2[7]) / 2.0
            ysh2 = (x3[5] + x3[7]) / 2.0
            xsh3 = (x2[20] + x2[22]) / 2.0
            ysh3 = (x3[20] + x3[22]) / 2.0
            xsh4 = (x2[25] + x2[27]) / 2.0
            ysh4 = (x3[25] + x3[27]) / 2.0
            # calculate center for rotation
            xr13 = (xsh1 + xsh3) / 2.0
            yr13 = (ysh1 + ysh3) / 2.0
            xr24 = (xsh2 + xsh4) / 2.0
            yr24 = (ysh2 + ysh4) / 2.0
            xr = (xr13 + xr24) / 2.
            yr = (yr13 + yr24) / 2.
            xr0 = xr
            yr0 = yr
            ra0 = ra_short
            dec0 = dec_short
            pa = theta_short+ 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            for shft in (0, 1, 2):
                v20 = xr0 - (shiftv2[shft])  # here we shift
                v30 = yr0 + (shiftv3[shft])  # here we shift
                m = attitude(v20, v30, ra0, dec0, pa)
                for k in range(len(v2)):
                    a = pointing(m, v2[k], v3[k])
                    myv2 = np.append(myv2, a[0])
                    myv3 = np.append(myv3, a[1])
                myv2 = np.array(myv2)
                myv3 = np.array(myv3)
            create_footprint(
                inputfile,
                myv2,
                myv3,
                24,
                outdir+'/ds9-short-three.reg',
                colshort)

        if dither_pattern_short == 'FULL3TIGHT':
            shiftv2 = [0.0, -58.0, 58.0]
            shiftv3 = [0.0, -7.5, 7.5]
            x2 = v2sh
            x3 = v3sh
            v2 = v2sh
            v3 = v3sh
            # determine center of rotation
            # search point in the center of each aperture
            xsh1 = (x2[0] + x2[2]) / 2.0
            ysh1 = (x3[0] + x3[2]) / 2.0
            xsh2 = (x2[5] + x2[7]) / 2.0
            ysh2 = (x3[5] + x3[7]) / 2.0
            xsh3 = (x2[20] + x2[22]) / 2.0
            ysh3 = (x3[20] + x3[22]) / 2.0
            xsh4 = (x2[25] + x2[27]) / 2.0
            ysh4 = (x3[25] + x3[27]) / 2.0

            # calculate center for rotation
            xr13 = (xsh1 + xsh3) / 2.0
            yr13 = (ysh1 + ysh3) / 2.0
            xr24 = (xsh2 + xsh4) / 2.0
            yr24 = (ysh2 + ysh4) / 2.0
            xr = (xr13 + xr24) / 2.
            yr = (yr13 + yr24) / 2.
            xr0 = xr
            yr0 = yr
            ra0 = ra_short
            dec0 = dec_short
            pa = theta_short+ 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            for shft in (0, 1, 2):
                v20 = xr0 - (shiftv2[shft])  # here we shift
                v30 = yr0 + (shiftv3[shft])  # here we shift
                m = attitude(v20, v30, ra0, dec0, pa)
                for k in range(len(v2)):
                    a = pointing(m, v2[k], v3[k])
                    myv2 = np.append(myv2, a[0])
                    myv3 = np.append(myv3, a[1])
                myv2 = np.array(myv2)
                myv3 = np.array(myv3)
            create_footprint(
                inputfile,
                myv2,
                myv3,
                24,
                outdir+'/ds9-short-threetight.reg',
                colshort)

        if dither_pattern_short == 'FULL6':
            shiftv2 = [-72.0, -43.0, -14.0, 15.0, 44.0, 73.0]
            shiftv3 = [-30.0, -18.0, -6.0, 6.0, 18.0, 30.0]

            # determine center of rotation using info from long dither pattern
            v2sh, v3sh, aper, v2ref, v3ref = read_table(os.path.join(PKG_DATA_DIR, 'table-nircam-long.txt'))
            v2sh = np.array(v2sh, np.float_)
            v3sh = np.array(v3sh, np.float_)

            v2 = v2sh + 73.0
            v3 = v3sh + 30.0
            xa = (v2[0] + v2[2]) / 2.0
            ya = (v3[0] + v3[2]) / 2.0
            v2 = v2sh - 72.0
            v3 = v3sh - 30.0
            xb = (v2[5] + v2[7]) / 2.0
            yb = (v3[5] + v3[7]) / 2.0
            xr = ((xa + xb) / 2.)
            yr = ((ya + yb) / 2.)

            v2sh, v3sh, aper, v2ref, v3ref = read_table(os.path.join(PKG_DATA_DIR, 'table-nircam-short.txt'))
            v2sh = np.array(v2sh, np.float_)
            v3sh = np.array(v3sh, np.float_)

            v2 = v2sh
            v3 = v3sh

            xr0 = xr
            yr0 = yr
            ra0 = ra_short
            dec0 = dec_short
            pa = theta_short+ 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            for shft in (0, 1, 2, 3, 4, 5):
                v20 = xr0 - (shiftv2[shft])  # here we shift
                v30 = yr0 + (shiftv3[shft])  # here we shift
                m = attitude(v20, v30, ra0, dec0, pa)
                for k in range(len(v2)):
                    a = pointing(m, v2[k], v3[k])
                    myv2 = np.append(myv2, a[0])
                    myv3 = np.append(myv3, a[1])
                myv2 = np.array(myv2)
                myv3 = np.array(myv3)
            create_footprint(
                inputfile,
                myv2,
                myv3,
                48,
                outdir+'/ds9-short-six.reg',
                colshort)


#  mosaic  short wavelength channel

        if (dither_pattern_short == 'FULL3' or dither_pattern_short ==
                'FULL3TIGHT' or dither_pattern_short == 'None') and mosaic == 'Yes':
            if dither_pattern_short == 'FULL3':
                shiftv3 = [0.0, -23.5, 23.5, usershiftv3 + 0.0,
                           usershiftv3 - 23.5, usershiftv3 + 23.5]
            if dither_pattern_short == 'FULL3TIGHT':
                shiftv3 = [0.0, -7.5, 7.5, usershiftv3 + 0.0,
                           usershiftv3 - 7.5, usershiftv3 + 7.5]

            shiftv2 = [0.0, -58.0, 58.0, usershiftv2 + 0.0,
                       usershiftv2 - 58.0, usershiftv2 + 58.0]

            if (dither_pattern_short == 'None'):
                shiftv3 = [0.0, usershiftv3 + 0.0]
                shiftv2 = [0.0, usershiftv2 + 0.0]
            v2 = v2sh
            v3 = v3sh

            # determine center of rotation
            v2 = np.append(v2, v2 + usershiftv2)
            v3 = np.append(v3, v3 + usershiftv3)
            ascii.write([v2, v3], 'values.dat')

            xa = (v2[0] + v2[22]) / 2.0
            ya = (v3[0] + v3[22]) / 2.0
            xb = (v2[8] + v2[26]) / 2.0
            yb = (v3[8] + v3[26]) / 2.0
            xr1 = ((xa + xb) / 2.)
            yr1 = ((ya + yb) / 2.)
            xa = (v2[40] + v2[62]) / 2.0
            ya = (v3[40] + v3[62]) / 2.0
            xb = (v2[48] + v2[66]) / 2.0
            yb = (v3[48] + v3[66]) / 2.0
            xr2 = ((xa + xb) / 2.)
            yr2 = ((ya + yb) / 2.)

            xr = ((xr1 + xr2) / 2.)
            yr = ((yr1 + yr2) / 2.)

            xr0 = xr
            yr0 = yr
            ra0 = ra_short
            dec0 = dec_short
            pa = theta_short+ 0.0265    #  12MAR2018  NRCALL_FULL_V2IdlYang = -0.0265
            myv2 = []
            myv3 = []
            v2 = v2sh
            v3 = v3sh
            for shft in range(len(shiftv2)):
                v20 = xr0 - (shiftv2[shft])  # here we shift
                v30 = yr0 + (shiftv3[shft])  # here we shift
                #print(v20, v30)
                m = attitude(v20, v30, ra0, dec0, pa)
                for k in range(len(v2)):
                    a = pointing(m, v2[k], v3[k])
                    myv2 = np.append(myv2, a[0])
                    myv3 = np.append(myv3, a[1])
                myv2 = np.array(myv2)
                myv3 = np.array(myv3)
            if (dither_pattern_short == 'None'):
                napertures = 16
            if (dither_pattern_short ==
                    'FULL3' or dither_pattern_short == 'FULL3TIGHT'):
                napertures = 48
            create_footprint(
                inputfile,
                myv2,
                myv3,
                napertures,
                outdir+'/ds9-short-mosaic.reg',
                colshort)
#  mosaic  short wavelength channel

    # Start xpans prior to running DS9
    pyds9.ds9_xpans()

    # Run DS9
    d = pyds9.DS9()
    d.set('tile yes')
    d.set('frame 1')
    d.set('cmap ' + ds9cmap)
    d.set('scale limits ' + ds9limmin + ' ' + ds9limmax)
    d.set('scale ' + ds9scale)
    d.set('file ' + inputfile)
    # load regions
    if plot_long == 'Yes':
        d.set('regions ' +outdir+'/ds9-long-centre.reg')
        if mosaic == 'No':
            if dither_pattern_long == 'FULL3TIGHT':
                d.set('regions ' +outdir+'/ds9-long-threetight.reg')
            if dither_pattern_long == 'FULL3':
                d.set('regions ' +outdir+'/ds9-long-three.reg')
            if dither_pattern_long == '8NIRSPEC':
                d.set('regions ' +outdir+'/ds9-long-8nirspec.reg')
            if dither_pattern_long == 'FULL6':
                d.set('regions ' +outdir+'/ds9-long-six.reg')
            if dither_pattern_long == 'None':
                d.set('regions ' +outdir+'/ds9-long-no.reg')
        if mosaic == 'Yes' and dither_pattern_long != '8NIRSPEC' :
            d.set('regions ' +outdir+'/ds9-long-mosaic.reg')
        if mosaic == 'Yes' and dither_pattern_long == '8NIRSPEC' :
            print('Mosaic pattern is disabled for 8NIRSPEC dither pattern')
    if plot_short == 'Yes':
        d.set('regions ' +outdir+'/ds9-short-centre.reg')
        if mosaic == 'No':
            if dither_pattern_short == 'FULL3TIGHT':
                d.set('regions ' +outdir+'/ds9-short-threetight.reg')
            if dither_pattern_short == 'FULL3':
                d.set('regions ' +outdir+'/ds9-short-three.reg')
            if dither_pattern_short == '8NIRSPEC':
                d.set('regions ' +outdir+'/ds9-short-8nirspec.reg')
            if dither_pattern_short == 'FULL6':
                d.set('regions ' +outdir+'/ds9-short-six.reg')
            if dither_pattern_short == 'None':
                d.set('regions ' +outdir+'/ds9-short-no.reg')
        if mosaic == 'Yes' and dither_pattern_short != '8NIRSPEC':
            d.set('regions ' +outdir+'/ds9-short-mosaic.reg')
        if mosaic == 'Yes' and dither_pattern_short == '8NIRSPEC':
            print('Mosaic pattern is disabled for 8NIRSPEC dither pattern')

    if plot_msa == 'Yes':
        d.set('regions ' +outdir+'/ds9-msa.reg')
        d.set('regions ' +outdir+'/ds9-msa-centre.reg')

    if plot_sources == 'Yes':
        if flagsources == 3:
            #print(plot_sources)
            d.set('regions ' +outdir+'/ds9-sources-fillers.reg')
            d.set('regions ' +outdir+'/ds9-sources-primary.reg')
        if flagsources == 2:
            #print(plot_sources)
            d.set('regions ' +outdir+'/ds9-sources.reg')
