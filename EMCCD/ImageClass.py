"""
   Created on Mar 16, 2010

   @author: madsfa
"""

import andor
import song_timeclass
import time
import os
import song_param_checker
import sys
import makeheader
import update_song_database

clock = song_timeclass.TimeClass()

class imClass(object):
   """
      @brief: This class acquires an image with specified settings.
   """    
   def acquire_one_image(self,cam,filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, comment, camera):
      """
         @brief: This function checks the parameters and parses the request to the performer code.

         @param cam: The camera handle to the Andor.py wrapper.
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

      if obj_ra == '':
         obj_ra = "00:00:00"
      if obj_dec == '':
         obj_dec = "00:00:00"

      ############################## This checks the parameters to see if they are valid #####################################
      Checker = song_param_checker.wrapper()
      value = Checker.value_checker(cam, filename, exptime, hsspeed, pregain, highcap, hbin, vbin, acmode, hstart, hend, vstart, vend)
      if value == -1:
         sys.exit(" wrong parameter(s)! Chek /tmp/song_camera.log for info.")
      elif value == 1:
         print 'Parameters were okay!'

      ########################################################################################################################
            
      if cam.GetTemperature() == 'DRV_NOT_INITIALIZED':
         print 'No power on camera or the camera is not initialized!!!'
         print clock.whattime()
         value = 'No power on camera or the camera is not initialized!!!'
         return value
               
      elif cam.GetTemperature() == 'DRV_TEMP_NOT_REACHED' or cam.GetTemperature() == 'DRV_TEMP_OFF' or cam.GetTemperature() == 'DRV_TEMP_NOT_STABILIZED':
         print 'The temperature was not stabilized!'
         return_value = self.take_sci_im(cam,filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, comment, camera)
         if return_value == 0:
            print 'Finished with acquiring an image!!!\n'
            return 0
         elif return_value == 1:
            print 'Acquisition was aborted!!!\n'
            return 1
         else:
            return return_value

      elif cam.GetTemperature() == 'DRV_TEMP_STABILIZED':
         return_value = self.take_sci_im(cam,filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, comment, camera)
         if return_value == 0:
            print 'Finished with acquiring an image!!!\n'
            return 0
         elif return_value == 1:
            print 'Acquisition was aborted!!!\n'
            return 1 
         else:
            return return_value

      else:
         print 'Something is wrong with the camera settings!'
         print clock.whattime()   
         return value
            

   def take_sci_im(self,cam,filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,object_name, obj_ra, obj_dec, comment, camera):
      """ 
         @brief: This function will take an image with user defined settings.
         
         @param cam: This is the camera handle from the Andor.py wrapper.
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

         @todo: Add the xml-rpc calls to start and stop the exposuremeter.
      """
       
      datapath = os.path.dirname(filename)
      if not os.path.exists(datapath):
         print 'The directory did not exist!'
         sys.exit("Wrong directory!")
        
      mh = makeheader.MakeHeader()
      print 'An acquisition is in progress...'
      print clock.whattime()
    
      ########################## Some camera values are collected ########################################
      cam.GetTemperatureF()
      ccdtemp = cam.temp_float
      cam.GetNumberPreAmpGains()
      cam.GetPreAmpGain()

      cam.SetOutputAmplifier(1)
      cam.SetADChannel(0)
#      cam.SetPreAmpGain(1)
        
      ########################## Some camera values are set ##############################################
      #cam.SetImageFlip(0,0) ##### This flips the the image in the horisontal axis.
      #cam.SetImageRotate(2) ##### This rotates the image 90 degrees clockwise. 
      #cam.SetImageRotate(1)


      if exptime == 0.0:
         # Set the trigger mode to internal triggering
         cam.SetTriggerMode(0)
         # The numbers 0 and 2 is to ensure that the shutter does not open when exptime = 0.0
         cam.SetShutter(0,2,0,0)
      elif imagetyp.lower() == 'dark':
         # Set the trigger mode to external triggering
         cam.SetTriggerMode(0)
         # The numbers 0 and 2 is to ensure that the shutter does not open when a DARK is acquired.
         cam.SetShutter(0,2,0,0)
      else:
         # Set the trigger mode to internal triggering
         cam.SetTriggerMode(0)
         # Set the shutter mode to be automatic. The 1 and 0 makes the shutter open when the trigger signal from the camera is high.
         cam.SetShutter(0,1,0,0)
        
      if highcap != '':
         cam.SetHighCapacity(int(highcap))
        
      if pregain != '':
         cam.SetPreAmpGain(int(pregain))
        
      if hsspeed != '':
         cam.SetHSSpeed(int(hsspeed))
        
      if exptime != '':
         cam.SetExposureTime(float(exptime))

      try:
      		cam.SetFrameTransferMode(0)
     		cam.SetAcquisitionMode(1)
      except Exception,e:
	  print e

        
      ############################## This is to ensure that image size and binning match ######################################  
      def imparam(hstart,hend,vstart,vend,hbin,vbin): 
         resth = (hend-hstart) % hbin
         restv = (vend-vstart) % vbin
            
         if resth % 2 == 0:
            new_hstart = hstart+(resth/2)
            new_hend = hend-(resth/2)
         else:
            new_hstart = hstart+resth
            new_hend = hend
            
         if restv % 2 == 0:
            new_vstart = vstart+(restv/2)
            new_vend = vend-(restv/2)
         else:
            new_vstart = vstart+restv
            new_vend = vend
         return (new_hstart+1),new_hend,(new_vstart+1),new_vend
      #########################################################################################################################
      if hbin == 1 and vbin == 1 and hstart == '' and hend == '' and vstart == '' and vend == '':
         hstart = 1
         hend = cam.width
         vstart = 1
         vend = cam.height

         cam.SetImage(hbin,vbin,hstart,hend,vstart,vend)

      elif hbin != 1 and vbin != 1 and hstart == '' and hend == '' and vstart == '' and vend == '':
         hstart = 1
         hend = cam.width
         vstart = 1
         vend = cam.height
            
         new_hstart,new_hend,new_vstart,new_vend = imparam(hstart,hend,vstart,vend,hbin,vbin)
         cam.SetImage(hbin,vbin,new_hstart,new_hend,new_vstart,new_vend)
            
      elif hstart != '' and hend != '' and vstart != '' and vend != '' and hbin == 1 and vbin == 1:
         cam.SetImage(1,1,hstart,hend,vstart,vend)
        
      elif hstart != '' and hend != '' and vstart != '' and vend != '' and hbin != 1 and vbin != 1:
         new_hstart,new_hend,new_vstart,new_vend = imparam(hstart,hend,vstart,vend,hbin,vbin)
         cam.SetImage(hbin,vbin,new_hstart,new_hend,new_vstart,new_vend)

   
#############################################################################################################################
        
      # Time of start exposure in Universal time
      date_obs = clock.obstimeUTC()
      mjd_obs = clock.obstimeMJD()
      jd_obs = clock.obstimeJD()
      print clock.whattime()

      ###########################################################################################################
      ################# Insert a XMLRPC call to send a signal to the exposuremeter (startsignal) ################
      ###########################################################################################################   

      #import timeoutafunction

      #def wait_for_readout():
      #   value = cam.WaitForAcquisition()
      #   return value	

      #wait_time = [5, 8, 15, 100]

      acq_start_time = time.time()

      cam.StartAcquisition()
      cam.WaitForAcquisition()
      value = 0

      if cam.abort == 0:
         try:
            #value = timeoutafunction.TimeoutFunction(wait_for_readout,timeout=wait_time[int(cam.hsspeed)],time_out_return_value=1)()
            cam.GetStatus()
	    value = cam.status
            print "finished waiting: ",clock.whattime()  
            if value == "DRV_ACQUIRING":
               cam.AbortAcquisition()
               value = 1
               print "Image was skiped!"
            if value != 1 and value != "DRV_ACQUIRING":
               value = cam.SaveAsFITS(filename,0)
            if value == "DRV_ACQUIRING":
               cam.AbortAcquisition()
               print "Image was skiped!"
	
         except Exception, e:
            print "ERROR: Image skipped", e
            value = 1

         acq_stop_time = time.time()

         used_exp_time = acq_stop_time - acq_start_time

      #########################################################################################################
      ################# Insert a XMLRPC call to send a signal to the exposuremeter (endsignal) ################
      #########################################################################################################

         tid = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

         params = "(exp_time, gain, x_begin, y_begin, x_end, y_end, x_bin, y_bin, file_name, photon_mid_time, req_no, param_1, param_2, ins_at)"
    
      #########################################################################################################
	###### WHEN WE START USING req_no the insertion string below should be modified.....##############
      #########################################################################################################
	 if req_no == '':
	    req_no = 0

	 if imagetyp.lower() == 'star':
		imagetype_vaule = 1
	 elif imagetyp.lower() == 'bias':
		imagetype_vaule = 2
	 elif imagetyp.lower() == 'thar':
		imagetype_vaule = 3
	 elif imagetyp.lower() == 'flat' or imagetyp.lower() == 'halo':
		imagetype_vaule = 4
	 elif imagetyp.lower() == 'flati2' or imagetyp.lower() == 'haloi2':
		imagetype_vaule = 5
	 else:
		imagetype_vaule = 0


         values = "(%f, %i, %i, %i, %i, %i, %i, %i, '%s', '%s', %i, %i, %i, '%s')" % (float(exptime), cam.preampgain, cam.hstart, cam.vstart, cam.hend, cam.vend, cam.hbin, cam.vbin, filename, tid, int(req_no), imagetype_vaule, 1, tid)

#         try:
#            update_song_database.insert("spectrograph_cam", params, values)
#         except Exception, e:
#            print "An error occured at insertion of data to database: ", e

      if req_no == 0:
	    req_no = ''

      if value != 1 and value != "DRV_ACQUIRING" and cam.abort == 0 and value != "DRV_P1INVALID":
         print "Image was saved: ",clock.whattime()    
	 try:
         	ret_val = mh.makeheader(cam, ccdtemp, date_obs, jd_obs, mjd_obs, filename, hsspeed, pregain, highcap, imagetyp, object_name, req_no, obj_ra, obj_dec, comment, used_exp_time, camera)
	 except Exception,e:
		print clock.timename(), "Could not update the header..."
		print clock.timename(), e 
		ret_val = 0

         print 'The header is updated'
         print clock.whattime()  
         return 0
      elif cam.abort == 1:
         #print "Acquisition was aborted!"
         return 1
      elif value == "DRV_P1INVALID":
         print "Filename was wrong. Check if permissions are OKAY for directories!"
         return 2

