# This is the configuration file for the APC-PDU unit software.

# IP adresses for the three Power destribution units:

DestHost_container = "10.8.0.15" # SONG IP
DestHost_nasmyth = "10.8.0.16" # SONG IP
DestHost_side_ports = "10.8.0.17" # SONG IP
DestHost_nasmyth_2 = "10.8.0.19"


names_container = ["16 Amps - Blue Spec.", "Andor CCD PSU	", "Pressure Sensor", "DMC Power	", "DMC Motor Power", "Shutter PSU	", "Vacuum Pump	", "Vacuum Valve	","16 Amp - Dome Light", "Temp. Controller", "Lamp Controller", "Iodine Controller", "Solar shutter state", "M8 Controller", "Prosilica Slit Cam", "Prosilica Pupil Cam", "16 Amp - Astelco PC", "Weather Staion", "RS232 Coverter" ,"Blue spec CCD" ,"Temp. Monitor" ,"BF-2300	" ,"Table 3-plugs" ,"Dome Controller"]

names_side_ports = ["South - Open","West - Open","North - Open","East - Open","South- Close","West - Close","North - Close","East - Close"]

names_nasmyth = ["Lucky PC 1","Lucky PC 2","DMC Power","Lucky Cam 1","Lucky Cam 2","HP PC	","SkyCam","SkyCam-2"]

names_nasmyth_2 = ["LI Guide Cam","	","	","	","	","	","	","	"]


# The settings for snmp community:
Community = "private"
