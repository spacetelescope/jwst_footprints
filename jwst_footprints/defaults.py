default_config = dict(
    #
    # Input filenames
    #
    fits_name='/Users/change-me/',
    cat_name='',
    out_dir='/Users/change-me/',
    #
    # to plot or not to plot ?
    #
    plot_names=['plot'],
    plot_msa="No",
    plot_short="No",
    plot_long="No",
    plot_src="No",
    dither="None",
    mosaic="No",
    #
    # color lines
    #
    color_msa='Red',
    color_short='Green',
    color_long='Blue',
    #
    # fiducial point equatorial coordinates
    # in degrees
    #
    ra_nircam=202.46959,
    dec_nircam=47.195187,
    theta_nircam=0.0,

    ra_nirspec=202.46959,
    dec_nirspec=47.195187,
    theta_nirspec=0.0,
    #
    # nircam dither offset
    #
    off_h=10.0,
    off_v=0.0,
    #
    # DS9 display
    #
    cmap='grey',    # grey, red, green, blue, heat
    lim_min=0.0,
    lim_max=100.0,
    scale='log'     # linear, log, power, squared
)
