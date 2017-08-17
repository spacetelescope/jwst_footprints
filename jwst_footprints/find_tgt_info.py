#! /usr/bin/env python
from __future__ import absolute_import, division, print_function

import os
import sys
import math

from . import ephemeris_old2x as EPH
from . import PKG_DATA_DIR

D2R = math.pi / 180.  # degrees to radians
R2D = 180. / math.pi  # radians to degrees
PI2 = 2. * math.pi   # 2 pi


def unit_limit(x): return min(max(-1., x), 1.)  # forces value to be in [-1,1]


def convert_ddmmss_to_float(astring):
    aline = aline.split(astring, ':')
    d = float(aline[0])
    m = float(aline[1])
    s = float(aline[2])
    hour_or_deg = (s / 60. + m) / 60. + d
    return hour_or_deg


def bound_angle(ang):
    while ang < 0.:
        ang += 360.
    while ang > 360.:
        ang -= 360.
    return ang


def angular_sep(obj1_c1, obj1_c2, obj2_c1, obj2_c2):
    """angular distance betrween two objects, positions specified in spherical coordinates."""
    x = math.cos(obj2_c2) * math.cos(obj1_c2) * math.cos(obj2_c1 -
                                                         obj1_c1) + math.sin(obj2_c2) * math.sin(obj1_c2)
    return math.acos(unit_limit(x))


def calc_ecliptic_lat(ra, dec):
    NEP_ra = 270.000000 * D2R
    NEP_dec = 66.560708 * D2R
    a_sep = angular_sep(ra, dec, NEP_ra, NEP_dec)
    ecl_lat = math.pi / 2. - a_sep
    return ecl_lat


def sun_pitch(aV):
    return math.atan2(aV.x, -aV.z)


def sun_roll(aV):
    return math.asin(-aV.y)


def allowed_max_sun_roll(sun_p):
    abs_max_sun_roll = 5.2 * D2R
    if sun_p > 2.5 * D2R:
        max_sun_roll = abs_max_sun_roll - 1.7 * D2R * \
            (sun_p - 2.5 * D2R) / (5.2 - 2.5) / D2R
    else:
        max_sun_roll = abs_max_sun_roll
    max_sun_roll -= 0.1 * D2R  # Pad away from the edge
    return max_sun_roll


def allowed_max_vehicle_roll(sun_ra, sun_dec, ra, dec):
    vehicle_pitch = math.pi / 2. - angular_sep(sun_ra, sun_dec, ra, dec)
    sun_roll = 5.2 * D2R
    last_sun_roll = 0.
    while abs(sun_roll - last_sun_roll) > 0.0001 * D2R:
        last_sun_roll = sun_roll
        sun_pitch = math.asin(
            unit_limit(
                math.sin(vehicle_pitch) /
                math.cos(last_sun_roll)))
        sun_roll = allowed_max_sun_roll(sun_pitch)
        # print sun_roll*R2D,sun_pitch*R2D,vehicle_pitch*R2D
    max_vehicle_roll = math.asin(
        unit_limit(
            math.sin(sun_roll) /
            math.cos(vehicle_pitch)))
    return max_vehicle_roll


def rollangle(ra, dec, outdir):
    NRCALL_FULL_V2IdlYang = -0.0265
    NRS_FULL_MSA_V3IdlYang = 137.4874
    NIS_V3IdlYang = -0.57
    MIRIM_FULL_V3IdlYang = 5.0152
    FGS1_FULL_V3IdlYang = -1.2508

    ECL_FLAG = False

    A_eph = EPH.Ephemeris(os.path.join(
        PKG_DATA_DIR, "horizons_EM_L2_wrt_Sun_2018_2022.txt"), ECL_FLAG)

    # search_start = 58484.00000000  #Jan 1, 2019
    search_start = 58392.00000000  # Oct 1, 2018         LEONARDO

    if search_start < A_eph.amin:
        print("Warning, search start time is earlier than ephemeris start.")
        search_start = A_eph.amin + 1

    scale = 10
    span = 365 * 3

    pa = "X"
    ra = float(ra) * D2R
    dec = float(dec) * D2R

    if len(sys.argv) > 3:
        pa = float(sys.argv[3]) * D2R
    # print "Checked interval [%f,%f] MJD" % (search_start,search_start+span)
    if pa == "X":
        iflag_old = A_eph.in_FOR(search_start, ra, dec)
    # print "|           Window [days]              |         Normal V3 PA
    # [deg]|"
    else:
        iflag_old = A_eph.is_valid(search_start, ra, dec, pa)
    # print "|           Window [days]              |         Specified V3 PA
    # [deg]|"

    # print "   Start[MJD]      End[MJD]    Duration         Start         End
    # coord1        coord2"

    if iflag_old:
        twstart = search_start
    else:
        twstart = -1.
    iflip = False

    # Step througth the interval and find where target goes in/out of field of
    # regard.
    for i in range(1, span * scale + 1):
        adate = search_start + float(i) / float(scale)
        # iflag = A_eph.in_FOR(adate,ra,dec)
        if pa == "X":
            iflag = A_eph.in_FOR(adate, ra, dec)
        else:
            iflag = A_eph.is_valid(adate, ra, dec, pa)
        if iflag != iflag_old:
            iflip = True
            if iflag:
                if pa == "X":
                    twstart = A_eph.bisect_by_FOR(adate, adate - 0.1, ra, dec)
                else:
                    twstart = A_eph.bisect_by_attitude(
                        adate, adate - 0.1, ra, dec, pa)
            else:
                if pa == "X":
                    wend = A_eph.bisect_by_FOR(adate - 0.1, adate, ra, dec)
                else:
                    wend = A_eph.bisect_by_attitude(
                        adate - 0.1, adate, ra, dec, pa)
                if twstart > 0.:
                    wstart = twstart  # Only set wstart if wend is valid
                    if pa == "X":
                        pa_start = A_eph.normal_pa(wstart, ra, dec)
                        pa_end = A_eph.normal_pa(wend, ra, dec)
                    else:
                        pa_start = pa
                        pa_end = pa
                    # print "%13.5f %13.5f %11.2f %13.5f %13.5f %13.5f %13.5f "
                    # %
                    # (wstart,wend,wend-wstart,pa_start*R2D,pa_end*R2D,ra*R2D,dec*R2D)
            iflag_old = iflag

    if iflip and iflag:
        if pa == "X":
            pa_start = A_eph.normal_pa(twstart, ra, dec)
            pa_end = A_eph.normal_pa(adate, ra, dec)
        else:
            pa_start = pa
            pa_end = pa
    # print "%13.5f %13.5f %11.2f %13.5f %13.5f %13.5f %13.5f " %
    # (twstart,adate,adate-twstart,pa_start*R2D,pa_end*R2D,ra*R2D,dec*R2D)

    '''
        if iflip == False and iflag == True and pa == "X":
            if dec >0.:
                print "%13s %13s %11s %13.5f %13.5f %13.5f %13.5f " % ('CVZ','CVZ','CVZ',360.,0.,ra*R2D,dec*R2D)
            else:
                print "%13s %13s %11s %13.5f %13.5f %13.5f %13.5f " % ('CVZ','CVZ','CVZ',0.,360.,ra*R2D,dec*R2D)
    '''
    if 1 == 1:
        wstart = search_start
        wend = wstart + span
        istart = int(wstart)
        iend = int(wend)
        iflag = A_eph.in_FOR(wstart, ra, dec)
        tgt_is_in = False
        if iflag:
            tgt_is_in = True
        # print()
        # print()
        # print "             V3PA          NIRCam           NIRSpec         NIRISS           MIRI          FGS"
        # print "   MJD    min    max      min    max      min    max      min    max      min    max      min    max"
        # 58849.0 264.83 275.18 264.80 264.80  42.32  42.32 264.26 264.26
        # 269.84 269.84 263.58 263.58
        # verify that outdir exists

        if not os.path.exists(outdir):
            os.makedirs(outdir, mode=0o0755)
            print("creating directory {}".format(outdir))

        outputfile = os.path.join(outdir, 'v3pa_nircam_nirspec.txt')
        print(outputfile)

        with open(outputfile, "w") as fp:
            # pos = 0
            # for i in range(0,napertures):
            #        newline = 'polygon '+ str(x[pos])+ '  '+ str(y[pos])+ '  '+ str(x[pos+1])+ '  '+ str(y[pos+1])+ '  '+ str(x[pos+2])+ '  '+ str(y[pos+2])+ '  '+ str(x[pos+3])+ '  '+ str(y[pos+3])+ '  '+ str(x[pos+4])+ '  '+ str(y[pos+4])+ '  ' +  '# text={}'+'\n'
            #        fp.write(newline)
            #        pos = pos + 5

            for itime in range(istart, iend):
                atime = float(itime)
                iflag = A_eph.in_FOR(atime, ra, dec)
                # print atime,A_eph.in_FOR(atime,ra,dec)
                if iflag:
                    if not tgt_is_in:
                        print()
                    tgt_is_in = True

                    V3PA = A_eph.normal_pa(atime, ra, dec) * R2D
                    (sun_ra, sun_dec) = A_eph.sun_pos(atime)
                    max_boresight_roll = allowed_max_vehicle_roll(
                        sun_ra, sun_dec, ra, dec) * R2D

                    minV3PA = bound_angle(V3PA - max_boresight_roll)
                    maxV3PA = bound_angle(V3PA + max_boresight_roll)
                    # minNIRCam_PA = bound_angle(V3PA - max_boresight_roll + NRCALL_FULL_V2IdlYang)
                    # maxNIRCam_PA = bound_angle(V3PA - max_boresight_roll + NRCALL_FULL_V2IdlYang)
                    # minNIRSpec_PA = bound_angle(V3PA - max_boresight_roll + NRS_FULL_MSA_V3IdlYang)
                    # maxNIRSpec_PA = bound_angle(V3PA - max_boresight_roll + NRS_FULL_MSA_V3IdlYang)
                    # minNIRISS_PA = bound_angle(V3PA - max_boresight_roll + NIS_V3IdlYang)
                    # maxNIRISS_PA = bound_angle(V3PA - max_boresight_roll + NIS_V3IdlYang)
                    # minMIRI_PA = bound_angle(V3PA - max_boresight_roll + MIRIM_FULL_V3IdlYang)
                    # maxMIRI_PA = bound_angle(V3PA - max_boresight_roll + MIRIM_FULL_V3IdlYang)
                    # minFGS_PA = bound_angle(V3PA - max_boresight_roll + FGS1_FULL_V3IdlYang)
                    # maxFGS_PA = bound_angle(V3PA - max_boresight_roll + FGS1_FULL_V3IdlYang)

                    minNIRCam_PA = bound_angle(
                        V3PA - max_boresight_roll + NRCALL_FULL_V2IdlYang)
                    maxNIRCam_PA = bound_angle(
                        V3PA + max_boresight_roll + NRCALL_FULL_V2IdlYang)
                    minNIRSpec_PA = bound_angle(
                        V3PA - max_boresight_roll + NRS_FULL_MSA_V3IdlYang)
                    maxNIRSpec_PA = bound_angle(
                        V3PA + max_boresight_roll + NRS_FULL_MSA_V3IdlYang)
                    minNIRISS_PA = bound_angle(
                        V3PA - max_boresight_roll + NIS_V3IdlYang)
                    maxNIRISS_PA = bound_angle(
                        V3PA + max_boresight_roll + NIS_V3IdlYang)
                    minMIRI_PA = bound_angle(
                        V3PA - max_boresight_roll + MIRIM_FULL_V3IdlYang)
                    maxMIRI_PA = bound_angle(
                        V3PA + max_boresight_roll + MIRIM_FULL_V3IdlYang)
                    minFGS_PA = bound_angle(
                        V3PA - max_boresight_roll + FGS1_FULL_V3IdlYang)
                    maxFGS_PA = bound_angle(
                        V3PA + max_boresight_roll + FGS1_FULL_V3IdlYang)

                    # fmt = '%7.1f' + '   %6.2f %6.2f' * 6
                    # print(
                    #    fmt %
                    #    (atime,
                    #     minV3PA,
                    #     maxV3PA,
                    #     minNIRCam_PA,
                    #     maxNIRCam_PA,
                    #     minNIRSpec_PA,
                    #     maxNIRSpec_PA,
                    #     minNIRISS_PA,
                    #     maxNIRISS_PA,
                    #     minMIRI_PA,
                    #     maxMIRI_PA,
                    #     minFGS_PA,
                    #     maxFGS_PA))
                    newline = str(atime) + '   ' + str(minV3PA) + \
                        ' ' + str(maxV3PA) + '  ' + str(minNIRCam_PA) + \
                        '  ' + str(maxNIRCam_PA) + '  ' + str(minNIRSpec_PA) + \
                        '  ' + str(maxNIRSpec_PA) + '  \n'

                    fp.write(newline)

                else:
                    tgt_is_in = False

    return ra, dec
