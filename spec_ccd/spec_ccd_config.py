# This is the setup file for the Andor iKon CCD camera

# Paths for the camera_server.py daemon.
#outstream = "/tmp/spec_ccd.log"
#outstream_old ="/tmp/spec_ccd_old.log"
outstream = "/home/obs/logs/spec_ccd.log"
outstream_old ="/home/obs/logs/spec_ccd_old.log"
pidfile = "/tmp/spec_ccd.pid"
shutter_file = "/home/obs/logs/shutter_count.txt"

##### data files ####
star_spec_dir = "/scratch/star_spec/"
#star_spec_dir = "/tmp/"
sun_spec_dir = "/scratch/sun_spec/"
site = 1 	# 1 = Tenerife, 2 = China, 

########
port = 8050 # Port for the XML-RPC connection DO NOT USE "" for this one!
serverhost = "ss4n1.prv" # IP address of the machine where the camera is pluged into. 
#serverhost = "hw.sstenerife.prv"
#serverhost = "sstenerife.prv"
# Abortfunction socket parameters:
abort_port = 8051

# Database values:
#db_host = "192.168.66.65"	#Tenerife site
#db_user = "postgres"
#db_password = ""

# Header paths:
weather_file = "/home/madsfa/SONG_programs/softw_test/spec_ccd/weather_teide.data"
#database from where to get data to header:
#db_table = "obs_request_1"
#db_header = "db_song"
#db_info_header = "db_tenerife"
db_weather_table = "weather_station"
db_coude_table = "coude_unit"
db_tel_dome_table = "tel_dome"


# Star checker. Insert other coordinates here if another site then Teide is used.
#lat_obs = "28.2983" # Teide: 28.2983
#lon_obs = "-16.5094" # Teide: -16.5094
#elev_obs = 2400 # Teide: 2400
epoch = 2000 # Epoch used for ra and dec determination
#lat_obs_aar = "56.17141"
#lon_obs_aar = "10.20039"
#elev_obs_aar = 50
#lat_obs_haw = "21.32"
#lon_obs_haw = "157.8"
#elev_obs_haw = 2000


#### IODINE
iodine_test_cell_id = 3		# ID of the iodine cell in the test position
iodine_primary_cell_id = 1	# ID of the iodine cell in the primary operation position
