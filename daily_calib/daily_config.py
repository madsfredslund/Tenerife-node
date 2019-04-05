do_morning_calib = 1
do_evening_calib = 1
exercise_m3 = "no"
m3_movements = 3
run_weekly_focus = "no"
shutter_handle = 1	# Power off the shutter electronics to activate the Stellar shutter

### This is the values used in the daily calibration script:

number_of_bias = 10
number_of_flats = 10
number_of_flatsi2 = 10
number_of_thar = 2
slit = 8
flat_exptime = 2.0
flati2_exptime = 2.0
thar_exptime = 1.0

DMC_PATH =  "/home/obs/programs/DMC/"
ANDOR_PATH = "/home/madsfa/subversion/trunk/spec_ccd/"
SLIT_PATH = "/home/obs/programs/guiders/slit"
ccd_server = 'http://ss4n1.prv:8050'

time_of_day = 8 	# At that time of the day should the calibration start? 7 means around 7 o'clock UTC.

web_images_dir = "/home/obs/web_images/"
pidfile = "/tmp/daily_calib.pid"
outstream = "/home/obs/logs/daily_calib.txt"
outstream_old = "/home/obs/logs/daily_calib_old.txt"

max_xy_offset = 50	# Maximum offset in x or y in pixels before sending out an email

################## ThAr lines ###################
# Reference:
#im_ref_1 = "/home/madsfa/20130504/daily_thar_1.fits"	
#im_ref_2 = "/home/madsfa/20130504/daily_thar_2.fits"
im_ref_1 = "/home/madsfa/20180704/daily_thar_1.fits"
im_ref_2 = "/home/madsfa/20180704/daily_thar_2.fits"

# line 1
thar1_x = 230		# 204
thar1_y = 1428		# 1387
# line 2
#thar2_x = 1850
#thar2_y = 300

### New line used for the red part from 2014-10-15:
thar2_x = 1941		# 1919
thar2_y = 731		# 688

line_area = 20
#################################################

##### Cross Corr area ######
cc_start = 700	# 800
cc_end = 1300	# 1200

###########################################################################
#### Focusing the spectrograph camera:
focus_filename  = '/home/obs/obs_scripts/FOCUS/auto/REFS/20131104/focus8_0007.lines.txt'
focus_ref_image = '/home/obs/obs_scripts/FOCUS/auto/REFS/20131104/focus8_0007.fits'
focus_slit = 8
which_day_to_focus = "Thu"	# ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
focus_at = 10		# UTC

###################################################
########## Evening calibration scripts ############

calib_sun_alt = 12	# When Sun is about to set the daily calibration will be carried out!

#slits_to_use = [6,8]	# A maximum of 3 slits are allowed!
slits_to_use = [5,6,8]	# A maximum of 3 slits are allowed!
script_path =   "/home/madsfa/subversion/trunk/daily_calib/"


#######################################################################
#######################################################################
#######################################################################
### SKYCAM control

power_skycam_1 = 1	# if 1 then powering skycam on and off is active
power_skycam_2 = 0	# if 1 then powering skycam on and off is active
start_skycam_1_daemon = 1	# if 1 then it will be started and stopped.



########### OBSERVING THE SUN ####################
observe_sun = "no"


####### Slit location
x_offsets = {"slit5": 0,
	     "slit6": 0,
	     "slit8": 0}
y_offsets = {"slit5": [0,0],	# first offset is real and last offset is for plotting
	     "slit6": [0,0],	# first offset is real and last offset is for plotting
	     "slit8": [0,0]}	# first offset is real and last offset is for plotting

x_ref = {"slit5": 311,
	 "slit6": 315,
	 "slit8": 319}
y_ref = {"slit5": 251,
	 "slit6": 251,
	 "slit8": 251}
