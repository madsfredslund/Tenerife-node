#!/usr/bin/python

##############################################################################
#   This program is intended for obtaining a sequence of calibration images
#   for use with the Iodine cell and stellar observations.
#
#
#   28042013: Started development
#   05122013: Added default directory to 'night' in the call to c_acq
##############################################################################
#
# Call from prompt:  PROMPT> python spec_calib1.py
#   OR  (after chmod 755 focus_script.py)
# Call from prompt:  PROMPT> ./spec_calib1.py
#
##############################################################################

import sys
import os
import time
import Set_M8

##############################################################################
# Paths to motor controller and Andor CCD programs.

DMC_PATH         = "/home/obs/programs/DMC"
ANDOR_PATH       = "/home/madsfa/subversion/trunk/spec_ccd"
SLIT_PATH        = "/home/obs/programs/guiders/slit"

##############################################################################
# Import the PST module, so we can read what the initial focus value was, 
# and return to this when we are done. The focus motor is nr. 5

sys.path.append( DMC_PATH )
import pst
#dum, focval0 = pst.PST().where(5)  # Get the current state of the CCD camera focus.

##############################################################################
# Define slit, exposure time etc....

daynight         = 'night'

slitpos          = 4               # allowed values are: 8,7,6,5,4,3,2,1
#focus_value      = 188000          # Use this value for the camera focus... compromise 
                                   # between slit 6 and 8.

#                                  # Slitpos  Width
#                                  #       9             OPEN
#                                  #       8             25um
#                                  #       7             30um
#                                  #       6             36um
#                                  #       5             45um
#                                  #       4             60um
#                                  #       3            100um
#                                  #       2             20um
#                                  #       1         100;20um

exp_time_thar    = 1.6             # The exposure time in seconds.
exp_time_flat    = 1.5             # The exposure time in seconds.
exp_time_flati2  = 1.5             # The exposure time in seconds.

# Set number of exposures
MAX_bias         = 120              # Number of last exposure
MAX_thar         =   3              # Number of last exposure
MAX_flat         = 120              # Number of last exposure
MAX_flati2       =  10              # Number of last exposure

# Set image types
imtypebias       = 'BIAS'          # Set a keyvord in the header for Imagetype.
imtypethar       = 'THAR'          # Set a keyvord in the header for Imagetype.
imtypeflat       = 'FLAT'          # Set a keyvord in the header for Imagetype.
imtypeflati2     = 'FLATI2'        # Set a keyvord in the header for Imagetype.

# Set CCD state
pre_amp_gain     = 2               # [0,1,2]   = [x1, x2, x4]
readoutspeed     = 1               # [0,1,2,3] = [5MHz, 3MHz, 1MHz, 0.05MHz]


##############################################################################
# Start the slit guider as we need to move M8 to illuminate the slit correctly
##############################################################################

#os.system( SLIT_PATH + "/slit_guider.py -t")      # Stop the slit guider
#os.system( "sleep 5" )                            # Wait till it is initialized
#os.system( SLIT_PATH + "/slit_guider.py -s")      # Start the slit guider
#os.system( "sleep 5" )                            # Wait till it is initialized
#os.system( SLIT_PATH + "/sigu.py display off")    # Dis-able the display
#os.system( SLIT_PATH + "/sigu.py display on")     # Enable the display
os.system( SLIT_PATH + "/sigu.py pause")          # Do not enable the guiding
os.system( "sleep 2" )                            # Wait till it is initialized
os.system( SLIT_PATH + "/sigu.py start")          # Start showing the image
os.system( SLIT_PATH + "/sigu.py texp manual")    # Set exposure time manually
os.system( SLIT_PATH + "/sigu.py texp 0.01")       # Set the exposure time value

##############################################################################
# Set the slit and the focus value
##############################################################################

os.system( "%s/pst.py move -m6 -p%s" % (DMC_PATH, str(slitpos)) )     # Move slit
#os.system( "%s/pst.py move -m5 -p%s" % (DMC_PATH, str(focus_value)) )  # Camera focus

##############################################################################
# Take the BIAS exposures.
##############################################################################

exp_time_bias = 0.0             # The exposure time in seconds.
i             = 1
while i <= MAX_bias:
    #os.system( "%s/c_acq.py -p%i -r%i -e%f -t%s" % (ANDOR_PATH, pre_amp_gain, readoutspeed, exp_time_bias, imtypebias ) )
    os.system( "%s/c_acq.py -p%i -r%i -e%f -t%s --daynight=%s" % (ANDOR_PATH, pre_amp_gain, readoutspeed, exp_time_bias, imtypebias, daynight) )
    i = i+1

##############################################################################
# Take the ThAr exposures.
##############################################################################

os.system( DMC_PATH + "/lamp.py thar on")        # Turn on the ThAr lamp
os.system( DMC_PATH + "/pst.py move -m 4 -p 3")  # Move input to ThAr fibre.
os.system( DMC_PATH + "/pst.py move -m 2 -p 3")  # Move input to ThAr fibre.
os.system( DMC_PATH + "/pst.py move -m 3 -p 2")  # Move Iodine-cell to free.
Set_M8.set_m8_pos()                              # Get the M8 ready for ThAr

i = 1
while i <= MAX_thar:
    #os.system( "%s/c_acq.py -p%i -r%i -e%f -t%s" % (ANDOR_PATH, pre_amp_gain, readoutspeed, exp_time_thar, imtypethar ) )
    os.system( "%s/c_acq.py -p%i -r%i -e%f -t%s --daynight=%s" % (ANDOR_PATH, pre_amp_gain, readoutspeed, exp_time_thar, imtypethar, daynight ) )
    i = i+1

##############################################################################
# Flat fields without
##############################################################################

os.system( DMC_PATH + "/lamp.py halo on")        # Turn on the halogen lamp
os.system( DMC_PATH + "/pst.py move -m 3 -p 2")  # Move Iodine-cell to free.
os.system( DMC_PATH + "/pst.py move -m 4 -p 2")  # Move input to flat field lamp 
os.system( DMC_PATH + "/pst.py move -m 2 -p 3")  # Move input to ThAr fibre.
Set_M8.set_m8_pos()                              # Get the M8 to the right position

# Take flat field spectra (no iodine)
i = 1
while i <= MAX_flat:
    #os.system( "%s/c_acq.py -p%i -r%i -e%f -t%s" % (ANDOR_PATH, pre_amp_gain, readoutspeed, exp_time_flat, imtypeflat ) )
    os.system( "%s/c_acq.py -p%i -r%i -e%f -t%s --daynight=%s" % (ANDOR_PATH, pre_amp_gain, readoutspeed, exp_time_flat, imtypeflat, daynight ) )
    i = i+1

##############################################################################
# Flat fields with Iodine
##############################################################################

os.system( DMC_PATH + "/pst.py move -m 3 -p 3")  # Move Iodine-cell in the beam
i = 1
while i <= MAX_flati2:
    #os.system( "%s/c_acq.py -p%i -r%i -e%f -t%s" % (ANDOR_PATH, pre_amp_gain, readoutspeed, exp_time_flati2, imtypeflati2 ) )
    os.system( "%s/c_acq.py -p%i -r%i -e%f -t%s --daynight=%s" % (ANDOR_PATH, pre_amp_gain, readoutspeed, exp_time_flati2, imtypeflati2, daynight ) )
    i = i+1

# Remove the iodine cell and turn off the halogen flat-field lamp
os.system( DMC_PATH + "/pst.py move -m 3 -p 2")  # Move Iodine-cell to free.
os.system( DMC_PATH + "/lamp.py halo off")       # Turn off halogen lamp


##############################################################################
# Finish off.
##############################################################################

os.system( DMC_PATH  + "/lamp.py thar off")       # Turn-off the ThAr lamp
#os.system( SLIT_PATH + "/slit_guider.py -t")      # Stop the slit guider
os.system( DMC_PATH + "/pst.py move -m 4 -p 1")   # Move to 'telescope' position

##############################################################################
# End of program
##############################################################################
##############################################################################
