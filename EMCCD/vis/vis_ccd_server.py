#!/usr/bin/python
"""
   Spectrograph CCD camera handler. This is the daemon.
 
   Created on Jan 04, 2011

   @author: madsfa
"""

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import os
import sys
import syslog
import time
sys.path.append("/home/madsfa/subversion/trunk/phot/")
sys.path.append("/home/madsfa/subversion/trunk/common/") 
import andor
import ccd_functions
import ImageClass
import song_timeclass
import psycopg2
from song_daemonize import Daemon
import getopt
import vis_ccd_config
import thread
import song_star_checker
import daily_logging_handler
import datetime
import master_config as m_conf
import beating_heart
import andorsetup
import numpy
import multiprocessing
import threading
import datasave

global cam
ac_one_im = ImageClass.imClass()
cam_functions = ccd_functions.CamFunctions()
clock = song_timeclass.TimeClass()
sun_handle = song_star_checker.sun_pos(site=m_conf.song_site)

class RequestHandler(SimpleXMLRPCRequestHandler):
   """
      Some XMLPRC-magic here. This is needed, and cannot be left out. Check the documentation?
   """
   rpc_paths = ('/RPC2')

def is_alive():
   """
      The PING function
   """
   return 1

def get_settings(id):
   """
      @brief: This function can be called to get current settings for the camera.

      @param id: Parameter to recieve settings about.
   """
   stamp = 0
   option = id
   try:
      value = cam_functions.GetSetting(cam,option)
   except Exception, e:
      print 'error: ', e
      stamp = 1
   if stamp != 1:
      return value

def get_values(id):
   """
      @brief: This function can be called to get current values for given parameters set in the camera.

      @param id: Parameter to recieve values for.
   """
   stamp = 0
   option = id
   try:
      value = cam_functions.GetValues(cam,option)
   except Exception, e:
      print 'error: ', e
      stamp = 1
   if stamp != 1:
      return value
   else:
      return e

def get_fields(curr, table_name, fields=[]):
      '''Returns specified fields from database table. 
      Arguments: cursor, table name, fields as list, returns dictionary''' 
      field_str = ','.join(fields)
	
      stmt = 'SELECT %s FROM %s WHERE ins_at = (SELECT max(ins_at) FROM %s)' % (field_str, table_name, table_name)
      curr.execute(stmt)
      results = curr.fetchone()
      res_dict = {}
      
      #### HACK!!! Because there are no values in nasmyth db ###
      if results == None:
          results = [30,30,0,30,30,0,2,2,2]
      ### END HACK ###
      
      if results != None:
         for i in range(len(results)):
            res_dict[fields[i]] = results[i]
         return res_dict
      else:
         return None

def stop_server():
   """
      @brief: This function stops the "while loop" and ends the daemon.
   """
   global RUNNING
   RUNNING = False
   print("The Camera Daemon has now been stoped!")
   return 1

def initialize_cam():
   """
      @brief: This will initialize the camera to default settings.
   """
   stamp = 0
   try:
      cam_functions.ini_cam(cam)
   except Exception, e:
      print 'error: ', e
      stamp = 1
   if stamp != 1:
      return 1
   else:
      return e
    
def cooler(state):
   """
      @brief: This handles the cooler internal to the camera. 

      @param state: Turns the cooler on/off.
   """
   stamp = 0
   try:
      cam_functions.cooler(cam,state)
   except Exception, e:
      print 'error: ', e
      stamp = 1
   if stamp != 1:
      return 1
   else:
      return e
    
def set_temp(cam_temp):
   """
      @brief: This function will set the temperature of the CCD cooler.
   
      @param cam_temp: The temperature to which the cooler cools the CCD.
   """
   stamp = 0
   try:
      cam_functions.ini_temp(cam,cam_temp)
   except Exception, e:
      print 'error: ', e
      stamp = 1
   if stamp != 1:
      return 1
   else:
      return e

def set_fan(mode):
	stamp = 0
	try:
		ret_val = cam_functions.fan(cam,mode)
	except Exception,e:
		print e
		stamp = 1

	if stamp != 1:
		return ret_val
	else:
		return e

def GatherConfiguration():
        '''Gathers relevant information form the SONG site database. 
        Argument: None, returns a dictionary'''
        configuration = {}
        configuration['TELESCOP']  = andorsetup.telescope
        configuration['INST']  = andorsetup.inst_name 
        configuration['CHANNEL']  =  "vis"
        configuration['SITE']  = andorsetup.site_name
        configuration['LAT']  = andorsetup.lat_obs
        configuration['LON']  = andorsetup.lon_obs
        configuration['ELEV']  = andorsetup.elev_obs
        try:
            conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" %
                                   (andorsetup.db_host,andorsetup.db_info_header, 
                                    andorsetup.db_user,andorsetup.db_password))
            curr = conn.cursor()
            tel_dome_values = get_fields(curr, andorsetup.db_tel_dome_table,
                                               ["tel_ra","tel_dec","tel_az","tel_alt","tel_zd",
                                                "tel_focus","third_mirror","gps_st"])
            configuration['TEL_RA']  = float(tel_dome_values["tel_ra"])
            configuration['TEL_DEC'] = float(tel_dome_values["tel_dec"])
            configuration['TEL_AZ']  = float(tel_dome_values["tel_az"])
            configuration['TEL_ALT'] = float(tel_dome_values["tel_alt"])
            configuration['TEL_FOC'] = tel_dome_values["tel_focus"]
            configuration['TEL_TM']  = tel_dome_values["third_mirror"]
            configuration['TEL_ST']  = tel_dome_values["gps_st"].isoformat()
            configuration['HA']      = 'calculate'
            configuration['ZDIST']   = 'calculate'
            nasmyth_values = get_fields(curr, andorsetup.db_nasmyth_unit,
                                               ["image_derotator_angle","image_derotator_orientation",
                                                "image_derotator_tracking","adc_angle_1","adc_angle_2",
                                                "adc_tracking","filter_wheel_red_pos",
                                                "filter_wheel_vis_pos","beam_selector"])
            print nasmyth_values
            configuration['IDR_A'] = float(nasmyth_values["image_derotator_angle"])
            configuration['IDR_O'] = float(nasmyth_values["image_derotator_orientation"])
            configuration['IDR_T'] = nasmyth_values["image_derotator_tracking"]
            configuration['ADC_1'] = float(nasmyth_values["adc_angle_1"])
            configuration['ADC_2'] = float(nasmyth_values["adc_angle_2"])
            configuration['ADC_T'] = nasmyth_values["adc_tracking"]
            configuration['FW_RED']  = nasmyth_values["filter_wheel_red_pos"]
            configuration['FW_VIS']  = nasmyth_values["filter_wheel_vis_pos"]
            configuration['BEAM_S']  = nasmyth_values["beam_selector"]
        except psycopg2.Error, e:
            print("Error connecting to database: %s"%e)
        except TypeError, e:
            print("Database Empty: %s"%e)
        return configuration


def Spool(number, target, emgain, exptime):
        '''Main method for acquiring data, gathers data from database and starts a DataSaver
        instance in a separate thread, establishes a Queue object to handle datafransfer 
        form the camera method SpoolToArray which feeds the data to a Queue object. 
        Finally it starts the camera SpoolToArray function in a separate thread.
        Arguments: number of exposures, target, and filter number (subject to change),
        returns None, but will throw exceptions
        *exposureTime* is set to *andorsetup.expTime[0]*'''
        # make a wrapper that sets the filters, make sure to implement transfer of configuration

        flat = [numpy.ones((512,538)),
                     numpy.ones((512,538)),
                     numpy.ones((512,538)),
                     numpy.ones((512,538)),
                     numpy.ones((512,538)),
                     numpy.ones((512,538))]
        flatConfiguration = [{},{},{},{},{},{}]
        for i in range(6):
            try:
                fitsFile = pyfits.open(andorsetup.calibrationDirectory["vis"]+'flat_'+str(i+1)+'.fits')[0]
                flat[i] = fitsFile.data
                flatConfiguration[i] = fitsFile.header
            except:
                print('No flat '+str(i)+' frame found, using default')
        try:
            fitsFile = pyfits.open(andorsetup.calibrationDirectory["vis"]+'bias.fits')[0]
            bias = fitsFile.data
            biasConfiguration = fitsFile.header
        except:
            print('Found no bias frame, using default, that is zero (pure offset)')
            bias = numpy.zeros((512,538))
            biasConfiguration = {}
        try:
            fitsFile = pyfits.open(andorsetup.calibrationDirectory["vis"]+'spurious.fits')[0]
            spurious = fitsFile.data
            spuriousConfiguration = fitsFile.header
        except:
            print('Found no spurious map, using default, that is zero.')
            spurious = numpy.zeros((512,538)) # Replace with real code
            spuriousConfiguration = {}
        try:
            fitsFile = pyfits.open(andorsetup.calibrationDirectory["vis"]+'flatbias.fits')[0]
            flatBias = fitsFile.data
        except:
            print('Found no flatbias map.')
            flatBias = None

	talkbackQue = multiprocessing.Queue()

        config = GatherConfiguration()
	cam.GetStatus()
        if cam.status != 20073:	#IDLE
            	starttime = time.time()
     #       try:
		exposureTime = exptime
		cam.SetGainValue(emgain)
		cam.SetupSpool(exposureTime)
		cam.UseGain(1)
		cam.SetBaselineOffset(1000)	# Setting bias level to plus 500
		imageQue = multiprocessing.Queue()
		nExposure = number
		if nExposure < andorsetup.subExposure:
		    nExposure = andorsetup.subExposure

		flat = numpy.ones((512,538))
		processor = multiprocessing.Process(target=datasave.DataSaver, args=(imageQue, talkbackQue, bias, biasConfiguration, flat, flatConfiguration, spurious, spuriousConfiguration, nExposure, config))
		processor.start()
		t = threading.Thread(target=cam.Acquire, args=(imageQue, target, nExposure, exposureTime))
		t.start()
		t.join()
      #      except Exception, e:
#		print e
 #               print('Spool is not working:'+e.__class__.__name__)
        else:
            print('Camera is acquiring')

	return 1

def acquire_simple_image(filename="/scratch/images/test.fits", req_no="", exptime="1.0", hsspeed="", pregain="", highcap="", hbin="", vbin="", acmode="", hstart="", hend="", vstart="", vend="", imagetyp="", object_name="", comment=""):

   stamp = 0
   try:
      value = ac_one_im.acquire_one_image(cam, filename, req_no, exptime, hsspeed, pregain, highcap, hbin, vbin, acmode, hstart, hend, vstart, vend, imagetyp, object_name, comment)
   except Exception, e:
      print 'error: ', e
      stamp = 1
   if stamp != 1:
      return value # Returns 0 if image was acquired and returns 1 if acquisition was aborted
   else:
      return e

def acquire_an_image(filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, DayNight_flag, comment, camera="vis"):
   """
      @brief: This function will acquire an image and save it as a FITS file. 

      @param filename: The name of the file to be saved.
      @param req_no: Observation request number.
      @param exptime: Exposure time in seconds.
      @param hsspeed: Horisontal Shift Speed.
      @param pregain: Pre Amplifier Gain value.
      @param highcap: High Capability. Can be set to on/off.
      @param hbin: Horisontal binning.
      @param vbin: Vertical binning.
      @param acmode: Acquisition mode, possible to set this with modifications of the code.
      @param hstart: Horisontal starting point of the read out field of the CCD.
      @param hend: Horisontal ending point of the read out field of the CCD.
      @param vstart: Vertical starting point of the read out field of the CCD.
      @param vend: Vertical ending point of the read out field of the CCD.
   """	

   image_dir = check_dir(DayNight_flag)
   filename = check_filename(filename, image_dir)
   stamp = 0
   print '\nConnection is achieved. Request to acquire an image is send to camera'
   value = ""
   try:
      value = ac_one_im.acquire_one_image(cam,filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, comment, camera)
   except Exception, e:
      print 'error: ', e
      stamp = 1

   if stamp != 1 and value == 0:
      return filename # Returns 0 if image was acquired and returns 1 if acquisition was aborted
   elif stamp != 1 and value == 1:  
      return "Acquisition was aborted!"
   else:
      return value

def acquire_an_image_thread(filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, DayNight_flag, comment, camera="vis"):
	"""
		@brief: This function will acquire an image and save it as a FITS file. 

		@param filename: The name of the file to be saved.
		@param req_no: Observation request number.
		@param exptime: Exposure time in seconds.
		@param hsspeed: Horisontal Shift Speed.
		@param pregain: Pre Amplifier Gain value.
		@param highcap: High Capability. Can be set to on/off.
		@param hbin: Horisontal binning.
		@param vbin: Vertical binning.
		@param acmode: Acquisition mode, possible to set this with modifications of the code.
		@param hstart: Horisontal starting point of the read out field of the CCD.
		@param hend: Horisontal ending point of the read out field of the CCD.
		@param vstart: Vertical starting point of the read out field of the CCD.
		@param vend: Vertical ending point of the read out field of the CCD.
	"""	

	if comment != "focus":
		image_dir = check_dir(DayNight_flag)
		filename = check_filename(filename, image_dir)

	stamp = 0
	print '\nConnection is achieved. Request to acquire an image is send to camera'
	value = ""

	def image_func(cam,filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, comment, camera):
		try:
			value = ac_one_im.acquire_one_image(cam,filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, comment, camera)
		except Exception, e:
			print 'error: ', e
			stamp = 1

	try:
		thread_value = thread.start_new_thread(image_func, (cam,filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, comment, camera))
	except Exception,e:
		print clock.whattime(), e

	return filename	

def acquire_an_or_image(filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, DayNight_flag, comment):
   """
      @brief: This function will acquire an image and save it as a FITS file. 

      @param filename: The name of the file to be saved.
      @param req_no: Observation request number.
      @param exptime: Exposure time in seconds.
      @param hsspeed: Horisontal Shift Speed.
      @param pregain: Pre Amplifier Gain value.
      @param highcap: High Capability. Can be set to on/off.
      @param hbin: Horisontal binning.
      @param vbin: Vertical binning.
      @param acmode: Acquisition mode, possible to set this with modifications of the code.
      @param hstart: Horisontal starting point of the read out field of the CCD.
      @param hend: Horisontal ending point of the read out field of the CCD.
      @param vstart: Vertical starting point of the read out field of the CCD.
      @param vend: Vertical ending point of the read out field of the CCD.
   """	
   image_dir = check_dir(DayNight_flag)
   filename = check_filename(filename, image_dir)
   stamp = 0
   print '\nConnection is achieved. Request to acquire an image is send to camera'
   try:
      value = ac_one_im.acquire_one_image(cam,filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, comment)
   except Exception, e:
      print 'error: ', e
      stamp = 1
   if stamp != 1 and value == 0:
      return 0 # Returns 0 if image was acquired and returns 1 if acquisition was aborted
   elif stamp != 1 and value == 1:  
      return 1
   else:
      return e

def shutdown_camera():
   """
      @brief: This function will shut down the camera properly. Not turning power off.
   """
   stamp = 0
   try:
      cam_functions.turn_of_cam(cam)
   except Exception, e:
      print 'error: ', e
      stamp = 1
   if stamp != 1:
      return 1
   else:
      return e
   
def turnon_camera():
   """
      @brief: This function will initialize the camera again after it has been shut down.
   """
   stamp = 0
   try:
      cam.__init__()
      cam_functions.ini_cam(cam)
   except Exception, e:
      print 'error: ', e
      stamp = 1
   if stamp != 1:
      return 1
   else:
      return e

def check_dir(DayNight_flag):
   """
      @brief: This function will check the input path and return a given value if the path is good or bad.
              The date used is local time. Better when combining data from different sites.
   """

   sun_alt = sun_handle.sun_alt()
   sun_alt_d = float(str(sun_alt).split(":")[0]) - float(str(sun_alt).split(":")[1])/60.0 - float(str(sun_alt).split(":")[2])/3600.0

   now_hour = time.strftime("%H", time.localtime())
   now_date = time.strftime("%Y%m%d", time.localtime())

   if DayNight_flag in ["night", "day"]:
	day_night_name = DayNight_flag
   elif float(sun_alt_d) > 0.0 and DayNight_flag != "night":
	day_night_name = "day"
   elif float(sun_alt_d) <= 0.0 and DayNight_flag != "day":
	day_night_name = "night"

   if DayNight_flag.lower() == "sun":
	use_dir = vis_ccd_config.sun_vis_dir
	day_night_name = "day"
   else:
	use_dir = vis_ccd_config.star_vis_dir

   if day_night_name == "night" and float(now_hour) < float(12.0):
      yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
      folder_date = yesterday.strftime('%Y%m%d')
   else:
      folder_date = now_date

   IMAGE_DIR_PATH = use_dir + folder_date + "/" + day_night_name +"/raw"
   IMAGE_DIR_PATH1= use_dir + folder_date + "/" + day_night_name 
   IMAGE_DIR_PATH2= use_dir + folder_date

   if not os.path.exists(IMAGE_DIR_PATH):
      print 'The directory did not exist!'
      if os.path.exists(IMAGE_DIR_PATH2):
         try:	
            os.mkdir(IMAGE_DIR_PATH1)
         except OSError, e:
            print e
	    print "Could not make image path 1"
      else:
         try:	
            os.mkdir(IMAGE_DIR_PATH2)
	    os.mkdir(IMAGE_DIR_PATH1)
         except OSError, e:
            print e
            print "Could not make image path 2"

      try:	
         os.mkdir(IMAGE_DIR_PATH)
      except OSError, e:
         print e
	 print "Could not make full image path"
         sys.exit("Wrong directory path!")

      print "The directory was created!"

   return IMAGE_DIR_PATH

def check_filename(filename, IMAGE_DIR_PATH):
   """
      @brief: This function will check the input path and return a given value if the path is good or bad.
   """

   if filename != "mfa.fits":
   	image_path = "%s/%s" % (IMAGE_DIR_PATH, filename)
   else:
	filename = "v%s_%s.fits" % (vis_ccd_config.site, time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime()))
	image_path = "%s/%s" % (IMAGE_DIR_PATH, filename)

   return image_path

def abort_function():
   cam.AbortAcquisition()
   time.sleep(1)
   cam.GetStatus()
   return_value = cam.status
   return return_value


class cam_server(Daemon):
   """
      @brief: This class deamonizes the process to make it run in the background. It inherits Daemon from song.py.
   """
   def run(self):
      """
         @brief: This function overwrites the Daemon function. While loop and connection end is in this function.
      """
      global RUNNING
      RUNNING = True

 #     val = beating_heart.start_heartbeat(job_id=m_conf.vis_ccd_id)
    
      stamp = 0
      try:
      	server = SimpleXMLRPCServer((vis_ccd_config.serverhost, vis_ccd_config.port), requestHandler=RequestHandler, logRequests=False)
      except Exception, e:
         print 'error: ', e
         stamp = 1
      if stamp != 1:
         pass

      stamp = 0
      try:
         server2 = SimpleXMLRPCServer((vis_ccd_config.serverhost, vis_ccd_config.abort_port), requestHandler=RequestHandler, logRequests=False)
      except Exception, e:
         print 'error: ', e
         stamp = 1
      if stamp != 1:
         pass

      # Makes the CCD camera handle global. This is essential.
      try:
         global cam
         cam = andor.Andor()
      except Exception, e:
	 print e
         sys.exit("Camera handle could not be made!")

      #register functions
      server.register_function(Spool)
      server.register_function(acquire_an_image)
      server.register_function(acquire_an_image_thread)
      server.register_function(acquire_an_or_image)
      server.register_function(shutdown_camera)
      server.register_function(stop_server)
      server.register_function(initialize_cam)
      server.register_function(set_temp)
      server.register_function(get_settings)
      server.register_function(get_values)
      server.register_function(turnon_camera)
      server.register_function(cooler)
      server.register_function(is_alive)
      server.register_function(acquire_simple_image)
      server.register_function(set_fan)



      server2.register_function(abort_function)
    
      value = ''
      try:
         value = get_settings('status')
         print value
      except Exception, e:
         print 'Error: Could not connect to the camera!'
         print 'Check if power is turned on!'
      if value != '' and value != None:
         print 'The camera daemon is ready to use!\n'
      else:
         print 'Error: Could not connect to the camera!'
         print 'Check if power is turned on!'
	 sys.exit()
    
      try:
         initialize_cam()
      except Exception, e:
         print 'Error: Could not run initialize on the Camera!!!'
         print 'Check if there is power on the camera!'


      def clear_log_function():
		done_param = 0
        	while RUNNING:
			### This should copy the content of the log file to old log file and clear it at 12 UTC.
			if int(float(time.strftime("%H", time.gmtime()))) == 12 and done_param == 0:
				daily_logging_handler.handle_log_files(vis_ccd_config.outstream, vis_ccd_config.outstream_old)
				done_param = 1
			if done_param == 1 and int(float(time.strftime("%H", time.gmtime()))) > 12:
				done_param = 0

			time.sleep(600)
      thread_value = thread.start_new_thread(clear_log_function, ())


      def test_function():
         while RUNNING:
	    server2.handle_request()

      thread_value = thread.start_new_thread(test_function, ())

      #start looping
      while RUNNING:
         server.handle_request()
    
def main():
   """
      @brief: This is the main part of the code that starts up everything else. 
   """
   
   daemon = cam_server(vis_ccd_config.pidfile, stdout=vis_ccd_config.outstream, stderr=vis_ccd_config.outstream)
   try:
      opts, list = getopt.getopt(sys.argv[1:], 'sth')
   except getopt.GetoptError, e:
      print("Bad options provided!")
      sys.exit()

   for opt, a in opts:
      if opt == "-s":
         try:
            pid_number = open(vis_ccd_config.pidfile,'r').readline()
            if pid_number:
               sys.exit('Daemon is already running!')
         except Exception, e:
            pass
         print("Starting daemon...\nWait 10 seconds for initialization to complete!")
         daemon.start()
      elif opt == "-t":
         import xmlrpclib
         server = xmlrpclib.ServerProxy('http://'+str(vis_ccd_config.serverhost)+':'+str(vis_ccd_config.port))
	 print("Shutting down the camera...") 
	 server.shutdown_camera()	
	 #now stop the server. Otherwise it might run forever
	 print 'Closing Camera Daemon...'
	 server.stop_server()
      elif opt == "-h":
         print "Options are:"
         print "python camera_server.py -s	# This starts the camera daemon"
         print "python camera_server.py -t	# This stops the camera daemon"
         print "python camera_server.py -h	# This prints this help message"
      else:
         print("Option %s not supported!" % (opt))

if __name__ == "__main__":
   global cam
   main()

