# This is the setup file for the Andor iKon CCD camera

# Paths for the camera_server.py daemon.
#outstream = "/tmp/spec_ccd.log"
#outstream_old ="/tmp/spec_ccd_old.log"
outstream = "/tmp/red_ccd.log"
outstream_old ="/tmp/red_ccd_old.log"
pidfile = "/tmp/red_ccd.pid"
##### data files ####
star_dir = "/scratch/photometry/"
site = 1 	# 1 = Tenerife, 2 = China, 

########
port = 8142 # Port for the XML-RPC connection DO NOT USE "" for this one!
serverhost = "luckycam2.prv" # IP address of the machine where the camera is pluged into. 
# Abortfunction socket parameters:
abort_port = 8143

db_weather_table = "weather_station"
db_coude_table = "coude_unit"
db_tel_dome_table = "tel_dome"

epoch = 2000 # Epoch used for ra and dec determination
