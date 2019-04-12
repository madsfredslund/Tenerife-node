"""
   Created on Mar 16, 2010

   @author: madsfa
"""

import andor
import time
import pyfits
import sys
import song_timeclass
import os
import song_star_checker
import string
import get_db_values
import psycopg2
import datetime
import numpy
#import barcor_song_mfa
import ephem
import master_config as m_conf

clock = song_timeclass.TimeClass()
    
db_handle = get_db_values.db_connection()
class MakeHeader(object):
   """
      This class will modify the header of the observed fits file to contain the relevant information
   """
   # cam is the cameraobject, ccdtemp is the temperature of the ccd just before the exposure. date_obs, jd_obs and mjd_obs is timestamps. file is the FITS file to be modified. 
   def makeheader(self,cam,ccdtemp,date_obs,jd_obs,mjd_obs,fits_file,hsspeed,pregain,highcap,imagetyp,object_name_1,req_no, obj_ra, obj_dec, remark, used_exp_time, camera):
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
         weather_values = db_handle.get_fields(curr, "weather_station", ["drd11_rain","wxt520_rain_int","bw_rain_cond","wxt520_wind_avg", "wxt520_wind_avgdir","wxt520_wind_speed","wxt520_temp1","wxt520_humidity","wxt520_wind_direction","wxt520_pressure","bw_cloud_cond","bw_dewp_temp","ins_at"])
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

########################## TELESCOPE AND DOME DATA ############################################
      collect_tel_dome_info_error = 0
      tel_dome_values = []
      try:
         conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
         curr = conn.cursor()
         tel_dome_values = db_handle.get_fields(curr, "tel_dome", ["tel_ra", "tel_dec", "tel_az", "tel_alt", "tel_zd", "tel_focus", "third_mirror", "gps_st", "temp_m1", "temp_m2", "temp_m3", "temp_n1"])
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


###############################################################################################
        
      # Her hentes fits filen ind
      #tmp_im, tmp_hdr = pyfits.getdata(fits_file, header=True)
      try:
         tmp_fits = pyfits.open(fits_file, uint16=True)#, do_not_scale_image_data = True) 
         tmp_im = tmp_fits[0].data
         tmp_hdr = tmp_fits[0].header
      except Exception, e:
         print "Error: Could not load fits file in makeheader"

      try:
         tmp_file_name = fits_file.split("/")
         file_name = tmp_file_name[len(tmp_file_name)-1]
      except Exception, e:
         print "Error: Could not split filename."
        
      ################################## Here is info from Andor header copied to be moved to right location in header #################
        
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
        
      ################################## Here some parameters are calculated and collected ###############################
      fullimtime = round(p_ro_t * cam.height * cam.width,3)
      subimtime = round(p_ro_t * float(tmp_hdr['NAXIS1']) * float(tmp_hdr['NAXIS2']),3)
      cam.GetHSSpeed()
      hss = cam.HSSpeed # the HSSpeeds in Mega Hertz (MHz). hss = [5.0, 3.0, 1.0, 0.05]
              
      hcap = cam.highcap
      if hcap == 0:
         hsen = 1
      else:
         hsen = 0

      ################################## Here usefull information from the database is collected ##########################
      print req_no
      if req_no != '' and req_no != 0:

		print "No OR can be made at the moment to observe with photometry"

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

#      try:
#		BJD, BVC = barcor_song_mfa.getbar_song2(epoch, ra_h, ra_m, ra_s, dec_d, dec_arcm, dec_arcs, site_lon, site_lat, site_elev, int(date_obs.year), int(date_obs.month), int(date_obs.day), int(date_obs.hour), int(date_obs.minute), float(date_obs_UT_sec), float(exptime), float(leap_s), 1,1 )
#      except Exception, e:
#		print e
#		BJD = 0
#		BVC = 0
            
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

#      del tmp_hdr['USERTXT1']
#      del tmp_hdr['USERTXT2']
#      del tmp_hdr['USERTXT3']
#      del tmp_hdr['USERTXT4']
#      del tmp_hdr['TEMP']
#      del tmp_hdr['UNSTTEMP']
#      del tmp_hdr['GAIN']
#      del tmp_hdr['VCLKAMP']
#      del tmp_hdr['PREAMP']
#      del tmp_hdr['PRECAN']
#      del tmp_hdr['FLIPX']
#      del tmp_hdr['FLIPY']
#      del tmp_hdr['XTYPE']
#      del tmp_hdr['XUNIT']
#      del tmp_hdr['CALIB']
#      del tmp_hdr['DLLVER']
#      del tmp_hdr['OPERATN']
#      del tmp_hdr['BLCLAMP']
#      del tmp_hdr['HEAD']
#      del tmp_hdr['DATATYPE']
#      del tmp_hdr['SERNO']
#      del tmp_hdr['COMMENT']
#      del tmp_hdr['EXPOSURE'] 
#      del tmp_hdr['ACQMODE'] 
#      del tmp_hdr['READMODE']
#      del tmp_hdr['IMGRECT']
#      del tmp_hdr['HBIN']
#      del tmp_hdr['VBIN']
#      del tmp_hdr['SUBRECT']
#      del tmp_hdr['TRIGGER']
#      del tmp_hdr['READTIME']
#      del tmp_hdr['VSHIFT']
#      del tmp_hdr['DATE']     # This is a time stamp the camera makes itself and is not accurate. 
#      del tmp_hdr['FRAME']    # This is a time stamp the camera makes itself and is not accurate.

######################Here the info are written to the fits header#######################################################
# Camera information --------------------------------------------------------------------------------------

      tmp_hdr.update('IMFORM','FITS', comment='Image format (Flexible Image Transport System)')
      tmp_hdr.update('DATATYPE',datatype, comment='Type of data')
      tmp_hdr.update('IMAGETYP',imagetyp, comment='Image type: flat, bias, star, etc.')
      tmp_hdr.update('COMMENT',remark, comment='Observers comment')
      tmp_hdr.update('FILE',file_name, comment='Path/filename')
      tmp_hdr.update('---C----', '-------CCD--------', comment='Detector parameters for specific exposure')
      tmp_hdr.update('HEAD',model, comment='CCD camera model name')
      tmp_hdr.update('SERNO',serno, comment='System serial number')
      tmp_hdr.update('CCD',camera, comment='VIS or RED camera')
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
      tmp_hdr.update('DETECTOR', 'iXon EMCCD', comment='The CCD detector used for the observations')
      tmp_hdr.update('INSTRUM', 'Photometer', comment='The used instrument for the observations')
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
#      tmp_hdr.update('BJD-MID', float("%.7f" % float(BJD)), comment='UT Barycentric midtime of exp. BJD-2400000')
#      tmp_hdr.update('BVC', float("%.7f" % float(BVC)), comment='Barycentric velocity correction in Km/s')
      # ----------------------------------------------------------------------------------------------------------
      tmp_hdr.update('---DB---', '------DEBUG-----', comment='-------------------------------------')
      tmp_hdr.update('UP-TIME', c_time, comment='Used seconds to update the header')
      tmp_hdr.update('EXP-READ', used_exp_time, comment='Exposure + readout time in seconds from imclass')     


      ########################## Here the modified FITS header is updated and saved ######################################
      pyfits.update(fits_file, tmp_im, tmp_hdr)

      return 1





