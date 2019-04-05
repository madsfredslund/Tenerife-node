# ASTELCO connection:
ASTELCO_IP = ''	# TSI connection from SONG machine
TCI_IP = ""	# TCI connection from Astelco pc
ASTELCO_TSI_PORT= 	
ASTELCO_TCI_PORT= 

#ASTELCO_USER= ""	# old
#ASTELCO_PASS= "" 	# old	
ASTELCO_USER= ""	# old
ASTELCO_PASS= "" 	# old	

# DAEMON settings:
SERVER_PORT1 = 8130
SERVER_HOST1 = "hw.ss3n1.prv"

SERVER_PORT2 = 8131
SERVER_HOST2 = "hw.ss3n1.prv"

SERVER_LOGFILE = "/home/obs/logs/telescope.log"
SERVER_LOGFILE_OLD = "/home/obs/logs/telescope.old_log"
SERVER_PIDFILE = "/tmp/telescope.pid"

VERBOSE = "yes"		# yes or no
DEBUG = "yes"

#### Info insert 
tel_data_insertion_delay = 10

##########################
# Pointing model:

load_pm = "no"	# "yes": loads the pm file from below, "no": does not load anything (uses the already set one from AsTelOS).
PM_measurement_file = '"coude_2015-04-17"'	#'"coude_2015-07-23"'	# coude_20141105 # Reads from /opt/tsi155/pm/

# M3 position:
set_m3 = "yes"	# "yes", "no"
m3_pos = 12 	#  (12 = coude)

# Hexapod values:
set_hexapod_at_startup = "no"
hexapod_x = -0.20160
hexapod_y = -0.19200
hexapod_z = 0.0
hexapod_u = -0.433333
hexapod_v = -0.216667
hexapod_w = 0.0

use_fixed_env_vals = "no"
pm_temp = 20
pm_pres = 765

set_mech_derotator_syncmode_startup = "yes"
mech_derot_syncmode = 0	# [0 = off, 2 = True Orientation, ... see openTSI manual for more options]

set_instrument_at_startup = "yes"
instrument_index = 0	# [0 = Coude 1, 1 = Shack Hartmann Sensor] 2 maybe to Blue spectrograph...


#### SET FOCUS AND AO SYNCMODE
apply_focus_syncmode = "yes"	# This is needed to set hexapod and more...
focus_syncmode_value = 67

#### SET DOME SYNCMODE
apply_dome_syncmode = "yes"
dome_syncmode_value = 2			# [0,1,2,3,4,5] = [off, fixed position, sync discrete, sync discret + offset, continues sync, continues sync + offset]
max_dome_devi = 2.0				# Maximum deviationin degrees in azimuth in sync discrete mode

