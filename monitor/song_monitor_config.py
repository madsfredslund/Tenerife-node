# This is the configuration file for the Monitor daemon.

# Monitor check time interval
monitor_sleep_time = 30 # The time between the checks are carried out.
tel_data_insertion_delay = 10
over_all_obs_state_delay = 60

## SMS, wakeup email sleep time after first message sent.
sms_wait_time = 3600

##### song_checker settings: #####

weather_test = 0		# if 1 the checker uses test function in stead of real weather data, 0 means real data.
weather_deduced = 0		# If set to 1 the weather check will return the bits of the triggered weather events.
write_to_db = 1 		# 0 = no, 1 = yes
verbose = "yes"			# yes or no ( yes means a lot is written into the log file)
send_notifications = "yes"	# if yes emails will be send at telescope startup and shutdown.
send_to_wake_up = "yes"		# Always only Mads
send_sms = "yes"
send_notify_sms = "yes"
#send_notify_email_to_whom = ["mads", "frank", "jens", "ditte", "vichi", "eric", "andrea"]
#send_notify_sms_to_whom = ["Jens", "Ditte", "Vichi", "Mads", "Andrea"]
#send_sms_to_whom = ["Jens", "Ditte", "Vichi", "Mads", "Andrea"]
send_to_support = "yes"

##############################################
########## monitor_daemon.py ##################
##############################################

# What should the Monitor daemon monitor?
mon_weather = 1			# 1 = yes, 0 = no	# Monitor the weather in general.
mon_wind_speed = 1		# 1 = yes, 0 = no	# Monitor the wind speed.
mon_network = 0 		# 1 = yes, 0 = no	# Monitor the connection to the outside world.
mon_time = 1 			# 1 = yes, 0 = no	# Monitor the time of day by suns altitude and hours to and from sun set. 
mon_side_ports = 1		# 1 = yes, 0 = no	# Monitor the side ports 
mon_telescope = 1		# 1 = yes, 0 = no	# Monitors the error state and altitude of the telescope
mon_telescope_info = 0		# 1 = yes, 0 = no	# reads data from the telescope and writes it to the database
mon_house_hold = 1		# 1 = yes, 0 = no	# Monitor temperatures inside container, spec box and dome
mon_cooling_unit = 1		# 1 = yes, 0 = no	# Monitors the dome openings to determine when to start or stop the cooler.
mon_slony = 1
mon_disk_space = 1					# Monitor hw disk space
mon_memory_hw = 1			
mon_OR_insertion = 1		# Check if ORs was inserted at sunset.
mon_OR_scheduler = 1
mon_iodine_heaters = 1

#####################################
### Monitor actions?
mon_side_ports_actions = 1 	# 1 = yes, 0 = no		# Open and closing of the side ports
mon_telescope_actions = 1	# 1 = yes, 0 = no		# Shutting down and starting up the telescope
mon_spec_ccd_actions = 0	# 1 = yes, 0 = no		# Warming up the CCD if...?
mon_house_hold_actions = 1	# 1 = yes, 0 = no		# Sends an e-mail
mon_cooler_actions = 1		# 1 = yes, 0 = no		# If 1 the monitor starts and stops the cooling unit.
mon_move_away_actions = 1
######################################

####################################################
################ SIDE PORTS ########################
####################################################
# Outlet numbers for the side port configuration.
outlet_south_open = 1
outlet_west_open = 2
outlet_north_open = 3
outlet_east_open = 4
outlet_south_close = 5
outlet_west_close = 6
outlet_north_close = 7
outlet_east_close = 8

hall_input = [1, 2, 3, 4, 1, 2, 3, 4]
side_port_db_names = ["side_port_1","side_port_2","side_port_3", "side_port_4","side_port_5","side_port_6","side_port_7"]
####
power_off_sleep_time = 180 	# 180 seconds matches the open and closing time plus a small amount (25 seconds). 
#open_time_side_port = 20.0	# When less than X hours to sun set the sideport can be opened.
#close_sun_alt_side_port = 1.0	# The altitude of the Sun when side port should close at sun rise



####################################################


####################################################
###################   TELESCOPE    #################
####################################################

allow_mc_open = "yes"		# Allow mirror cover to be open at any time
open_mc_sun_alt = -4.0		# At what altitude of the sun should the mirror covers open after sunset if they do not open at startup.

# What to open at startup:
open_mirror_covers = "no"	# Should the monitor open the mirror covers at startup? 
open_slit = "yes"		# Should the monitor open the dome slit at startup? 
open_flap = "no"		# Should the monitor open the dome flap at startup? 

#tel_min_alt = 16.0		# The minimum altitude of the telescope before stopping
#sun_alt_night_day = -5.0	# The altitude of the Sun that determines when the telescope should stop and dome closes.
#open_time_tel = 2.0		# When less than 2.0 hour to sun set the dome is allowed to be opened.
power_off_at_shutdown = "yes"	# If yes the telescope will be powered off when system is stopped. 

#### PARK POSITION - This is not needed when power of at shut down is set.
#dome_az = 180.0	# Azimuth of the dome as an offset fromt the telescope position.
#park_az = 90.0		# Pointing towards east
#park_alt = 75.0		# Pointing to make air from cooling unit go to M1

dome_flap_open_angle = 40	# Telescope angle at which the flap should open.

#### If wind into dome is too high this the telescope will be moved away by this much.
tel_away_alt = 75
tel_away_angle = 180

dome_syncmode_value = 2	



####################################################
###################     DUST       #################
####################################################

dust_limit = 0.003
open_time_side_port_if_dust = 0.0
open_time_tel_if_dust = 0.5


####################################################
###################     Network    #################
####################################################
check_conn_ip_1 = "173.194.32.0" 		# Google.com ip
####################################################

########################################################
###################     Other stuff    #################
########################################################
#cooling_temp = 10.0	# Temperature in degrees which the cooling unit will be set to when turned on.
#start_skycam_movie = 1	# 1 = yes, 0 = no
####################################################

########################################################
###################     Skycam    #################
########################################################
#skycam_start_sun_alt = -7.0	# Altitude of the Sun when skycam movie should start.
start_skycam2_loop = "no"
#skycam2_cool_temp = -30
####################################################

#### DISK SPACE:
hw_ds_limit = 5000000.0		# When there is less than 5000000 bytes (5GB) left someone should be notified!
hw_ds_soft_limit_percent = 15.0	# If only 15 percent diskspace is left a notification should be sent

scratch_ds_limit = 50000000.0		# When there is less than 20000000 bytes (20GB) left someone should be notified!
scratch_ds_soft_limit = 300000000.0	# When there is less than 100000000 bytes (100GB) left someone should be notified!

#### Memory:
hw_mem_limit = 50.	# Minimum limit in MegaBytes before notification
hw_swap_limit = 500.	# Maximum used swap space before sms notification

# Daemon log and pid file:
outstream = "/home/obs/logs/monitor.log"
outstream_old = "/home/obs/logs/monitor.old_log"
pidfile = "/tmp/monitor.pid"

# This is the port and server for XML_RPC communication:
#rpc_port = 8037
#serverhost = "localhost"

#### Iodine cells:
tset_temp = 65		# The temperature to which the cell should be heated
tset_temp_test = 60	# The temperature to which the test cell should be heated
temp_diff_limit = 1.0	# Actual value must be within 1. degree from set temperature

############ Servers and vertual machines to check:
machines = ["madsfa@dbhub.sstenerife.prv", "song.sscentral.prv", "madsfa@srf.sscentral.prv", "iodinepipe.kvmtenerife.prv", "madsfa@central.sscentral.prv"]


##############################################
##############################################
##############################################

