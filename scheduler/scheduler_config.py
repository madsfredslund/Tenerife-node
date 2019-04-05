#default config file

#[LOGGING]
#refer to python documentation for logging-levels [debug, info, warning, critical, error]
#level='debug'
level='debug'

#[SITE]
site_num=1

sort_param1= 'req_prio'		# Only one parameter is used!!!!
#sort_param2= 'stop_window'
#sort_param3= 'start_window'
readout_lim=10

#[OR]
#or_host='site02'
#or_db='db_song'
#or_table='obs_request_1'

#[OR Central]
#or_c_host='central'
#or_c_db='db_song'
#or_c_table='obs_request_1'

#user='postgres'
#password=''

#[STATUS]
#status_host='site02'
#status_db='db_tenerife'
#status_table='obs_request_status_1'

#[INSTRUMENTS]
### This actually means which obs_request_x table to look at:
use_main_spec = "yes"
use_blue_spec = "no"

#[SCRIPT]
#template_script_name = '/home/madsfa/subversion/trunk/obs_scripts/SONG_obs/template_script.py'
template_script_name = '/home/madsfa/subversion/trunk/obs_scripts/SONG_obs/OR_template_script.py'
or_script_name = '/home/madsfa/subversion/trunk/obs_scripts/SONG_obs/OR_script.py'
#or_script_name = '/home/madsfa/subversion/trunk/obs_scripts/SONG_obs/OR_TEST_script.py'
sun_script_name = '/home/madsfa/subversion/trunk/obs_scripts/SONG_obs/blue_sky_script.py'
blue_spec_script = '/home/obs/simon/song-eshel/song-eshel-req.py'
sun_fibre_script = '/home/madsfa/subversion/trunk/obs_scripts/SONG_obs/sun_obs_fibre.py'
moon_script = '/home/madsfa/subversion/trunk/obs_scripts/SONG_obs/moon_obs_script.py'

#or_script_name='/home/obs/obs_scripts/test_of_scheduler.py'		
#template_script_name = '/home/madsfa/subversion/tags/obs_scripts_v0.1/template_script.py'
#or_script_name='/home/madsfa/subversion/tags/obs_scripts_v0.1/OR_script.py'

timeout_overhead = 120	# two minutes

#[DAEMON]
#note that output is redirected using both logging-functionality (see above section)
pidfile='/tmp/or_scheduler.pid'
outstream='/home/obs/logs/or_scheduler.log'
outstream_old='/home/obs/logs/or_scheduler.old_log'
check_time = 1	#Checks for new ORs every second.
check_time_sleeping = 1800	# Time in seconds between checks during daytime from (9:00 UTC to 17:00 UTC)


#[CHECKER]
#configuration of the checkers. For weather, day, and wind, a list of allowed return-values for the checker can be provided (the observation is only performned if the checker returns one of these values).
#In all cases a value of 'all' means that no check is performed (any return value from the checker is acceptable)
#object check returns a True/False value. For this checker it is only necessary to indicate whether the check should be made (1) or not (0)

#list of allowed values for the weather_checker. See documentation of checker for a list of possible values. use 'all' for no check
weather_allowed_values=[0,]
#options include -1, 1, 2, 3, 4. For no check use 'all' [-1 = night, 1=ast twl, 2 = nau twl, 3 = civ twl, 4 = day]	
day_allowed_values=[-1, 1, 2]
#whether to check if the object is observable at the moment. false means no check, true means the check is performed	
object_check=True	# True in observing mode
	
#[SCHEDULING]
scheduler_mode = "simple"	# or "advanced"
project_tables = ["backup"]

