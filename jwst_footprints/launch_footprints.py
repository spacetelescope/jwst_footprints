#!/usr/bin/env python
# encoding: utf-8


from tkinter import *
import tkinter as tk
import tkinter.constants, tkinter.filedialog
from tkinter import Tk
from tkinter.filedialog import askopenfilename


import io
import base64
from PIL import Image, ImageTk
import PIL.Image
from .footprints   import *
from .inputdata  import *

import shutil, sys, os

from astropy.io import ascii
from .plot_timeline  import *


global catalogue



class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
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
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=0,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()


def readcataloguename():
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file
    print(filename)
    catVar.set(filename)

    catvalue = tk.Entry(win,textvariable=catVar,width=40,justify='right')
    catvalue.place(relx=0.02, rely=0.24, anchor="w")
 
def readfitsfilename():
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file
    print(filename)
    pos= filename.rfind('/')
    name = filename[pos+1:]
    fileVar.set(filename)
    filevalue = tk.Entry(win,textvariable=fileVar,width=40,justify='right') #,background="#336699",relief='solid', borderwidth=3)
    filevalue.place(relx=0.02, rely=0.15, anchor="w")
    


def makefootprints():
    if ptVar.get() == 'footprints':
        print(catVar.get())
        footprints(\
        fileVar.get(),\
        catVar.get(),\
        plotlongVar.get(),\
        plotshortVar.get(),\
        plotmsaVar.get(),\
        plotsourcesVar.get(),\
        float(ranrcmVar.get()),\
        float(decnrcmVar.get()),\
        float(thnrcmVar.get()),\
        ditherVar.get(),\
        float(ramsaVar.get()),\
        float(decmsaVar.get()),\
        float(thmsaVar.get()),\
        mosaicVar.get(),\
        offhorVar.get(),\
        offverVar.get(),\
        colmsaVar.get(),\
        colshortVar.get(),\
        collongVar.get(),\
        ds9cmapVar.get(),\
        ds9limminVar.get(),\
        ds9limmaxVar.get(),\
        ds9scaleVar.get())




def maketimeline():
        print(ramsaVar.get())
        plottimeline(\
        float(ramsaVar.get()),\
        float(decmsaVar.get()),\
        float(thmsaVar.get()))     
 



def loadom(value) :
    #global name
    name = variable.get()
    pt = plotmsa[variable.get()]
    ptshort = plotshort[variable.get()]
    ptlong = plotlong[variable.get()]
    ptsources = plotsrc[variable.get()]
    ptdither = dither[variable.get()]
    ptmosaic = mosaic[variable.get()]
    ranircam = ranircam[variable.get()]
    decnircam = decnircam[variable.get()]
    thetanircam = thetanircam[variable.get()]
    ramsa = ranirspec[variable.get()]
    decmsa = decnirspec[variable.get()]
    thetamsa = thetanirspec[variable.get()]
    catalogue = catname[variable.get()]
    fitsname = fitsname[variable.get()]
    colmsa = colormsa[variable.get()]
    collong = colorlong[variable.get()]
    colshort = colorshort[variable.get()]

    ds9cmap = cmap[variable.get()]
    ds9limmin = limmin[variable.get()]
    ds9limmax = limmax[variable.get()]
    ds9scale = scale[variable.get()]
    
    ds9cmapVar.set(ds9cmap)
    ds9limminVar.set(ds9limmin)
    ds9limmaxVar.set(ds9limmax)
    ds9scaleVar.set(ds9scale)

    colshortVar.set(colshort)
    collongVar.set(collong)
    plotmsaVar.set(pt)
    plotshortVar.set(ptshort)
    plotlongVar.set(ptlong)
    plotsourcesVar.set(ptsources)
    ditherVar.set(ptdither)
    mosaicVar.set(ptmosaic)
    ranrcmVar.set(ranircam)
    decnrcmVar.set(decnircam)
    thnrcmVar.set(thetanircam)
    ramsaVar.set(ramsa)
    decmsaVar.set(decmsa)
    thmsaVar.set(thetamsa)
    fileVar.set(fitsname)
    cataVar.set(catalogue)
    offhorVar.set(offh)
    offverVar.set(offv)
    colmsaVar.set(colormsa)

# sys.exit("quitting now...")

   

def makeWindow() :
   # global nameVar, xminVar, xmaxVar, variable, ptVar, select
    global w, ranrcmVar, decnrcmVar, thnrcmVar, variable, ptVar, select
    global colshortVar,collongVar, image1
    global ramsaVar, decmsaVar, infileVar, thmsaVar,plotmsaVar,plotshortVar 
    global vminVar, vmaxVar, CheckLong, CheckShort, CheckNirspec
    global fileVar, offhorVar
    global plotlongVar, ditherVar,filepathVar,catVar, plotsourcesVar
    global mosaicVar, offverVar, colmsaVar
    global ds9cmapVar, ds9limminVar, ds9limmaxVar, ds9scaleVar

    win = Tk()
    win.resizable(width=FALSE, height=FALSE)
    win.title('STScI JWST/NIRspec visualization tool')

    #im = base64.b64decode(encoded)
    #file_like = cStringIO.StringIO(im)
    #image = PIL.Image.open(file_like)
    #image.save('test.png')
    #image1 = ImageTk.PhotoImage(Image.open("test.png"))
    image1 = ImageTk.PhotoImage(Image.open("back-04.png"))
   
    w = image1.width()
    h = image1.height()
     
    # position coordinates of root 'upper left corner'
    x = 0
    y = 0
     
    # make the root window the size of the image
    win.geometry("%dx%d+%d+%d" % (w, h, x, y))
    # root has no image argument, so use a label as a panel
    panel1 = tk.Label(win, image=image1)
    #panel1.pack(side='top', fill='both', expand='yes')
    panel1.place(x=0, y=0)
   # panel1.image = image1 


    # assigning values to colors
    colmsaVar= StringVar()
    colmsaVar.set(colormsa[plotnames[0]])
    colshortVar= StringVar()
    colshortVar.set(colorshort[plotnames[0]])
    collongVar= StringVar()
    collongVar.set(colorlong[plotnames[0]])
    
    # assigning values to ds9 variable

    ds9cmapVar = StringVar()
    ds9cmapVar.set(cmap[plotnames[0]])
    ds9limminVar = StringVar()
    ds9limminVar.set(limmin[plotnames[0]])
    ds9limmaxVar = StringVar()
    ds9limmaxVar.set(limmax[plotnames[0]])
    ds9scaleVar = StringVar()
    ds9scaleVar.set(scale[plotnames[0]])

    labplotsources = tk.Label(win, text=" Catalog on ?")   
    labplotsources.place(relx=0.65, rely=0.20, anchor="w")
    plotsourcesVar = StringVar()
    plotsourcesVar.set('no')
    pt = OptionMenu(win, plotsourcesVar, 'yes','no')
    pt.place(relx=0.35, rely=0.20, anchor="w")

    labplotmsa = tk.Label(win, text="MSA footprint on ?")   
    labplotmsa.place(relx=0.65, rely=0.34, anchor="w")
    plotmsaVar = StringVar()
    plotmsaVar.set('no')
    pt = OptionMenu(win, plotmsaVar, 'yes','no')
    pt.place(relx=0.35, rely=0.34, anchor="w")

    labramsa = tk.Label(win, text="RA center of MSA")
    labramsa.place(relx=0.65, rely=0.38, anchor="w")
    ramsaVar= StringVar()
    ramsaVar.set(ranirspec[plotnames[0]])
    ramsa = tk.Entry(win, textvariable=ramsaVar)
    ramsa.place(relx=0.35, rely=0.38, anchor="w")

    ramsa_ttp = CreateToolTip(ramsa, \
    'Enter RA value in degrees')

    labdecmsa = tk.Label(win, text="DEC center of MSA")
    labdecmsa.place(relx=0.65, rely=0.42 ,anchor="w")
    decmsaVar= StringVar()
    decmsaVar.set(decnirspec[plotnames[0]])
    decmsa = tk.Entry(win, textvariable=decmsaVar)
    decmsa.place(relx=0.35, rely=0.42, anchor="w")
    decmsa_ttp = CreateToolTip(decmsa, \
    'Enter DEC value in degrees')

    labthmsa = tk.Label(win, text="MSA aperture PA")
    labthmsa.place(relx=0.65, rely=0.46, anchor="w")
    thmsaVar= StringVar()
    thmsaVar.set(thetanirspec[plotnames[0]])
    thmsa = tk.Entry(win, textvariable=thmsaVar)
    thmsa.place(relx=0.35, rely=0.46, anchor="w")
    thmsa_ttp = CreateToolTip(thmsa, \
    'Enter MSA Aperture PA value in degrees')

    labplotshort = tk.Label(win, text="Short channel on ?")   
    labplotshort.place(relx=0.65, rely=0.57, anchor="w")
    plotshortVar = StringVar()
    plotshortVar.set('no')
    pt = OptionMenu(win, plotshortVar, 'yes','no')
    pt.place(relx=0.35, rely=0.57, anchor="w")

    labplotlong = tk.Label(win, text="Long channel on ?")   
    labplotlong.place(relx=0.65, rely=0.61, anchor="w")
    plotlongVar = StringVar()
    plotlongVar.set('no')
    pt = OptionMenu(win, plotlongVar, 'yes','no')
    pt.place(relx=0.35, rely=0.61, anchor="w")

    labranrcm = tk.Label(win, text="RA center of NIRCam")
    labranrcm.place(relx=0.65, rely=0.65, anchor="w")
    ranrcmVar= StringVar()
    ranrcmVar.set(ranircam[plotnames[0]])
    ranrcm = tk.Entry(win, textvariable=ranrcmVar)
    ranrcm.place(relx=0.35, rely=0.65, anchor="w")
    ranrcm_ttp = CreateToolTip(ranrcm, \
    'Enter RA value in degrees')

    labdecnrcm = tk.Label(win, text="DEC center of NIRCam")
    labdecnrcm.place(relx=0.65, rely=0.69, anchor="w")
    decnrcmVar= StringVar()
    decnrcmVar.set(decnircam[plotnames[0]])
    decnrcm = tk.Entry(win, textvariable=decnrcmVar)
    decnrcm.place(relx=0.35, rely=0.69, anchor="w")
    decnrcm_ttp = CreateToolTip(decnrcm, \
    'Enter DEC value in degrees')
    labthnrcm = tk.Label(win, text="NIRCam aperture PA")
    labthnrcm.place(relx=0.65, rely=0.73, anchor="w")
    thnrcmVar= StringVar()
    thnrcmVar.set(thetanircam[plotnames[0]])
    thnrcm = tk.Entry(win, textvariable=thnrcmVar)
    thnrcm.place(relx=0.35, rely=0.73, anchor="w")
    thnrcm_ttp = CreateToolTip(thnrcm, \
    'Enter NIRCam Aperture PA value in degrees')


    labdither = tk.Label(win, text="NIRCam dither pattern")   
    labdither.place(relx=0.35, rely=0.77, anchor="w")
    ditherVar = StringVar()
    ditherVar.set('no')
    pt = OptionMenu(win, ditherVar, 'no','three','threetight','six')
    pt.place(relx=0.65, rely=0.77, anchor="w")

    labmosaic = tk.Label(win, text="NIRCam mosaic")   
    labmosaic.place(relx=0.35, rely=0.81, anchor="w")
    mosaicVar = StringVar()
    mosaicVar.set('no')
    pt = OptionMenu(win, mosaicVar, 'no','yes')
    pt.place(relx=0.65, rely=0.81, anchor="w")

    laboffhor = tk.Label(win, text="Offset")   
    laboffhor.place(relx=0.35, rely=0.85, anchor="w")
    offhorVar= StringVar()
    offhorVar.set(offh[plotnames[0]])
    offhor = tk.Entry(win, textvariable=offhorVar)
    offhor.place(relx=0.65, rely=0.85, anchor="w")
    offhor_ttp = CreateToolTip(offhor, \
    'Enter NIRCam offset in arcsec')


    laboffver = tk.Label(win, text="Offset")   
    laboffver.place(relx=0.35, rely=0.89, anchor="w")
    offverVar= StringVar()
    offverVar.set(offv[plotnames[0]])
    offver = tk.Entry(win, textvariable=offverVar)
    offver.place(relx=0.65, rely=0.89, anchor="w")
    offver_ttp = CreateToolTip(offver, \
    'Enter NIRCam offset in arcsec')
    ptVar = StringVar()
    ptVar.set('footprints')
    
  
    b5 = Button(win,text=" Select File ",command=readfitsfilename)
    b5.place(relx=0.65, rely=0.15, anchor="w")
    fileVar= StringVar()
    fileVar.set(fitsname[plotnames[0]])
    filevalue = tk.Entry(win,textvariable=fileVar,width=40,justify='right')
    filevalue.place(relx=0.02, rely=0.15, anchor="w")


    b6 = Button(win,text=" Select File ",command=readcataloguename)
    b6.place(relx=0.65, rely=0.24, anchor="w")
    catVar= StringVar()
    catVar.set(catname[plotnames[0]])
    catvalue = tk.Entry(win,textvariable=catVar,width=40,justify='right')
    catvalue.place(relx=0.02, rely=0.24, anchor="w")

    b7 = Button(win,text="View timeline",command=maketimeline)
    b7.place(relx=0.6, rely=0.96, anchor="w")
    b3 = Button(win,text=" Quit ", command=win.quit)
    b3.place(relx=0.2, rely=0.96, anchor="w")

    b4 = Button(win,text=" Display ",command=makefootprints)
    b4.place(relx=0.8, rely=0.96, anchor="w")

    

    return win



win = makeWindow()
win.mainloop()

 
