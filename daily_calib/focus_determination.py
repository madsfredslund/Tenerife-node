import time
import numpy as np
import pyfits
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit, leastsq
import scipy.optimize._minpack as minpack
import os
import sys
import glob
import itertools
import daily_config
## These two must be copied to hw ro this to work.
import robust_fgj          ## remember
import fgauss          ## remember
import ffttest_fgj

"""
    This program attempts to include an automatic offset determination 
    between the focus images from today and that of a reference. 

    The script has only been tested for slit no. 8 !!

    The fits-file names with the focus exposures are assumed to have the 
    structure:  'name' + '_YYYY' where '_YYYY' is a running number: 0001 0002 .... 0013

    The first version of this was in IDL by FG - later Pieter de Groote and Steven Deneuve
    helped to port this into Python and make it fast. (summer 2013).

    To include the Fortran program for the gauss function do this: 

    hw: f2py -c -m fgauss gauss.f
"""

#######################################
def gauss(x, *p):
    return p[0]*np.exp(-(x-p[1])**2/(2.*p[2]**2)) + p[3] 

def gauss_res(p, x,y):
    return y-p[0]*np.exp(-(x-p[1])**2/(2.*p[2]**2)) - p[3] 


def jacob(p, x,y):
    z    = (x-p[1])/p[2]
    dA   = np.exp(-z**2/2.)
    dmu  = z/p[2] * p[0]*np.exp(-z**2/2.)
    dsig = z**2/p[2] * p[0]*np.exp(-z**2/2.)
    dc   = np.ones(len(x))
    out  = np.array([dA,dmu,dsig,dc])
    return -out


def fit_with_gauss(x, y):
    # It is better to start as close as possible to the real solution. So I
    # take the maximum value of the y's as a prior for the amplitude, and
    # the location of the peak as a prior for the mu
    peak = np.argmax(y)
    p0   = [y[peak], x[peak], 1., 0.0]
    #p0 = [1., 0., 1., 0.]
    #coeff, var_matrix = curve_fit(fgauss.gauss, x, y, p0=p0)
    #coeff, var_matrix = curve_fit(gauss, x, y, p0=p0)
    #coeff = leastsq(fgauss.gauss_res, p0, args=(x,y), maxfev=500, full_output=True)
    #coeff = leastsq(fgauss.gauss_res, p0, args=(x,y), Dfun=fgauss.gauss_jacob, col_deriv=1, maxfev=500)[0]
    #coeff = minpack._lmdif(fgauss.gauss_res, p0, (x,y), 0,  1.49012e-8, 1.49012e-8,
    #            0.0, 500, 0.0, 100, None)[0]    
    coeff = minpack._lmder(fgauss.gauss_res, fgauss.gauss_jacob, p0, (x,y), 0, 1,
                1.49012e-8, 1.49012e-8, 0.0, 500, 100, None)[0]
    return coeff



def update_progress(progress, width=80):
    """
    Displays or updates a console progress bar
    
    Accepts a float between 0 and 1. Any int will be converted to a float.
    A value under 0 represents a 'halt'.
    A value at 1 or bigger represents 100%
    """
    barLength = max(1, width-20-20) # Modify this to change the length of the progress bar
    
    progress = float(progress)
    if progress < 0:
        progress = 0
        status = "{:20s}".format("First time point...")+"\r"
    # At the end, report and let the progressbar disappear
    elif progress > 1:
        progress = 1
        status = "{:20s}".format('Done...')+"\r" + " "*(20+20+barLength)+"\r"
    elif progress <= 0.25:
        status = "{:20s}".format("Warming up...")
    elif progress <= 0.50:
        status = "{:20s}".format("Going steady...")
    elif progress <= 0.75:
        status = "{:20s}".format("Wait for it...")
    elif progress <= 1.00:
        status = "{:20s}".format("Almost there...")    
    else:
        status = "{:20s}".format("Running...")
    block = int(round(barLength*progress))
    text = "FOCUS: [{0}] {1:7.3f}% {2}".format( "#"*block + "-"*(barLength-block), progress*100, status)
    text = "\r" + text[-width:]
    sys.stdout.write(text)
    sys.stdout.flush()


def main(debug=False):

    # Provide the directory where the focus-sequence images are located.

#    dir0 = '/scratch/star_spec/20141015/day/raw/focus3'
    dir0 = "/scratch/star_spec/%s/day/raw/focus%s" % (time.strftime("%Y%m%d", time.localtime()), str(daily_config.focus_slit))

    # These are the ThAr reference list of lines and the corresponding image. Note that 
    # (currently) the x,y positions of the lines refer to a 'readfits_song.pro' image with 
    # a 10 pixel y-offset. 
    filename  = daily_config.focus_filename
    ref_image = daily_config.focus_ref_image

    # Check if the file exists. If not, report and terminate the program with
    # exitcode 0
    if not os.path.isfile(filename):
        print('File does not exist - quitting')
        sys.exit(0)

    # Read in the positions of the ThAr lines..
    yl, xl = np.loadtxt(filename, skiprows=1, unpack=True)
    xl += 10.0

    # Avoiding edge effect by cutting out the borders from 20 or 40 px: you can
    # use boolean arrays to index numpy arrays
    select = (40<=xl) & (xl<=2048) & (20<yl) & (yl<=2020)
    xl = xl[select]
    yl = yl[select]
    
    specnames = ["{:s}_{:04d}.fits".format(dir0,i) for i in range(1,14)]
    # or:
    # specnames = sorted(glob.glob(*.fits'))
    
    nim  = len(specnames)
    npar = 7
    nl   = len(xl)

    ##### Now we must determine to frame - to - reference frame offset.... here 
    #     we assume that exposure no. 7 is adequate (middle of the sequence, and 
    #     hopefully close to focus).
    xoff, yoff = ffttest_fgj.ffttest( specnames[7] )
    print ' --(X,Y) offset: ', xoff,yoff
    xl = xl + yoff
    yl = yl + xoff
    #####

    
    # Make one big array with all the images: if you have a lot of images,
    # this might become an issue to keep in memory
    im     = np.zeros((nim, 2088, 2048))
    focval = np.zeros(nim)
    
    # Read the FITS file and extract camera focus values   
    for i,specname in enumerate(specnames):
        data, hdr = pyfits.getdata(specname, header=True)
        im[i]     = data
        focval[i] = float(hdr['CAMFOCS'])
    
    # Prepare for the measurement of line positions and widths. We'll put these
    # in a record array, which is basically a normal array, of which you can
    # access columns by names rather than by index
    column_names = ['scale', 'x', 'sigma', 'background']
    dum          = np.zeros((4, nim))
    dum          = np.rec.fromarrays(dum, names=column_names)
    
    column_names = ['x0','y0','focus', 'scale', 'x', 'sigma', 'background']
    results      = np.zeros((len(column_names), nl))
    results[0]   = xl
    results[1]   = yl + 4.0
    results      = np.rec.fromarrays(results, names=column_names)

    #sigmafit = np.zeros((nl, nim))
    
    # X-axis for fitting purposes
    x = np.arange(39)
    w = np.ones(nim)
    
    # Make a nice image of the mask to see if these masks could be improved,
    # and to check if they are at the right location
    if debug:
        mask = np.zeros(im.shape[1:],bool)
        for i,(x0, yy) in enumerate(zip(xl, yl+4.0)):
            mask[yy-19:yy+20,x0-3:x0+4] = np.nan
    
        plt.figure()
        plt.title('Check mask')
        plt.imshow(im[0], cmap=plt.cm.gray)
        plt.imshow(mask,alpha=0.5, cmap=plt.cm.gray)
        plt.show()
    
    # Loop over each line
    for i,(x0, yy) in enumerate(zip(xl, yl+4.0)):
        # Loop over each image and update the progress bar every once in a while
        if i%10==0:
            update_progress(float(i)/nl)
        
        # Make a plot of the fits when debugging
        if debug:
            plt.figure()
            plt.subplot(121)
            plt.title("Check Gauss")
            color_cycle = itertools.cycle(plt.cm.spectral(np.linspace(0,1,nim)))
            
        
        for j,image in enumerate(im):
            # Extract the averaged y-values
            y = np.sum((image[yy-19:yy+20,x0-3:x0+4]),axis=1) / 7.0
            
            # Try to do a fit, if it fails, forget about it
            
            coeff = fit_with_gauss(x, y)
            # Make a plot of the fit when debugging
            if debug:
                color = color_cycle.next()
                plt.plot(x,y,'o-', color=color)
                xfit = np.linspace(x[0],x[-1],1000)
                plt.plot(xfit, gauss(xfit, *coeff), '-', color=color, lw=2)
            
            # Remember the coefficients
            dum[j] = coeff
            results['scale'][i]      = coeff[0]
            results['x'][i]          = coeff[1]
            results['sigma'][i]      = coeff[2]
            results['background'][i] = coeff[3]
                
            
        # Check that the line is sufficiently strong.
        if np.median( dum['scale'] ) >= 100:
            #cc = np.polyfit(focval, dum['sigma'], 2, w=w)
            cc = robust_fgj.polyfit(focval, dum['sigma'], 2)
            results['focus'][i] = -cc[1] / (2*cc[0])
            #sigmafit[i] = np.polyval(cc, focval)
  

            if debug:
                plt.subplot(122)
                plt.title("Find best focus")
                plt.plot(focval, dum['sigma'],'ko-')
                plt.plot(focval, np.polyval(cc, focval), 'r-', lw=2)
                plt.axvline(results['focus'][i],color='b',lw=2)
                plt.show()
            
        
        if debug:
            plt.close()


    print '\nMedian focus value: ', np.median( results['focus'] )

    plt.figure(figsize=(10.0, 8.0),facecolor='w', edgecolor='k')
    plt.subplots_adjust(left=0.20, bottom=0.10, right=0.95, top=0.90, wspace=0.4, hspace=0.3)
    ax = plt.subplot(111)
    
    plt.plot( results['x0'], results['focus'], 'ro')   # Focus vs. image-x
    plt.plot( results['y0'], results['focus'], 'go')   # Focus vs. image-y

    plt.xlabel('X,Y position')
    plt.ylabel('Focus value')
    plt.xlim(0, 2100)
    plt.ylim(160000, 220000)
    plt.grid(True)

    title = "Best focus was: %f" % float(np.median(results['focus']))
    plt.title(title)
    plt.savefig("/scratch/star_spec/%s/spec_focus_plot.jpg" % time.strftime("%Y%m%d", time.localtime()))

    return np.median( results['focus'] )
    
    
#if __name__=="__main__":
    
#    start_time = time.time()
#    print '[SIMPLE THREAD VERSION]'
#    results = main(debug=False)
    
    #print(plt.mlab.rec2txt(results[:10))
#    print '\nmedian focus value: ', np.median( results['focus'] )
#    print '\nDONE\nRunning time : {} sec'.format(time.time() - start_time)

#    fig = plt.figure()
#    ax  = fig.add_subplot(111)
    
#    plt.plot( results['x0'], results['focus'], 'ro')   # Focus vs. image-x
#    plt.plot( results['y0'], results['focus'], 'go')   # Focus vs. image-y

#    ax.set_xlabel('X,Y position')
#    ax.set_ylabel('Focus value')
#    ax.set_xlim(0, 2100)
#    ax.set_ylim(160000, 220000)
#    ax.grid(True)

#    plt.savefig("/scratch/star_spec/%s/spec_focus_plot.jpg" % time.strftime("%Y%m%d", time.localtime()))
