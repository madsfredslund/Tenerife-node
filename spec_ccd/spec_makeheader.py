"""
   Created on Mar 16, 2010

   @author: madsfa
"""

import time
import pyfits
import sys
import song_timeclass
import os
import song_star_checker
import string
import spec_ccd_config
import get_db_values
import timeoutafunction
import psycopg2
import datetime
import barcor_song_mfa
import ephem
import master_config as m_conf
import numpy

clock = song_timeclass.TimeClass()
    
db_handle = get_db_values.db_connection()
class MakeHeader(object):
   """
      This class will modify the header of the observed fits file to contain the relevant information
   """
   # cam is the cameraobject, ccdtemp is the temperature of the ccd just before the exposure. date_obs, jd_obs and mjd_obs is timestamps. file is the FITS file to be modified. 
   def makeheader(self,cam,ccdtemp,date_obs,jd_obs,mjd_obs,fits_file,hsspeed,pregain,highcap,imagetyp,object_name_1,req_no, obj_ra, obj_dec, remark, used_exp_time):
      """
         @brief: This function modifies, updates and fills the header of given FITS files.

         @param cam: This is the camera handle from the Andor.py wrapper.
         @param ccdtemp: The temperature of the CCD chip just before the acquisition.
         @param date_obs: Time stamp in readable format and UT.
         @param jd_obs: Time stamp in Julian date.
         @param mjd_obs: Time stamp in Modified Julian date.
         @param fits_file: The name of the FITS file to be loaded and saved.
         @param hsspeed: Horisontal Shift Speed.
         @param pregain: Pre Amplifier Gain value.
         @param highcap: High Capability. Can be set to on/off.
         @param req_no: Observation request number. Needed to load data from database.

         @todo: A lot of data from the database should be included. Use: get_db_values.py       
      """
      creation_start_time = time.time()
      try:
	      #### Count number of shutter openings:
		if imagetyp.lower() != "dark" or imagetyp.lower() != "bias":
			tmp_file = open(spec_ccd_config.shutter_file, "r")
			old_number = int(float(tmp_file.readline()))
			tmp_file.close()
			new_number = old_number + 1
			tmp_file = open(spec_ccd_config.shutter_file, "w")	
			tmp_file.write(str(new_number))
			tmp_file.close()
			print "Shutter was opened %i times in total" % (new_number)
      except Exception,e:
		print e
		print "Could not increase the count number of shutter openings!"
		 

###############################################################################################
#############################    COLLECT DATA FROM DATABASE ###################################
###############################################################################################

#######################################  WEATHER  #############################################
      # This only works when the connection to the database is possible.
      collect_weather_info_error = 0
      weather_values = []
      try:
         conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
         curr = conn.cursor()
         weather_values = db_handle.get_fields(curr, spec_ccd_config.db_weather_table, ["drd11_rain","wxt520_rain_int","bw_rain_cond","wxt520_wind_avg", "wxt520_wind_avgdir","wxt520_wind_speed","wxt520_temp1","wxt520_humidity","wxt520_wind_direction","wxt520_pressure","bw_cloud_cond","bw_dewp_temp","ins_at"])
      except Exception, e:
         print "Error: ", e
         collect_weather_info_error = 1

      if weather_values == None or collect_weather_info_error == 1 :
         weather_values = []

      if collect_weather_info_error != 1 and len(weather_values) > 1:
         rain_drd11 = weather_values["drd11_rain"]
         rain_int_wxt520 = weather_values["wxt520_rain_int"]
         rain_bw = weather_values["bw_rain_cond"]
         #wind = weather_values["wxt520_wind_speed"]
         wind = weather_values["wxt520_wind_avg"]
         temp = weather_values["wxt520_temp1"]
         hum = weather_values["wxt520_humidity"]
         #wdir = weather_values["wxt520_wind_direction"]
         wdir = weather_values["wxt520_wind_avgdir"]
         pres = weather_values["wxt520_pressure"]
         clouds = weather_values["bw_cloud_cond"]
         dpoint = weather_values["bw_dewp_temp"]
         ins_at = weather_values["ins_at"] 


      else:
         rain_drd11 = -999
         rain_int_wxt520 = -999
         rain_bw = -999
         wind = -999
         temp = -999
         hum = -999
         wdir = -999
         pres = -999
         clouds = -999
         dpoint = -999
         ins_at = "1984-03-23 11:00:00"    

      time_diff = datetime.datetime.utcnow() - ins_at
      time_diff = time_diff.days*24*3600 + time_diff.seconds

      if time_diff < 300:
         weather_info_time = "Current Data"
      elif time_diff >= 300 and temp == -999:
         weather_info_time = "No Data!!!"   
      else:
         weather_info_time = "Old Data!!!" 

###############################################################################################

############################## COUDE UNIT AND SPECTROGRAPH ####################################
      collect_coude_info_error = 0
      coude_values = []
      try:
         conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
         curr = conn.cursor()
         coude_values = db_handle.get_fields(curr, spec_ccd_config.db_coude_table, ["iodine_pos","filter_pos","calib_mirror_pos","mirror_slide","spectrograph_foc","slit_pos","iodine_temp_set", "iodine_temp_read","iodine_heater_on","lamp_halogen_on","lamp_thar_on","lamp_optional_on","ins_at"])
      except Exception, e:
         print "Error: ", e
         collect_coude_info_error = 1

      if collect_coude_info_error == 1 or coude_values == None:
         coude_values = []

      if collect_coude_info_error != 1 and len(coude_values) > 1:
         iodine_pos = coude_values["iodine_pos"]
         filter_pos = coude_values["filter_pos"]
         calib_mirror_pos = coude_values["calib_mirror_pos"]
         mirror_slide = coude_values["mirror_slide"]
         spec_focus = coude_values["spectrograph_foc"]
         slit_pos = coude_values["slit_pos"]
         iodine_temp_set = coude_values["iodine_temp_set"]
         iodine_temp_read = coude_values["iodine_temp_read"]
         iodine_heater_on = coude_values["iodine_heater_on"]
         lamp_halogen_on = coude_values["lamp_halogen_on"]
         lamp_thar_on = coude_values["lamp_thar_on"]
         lamp_option_on = coude_values["lamp_optional_on"]
         ins_at = coude_values["ins_at"]
      else:
         iodine_pos = -999
         filter_pos = -999
         calib_mirror_pos = -999
         mirror_slide = -999
         spec_focus = -999
         slit_pos = -999
         iodine_temp_set = -999
         iodine_temp_read = -999
         iodine_heater_on = -999
         lamp_halogen_on = -999
         lamp_thar_on = -999
         lamp_option_on = -999


########################## TELESCOPE AND DOME DATA ############################################
      collect_tel_dome_info_error = 0
      tel_dome_values = []
      try:
         conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
         curr = conn.cursor()
         tel_dome_values = db_handle.get_fields(curr, spec_ccd_config.db_tel_dome_table, ["tel_ra", "tel_dec", "tel_az", "tel_alt", "tel_zd", "tel_focus", "third_mirror", "gps_st", "temp_m1", "temp_m2", "temp_m3", "temp_n1"])
      except Exception, e:
         print "Error: ", e
         collect_tel_dome_info_error = 1

      if tel_dome_values == None or collect_tel_dome_info_error == 1:
         tel_dome_values = []

      if collect_tel_dome_info_error != 1 and len(tel_dome_values) > 1:
         tel_ra = tel_dome_values["tel_ra"]
         tel_dec = tel_dome_values["tel_dec"]
         tel_az = tel_dome_values["tel_az"]
         tel_alt = tel_dome_values["tel_alt"]
         tel_focus = tel_dome_values["tel_focus"]
         tel_third_mirror = tel_dome_values["third_mirror"]
         tel_sid_time = tel_dome_values["gps_st"]
	 tel_temp_m1 = float(tel_dome_values["temp_m1"] - 3.7)	# Correction bue to missing calibration
	 tel_temp_m2 = tel_dome_values["temp_m2"]
	 tel_temp_m3 = tel_dome_values["temp_m3"]
	 tel_temp_tt = tel_dome_values["temp_n1"]
      else:
         tel_state = -999
         tel_ra = 0
         tel_dec = 0
         tel_az = 0
         tel_alt = 0
         tel_focus = 0
         tel_third_mirror = 0
         tel_sid_time = "1984-03-23 11:00:00"
	 tel_temp_m1 = -99
	 tel_temp_m2 = -99
	 tel_temp_m3 = -99
	 tel_temp_tt = -99


########################## Seeing and pupil flux ############################################
      collect_ccd_header_info_error = 0
      ccd_header_values = []
      try:
         conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
         curr = conn.cursor()
         ccd_header_values = db_handle.get_fields(curr, "ccd_header", ["seeing_curr", "seeing_mean", "pupil_flux_left", "pupil_flux_right"])
      except Exception, e:
         print "Error: ", e
         collect_ccd_header_info_error = 1

      if collect_ccd_header_info_error == 0:
	 seeing1 = ccd_header_values["seeing_curr"]			# Current seeing value on the slit guide camera
	 seeing2 = ccd_header_values["seeing_mean"]			# Running mean of the seeing from the slit guider
	 pupil_flux_left = ccd_header_values["pupil_flux_left"]		# Flux on the left side of pupil
	 pupil_flux_right = ccd_header_values["pupil_flux_right"]	# Flux on the right side of the pupil
      else:
	 seeing1 = 0.0
	 seeing2 = 0.0
	 pupil_flux_left = 0.0
	 pupil_flux_right = 0.0

####################### Temperatures from container #######################################
      collect_temps_info_error = 0
      temps_values = []
      try:
         conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))

         curr = conn.cursor()
         temps_values = db_handle.get_fields_temps(curr, "house_hold", ["temperature_16","temperature_10","temperature_12","temperature_15","ins_at"])
      except Exception, e:
         print "Error: ", e
         collect_weather_info_error = 1

      if temps_values == None or collect_temps_info_error == 1 :
         temps_values = []

      if collect_temps_info_error != 1 and len(temps_values) > 1:
         c_flange_temp = temps_values["temperature_16"]
         cross_d_temp = temps_values["temperature_15"]
         cont_air_temp = temps_values["temperature_10"]
         spec_table_temp = temps_values["temperature_12"]

      else:
 	 c_flange_temp = 999
         cross_d_temp = 999
         cont_air_temp = 999
         spec_table_temp = 999 
	

###############################################################################################
        
      # Her hentes fits filen ind
      #tmp_im, tmp_hdr = pyfits.getdata(fits_file, header=True)
      try:
         tmp_fits = pyfits.open(fits_file, uint=True)#, do_not_scale_image_data = True) 
         tmp_im_or = tmp_fits[0].data
         tmp_hdr = tmp_fits[0].header
      except Exception, e:
         print "Error: Could not load fits file in makeheader"
      else:
	#### Rotate image after 2018-03-18: CCD physical rotation on the spectrograph
	tmp_im = numpy.rot90(tmp_im_or,1)

######################### ROTATE IMAGE 90 degrees clockwise #####################

      try:
         tmp_file_name = fits_file.split("/")
         file_name = tmp_file_name[len(tmp_file_name)-1]
      except Exception, e:
         print "Error: Could not split filename."
        
      ################################## Here is info from Andor header copied to be moved to right location in header #################

      cam.GetHSSpeed()
      hss = cam.HSSpeed # the HSSpeeds in Mega Hertz (MHz). hss = [5.0, 3.0, 1.0, 0.05]
      cam.GetPreAmpGain()
      preamp = cam.preAmpGain[cam.preampgain]
 
      try:       
	      exptime = tmp_hdr['EXPOSURE']
	      preamp = tmp_hdr['PREAMP']
	      ac_mode = tmp_hdr['ACQMODE']
	      readmode = tmp_hdr['READMODE']
	      full_im_format = tmp_hdr['IMGRECT']
	      hbin = tmp_hdr['HBIN']
	      vbin = tmp_hdr['VBIN']
	      sub_im_format = tmp_hdr['SUBRECT']
	      trigger = tmp_hdr['TRIGGER']
	      p_ro_t = tmp_hdr['READTIME']
	      vss = tmp_hdr['VSHIFT']
		
	      model = tmp_hdr['HEAD']
	      datatype = tmp_hdr['DATATYPE']
	      serno = tmp_hdr['SERNO']
      except Exception,e:
	      exptime = cam.exptime
	     # preamp = cam.preampgain
	      if int(cam.ac_mode) == 1:
	      	ac_mode = "Single Scan"
	      else:
		ac_mode = cam.ac_mode
	      if int(cam.readmode) == 4:
		readmode = "Image"
	      else:
		readmode = cam.readmode
	      if int(cam.trigger) == 0:
		trigger = "Internal"
	      else:
	        trigger = cam.trigger
	      full_im_format = "1," + str(cam.width) + ", " +str(cam.height) + ",1"
	      hbin = cam.hbin
	      vbin = cam.vbin
	      sub_im_format = str(cam.hstart) +", " + str(cam.hend) + ", " + str(cam.vend) + ", " + str(cam.vstart)

	      p_ro_t = 1. / (float(hss) * 1e6)
	      vss = cam.vsspeed		
	      model = cam.head
	      datatype = 'Counts'
	      serno = cam.serial	     
        
      ################################## Here some parameters are calculated and collected ###############################
      fullimtime = round(p_ro_t * cam.height * cam.width,3)
      subimtime = round(p_ro_t * float(tmp_hdr['NAXIS1']) * float(tmp_hdr['NAXIS2']),3)

              
      hcap = cam.highcap
      if hcap == 0:
         hsen = 1
      else:
         hsen = 0

      ################################## Here usefull information from the database is collected ##########################
      if req_no != '':

         collect_obs_req_info_error = 0
         obs_req_values = []
         try:
	    print "Data from OR number: ", req_no, " will now be collected from the database"
            conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.or_db, m_conf.db_user, m_conf.db_password))
            curr = conn.cursor()
            obs_req_values = db_handle.get_fields_req_no(curr, m_conf.or_table, ["right_ascension","declination", "ra_pm", "dec_pm","epoch","magnitude","object_name","observer","project_name", "project_id", "site", "obs_mode"],req_no)
         except Exception, e:
            print "Error: ", e
            collect_obs_req_info_error = 1

         if obs_req_values == None:
            obs_req_values = []

         if collect_obs_req_info_error != 1 and len(obs_req_values) > 1:            
            right_ascension = str(obs_req_values["right_ascension"]) # in decimal hours
            declination = str(obs_req_values["declination"]) # in decimal degrees
            ra_pm = float(obs_req_values["ra_pm"]) # in decimal hours
            dec_pm = float(obs_req_values["dec_pm"]) # in decimal degrees
            epoch = int(obs_req_values["epoch"])
            magnitude = obs_req_values["magnitude"]
            object_name = obs_req_values["object_name"]
            observer = obs_req_values["observer"]
	    obs_pi = ""
	    count = 0
	    non_a = ""
	    for char in observer:
		try:
			char.decode('ascii')
		except UnicodeDecodeError, e:
			if count == 1:
				print "NON-ascii character found"
				char = non_a + char
				if char == '\xc3\xa9' or char == '\xc3\xa8' or char == '\xe1\xba\xbd':
					obs_pi = obs_pi + "e"
				elif char == '\xc3\xa1' or char == '\xc3\xa0' or char == '\xc3\xa3':
					obs_pi = obs_pi + "a"
				elif char == '\xc3\xba' or char == '\xc3\xb9' or char == '\xc5\xa9':
					obs_pi = obs_pi + "u"
				elif char == '\xc5\x84' or char == '\xc7\xb9' or char == '\xc3\xb1':
					obs_pi = obs_pi + "n"
				elif char == '\xc3\xa6':
					obs_pi = obs_pi + "ae"
				elif char == '\xc3\x86':
					obs_pi = obs_pi + "Ae"
				elif char == '\xc3\xb8':
					obs_pi = obs_pi + "oe"
				elif char == '\xc3\x98':
					obs_pi = obs_pi + "Oe"
				elif char == '\xc3\xa5':
					obs_pi = obs_pi + "aa"
				elif char == '\xc3\x85':
					obs_pi = obs_pi + "Aa"		
				else:
					obs_pi = obs_pi + ""
			else:
				non_a = char
				count = 1				
		else:
			obs_pi = obs_pi + char
			count = 0

	    observer = obs_pi
	
            project_name = obs_req_values["project_name"]
            project_id = obs_req_values["project_id"]
            obs_mode = obs_req_values["obs_mode"]
            site_value = int(obs_req_values["site"])
            if site_value == 1: 
               site_name = "Observatorio del Teide"
               site_lat = m_conf.lat_obs
               site_lon = m_conf.lon_obs
               site_elev = m_conf.elev_obs
               site_note = "Node 1"
         ############################### This is to change the coordinate values to the format hh:mm:ss ###################
            try:
               ra_hours,ra1 = right_ascension.split('.')
               ra2 = float(str('0.'+str(ra1)))*60.0
               ra_minutes, ra3 = str(ra2).split('.')
               ra_seconds = float(str('0.'+str(ra3))) * 60.0
               ra_object = str(ra_hours)+':'+str(ra_minutes)+':'+str("%2.5s" % ra_seconds)
            except Exception, e:
               print e
               ra_object = str(right_ascension)
            try:
               dec_degrees, dec1 = declination.split('.')
               dec2 = float(str('0.'+str(dec1)))*60.0
               dec_arcminutes, dec3 = str(dec2).split('.')
               dec_arcseconds = float(str('0.'+str(dec3))) * 60.0
               dec_object = str(dec_degrees)+':'+str(dec_arcminutes)+':'+str("%2.5s" % dec_arcseconds)
            except Exception, e:
               print e
               dec_object = str(declination)

            coor_checker = song_star_checker.coordinates()
            if coor_checker.coordinate_check(ra_object, dec_object) == 0:
               pass

	######################################    
	###### RA PROPER MOTION CONVERTION #######
	######################################	
	    ra_pm2 = (float(ra_pm) / (1000. * 3600. * 15. ))
	######################################
	###### DEC PROPER MOTION CONVERTION #######
	######################################
	    dec_pm2 = (float(dec_pm) / (1000. * 3600.))	
	######################################
	###### Difference in time from epoch 2000 to now
	    start_date = datetime.datetime(2000, 1, 1, 0, 0)
	    end_date = datetime.datetime.utcnow()
	    difference  = end_date - start_date
	    difference_in_years = (difference.days + difference.seconds/86400.)/365.2425

	    ra_object_bvc = float(right_ascension) + (float(ra_pm2) * float(difference_in_years))
	    dec_object_bvc = float(declination) + (float(dec_pm2) * float(difference_in_years))

            try:
               ra_h,ra1 = str(ra_object_bvc).split('.')
               ra2 = float(str('0.'+str(ra1)))*60.0
               ra_m, ra3 = str(ra2).split('.')
               ra_s = float(str('0.'+str(ra3))) * 60.0
            except Exception, e:
               print e
            try:
               dec_d, dec1 = str(dec_object_bvc).split('.')
               dec2 = float(str('0.'+str(dec1)))*60.0
               dec_arcm, dec3 = str(dec2).split('.')
               dec_arcs = float(str('0.'+str(dec3))) * 60.0
            except Exception, e:
               print e

            try:
		    site_value = 1
		    sun_handle = song_star_checker.sun_pos(site = site_value)
		    sun_ra = sun_handle.sun_ra()
		    sun_dec = sun_handle.sun_dec()
		    if object_name.lower() == "sun" or imagetyp.lower() == "sun":
			    ra_object = sun_ra 
			    dec_object = sun_dec
			    ra_h = str(sun_ra).split(":")[0]
			    ra_m = str(sun_ra).split(":")[1]
			    ra_s = str(sun_ra).split(":")[2]
			    dec_d = str(sun_dec).split(":")[0]
			    dec_arcm = str(sun_dec).split(":")[1]
			    dec_arcs = str(sun_dec).split(":")[2]
            except Exception, e:
               print e
      ################################ If the acquisition is a test no connection to the database is made ##################
      else:         
         epoch = 2000
         magnitude = 00
         observer = 'Unknown'
         project_name = 'Unknown'
         project_id = 0
         obs_mode = 'Unknown'
         site_value = 1
         site_name = "Observatorio del Teide"
         site_lat = m_conf.lat_obs
         site_lon = m_conf.lon_obs
         site_elev = m_conf.elev_obs
         site_note = "Node 1"
         sun_handle = song_star_checker.sun_pos(site = site_value)
         sun_ra = sun_handle.sun_ra()
         sun_dec = sun_handle.sun_dec()
         object_name = 'Unknown'
         ra_pm = 0.0
         dec_pm = 0.0
         if imagetyp.lower() == "sun":
            object_name = 'Sun'
            ra_object = sun_ra 
            dec_object = sun_dec
	    ra_h = str(sun_ra).split(":")[0]
	    ra_m = str(sun_ra).split(":")[1]
	    ra_s = str(sun_ra).split(":")[2]
	    dec_d = str(sun_dec).split(":")[0]
	    dec_arcm = str(sun_dec).split(":")[1]
            dec_arcs = str(sun_dec).split(":")[2]
         else:
	    if obj_ra == '':
	       obj_ra = "00:00:00"
	    if obj_dec == '':
	       obj_dec = "00:00:00"
            ra_object = str(obj_ra) #'06:44:8.9'		
            dec_object = str(obj_dec) #-16:42:58'
	    ra_h = str(obj_ra).split(":")[0]
	    ra_m = str(obj_ra).split(":")[1]
	    ra_s = str(obj_ra).split(":")[2]
	    dec_d = str(obj_dec).split(":")[0]
	    dec_arcm = str(obj_dec).split(":")[1]
            dec_arcs = str(obj_dec).split(":")[2]

      ### For template observations the o-star coordinates for the header needs to be handled in another way to go to the header. 
      if "TemplateObs" in remark:
            ra_object = str(obj_ra) 		
            dec_object = str(obj_dec)
	    ra_hours = str(obj_ra).split(":")[0]
	    ra_minutes = str(obj_ra).split(":")[1]
	    ra_seconds = str(obj_ra).split(":")[2]
	    dec_degrees = str(obj_dec).split(":")[0]
	    dec_arcminutes = str(obj_dec).split(":")[1]
            dec_arcseconds = str(obj_dec).split(":")[2]

      ################################### TIME ############################################################################
        
      midtime_jd = float(jd_obs)+(float(exptime)/(2.0*60.0*60.0*24.0))
      midtime_mjd = float(mjd_obs)+(float(exptime)/(2.0*60.0*60.0*24.0))
            
      midtime_UT = date_obs + datetime.timedelta(0,(float(exptime) / 2.0))

      date_obs_UT_sec = float(date_obs.second) + float( '0.' + "%06i" % date_obs.microsecond)


      #### Sidereal time ####
      song_site = ephem.Observer()
      song_site.lat = m_conf.lat_obs
      song_site.long = m_conf.lon_obs
      song_site.elev = m_conf.elev_obs
      song_site.date = midtime_UT
      sidereal_time = song_site.sidereal_time()
      
      ############ Barycentric time #############
      # The BJD-2400000 for the midtime of the exposure.
      # The barycentric velocity correction for the midtime of the exposure. (km/s)      

      leap_s = ephem.delta_t("%i/%i/%i" % (date_obs.year, date_obs.month, date_obs.day))

      try:
		BJD, BVC = barcor_song_mfa.getbar_song2(epoch, ra_h, ra_m, ra_s, dec_d, dec_arcm, dec_arcs, site_lon, site_lat, site_elev, int(date_obs.year), int(date_obs.month), int(date_obs.day), int(date_obs.hour), int(date_obs.minute), float(date_obs_UT_sec), float(exptime), float(leap_s), 1,1 )
      except Exception, e:
		print e
		BJD = 0
		BVC = 0
            
      ############################### Here values for object, Sun and Moon is calculated ####################################
      moon_handle = song_star_checker.moon_pos(site=site_value)
      sun_handle = song_star_checker.sun_pos(site=site_value)
      star_handle = song_star_checker.star_pos(site=site_value)
      
      moon_alt = moon_handle.moon_alt()
      moon_az = moon_handle.moon_az()      
      moon_phase = moon_handle.moon_phase()
      if object_name_1.lower() not in ["","flat", "bias", "flati2"] or object_name.lower() != "unknown":
		object_alt = star_handle.star_alt(ra_object,dec_object)
		object_az = star_handle.star_az(ra_object,dec_object)
		moon_dist = moon_handle.moon_dist(ra_object,dec_object)
		sun_dist = sun_handle.sun_dist(ra_object,dec_object)
      else:
      		object_alt = ""
		object_az = ""
		moon_dist = ""
		sun_dist = ""

      sun_alt = sun_handle.sun_alt()
      sun_az = sun_handle.sun_az()
      sun_set = sun_handle.sun_set_pre()
      sun_rise = sun_handle.sun_rise_next()
      sun_ra = sun_handle.sun_ra()
      sun_dec = sun_handle.sun_dec()
    
      ################################ The values in the Andor header which is not usefull and/or is replaced.
      try:
	      del tmp_hdr['HIERARCH EMREALGAIN']
	      del tmp_hdr['HIERARCH COUNTCONVERTMODE']
	      del tmp_hdr['HIERARCH COUNTCONVERT']
	      del tmp_hdr['HIERARCH DETECTIONWAVELENGTH']
	      del tmp_hdr['HIERARCH SENSITIVITY']
	      del tmp_hdr['HIERARCH SPURIOUSNOISEFILTER']
	      del tmp_hdr['HIERARCH THRESHOLD']
	      del tmp_hdr['HIERARCH PHOTONCOUNTINGENABLED']
	      del tmp_hdr['HIERARCH NOTHRESHOLDS']
	      del tmp_hdr['HIERARCH PHOTONCOUNTINGTHRESHOLD1']
	      del tmp_hdr['HIERARCH PHOTONCOUNTINGTHRESHOLD2']
	      del tmp_hdr['HIERARCH PHOTONCOUNTINGTHRESHOLD3']
	      del tmp_hdr['HIERARCH PHOTONCOUNTINGTHRESHOLD4']
	      del tmp_hdr['HIERARCH AVERAGINGFILTERMODE']
	      del tmp_hdr['HIERARCH AVERAGINGFACTOR']
	      del tmp_hdr['HIERARCH FRAMECOUNT']

	      del tmp_hdr['USERTXT1']
	      del tmp_hdr['USERTXT2']
	      del tmp_hdr['USERTXT3']
	      del tmp_hdr['USERTXT4']
	      del tmp_hdr['TEMP']
	      del tmp_hdr['UNSTTEMP']
	      del tmp_hdr['GAIN']
	      del tmp_hdr['VCLKAMP']
	      del tmp_hdr['PREAMP']
	      del tmp_hdr['PRECAN']
	      del tmp_hdr['FLIPX']
	      del tmp_hdr['FLIPY']
	      del tmp_hdr['XTYPE']
	      del tmp_hdr['XUNIT']
	      del tmp_hdr['CALIB']
	      del tmp_hdr['DLLVER']
	      del tmp_hdr['OPERATN']
	      del tmp_hdr['BLCLAMP']
	      del tmp_hdr['HEAD']
	      del tmp_hdr['DATATYPE']
	      del tmp_hdr['SERNO']
	      del tmp_hdr['COMMENT']
	      del tmp_hdr['EXPOSURE'] 
	      del tmp_hdr['ACQMODE'] 
	      del tmp_hdr['READMODE']
	      del tmp_hdr['IMGRECT']
	      del tmp_hdr['HBIN']
	      del tmp_hdr['VBIN']
	      del tmp_hdr['SUBRECT']
	      del tmp_hdr['TRIGGER']
	      del tmp_hdr['READTIME']
	      del tmp_hdr['VSHIFT']
	      del tmp_hdr['DATE']     # This is a time stamp the camera makes itself and is not accurate. 
	      del tmp_hdr['FRAME']    # This is a time stamp the camera makes itself and is not accurate.
      except Exception,e:
	pass
######################Here the info are written to the fits header#######################################################
# Camera information --------------------------------------------------------------------------------------

      try:
	      tmp_hdr.update('IMFORM','FITS', comment='Image format (Flexible Image Transport System)')
	      tmp_hdr.update('DATATYPE',datatype, comment='Type of data')
	      tmp_hdr.update('IMAGETYP',imagetyp, comment='Image type: flat, bias, star, etc.')
	      tmp_hdr.update('COMMENT',remark, comment='Observers comment')
	      tmp_hdr.update('FILE',file_name, comment='Path/filename')
	      tmp_hdr.update('---C----', '-------CCD--------', comment='Detector parameters for specific exposure')
	      tmp_hdr.update('HEAD',model, comment='CCD camera model name')
	      tmp_hdr.update('SERNO',serno, comment='System serial number')
	      tmp_hdr.update('CCD_TEMP',round(ccdtemp,3), comment='The temperature of the CCD in degrees')
	      tmp_hdr.update('EXPTIME',exptime, comment='The exposure time in seconds')
	      tmp_hdr.update('PRE_GAIN',preamp, comment='The pre amplifier gain value')
	      tmp_hdr.update('HSSPEED',hss, comment='The Horizontal Shift Speed in MHz')
	      #tmp_hdr.update('VSSPEED',vss, comment='The Vertical Shift Speed in MHz^(-1)')???
	      tmp_hdr.update('HIGHCAP',hcap, comment='High Capacity: 0 = Off, 1 = On')
	      tmp_hdr.update('HIGHSEN',hsen, comment='High Sensitivity: 0 = Off, 1 = On')
	      tmp_hdr.update('READTIME',p_ro_t, comment='Pixel readout time')
	      tmp_hdr.update('HOR_BIN',hbin, comment='Horizontal binning')
	      tmp_hdr.update('VER_BIN',vbin, comment='Vertical binning')
	      tmp_hdr.update('FULL_ROT',fullimtime, comment='The full image read out time in seconds ')
	      tmp_hdr.update('SUB_ROT',subimtime, comment='The sub image read out time in seconds ')
	      tmp_hdr.update('FULL_IM',full_im_format, comment='Full image format (hstart,hend,vend,vstart)')
	      tmp_hdr.update('SUB_IM',sub_im_format, comment='Sub image format (hstart,hend,vend,vstart)')
	      tmp_hdr.update('AC_MODE',ac_mode, comment='Acquisition mode')
	      tmp_hdr.update('READMODE',readmode, comment='Image readout mode')
	      tmp_hdr.update('TRIGGER',trigger, comment='The shutter trigger mode')
	      tmp_hdr.update('ROT','ROT_ANGLE', comment='Rotation angle of the detector if any')
	      
	# Mixed information -------------------------------------------------------------------------------------------
	      tmp_hdr.update('---M----', '-------MIXED------', comment='-------------------------------------')
	      tmp_hdr.update('OBSERVER', 'Mads Fredslund Andersen', comment='The SONG robot developer')
	      tmp_hdr.update('OBS-PI', observer, comment='The PI of the observations')
	      tmp_hdr.update('OBS-MODE', obs_mode, comment='The observing mode')
	      tmp_hdr.update('PROJ-ID', project_id, comment='The SONG project id provided by the TAC')
	      tmp_hdr.update('PROJECT', project_name, comment='The project name provided by the TAC')
	      tmp_hdr.update('OBSERVAT', site_name, comment='The observatory')
	      tmp_hdr.update('SITELONG',site_lon, comment='The longitude of the specific location (west).')
	      tmp_hdr.update('SITELAT',site_lat, comment='The latitude of the specific location.')
	      tmp_hdr.update('SITEELEV',site_elev, comment='The elevation (m) at the specific location.')
	      tmp_hdr.update('TELESCOP', site_note, comment='The telescope from were the object is observed')
	      tmp_hdr.update('DETECTOR', 'iKon-L DZ 936 BV', comment='The CCD detector used for the observations')
	      tmp_hdr.update('INSTRUM', 'Spectrograph', comment='The used instrument for the observations')
	      tmp_hdr.update('REQ_NO', req_no, comment='The observation request number')
	    
	# object information--------------------------------------------------------------------------
	      tmp_hdr.update('---O----', '------OBJECT------', comment='-------------------------------------')
	      tmp_hdr.update('OBJECT',object_name_1, comment='The name of the object observed')
	      tmp_hdr.update('OBJ-NAME',object_name, comment='The name of the object observed')
	      tmp_hdr.update('OBJ-RA',str(ra_object), comment='Right Ascension of the object')
	      tmp_hdr.update('OBJ-DEC',str(dec_object), comment='Declination of the object')
	      tmp_hdr.update('EPOCH',"J" + str(epoch), comment='Epoch of coordinates')
	      tmp_hdr.update('RA_PM',ra_pm, comment='Proper motion in RA in mas per year')
	      tmp_hdr.update('DEC_PM',dec_pm, comment='Proper motion in DEC in mas per year')
	      tmp_hdr.update('OBJ-ALT',str(object_alt), comment='Altitude of the object')
	      tmp_hdr.update('OBJ-AZ',str(object_az), comment='Azimuth of the object')
	      tmp_hdr.update('OBJ-MAG',magnitude, comment='The V magnitude of the object')
	     
	# Spectrograph information ---------------------------------------------------------------------------------             
	      tmp_hdr.update('---SP---', '---SPECTROGRAPH---', comment='-------------------------------------')
	      tmp_hdr.update('SLIT',int(slit_pos), comment='Slit position (1 to 9)')
	      tmp_hdr.update('CAMFOCS',int(spec_focus), comment='The camera mirror focus')
	      tmp_hdr.update('TEMP1',round(float(c_flange_temp),2), comment='The temperature of camera flange inside')
	      tmp_hdr.update('TEMP2',round(float(cross_d_temp),2), comment='The temperature of cross disperser')
	      tmp_hdr.update('TEMP3',round(float(spec_table_temp),2), comment='The temperature of spectrograph table')
	      tmp_hdr.update('TEMP4',round(float(cont_air_temp),2), comment='The temperature of container air')
	      tmp_hdr.update('THAR',int(lamp_thar_on), comment='ThAr lamp (off=0, on=1)')
	      tmp_hdr.update('HALOGEN',int(lamp_halogen_on), comment='Halogen lamp (off=0, on=1)')
	      tmp_hdr.update('I2POS',int(iodine_pos), comment='Iodine pos (1=test-cell,2=free,3=iodine)')
	      tmp_hdr.update('I2T_ACT',float(iodine_temp_read), comment='The actual temp. of the iodine cell')
	      tmp_hdr.update('I2T_SET',float(iodine_temp_set), comment='The set temp. of the iodine cell')
	      tmp_hdr.update('FILTWH',int(filter_pos), comment='Filter wh. (1=n1.3,2=n2,3=n3,4=5=free,6=n0.7)')
	      tmp_hdr.update('CALIB_M',int(calib_mirror_pos), comment='Calib. mirror: (1=out,2=in,3=ThAr,4=Aux)')
	      tmp_hdr.update('MIRR_SL',int(mirror_slide), comment='Beamsplit: (1=end,2=acqui,3=cube)')
	      #tmp_hdr.update('MIRR_SL',int(mirror_slide), comment='Mirror slide position')
	      if int(iodine_pos) == 1: 
		 tmp_hdr.update('IODID',spec_ccd_config.iodine_test_cell_id, comment='Cell-ID of the iodine cell in use.')
	      else:
		  tmp_hdr.update('IODID',spec_ccd_config.iodine_primary_cell_id, comment='Cell-ID of the iodine cell in use.')
	      #tmp_hdr.update('IODSCAN','iodinescan', comment='Scan name for the iodine cell.')
	      
	# Telescope information ---------------------------------------------------------------------------------             
	      tmp_hdr.update('---TEL--', '-----TELESCOPE----', comment='-------------------------------------')
	      tmp_hdr.update('TEL_RA',float(tel_ra), comment='Right Ascension of the telescope')
	      tmp_hdr.update('TEL_DEC',float(tel_dec), comment='Declination of the telescope')
	      tmp_hdr.update('TEL_AZ',float(tel_az), comment='Azimuth of the telescope')
	      tmp_hdr.update('TEL_ALT',float(tel_alt), comment='Altitude of the telescope')
	      tmp_hdr.update('TEL_FOC',float(tel_focus), comment='Focus of the telescope')
	      tmp_hdr.update('TEL_TM',int(tel_third_mirror), comment='Third mirror position')
	      tmp_hdr.update('TEMP_M1',round(float(tel_temp_m1),2), comment='Temperature M1')
	      tmp_hdr.update('TEMP_M2',round(float(tel_temp_m2),2), comment='Temperature M2')
	      tmp_hdr.update('TEMP_M3',round(float(tel_temp_m3),2), comment='Temperature M3')
	      tmp_hdr.update('TEMP_TT',round(float(tel_temp_tt),2), comment='Temperature Structure')
	      #tmp_hdr.update('HA','hour angle', comment='Hour angle of the telescope')
	      #tmp_hdr.update('ZDIST','Zenit distance', comment='Distance to Zenit from telescope')
	  
	# weather information-----------------------------------------------------------------------
	      tmp_hdr.update('---W----', '------WEATHER-----', comment='-------------------------------------')
	     #tmp_hdr.update('W_SITE', weather_page, comment='Weather homepage')
	      tmp_hdr.update('W_TIME',weather_info_time, comment='Reliability of weather data')
	      tmp_hdr.update('OUTTEMP',round(float(temp),3), comment='The temp (Celsius) outside the container')
	      tmp_hdr.update('OUTHUMID',round(float(hum),3), comment='The humidity (%) outside the container')
	      tmp_hdr.update('OUTPRESS',round(float(pres),3), comment='The pressure (mb) outside the container.')
	      tmp_hdr.update('WINDSPEE',round(float(wind),3), comment='The windspeed (m/s) outside the container.')
	      tmp_hdr.update('WIND-DIR',round(float(wdir),3), comment='The wind direction outside the container')
	      tmp_hdr.update('SEEING1',round(float(seeing1),2), comment='The current seeing value on slit guiders')
	      tmp_hdr.update('SEEING2',round(float(seeing2),2), comment='The running mean seeing on slit guiders')
	      tmp_hdr.update('PUPIL_FL',round(float(pupil_flux_left),2), comment='Left side pupil flux level')
	      tmp_hdr.update('PUPIL_FR',round(float(pupil_flux_right),2), comment='Right side pupil flux level')
	      #tmp_hdr.update('SUN-RADI',float(sun_r), comment='Solar radiation in watts per square meters')

	# moon information-------------------------------------------------------------------------
	      tmp_hdr.update('---SM---', '-----SUN/MOON-----', comment='-------------------------------------')
	      tmp_hdr.update('MOON-PHA', round(float(moon_phase),3), comment='The Moons phase at the moment')
	      tmp_hdr.update('MOON-D', str(moon_dist), comment='Distance to the moon from the object')
	      tmp_hdr.update('MOON-ALT', str(moon_alt), comment='Altitude of the moon from horizon')
	      tmp_hdr.update('MOON-AZ', str(moon_az), comment='Azimuth of the moon')
	# Sun information -------------------------------------------------------------------------
	      tmp_hdr.update('SUN-ALT', str(sun_alt), comment='Altitude of the Sun from horizon')
	      tmp_hdr.update('SUN-AZ', str(sun_az), comment='Azimuth of the Sun')
	      tmp_hdr.update('SUN-SET', str(sun_set), comment='Time of previous sunset in UT')
	      tmp_hdr.update('SUN-RISE', str(sun_rise), comment='Time of next sunrise in UT')
	      tmp_hdr.update('SUN-RA', str(sun_ra), comment='The right ascension of the Sun')
	      tmp_hdr.update('SUN-DEC', str(sun_dec), comment='The declination of the Sun')
	      tmp_hdr.update('SUN-DIST', str(sun_dist), comment='Distance from object to Sun')
	      

	      now_time = datetime.datetime.now() # Local time when header was updated
	      now_time = str(now_time).replace(" ", "T")
	      now_time_ut = datetime.datetime.utcnow() # UTC time when header was updated
	      now_time_ut = str(now_time_ut).replace(" ", "T")

	      creation_stop_time = time.time()

	      c_time = creation_stop_time - creation_start_time

	# Time stamps ---------------------------------------------------------------------------------             
	      tmp_hdr.update('---TI---', '--------TIME------', comment='-------------------------------------')
	      tmp_hdr.update('DATE-UP', str(now_time), comment='Local time when header was updated')
	      tmp_hdr.update('DATE-UP2', str(now_time_ut), comment='UTC time when header was updated')
	      tmp_hdr.update('DATE-OBS', str(date_obs).replace(" ", "T"), comment='Start time of exposure in UTC')
	      tmp_hdr.update('JD-DATE', float("%.7f" % float(jd_obs)), comment='Time for start of exposure in Julian date')
	      tmp_hdr.update('MJD-DATE', float("%.7f" % float(mjd_obs)), comment='Time for start of exposure in Modified JD')
	      tmp_hdr.update('OBS-MID', str(midtime_UT).replace(" ", "T"), comment='Time for midtime of exposure in UT')
	      tmp_hdr.update('JD-MID', float("%.7f" % float(midtime_jd)), comment='Time for midtime of exposure in Julian date')
	      tmp_hdr.update('MJD-MID', float("%.7f" % float(midtime_mjd)), comment='Time for midtime of exposure in Modified JD')
	      tmp_hdr.update('ST-MID', str(sidereal_time), comment='Midtime of exposure in local sidereal time')
	      tmp_hdr.update('BJD-MID', float("%.7f" % float(BJD)), comment='UT Barycentric midtime of exp. BJD-2400000')
	      tmp_hdr.update('BVC', float("%.7f" % float(BVC)), comment='Barycentric velocity correction in Km/s')
	      # ----------------------------------------------------------------------------------------------------------
	      tmp_hdr.update('---DB---', '------DEBUG-----', comment='-------------------------------------')
	      tmp_hdr.update('UP-TIME', c_time, comment='Used seconds to update the header')
	      tmp_hdr.update('EXP-READ', used_exp_time, comment='Exposure + readout time in seconds from imclass')     
      except Exception,e:
	      tmp_hdr.append(('IMFORM', 'FITS', 'Image format (Flexible Image Transport System)'))
	      tmp_hdr.append(('DATATYPE',datatype, 'Type of data'))
	      tmp_hdr.append(('IMAGETYP',imagetyp, 'Image type: flat, bias, star, etc.'))
	      tmp_hdr.append(('COMMENT',remark, 'Observers comment'))
	      tmp_hdr.append(('FILE',file_name, 'Path/filename'))
	      tmp_hdr.append(('---C----', '-------CCD--------', 'Detector parameters for specific exposure'))
	      tmp_hdr.append(('HEAD',model, 'CCD camera model name'))
	      tmp_hdr.append(('SERNO',serno, 'System serial number'))
	      tmp_hdr.append(('CCD_TEMP',round(ccdtemp,3), 'The temperature of the CCD in degrees'))
	      tmp_hdr.append(('EXPTIME',exptime, 'The exposure time in seconds'))
	      tmp_hdr.append(('PRE_GAIN',preamp, 'The pre amplifier gain value'))
	      tmp_hdr.append(('HSSPEED',hss, 'The Horizontal Shift Speed in MHz'))
	      #tmp_hdr.append(('VSSPEED',vss, 'The Vertical Shift Speed in MHz^(-1)')???
	      tmp_hdr.append(('HIGHCAP',hcap, 'High Capacity: 0 = Off, 1 = On'))
	      tmp_hdr.append(('HIGHSEN',hsen, 'High Sensitivity: 0 = Off, 1 = On'))
	      tmp_hdr.append(('READTIME',p_ro_t, 'Pixel readout time'))
	      tmp_hdr.append(('HOR_BIN',hbin, 'Horizontal binning'))
	      tmp_hdr.append(('VER_BIN',vbin, 'Vertical binning'))
	      tmp_hdr.append(('FULL_ROT',fullimtime, 'The full image read out time in seconds '))
	      tmp_hdr.append(('SUB_ROT',subimtime, 'The sub image read out time in seconds '))
	      tmp_hdr.append(('FULL_IM',full_im_format, 'Full image format (hstart,hend,vend,vstart)'))
	      tmp_hdr.append(('SUB_IM',sub_im_format, 'Sub image format (hstart,hend,vend,vstart)'))
	      tmp_hdr.append(('AC_MODE',ac_mode, 'Acquisition mode'))
	      tmp_hdr.append(('READMODE',readmode, 'Image readout mode'))
	      tmp_hdr.append(('TRIGGER',trigger, 'The shutter trigger mode'))
	      tmp_hdr.append(('ROT','ROT_ANGLE', 'Rotation angle of the detector if any'))
	      
	# Mixed information -------------------------------------------------------------------------------------------
	      tmp_hdr.append(('---M----', '-------MIXED------', '-------------------------------------'))
	      tmp_hdr.append(('OBSERVER', 'Mads Fredslund Andersen', 'The SONG robot developer'))
	      tmp_hdr.append(('OBS-PI', observer, 'The PI of the observations'))
	      tmp_hdr.append(('OBS-MODE', obs_mode, 'The observing mode'))
	      tmp_hdr.append(('PROJ-ID', project_id, 'The SONG project id provided by the TAC'))
	      tmp_hdr.append(('PROJECT', project_name, 'The project name provided by the TAC'))
	      tmp_hdr.append(('OBSERVAT', site_name, 'The observatory'))
	      tmp_hdr.append(('SITELONG',site_lon, 'The longitude of the specific location (west).'))
	      tmp_hdr.append(('SITELAT',site_lat, 'The latitude of the specific location.'))
	      tmp_hdr.append(('SITEELEV',site_elev, 'The elevation (m) at the specific location.'))
	      tmp_hdr.append(('TELESCOP', site_note, 'The telescope from were the object is observed'))
	      tmp_hdr.append(('DETECTOR', 'iKon-L DZ 936 BV', 'The CCD detector used for the observations'))
	      tmp_hdr.append(('INSTRUM', 'Spectrograph', 'The used instrument for the observations'))
	      tmp_hdr.append(('REQ_NO', req_no, 'The observation request number'))
	    
	# object information--------------------------------------------------------------------------
	      tmp_hdr.append(('---O----', '------OBJECT------', '-------------------------------------'))
	      tmp_hdr.append(('OBJECT',object_name_1, 'The name of the object observed'))
	      tmp_hdr.append(('OBJ-NAME',object_name, 'The name of the object observed'))
	      tmp_hdr.append(('OBJ-RA',str(ra_object), 'Right Ascension of the object'))
	      tmp_hdr.append(('OBJ-DEC',str(dec_object), 'Declination of the object'))
	      tmp_hdr.append(('EPOCH',"J" + str(epoch), 'Epoch of coordinates'))
	      tmp_hdr.append(('RA_PM',ra_pm, 'Proper motion in RA in mas per year'))
	      tmp_hdr.append(('DEC_PM',dec_pm, 'Proper motion in DEC in mas per year'))
	      tmp_hdr.append(('OBJ-ALT',str(object_alt), 'Altitude of the object'))
	      tmp_hdr.append(('OBJ-AZ',str(object_az), 'Azimuth of the object'))
	      tmp_hdr.append(('OBJ-MAG',magnitude, 'The V magnitude of the object'))
	     
	# Spectrograph information ---------------------------------------------------------------------------------             
	      tmp_hdr.append(('---SP---', '---SPECTROGRAPH---', '-------------------------------------'))
	      tmp_hdr.append(('SLIT',int(slit_pos), 'Slit position (1 to 9)'))
	      tmp_hdr.append(('CAMFOCS',int(spec_focus), 'The camera mirror focus'))
	      tmp_hdr.append(('TEMP1',round(float(c_flange_temp),2), 'The temperature of camera flange inside'))
	      tmp_hdr.append(('TEMP2',round(float(cross_d_temp),2), 'The temperature of cross disperser'))
	      tmp_hdr.append(('TEMP3',round(float(spec_table_temp),2), 'The temperature of spectrograph table'))
	      tmp_hdr.append(('TEMP4',round(float(cont_air_temp),2), 'The temperature of container air'))
	      tmp_hdr.append(('THAR',int(lamp_thar_on), 'ThAr lamp (off=0, on=1)'))
	      tmp_hdr.append(('HALOGEN',int(lamp_halogen_on), 'Halogen lamp (off=0, on=1)'))
	      tmp_hdr.append(('I2POS',int(iodine_pos), 'Iodine pos (1=test-cell,2=free,3=iodine)'))
	      tmp_hdr.append(('I2T_ACT',float(iodine_temp_read), 'The actual temp. of the iodine cell'))
	      tmp_hdr.append(('I2T_SET',float(iodine_temp_set), 'The set temp. of the iodine cell'))
	      tmp_hdr.append(('FILTWH',int(filter_pos), 'Filter wh. (1=n1.3,2=n2,3=n3,4=5=free,6=n0.7)'))
	      tmp_hdr.append(('CALIB_M',int(calib_mirror_pos), 'Calib. mirror: (1=out,2=in,3=ThAr,4=Aux)'))
	      tmp_hdr.append(('MIRR_SL',int(mirror_slide), 'Beamsplit: (1=end,2=acqui,3=cube)'))
	      #tmp_hdr.append(('MIRR_SL',int(mirror_slide), 'Mirror slide position'))

	      ##### IODINE-ID:  1: Primary (position 3), 2: Debra Fishers (position 1), 3: Paul Butlers (position 1)
	      if int(iodine_pos) == 1: 
		 tmp_hdr.append(('IODID',3, 'Cell-ID of the iodine cell in use.'))
	      else:
		  tmp_hdr.append(('IODID',1, 'Cell-ID of the iodine cell in use.'))
	      #tmp_hdr.append(('IODSCAN','iodinescan', comment='Scan name for the iodine cell.'))
	      
	# Telescope information ---------------------------------------------------------------------------------             
	      tmp_hdr.append(('---TEL--', '-----TELESCOPE----', '-------------------------------------'))
	      tmp_hdr.append(('TEL_RA',float(tel_ra), 'Right Ascension of the telescope'))
	      tmp_hdr.append(('TEL_DEC',float(tel_dec), 'Declination of the telescope'))
	      tmp_hdr.append(('TEL_AZ',float(tel_az), 'Azimuth of the telescope'))
	      tmp_hdr.append(('TEL_ALT',float(tel_alt), 'Altitude of the telescope'))
	      tmp_hdr.append(('TEL_FOC',float(tel_focus), 'Focus of the telescope'))
	      tmp_hdr.append(('TEL_TM',int(tel_third_mirror), 'Third mirror position'))
	      tmp_hdr.append(('TEMP_M1',round(float(tel_temp_m1),2), 'Temperature M1'))
	      tmp_hdr.append(('TEMP_M2',round(float(tel_temp_m2),2), 'Temperature M2'))
	      tmp_hdr.append(('TEMP_M3',round(float(tel_temp_m3),2), 'Temperature M3'))
	      tmp_hdr.append(('TEMP_TT',round(float(tel_temp_tt),2), 'Temperature Structure'))
	      #tmp_hdr.append(('HA','hour angle', 'Hour angle of the telescope'))
	      #tmp_hdr.append(('ZDIST','Zenit distance', 'Distance to Zenit from telescope'))
	  
	# weather information-----------------------------------------------------------------------
	      tmp_hdr.append(('---W----', '------WEATHER-----', '-------------------------------------'))
	     #tmp_hdr.append(('W_SITE', weather_page, 'Weather homepage'))
	      tmp_hdr.append(('W_TIME',weather_info_time, 'Reliability of weather data'))
	      tmp_hdr.append(('OUTTEMP',round(float(temp),3), 'The temp (Celsius) outside the container'))
	      tmp_hdr.append(('OUTHUMID',round(float(hum),3), 'The humidity (%) outside the container'))
	      tmp_hdr.append(('OUTPRESS',round(float(pres),3), 'The pressure (mb) outside the container.'))
	      tmp_hdr.append(('WINDSPEE',round(float(wind),3), 'The windspeed (m/s) outside the container.'))
	      tmp_hdr.append(('WIND-DIR',round(float(wdir),3), 'The wind direction outside the container'))
	      tmp_hdr.append(('SEEING1',round(float(seeing1),2), 'The current seeing value on slit guiders'))
	      tmp_hdr.append(('SEEING2',round(float(seeing2),2), 'The running mean seeing on slit guiders'))
	      tmp_hdr.append(('PUPIL_FL',round(float(pupil_flux_left),2), 'Left side pupil flux level'))
	      tmp_hdr.append(('PUPIL_FR',round(float(pupil_flux_right),2), 'Right side pupil flux level'))
	      #tmp_hdr.append(('SUN-RADI',float(sun_r), 'Solar radiation in watts per square meters'))

	# moon information-------------------------------------------------------------------------
	      tmp_hdr.append(('---SM---', '-----SUN/MOON-----', '-------------------------------------'))
	      tmp_hdr.append(('MOON-PHA', round(float(moon_phase),3), 'The Moons phase at the moment'))
	      tmp_hdr.append(('MOON-D', str(moon_dist), 'Distance to the moon from the object'))
	      tmp_hdr.append(('MOON-ALT', str(moon_alt), 'Altitude of the moon from horizon'))
	      tmp_hdr.append(('MOON-AZ', str(moon_az), 'Azimuth of the moon'))
	# Sun information -------------------------------------------------------------------------
	      tmp_hdr.append(('SUN-ALT', str(sun_alt), 'Altitude of the Sun from horizon'))
	      tmp_hdr.append(('SUN-AZ', str(sun_az), 'Azimuth of the Sun'))
	      tmp_hdr.append(('SUN-SET', str(sun_set), 'Time of previous sunset in UT'))
	      tmp_hdr.append(('SUN-RISE', str(sun_rise), 'Time of next sunrise in UT'))
	      tmp_hdr.append(('SUN-RA', str(sun_ra), 'The right ascension of the Sun'))
	      tmp_hdr.append(('SUN-DEC', str(sun_dec), 'The declination of the Sun'))
	      tmp_hdr.append(('SUN-DIST', str(sun_dist), 'Distance from object to Sun'))
	      

	      now_time = datetime.datetime.now() # Local time when header was updated
	      now_time = str(now_time).replace(" ", "T")
	      now_time_ut = datetime.datetime.utcnow() # UTC time when header was updated
	      now_time_ut = str(now_time_ut).replace(" ", "T")

	      creation_stop_time = time.time()

	      c_time = creation_stop_time - creation_start_time

	# Time stamps ---------------------------------------------------------------------------------             
	      tmp_hdr.append(('---TI---', '--------TIME------', '-------------------------------------'))
	      tmp_hdr.append(('DATE-UP', str(now_time), 'Local time when header was updated'))
	      tmp_hdr.append(('DATE-UP2', str(now_time_ut), 'UTC time when header was updated'))
	      tmp_hdr.append(('DATE-OBS', str(date_obs).replace(" ", "T"), 'Start time of exposure in UTC'))
	      tmp_hdr.append(('JD-DATE', float("%.7f" % float(jd_obs)), 'Time for start of exposure in Julian date'))
	      tmp_hdr.append(('MJD-DATE', float("%.7f" % float(mjd_obs)), 'Time for start of exposure in Modified JD'))
	      tmp_hdr.append(('OBS-MID', str(midtime_UT).replace(" ", "T"), 'Time for midtime of exposure in UT'))
	      tmp_hdr.append(('JD-MID', float("%.7f" % float(midtime_jd)), 'Time for midtime of exposure in Julian date'))
	      tmp_hdr.append(('MJD-MID', float("%.7f" % float(midtime_mjd)), 'Time for midtime of exposure in Modified JD'))
	      tmp_hdr.append(('ST-MID', str(sidereal_time), 'Midtime of exposure in local sidereal time'))
	      tmp_hdr.append(('BJD-MID', float("%.7f" % float(BJD)), 'UT Barycentric midtime of exp. BJD-2400000'))
	      tmp_hdr.append(('BVC', float("%.7f" % float(BVC)), 'Barycentric velocity correction in Km/s'))
	      # ----------------------------------------------------------------------------------------------------------
	      tmp_hdr.append(('---DB---', '------DEBUG-----', '-------------------------------------'))
	      tmp_hdr.append(('UP-TIME', c_time, 'Used seconds to update the header'))
	      tmp_hdr.append(('EXP-READ', used_exp_time, 'Exposure + readout time in seconds from imclass'))  	

      ########################## Here the modified FITS header is updated and saved ######################################
      pyfits.update(fits_file, tmp_im, tmp_hdr)

      return 1





