#!/usr/bin/python

##############################################################################
#   This program is intended for obtaining a focus sequence of ThAr images
#   with the SONG spectrograph. 
#   Nov./Dec. 2011: Started development
#   March 2012: Try to include slit startup.
#   June 2012, after return of the Andor camera, try to include adjustments to 
#   M8, for centering the light input on the slit. 
#   09012013: read the starting focus value, so we can return the camera
#             to this value when the exposures are done.
#             with each sequence, take also a single flat field for order 
#             tracing.
#   28042013: Try to implemnt the function from Mads which automatically
#             sets M8 to the correct position.
##############################################################################
#
# Call from prompt:  PROMPT> python focus_script4.py
#   OR  (after chmod 755 focus_script.py)
# Call from prompt:  PROMPT> ./focus_script4.py
#
##############################################################################

import sys
import os
import time
import Set_M8
import daily_config
import focus_determination

def focus_the_spectrograph():

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
	dum, focval0 = pst.PST().where(5)  # Get the current state of the CCD camera focus.

	##############################################################################
	#		     8     7     6     5     4     3      2
	#width            = [25.0, 30.0, 36.0, 45.0, 60.0, 100.0, 20.0 ]

	width            = [0, 0, 20.0, 100.0, 60.0, 45.0, 36.0, 30.0, 25.0]
	slit             = daily_config.focus_slit   #
	name             = 'focus' + str(daily_config.focus_slit) + '_'  # Image basename for FITS file.
	flatname         = 'FOCUS_FLAT' + str(daily_config.focus_slit) + '.fits'
	flatname         = 'FOCUS_FLAT.fits'

	scale            = 25.0 / width[slit]
	exp_time_thar    = scale*2.0       # The exposure time in seconds.
	exp_time_flat    = scale*2.0       # The exposure time in seconds.
	b0               = 166000          # Start value for focus sequence
	b                = 4000            # Step value
	i                = 1               # Number of 1st exposure
	MAX              = 13              # Number of last exposure

	ext              = '.fits'         # Extension of imagename
	imtype           = 'FOCUS'         # Set a keyvord in the header for Imagetype.
	imtypeflat       = 'FLAT'          # Set a keyvord in the header for Imagetype.

	pre_amp_gain     = 2               # [0,1,2]   = [x1, x2, x4]
	readoutspeed     = 1               # [0,1,2,3] = [5MHz, 3MHz, 1MHz, 0.05MHz]


	##############################################################################
	# Start the guiders and set M8 in right position

#	os.system( SLIT_PATH + "/slit_guider.py -t")      # Stop the slit guider
#	os.system( "sleep 5" )                            # Wait till it is initialized
#	os.system( SLIT_PATH + "/slit_guider.py -s")      # Start the slit guider
#	os.system( "sleep 5" )                            # Wait till it is initialized
	#os.system( SLIT_PATH + "/sigu.py display on")     # Enable the display
	os.system( SLIT_PATH + "/sigu.py pause")          # Do not enable the guiding
	#os.system( "sleep 2" )                            # Wait till it is initialized
	#os.system( SLIT_PATH + "/sigu.py start")          # Start showing the image
	#os.system( SLIT_PATH + "/sigu.py texp manual")    # Set exposure time manually
	#os.system( SLIT_PATH + "/sigu.py texp 0.05")       # 

	##############################################################################


	##############################################################################
	# Setup and take a flat field - assume we have close to the right focus and 
	# that we use the same slit af for the ThAr exposures.

	os.system( DMC_PATH + "/pst.py move -m 2 -p 3")  # Make sure we get light to slit, not acq mirror.
	os.system( DMC_PATH + "/pst.py move -m 3 -p 2")  # Move Iodine-cell to free.
	os.system( DMC_PATH + "/lamp.py halo on")        # Turn on the halogen lamp
	os.system( DMC_PATH + "/pst.py move -m 4 -p 2")  # Move input to flat field lamp 
	os.system( "%s/pst.py move -m6 -p%s" % (DMC_PATH, str(slit)) )  # Move slit
	Set_M8.set_m8_pos() # Get the M8 to the right position
	# Take flat field spectrum
	os.system( "%s/c_acq.py -p%i -r%i -e%f -t%s -f%s" % (ANDOR_PATH, pre_amp_gain, readoutspeed, exp_time_flat, imtypeflat, flatname ) )

	os.system( DMC_PATH + "/lamp.py halo off")        # Turn off the halogen lamp

	##############################################################################
	# Get the ThAr ready

	os.system( DMC_PATH + "/lamp.py thar on")        # Turn on the ThAr lamp
	os.system( DMC_PATH + "/pst.py move -m 4 -p 3")  # Move input to ThAr fibre.
	Set_M8.set_m8_pos() # Get the M8 ready for ThAr
	#os.system( SLIT_PATH + "/sigu.py texp 0.10")       # 

	##############################################################################
	# Execute loop to take ThAr exposures at each focus value.

	while i <= MAX:

	    focval   = b0 + (i-1) * b 
	    filename = "%s%04i.fits" % (name, i)
	    os.system( "%s/pst.py move -m5 -p%s" % (DMC_PATH, str(focval) ) )
	    os.system( "%s/c_acq.py -p%i -r%i -e%f -t%s -f%s" % (ANDOR_PATH, pre_amp_gain, readoutspeed, exp_time_thar, imtype, filename ) )
	    i = i+1   # same as i += i.... but this is tooooo fancy!

	##############################################################################
	# Finish off.

	os.system( DMC_PATH  + "/lamp.py thar off")       # Turn-off the ThAr lamp
	os.system( SLIT_PATH + "/slit_guider.py -t")      # Stop the slit guider
	os.system( "%s/pst.py move -m5 -p%s" % (DMC_PATH, str(focval0) ) )  # Return to start focus value
	#os.system( DMC_PATH + "/pst.py move -m 4 -p 1")  # Move to 'telescope' position

	##############################################################################
	# Call the script that calcullates the optimum focus:

	return "done"


