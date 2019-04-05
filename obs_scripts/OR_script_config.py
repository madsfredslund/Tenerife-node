#### Settings script for the spectroscopic observations script OR_script.py and OR_actions.py

check_weather = 1	# Check if weather is fine: 1 = yes. 
check_daytime = 1	# Check if the Sun is below 12 degrees below the horizon: 1 = yes.
check_telescope = 1	# Check if the script can connect to the telescope daemon: 1 = yes.
use_sigu = 1		# Check if sigu runs and use slit guiding
use_pugu = 1		# Check if pugu is running and use pupil guiding
check_or_values = 1	# Check the values from the OR database request
check_obs_window = 1	# Check if we are inside the observing window
check_object = 1	# Check if object is high enough and that the wind in that direction is low enough.
check_dome = 1		# Check if dome is open. Aborts if it is not open.
check_mirror_covers = 1	# Check if mirror covers are open. Opens them if they were closed.
track_object = 1	# Set coordinates and start tracking object.
move_motors = 1		# Move PST and other motors according to the OR

move_new_motors = 1		# Move PST and other motors according to the OR

do_acquisition = 1	# Perform acquisition to put light on the slit	

use_skycam = 0		# Repoint using skycam if acquisition fails.
acq_spectres = 1	# Acquire spectres
finish_off = 1		# Stop telescope and some other stuff.
observe_o_star = 1	# In template observations... observe o-star or not

on_hold_time = 3	# number of minutes an OR should be on hold after acquisition failure
on_hold_wind_time = 20	# number of minutes an OR should be on hold if telescope was not tracking


use_sigu_on_sstenerife = "yes"
####
#min_moon_dist = 5.0	# Minimum Moon distance which is allowed.
#min_sun_dist = 25.0	# Minimum Sun distance which is allowed.

#tel_zd_offset = - 8.0 / 3600. 	 # -0.00776146	# Preset offset of telescope zenith distance to this value
#tel_az_offset = 20. / 3600. 	 # 0.0045598	# Preset offset of telescope azimuth distance to this value
#tel_zd_offset = - 12.0 / 3600. 	 # 2015-10-09
#tel_az_offset = 15. / 3600. 	 # 2015-10-09
#tel_zd_offset = - 30.0 / 3600. 	 # 2015-11-06
#tel_az_offset = -25. / 3600. 	 # 2015-11-06
#tel_zd_offset = -12.0 / 3600. 	 # 2015-11-08
#tel_az_offset = 15. / 3600. 	 # 2015-11-08
#tel_zd_offset = 13.0 / 3600.	 # 2016-10-11
#tel_az_offset = 15.0 / 3600.	 # 2016-10-11
tel_zd_offset = 0.0 / 3600.	 # 2016-10-11
tel_az_offset = 0.0 / 3600.	 # 2016-10-11

zd_offset_limit = 60.	# Maximum zd offsets
az_offset_limit = 100.	# Maximum az offsets
focus_offset_limit = 0.7

m2_focus_offset = 0.6 # mm

#tel_zd_offset = 0.0	# Preset offset of telescope zenith distance to this value
#tel_az_offset = 0.0	# Preset offset of telescope azimuth distance to this value

###### SkyCam-2
phot_stars = {"hd 37022": {"exptime": 60, "derot": True, "filterpos": 2, "sub_im": [0,0,0,0]},
		"hip 69483": {"exptime": 1, "derot": True, "filterpos": 1, "sub_im": [1478, 1068, 400, 400]}} # sub = [left, top, width, height]


#######
## Shut down telescope if failure
tel_shut_down = 1

m3_position = 12		# 12 = coude.
dome_syncmode_value = 2		# Synchronization mode of the dome. [0,1,2,3,4,5] = [off, fixed position, sync discrete, sync discret + offset, continues sync, continues sync + offset]
dome_max_deviation = 3.0	# Maximum deviation of dome azimuth from telescope azimuth in degrees.

close_to_zenith = 83.0 	# Altitude of telescope in which "slewing" is allowed when starting to track.
pointing_dist = 1.0	# Distance in arcseconds (ra and dec) of which we assume we are there. 
focus_min = 1.8		# If calculated focus value is less than this the focus will not be set.
focus_max = 3.8		# If calculated focus value is larger than this the focus will not be set.

tracking_timeout = 120 	# seconds in which the telescope should have reach the new object and started to track.

ao_settings = "lookup"	# auto, manual, lookup or off
tel_focus_table = 1	# Use focus table when applying ao corrections 0 = no, 1 = yes
m1_ao_table = 1		# Use ao correction table 0 = no, 1 = yes


o_star_dir = "/home/obs/CONFIG_FILES/o-stars/"
#site_value = 1		# 1 = Tenerife

#sun_alt_when_to_stop = -6	# altitude of the Sun when the script should stop: "ast. twi" = -12, "nau. twi" = -6... 
#tel_alt_min = 16	# Minimum altitude of the telescope

send_notifications = 1	# Send out info mails
#send_notify_email_to_whom  = ["jens", "mads", "ditte", "vichi", "frank"]

############### HEXAPOD ################
check_hexapod = "yes"
set_hexapod = 0

hexapod_x = -0.20160
hexapod_y = -0.19200
hexapod_u = -0.433333
hexapod_v = -0.216667
hexapod_w = 0.0

### Blue sky observations:
m8_pos_x = 60
m8_pos_y = 45
sigu_texp_sun = 0.05
pugu_texp_sun = 0.1

### SLIT GUIDER TARGET POSITIONS:
# New 90/10 beamsplitter
guide_targets = { 1:	[320, 287],
 		  2:	[320, 287],
 		  3:	[320, 287],
 		  4:	[325, 281],
 		  5:	[311, 251],    # 311, 251 as reference on 2018-08-22
 		  6:	[315, 251],    # 315, 251 as reference on 2018-05-21	
 		  7:	[315, 248],
 		  8:	[319, 251],    # 319, 251 as reference on 2018-08-22
 		  9:	[320, 287]
}

# Old slit guide camera: Prosilica
#guide_targets = { 1:	[320, 287],
# 		  2:	[320, 287],
# 		  3:	[320, 287],
# 		  4:	[325, 281],
# 		  5:	[350, 290],	
# 		  6:	[350, 286],	
# 		  7:	[340, 287],
# 		  8:	[350, 292],    
# 		  9:	[320, 287]
#}

#### OLD values from 98/2 beamsplitter
#guide_targets = { 1:	[320, 287],
# 		  2:	[320, 287],
# 		  3:	[320, 287],
# 		  4:	[325, 281],
# 		  5:	[330, 284],	# 330, 284
# 		  6:	[335, 293],	# 335, 285
# 		  7:	[340, 287],
# 		  8:	[350, 285],	# [330, 282]
# 		  9:	[320, 287]
#}


