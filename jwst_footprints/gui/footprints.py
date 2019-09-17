#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, division, print_function

import json
import os

from .. import PKG_DATA_DIR, CONFIG_DIR, CONFIG_FILE
from ..footprints import footprints
from ..defaults import default_config
from ..plot_timeline import plottimeline

try:
    from Tkinter import (Tk, Button, Entry, Label, OptionMenu, StringVar, \
                         Toplevel, TRUE, FALSE)
    from tkFileDialog import askopenfilename
except ImportError as e:
    from tkinter.filedialog import askopenfilename
    from tkinter import (Tk, Button, Entry, Label, OptionMenu, StringVar, \
                         Toplevel, TRUE, FALSE)

from PIL import ImageTk


class Config(object):
    def __init__(self, filename=CONFIG_FILE):
        self.filename = os.path.abspath(filename)
        self.exists = False
        self.data = {}

        self._check()
        self._parse()

    def __getitem__(self, x):
        if x in self.data:
            return self.data[x]

    def __setitem__(self, k, v):
        self.data[k] = v

    def _check(self):
        if CONFIG_DIR in CONFIG_FILE:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR, mode=0o0755)

        if os.path.exists(self.filename):
            self.exists = True

    def _parse(self):
        # If we already have a config file, but haven't populated the data,
        # then do so:
        if self.exists and not self.data:
            with open(self.filename, 'r') as cfg:
                self.data = json.load(cfg)

        # Use pre-determined configuration, but generate a new user-config
        # based on it:
        elif not self.exists:
            self.data = default_config
            self.commit()

    def commit(self):
        with open(self.filename, 'w+') as cfg:
            json.dump(self.data, cfg, sort_keys=True, indent=4)


class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """

    def __init__(self, widget, text='widget info'):
        self.waittime = 500  # miliseconds
        self.wraplength = 180  # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tw, text=self.text, justify='left',
                      background="#ffffff", relief='solid', borderwidth=0,
                      wraplength=self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


class FootprintsUI(object):
    def __init__(self, master):
        self.config = Config()
        self.master = master
        self.master.resizable(width=FALSE, height=FALSE)
        self.master.title('NIRspec Observation Visualization Tool')
        self.background = ImageTk.PhotoImage(file=os.path.join(PKG_DATA_DIR, "back-08.png"))

        w = self.background.width()
        h = self.background.height()

        # position coordinates of root 'upper left corner'
        x = 0
        y = 0

        # make the root window the size of the image
        self.master.geometry("%dx%d+%d+%d" % (w, h, x, y))
        # root has no image argument, so use a label as a panel
        self.panel1 = Label(self.master, image=self.background)
        # panel1.pack(side='top', fill='both', expand='Yes')
        self.panel1.place(x=0, y=0)
        # panel1.image = image1


        # assigning values to colors
        self.colmsaVar = StringVar()
        self.colmsaVar.set(self.config['color_msa'])
        self.colshortVar = StringVar()
        self.colshortVar.set(self.config['color_short'])
        self.collongVar = StringVar()
        self.collongVar.set(self.config['color_long'])

        self.readfitsimageVar = StringVar()
        self.readfitsimageVar.set(self.config['readfitsimage'])
      #  print(readfitsimageVar)


        self.labplotsources = Label(self.master, text=" Catalog on ?")
        self.labplotsources.place(relx=0.44, rely=0.26, anchor="w")
        self.plotsourcesVar = StringVar()
        self.plotsourcesVar.set(self.config['plot_src'])
        self.pt = OptionMenu(self.master, self.plotsourcesVar, 'Yes', 'No')
        self.pt.place(relx=0.29, rely=0.26, anchor="w")

        self.labplotmsa = Label(self.master, text="MSA footprint on ?")
        self.labplotmsa.place(relx=0.65, rely=0.38, anchor="w")
        self.plotmsaVar = StringVar()
        self.plotmsaVar.set(self.config['plot_msa'])
        self.pt = OptionMenu(self.master, self.plotmsaVar, 'Yes', 'No')
        self.pt.place(relx=0.35, rely=0.38, anchor="w")

        self.colmsaVar = StringVar()
        self.colmsaVar.set(self.config['color_msa'])
        self.colmsa = OptionMenu(self.master, self.colmsaVar, 'Red', 'Cyan', 'Blue', 'Yellow','Green')
        self.colmsa.config(width=9)
        self.colmsa.place(relx=0.49, rely=0.38, anchor="w")


        self.labramsa = Label(self.master, text="RA center of MSA")
        self.labramsa.place(relx=0.65, rely=0.42, anchor="w")
        self.ramsaVar = StringVar()
        self.ramsaVar.set(self.config['ra_nirspec'])
        self.ramsa = Entry(self.master, textvariable=self.ramsaVar)
        self.ramsa.place(relx=0.35, rely=0.42, anchor="w")

        self.ramsa_ttp = CreateToolTip(self.ramsa,
                                       'Enter RA value.\nxxx.xxxx (degrees)\nhh mm ss.sss')

        self.labdecmsa = Label(self.master, text="DEC center of MSA")
        self.labdecmsa.place(relx=0.65, rely=0.46, anchor="w")
        self.decmsaVar = StringVar()
        self.decmsaVar.set(self.config['dec_nirspec'])
        self.decmsa = Entry(self.master, textvariable=self.decmsaVar)
        self.decmsa.place(relx=0.35, rely=0.46, anchor="w")
        self.decmsa_ttp = CreateToolTip(self.decmsa,
                                        'Enter DEC value.\nxxx.xxxx (degrees)\nhh mm ss.sss')

        self.labthmsa = Label(self.master, text="MSA aperture PA")
        self.labthmsa.place(relx=0.65, rely=0.50, anchor="w")
        self.thmsaVar = StringVar()
        self.thmsaVar.set(self.config['theta_nirspec'])
        self.thmsa = Entry(self.master, textvariable=self.thmsaVar)
        self.thmsa.place(relx=0.35, rely=0.50, anchor="w")
        self.thmsa_ttp = CreateToolTip(self.thmsa,
                                       'Enter MSA Aperture PA value in degrees')

        self.labplotshort = Label(self.master, text="Short channel on ?")
        self.labplotshort.place(relx=0.65, rely=0.61, anchor="w")
        self.plotshortVar = StringVar()
        self.plotshortVar.set(self.config['plot_short'])
        self.pt = OptionMenu(self.master, self.plotshortVar, 'Yes', 'No')
        self.pt.config(width=8)
        self.pt.place(relx=0.35, rely=0.61, anchor="w")

        self.labplotlong = Label(self.master, text="Long channel on ?")
        self.labplotlong.place(relx=0.65, rely=0.65, anchor="w")
        self.plotlongVar = StringVar()
        self.plotlongVar.set(self.config['plot_long'])
        self.pt = OptionMenu(self.master, self.plotlongVar, 'Yes', 'No')
        self.pt.config(width=8)
        self.pt.place(relx=0.35, rely=0.65, anchor="w")

        self.labranrcm = Label(self.master, text="RA center of NIRCam")
        self.labranrcm.place(relx=0.65, rely=0.69, anchor="w")
        self.ranrcmVar = StringVar()
        self.ranrcmVar.set(self.config['ra_nircam'])
        self.ranrcm = Entry(self.master, textvariable=self.ranrcmVar)
        self.ranrcm.place(relx=0.35, rely=0.69, anchor="w")
        self.ranrcm_ttp = CreateToolTip(self.ranrcm,
                                        'Enter RA value.\nxxx.xxxx (degrees)\nhh mm ss.sss')

        self.labdecnrcm = Label(self.master, text="DEC center of NIRCam")
        self.labdecnrcm.place(relx=0.65, rely=0.73, anchor="w")
        self.decnrcmVar = StringVar()
        self.decnrcmVar.set(self.config['dec_nircam'])
        self.decnrcm = Entry(self.master, textvariable=self.decnrcmVar)
        self.decnrcm.place(relx=0.35, rely=0.73, anchor="w")
        self.decnrcm_ttp = CreateToolTip(self.decnrcm,
                                         'Enter DEC value.\nxxx.xxxx (degrees)\nhh mm ss.sss')
        self.labthnrcm = Label(self.master, text="NIRCam aperture PA")
        self.labthnrcm.place(relx=0.65, rely=0.77, anchor="w")
        self.thnrcmVar = StringVar()
        self.thnrcmVar.set(self.config['theta_nircam'])
        self.thnrcm = Entry(self.master, textvariable=self.thnrcmVar)
        self.thnrcm.place(relx=0.35, rely=0.77, anchor="w")
        self.thnrcm_ttp = CreateToolTip(self.thnrcm,
                                        'Enter NIRCam Aperture PA value in degrees')

        self.labdither = Label(self.master, text="NIRCam dither pattern")
        self.labdither.place(relx=0.02, rely=0.81, anchor="w")
        self.ditherVar = StringVar()
        self.ditherVar.set(self.config['dither'])
        self.pt = OptionMenu(self.master, self.ditherVar, 'None', 'FULL3', 'FULL3TIGHT', 'FULL6', '8NIRSPEC')
        self.pt.place(relx=0.35, rely=0.81, anchor="w")

        self.labmosaic = Label(self.master, text="NIRCam mosaic")
        self.labmosaic.place(relx=0.02, rely=0.87, anchor="w")
        self.mosaicVar = StringVar()
        self.mosaicVar.set(self.config['mosaic'])
        self.pt = OptionMenu(self.master, self.mosaicVar, 'No', 'Yes')
        self.pt.place(relx=0.35, rely=0.87, anchor="w")

        self.laboffhor = Label(self.master, text="Offset")
        self.laboffhor.place(relx=0.50, rely=0.85, anchor="w")
        self.offhorVar = StringVar()
        self.offhorVar.set(self.config['off_h'])
        self.offhor = Entry(self.master, textvariable=self.offhorVar)
        self.offhor.place(relx=0.65, rely=0.85, anchor="w")
        self.offhor_ttp = CreateToolTip(self.offhor,
                                        'Enter NIRCam offset in arcsec')

        self.laboffver = Label(self.master, text="Offset")
        self.laboffver.place(relx=0.50, rely=0.89, anchor="w")
        self.offverVar = StringVar()
        self.offverVar.set(self.config['off_v'])
        self.offver = Entry(self.master, textvariable=self.offverVar)
        self.offver.place(relx=0.65, rely=0.89, anchor="w")
        self.offver_ttp = CreateToolTip(self.offver,
                                        'Enter NIRCam offset in arcsec')




        self.ptVar = StringVar()
        self.ptVar.set('footprints')

        self.b5 = Button(self.master, text=" Select File ", command=self.readfitsfilename)
        self.b5.place(relx=0.43, rely=0.12, anchor="w")

        self.fileVar = StringVar()
        self.fileVar.set(self.config['fits_name'])
        self.filevalue = Entry(self.master, textvariable=self.fileVar, width=40, justify='left')
        self.filevalue.place(relx=0.02, rely=0.15, anchor="w")

        self.b6 = Button(self.master, text=" Select File ", command=self.readcataloguename)
        self.b6.place(relx=0.43, rely=0.295, anchor="w")
        self.catVar = StringVar()
        self.catVar.set(self.config['cat_name'])
        self.catvalue = Entry(self.master, textvariable=self.catVar, width=28, justify='left')
        self.catvalue.place(relx=0.02, rely=0.295, anchor="w")

        self.b7 = Button(self.master, text="View Timeline", command=self.maketimeline)
        self.b7.place(relx=0.6, rely=0.96, anchor="w")
        self.b3 = Button(self.master, text=" Quit ", command=self.quit)
        self.b3.place(relx=0.2, rely=0.96, anchor="w")

        self.b4 = Button(self.master, text=" Display ", command=self.makefootprints)
        self.b4.place(relx=0.8, rely=0.96, anchor="w")


        self.outdirVar = StringVar()
        self.outdirVar.set(self.config['out_dir'])
        self.outdirvalue = Entry(self.master, textvariable=self.outdirVar, width=40, justify='left')
        self.outdirvalue.place(relx=0.02, rely=0.219, anchor="w")
        #self.laboutdir = Label(self.master, text="Output directory")
        #self.laboutdir.place(relx=0.02, rely=0.25, anchor="w")
      

        self.colshortVar = StringVar()
        self.colshortVar.set(self.config['color_short'])
        self.colshort = OptionMenu(self.master, self.colshortVar, 'Green', 'Cyan','Blue','Yellow','Red')
        self.colshort.config(width=9)
        self.colshort.place(relx=0.49, rely=0.61, anchor="w")

        self.collongVar = StringVar()
        self.collongVar.set(self.config['color_long'])
        self.collong = OptionMenu(self.master, self.collongVar, 'Blue', 'Cyan','Green','Yellow','Red')
        self.collong.config(width=9)
        self.collong.place(relx=0.49, rely=0.65, anchor="w")

 

        self.labcmap= Label(self.master, text="Colour Map")
        self.labcmap.place(relx=0.65, rely=0.18, anchor="w")
        self.ds9cmapVar = StringVar()
        self.ds9cmapVar.set(self.config['cmap'])
        self.ds9cmap = OptionMenu(self.master, self.ds9cmapVar, 'grey', 'red', 'green', 'blue', 'heat')
        self.ds9cmap.place(relx=0.80, rely=0.18, anchor="w")
        self.ds9cmap.config(width=10)


        self.labscale = Label(self.master, text="Scale")
        self.labscale.place(relx=0.65, rely=0.21, anchor="w")
        self.ds9scaleVar = StringVar()
        self.ds9scaleVar.set(self.config['scale'])
        self.ds9scale = OptionMenu(self.master, self.ds9scaleVar, 'log', 'linear', 'power', 'sqrt', 'zscale', 'minmax')
        self.ds9scale.place(relx=0.80, rely=0.21, anchor="w")
        self.ds9scale.config(width=10)

        self.ds9limmin = Label(self.master, text="Low")
        self.ds9limmin.place(relx=0.65, rely=0.24, anchor="w")
        self.ds9limminVar = StringVar()
        self.ds9limminVar.set(self.config['lim_min'])
        self.ds9limmin = Entry(self.master, textvariable=self.ds9limminVar)
        self.ds9limmin.place(relx=0.80, rely=0.24, anchor="w")
        self.ds9limmin.config(width=10)
       
        self.ds9limmax = Label(self.master, text="High")
        self.ds9limmax.place(relx=0.65, rely=0.27, anchor="w")
        self.ds9limmaxVar = StringVar()
        self.ds9limmaxVar.set(self.config['lim_max'])
        self.ds9limmax = Entry(self.master, textvariable=self.ds9limmaxVar)
        self.ds9limmax.place(relx=0.80, rely=0.27, anchor="w")
        self.ds9limmax.config(width=10)
  

    def quit(self):
        self.config['fits_name'] = self.fileVar.get()
        self.config['cat_name'] = self.catVar.get()
        self.config['plot_long'] = self.plotlongVar.get()
        self.config['plot_short'] = self.plotshortVar.get()
        self.config['plot_msa'] = self.plotmsaVar.get()
        self.config['plot_src'] = self.plotsourcesVar.get()
        self.config['ra_nircam'] = self.ranrcmVar.get()
        self.config['dec_nircam'] = self.decnrcmVar.get()
        self.config['theta_nircam'] = float(self.thnrcmVar.get())
        self.config['dither'] = self.ditherVar.get()
        self.config['ra_nirspec'] = self.ramsaVar.get()
        self.config['dec_nirspec'] = self.decmsaVar.get()
        self.config['theta_nirspec'] = float(self.thmsaVar.get())
        self.config['mosaic'] = self.mosaicVar.get()
        self.config['off_h'] = float(self.offhorVar.get())
        self.config['off_v'] = float(self.offverVar.get())
        self.config['color_msa'] = self.colmsaVar.get()
        self.config['color_short'] = self.colshortVar.get()
        self.config['color_long'] = self.collongVar.get()
        self.config['cmap'] = self.ds9cmapVar.get()
        self.config['lim_min'] = float(self.ds9limminVar.get())
        self.config['lim_max'] = float(self.ds9limmaxVar.get())
        self.config['scale'] = self.ds9scaleVar.get()
        
        self.config.commit()
        self.master.quit()

    def makefootprints(self):
        if self.ptVar.get() == 'footprints':
            #print(self.catVar.get())
            footprints(self.fileVar.get(),
                       self.catVar.get(),
                       self.plotlongVar.get(),
                       self.plotshortVar.get(),
                       self.plotmsaVar.get(),
                       self.plotsourcesVar.get(),
                       self.ranrcmVar.get(),
                       self.decnrcmVar.get(),
                       float(self.thnrcmVar.get()),
                       self.ditherVar.get(),
                       self.ramsaVar.get(),
                       self.decmsaVar.get(),
                       float(self.thmsaVar.get()),
                       self.mosaicVar.get(),
                       self.offhorVar.get(),
                       self.offverVar.get(),
                       self.colmsaVar.get(),
                       self.colshortVar.get(),
                       self.collongVar.get(),
                       self.ds9cmapVar.get(),
                       self.ds9limminVar.get(),
                       self.ds9limmaxVar.get(),
                       self.ds9scaleVar.get(),
                       self.outdirVar.get())
                       #self.readfitsimageVar.get())

    def readcataloguename(self):
        Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        # show an "Open" dialog box and return the path to the selected file
        filename = askopenfilename(initialdir=os.path.abspath(os.curdir),
                                   title='Select RADEC file',
                                   filetypes=(('RADEC files', '*.radec'),
                                              ('all files', '*.*')))

        #print(filename)
        self.catVar.set(filename)

        catvalue = Entry(self.master, textvariable=self.catVar, width=28, justify='right')
        catvalue.place(relx=0.02, rely=0.295, anchor="w")

    def readfitsfilename(self):
        #readfitsimage =True     # set variable to read new image

        Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        # show an "Open" dialog box and return the path to the selected file
        filename = askopenfilename(initialdir=os.path.abspath(os.curdir),
                                   title='Select FITS file',
                                   filetypes=(('FITS files', '*.fits'),
                                              ('all files', '*.*')))
        #print(filename)
        self.fileVar.set(filename)

        filevalue = Entry(self.master, textvariable=self.fileVar, width=40, justify='right')
        filevalue.place(relx=0.02, rely=0.15, anchor="w")

    def maketimeline(self):
        #print(self.ramsaVar.get())
        plottimeline(self.ramsaVar.get(),
                     self.decmsaVar.get(),
                     float(self.thmsaVar.get()),
                     self.outdirVar.get())


def main():
    root = Tk()
    FootprintsUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
