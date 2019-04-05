"""
	Created on Oct 6, 2011

	@author: Mads Fredslund Andersen
"""
import time
import song_timeclass
import os
import sys

clock = song_timeclass.TimeClass()

class CamFunctions(object):
	"""
	@brief: This class initializes the cooler and the CCD camera and sets some standard parameters to there default values.
	"""  
	def ini_temp(self,cam,cam_temp):
		"""
		 @brief: This will set the temperature of the internal cooler in the CCD camera from Andor.

		 @param cam: The camera handle from the Andor.py wrapper.
		 @param cam_temp: The specified temperature to which the cooler will cool the CCD.
		"""

		print '\n'        
		print 'Setting the temperature...'
		print clock.whattime()

		# Switch on the cooler
		if cam.GetStatus() == 'DRV_NOT_INITIALIZED':
			print 'The camera was not initialized!'
			sys.exit("Camera not initialized or shut down!")

		tmpTIME = clock.whattime()

		################## Turns the cameras internal cooler on ############################
		cam.CoolerON()


		cam.SetTemperature(int(cam_temp))
		tempstatus = cam.GetTemperature()
		cam.GetTemperatureF()
		tmpTEMP = cam.temp_float  
		print 'The temperature of the CCD is now: '+str(tmpTEMP)+ unichr(176).encode("UTF-8") + 'C and set to '+str(cam_temp)+ unichr(176).encode("UTF-8") + 'C'      

		############# This makes sure that the temperature is stabilized before continuing ########################################
		while tempstatus != 'DRV_TEMP_STABILIZED':
			time.sleep(10)
			tempstatus = cam.GetTemperatureF()
			tmpTEMP = cam.temp_float
			print 'The temperature of the CCD is now: '+str(tmpTEMP)+ unichr(176).encode("UTF-8") + 'C'
		time.sleep(10) # wait for stabilized temperature to be reached
		#------------------------------------------------------------------------------
		print 'The temperature is stabilized!'
		print clock.whattime()
        
	def cooler(self,cam,state):
		"""
			@brief: This will turn the internal cooler on or off.

			@param cam: The camera handle from the Andor.py wrapper.
			@param state: The specified state to which the cooler should be switched.
		"""
		if state == 'on':
			print '\n'        
			print 'Switching on the cooler...'
			print clock.whattime()
			cam.CoolerON()
			print 'The cooler has been turned on'
		elif state == 'off':
			print '\n'        
			print 'Switching off the cooler...'
			print clock.whattime()
            
			cam.GetTemperature()
			temp = cam.temp_int
			if temp < -20 and temp > -250:
				cam.SetTemperature(-15)
				while temp < -20:
					time.sleep(5)
					cam.GetTemperature()
					temp = cam.temp_int
					print 'The temperature is '+str(temp)+ unichr(176).encode("UTF-8") + 'C'
				cam.CoolerOFF()
			else:
				cam.CoolerOFF()
				print 'The cooler has been turned off'
		else:
			print 'Nothing was done to the cooler!!!'

	def fan(self, cam, mode):
		if mode == 0:
			print '\n'        
			print 'Switching the fan to high mode...'
			print clock.whattime()
			ret_val = cam.SetFanMode(0)
			print 'The fan was set in high mode'
		elif mode == 1:
			print '\n'        
			print 'Switching the fan to low mode...'
			print clock.whattime()
			ret_val = cam.SetFanMode(1)
			print 'The fan was set in low mode'
		elif mode == 2:
			print '\n'        
			print 'Switching off the fan...'
			print clock.whattime()            
			ret_val = cam.SetFanMode(2)
		else:
			print '\n'        
			print 'Something was not right'
			print clock.whattime()    
			print "The fan mode specified was not set"	
			ret_val = "Error"
		return ret_val
        
	def ini_cam(self,cam):
		"""
			@brief: This will initialize the camera to default values.

			@param cam: The camera handle from the Andor.py wrapper.
		"""
		print '\n'        
		print 'Starting to initialize the camera...'
		print clock.whattime()

		if cam.GetStatus() == 'DRV_NOT_INITIALIZED':
			print 'The camera was not initialized!'
			sys.exit("Camera not initialized or shutdown!")

		tmpTIME = clock.whattime()
        
		# Set Acquisition mode (default is "single scan")
		cam.SetAcquisitionMode(1)
        
		# Set exposure time to 1.0 seconds as default.
		cam.SetExposureTime(1.0)

		# Set the High Capacity mode to Off as default:
		cam.SetHighCapacity(0)

		# Set the trigger mode to internal triggering
		cam.SetTriggerMode(0)

		# Set the shutter mode to be automatic
		# (type, mode, closingtime, openingtime) 
		# type: 0 = Low signal to open shutter, 1 = high signal to open shutter
		# mode: 0 = Auto, 1 = open, 2 = close
		cam.SetShutter(1,0,50,50) 

		# Set read out speed to 3 MHz
		cam.SetHSSpeed(0,1)

		# Set pre amplifier gain to 1  
		cam.SetPreAmpGain(0)

		# Set binning (default is no binning) and image to full frame.
		h_bin = 1
		v_bin = 1
		h_start = 1
		h_end = cam.width
		v_start = 1
		v_end = cam.height
		cam.SetImage(h_bin,v_bin,h_start,h_end,v_start,v_end)
        
		# Set the read out mode (default is Image)
		cam.SetReadMode(4)

		#---------------------------------------------------------------------------
		print 'Finnished initializing cam settings at:'
		print clock.whattime()

	def turn_of_cam(self,cam):
		"""
			@brief: This function will shut down the camera.
		"""

		print 'Shutting down the camera...'
		print clock.whattime()

		cam.GetTemperature()
		temp = cam.temp_int
		if temp < -20 and temp > -250:
			cam.SetTemperature(-15)
			while temp < -20:
				time.sleep(5)
				cam.GetTemperature()
				temp = cam.temp_int
				print 'The temperature is '+str(temp)+ unichr(176).encode("UTF-8") + 'C'
			cam.CoolerOFF()
			cam.ShutDown()
		else:
			cam.CoolerOFF()
			cam.ShutDown()
            
		print 'Shutdown at: ', clock.whattime()
		print 'The camera has been shut down\n'

	def GetValues(self,cam,option):
		"""
			@brief: This function handles request for specific values set in the camera.

			@param cam: This is the camera handle from the Andor.py wrapper.
			@param option: This is the parameter for which the value of it is returned.
		"""
		if option == 'temp':   
			def GetTemperature(self,cam):
            			"""This function returns the current temperature of the CCD"""
         
				tempstatus = cam.GetTemperatureF()
				ccdtemp = cam.temp_float
				return float("%.2f" % ccdtemp)
			value1 = GetTemperature(self,cam)
			return value1
		if option == 'preamp':
			def GetPreAmpGain(self,cam):
				"""This function returns the current PreAmpGain value of the camera"""
				cam.GetNumberPreAmpGains()
				cam.GetPreAmpGain()
				pregains = cam.preAmpGain
				if cam.preampgain == None:
					return 999
				else:
					preampgain = pregains[cam.preampgain]
					return preampgain
         		value = GetPreAmpGain(self,cam)
         		return value
		if option == 'exptime':
			def GetExpTime(self,cam):
				"""This function returns the current exposure time for the camera"""

				exptime = cam.exptime
				return exptime
			value = GetExpTime(self,cam)
			return value
		if option == 'ac_mode':
			def GetAcquisitionMode(self,cam):
				"""This function returns the current Acquisition mode for the camera"""
				ac_mode = cam.ac_mode
				return ac_mode
			value = GetAcquisitionMode(self,cam)
			return value
		if option == 'status':    
			def GetStatus(self,cam):
				"""This function returns the status for the camera"""
				cam.GetStatus()
				status = cam.status
				if status == 'DRV_IDLE':
					return 'IDLE waiting on instructions'
				if status == 'DRV_TEMPCYCLE':
					return 'Executing temerature cycle'
				if status == 'DRV_ACQUIRING':
					return 'Acquisition in progress'
				if status == 'DRV_ACCUM_TIME_NOT_MET':
					return 'Unable to meet Accumulate cycle time'
				if status == 'DRV_KINETIC_TIME_NOT_MET':
					return 'Unable to meet Kinetic cycle time'
				if status == 'DRV_ERROR_ACK':
					return 'Unable to communicate with card'
				if status == 'DRV_ACQ_BUFFER':
					return 'Computer unable to read the data via the ISA slot at required rate'
				if status == 'DRV_SPOOLERROR':
					return 'Overflow of the spool buffer'
			value = GetStatus(self,cam)
			return value
		if option == 'binning':
			def GetBinning(self,cam):
				"""This function returns the current binning settings for the camera"""

				hbin = cam.hbin
				vbin = cam.vbin
				return hbin,vbin
			value = GetBinning(self,cam)
			return value[0],value[1]
		if option == 'readmode':
			def GetReadMode(self,cam):
				"""This function returns the Read Mode for the camera"""

				readmode = cam.readmode
				return readmode
			value = GetReadMode(self,cam)
			return value
		if option == 'hsspeed':
			def GetHSSpeed(self,cam):
				"""This function returns the Horizontal Shift Speed (readouttime) for the camera"""

				hsspeed = cam.hsspeed
				return hsspeed
			value = GetHSSpeed(self,cam)
			return value
		if option == 'highcap':
			def GetHighCapacity(self,cam):
				"""This function returns the mode for High Capacity for the camera"""

				highcap = cam.highcap
				return highcap
			value = GetHighCapacity(self,cam)
			return value
		if option == 'imsize':
			def GetImageSize(self,cam):
				"""This function returns the Image Size for the current settings"""

				hstart = cam.hstart
				hend = cam.hend
				vstart = cam.vstart
				vend = cam.vend
				return hstart,hend,vstart,vend
			value = GetImageSize(self,cam)
			return value[0],value[1],value[2],value[3]

	def GetSetting(self,cam,option): 
		"""
			@brief: This function handles request for specific settings in the camera.

			@param cam: This is the camera handle from the Andor.py wrapper.
			@param option: This is the parameter for which the settings of it is returned.
		"""
		if option == 'temp':   
			def GetTemperature(self,cam):
				"""This function returns the current temperature of the CCD"""

				tempstatus = cam.GetTemperatureF()
				ccdtemp = cam.temp_float
				return float("%.2f" % ccdtemp), tempstatus
			value1, value2 = GetTemperature(self,cam)
			return ('The temperature is: '+str(value1)+ unichr(176).encode("UTF-8") + 'C\n' + 'Cooling status = '+str(value2))

		if option == 'preamp':
			def GetPreAmpGain(self,cam):
				"""This function returns the current PreAmpGain value of the camera"""
				cam.GetNumberPreAmpGains()
				cam.GetPreAmpGain()
				pregains = cam.preAmpGain
				if cam.preampgain == None:
					return 'Not set (default is 1.0)'
				else:
					preampgain = pregains[cam.preampgain]
					return preampgain
			value = GetPreAmpGain(self,cam)
			return 'The PreAmpGain setting is: '+str(value)
		if option == 'exptime':
			def GetExpTime(self,cam):
				"""This function returns the current exposure time for the camera"""

				exptime = cam.exptime
				return exptime
			value = GetExpTime(self,cam)
			return 'The Exposure time is set to: '+str(value)+' sec'
		
		if option == 'ac_mode':
			def GetAcquisitionMode(self,cam):
				"""This function returns the current Acquisition mode for the camera"""

				ac_mode = cam.ac_mode
				if ac_mode == 1:
					return 'Single Scan'
				elif ac_mode == 2:
					return 'Accumulate'
				elif ac_mode == 3:
					return 'Kinetic Series'
				elif ac_mode == 4:
					return 'Run Till Abort'
				elif ac_mode == 5:
					return 'Fast Kinetics'
				else:
					return 'Not set'
			value = GetAcquisitionMode(self,cam)
			return 'The Acquisition mode is set to: '+value
		if option == 'status':    
			def GetStatus(self,cam):
				"""This function returns the status for the camera"""
				cam.GetStatus()
				status = cam.status
				if status == 'DRV_IDLE':
					return 'IDLE waiting on instructions'
				if status == 'DRV_TEMPCYCLE':
					return 'Executing temerature cycle'
				if status == 'DRV_ACQUIRING':
					return 'Acquisition in progress'
				if status == 'DRV_ACCUM_TIME_NOT_MET':
					return 'Unable to meet Accumulate cycle time'
				if status == 'DRV_KINETIC_TIME_NOT_MET':
					return 'Unable to meet Kinetic cycle time'
				if status == 'DRV_ERROR_ACK':
					return 'Unable to communicate with card'
				if status == 'DRV_ACQ_BUFFER':
					return 'Computer unable to read the data via the ISA slot at required rate'
				if status == 'DRV_SPOOLERROR':
					return 'Overflow of the spool buffer'
			value = GetStatus(self,cam)
			return 'The status of the camera is: '+value
		if option == 'binning':
			def GetBinning(self,cam):
				"""This function returns the current binning settings for the camera"""

				hbin = cam.hbin
				vbin = cam.vbin
				return hbin,vbin
			value = GetBinning(self,cam)
			return 'The binning is set to: horizontal = '+str(value[0])+' vertical = '+str(value[1])
		if option == 'readmode':
			def GetReadMode(self,cam):
				"""This function returns the Read Mode for the camera"""

				readmode = cam.readmode
				if readmode == 0:
					return 'Full Vertical Binning'
				elif readmode == 1:
					return 'Single-Track'
				elif readmode == 2:
					return 'Multi-Track'
				elif readmode == 3:
					return 'Random-Track'
				elif readmode == 4:
					return 'Image'
				elif readmode == 5:
					return 'Cropped'
				else:
					return 'Not set'
			value = GetReadMode(self,cam)
			return 'The Read Mode is set to: '+value
		if option == 'hsspeed':
			def GetHSSpeed(self,cam):
				"""This function returns the Horizontal Shift Speed (readouttime) for the camera"""

				hsspeed = cam.hsspeed
				if hsspeed == 0:
					return '5.0 MHz'
				elif hsspeed == 1:
					return '3.0 MHz'
				elif hsspeed == 2:
					return '1.0 MHz'
				elif hsspeed == 3:
					return '0.05 MHz'
				else:
					return 'Not set (default is 5.0 MHz)'
			value = GetHSSpeed(self,cam)
			return 'The HSSpeed is set to: '+str(value)
		if option == 'highcap':
			def GetHighCapacity(self,cam):
				"""This function returns the mode for High Capacity for the camera"""

				highcap = cam.highcap
				if highcap == 0:
					return 'Off'
				elif highcap == 1:
					return 'On'
				else:
					return 'Not set (default is Off)'
			value = GetHighCapacity(self,cam)
			return 'The settings for High Capacity is: '+value
		if option == 'imsize':
			def GetImageSize(self,cam):
				"""This function returns the Image Size for the current settings"""

				hstart = cam.hstart
				hend = cam.hend
				vstart = cam.vstart
				vend = cam.vend
				return hstart,hend,vstart,vend
			value = GetImageSize(self,cam)
			return 'The image size is set to: hstart = '+str(value[0])+' hend = '+str(value[1])+' vstart = '+str(value[2])+' vend = '+str(value[3])
		if option == 'all':
			def GetAll(self,cam):
				"""This function returns all the current settings"""

				tempstatus = cam.GetTemperatureF()
				ccdtemp = float("%.2f" % cam.temp_float)

				cam.GetNumberPreAmpGains()
				cam.GetPreAmpGain()
				pregains = cam.preAmpGain
				if cam.preampgain == None:
					preamp = 'Not set (default is 1.0)'
				else:
					preamp = pregains[cam.preampgain]
                
				exptime = cam.exptime
				ac_mode = cam.ac_mode
				if ac_mode == 1:
					acmode = 'Single Scan'
				elif ac_mode == 2:
					acmode = 'Accumulate'
				elif ac_mode == 3:
					acmode = 'Kinetic Series'
				elif ac_mode == 4:
					acmode = 'Run Till Abort'
				elif ac_mode == 5:
					acmode = 'Fast Kinetics'
				else:
					acmode = 'Not set'
                
				cam.GetStatus()
				status = cam.status
				if status == 'DRV_IDLE':
					sta = 'IDLE waiting on instructions'
				if status == 'DRV_TEMPCYCLE':
					sta = 'Executing temerature cycle'
				if status == 'DRV_ACQUIRING':
					sta = 'Acquisition in progress'
				if status == 'DRV_ACCUM_TIME_NOT_MET':
					sta = 'Unable to meet Accumulate cycle time'
				if status == 'DRV_KINETIC_TIME_NOT_MET':
					sta = 'Unable to meet Kinetic cycle time'
				if status == 'DRV_ERROR_ACK':
					sta = 'Unable to communicate with card'
				if status == 'DRV_ACQ_BUFFER':
					sta = 'Computer unable to read the data via the ISA slot at required rate'
				if status == 'DRV_SPOOLERROR':
					sta = 'Overflow of the spool buffer'

				hbin = cam.hbin
				vbin = cam.vbin
					    
				readmode = cam.readmode
				if readmode == 0:
					rmode = 'Full Vertical Binning'
				elif readmode == 1:
					rmode = 'Single-Track'
				elif readmode == 2:
					rmode = 'Multi-Track'
				elif readmode == 3:
					rmode = 'Random-Track'
				elif readmode == 4:
					rmode = 'Image'
				elif readmode == 5:
					rmode = 'Cropped'
				else:
					rmode = 'Not set'

				hsspeed = cam.hsspeed
				if hsspeed == 0:
					hss = '5.0 MHz'
				elif hsspeed == 1:
					hss = '3.0 MHz'
				elif hsspeed == 2:
					hss = '1.0 MHz'
				elif hsspeed == 3:
					hss = '0.05 MHz'
				else:
					hss = 'Not set (default is 5.0 MHz)'

				highcap = cam.highcap
				if highcap == 0:
					hcap = 'Off'
				elif highcap == 1:
					hcap = 'On'
				else:
					hcap = 'Not set (default is Off)'

				hstart = cam.hstart
				hend = cam.hend
				vstart = cam.vstart
				vend = cam.vend
                
				return ccdtemp,tempstatus,preamp,exptime,acmode,sta,hbin,vbin,rmode,hss,hcap,hstart,hend,vstart,vend

			ccdtemp,tempstatus,preamp,exptime,acmode,sta,hbin,vbin,rmode,hss,hcap,hstart,hend,vstart,vend = GetAll(self,cam)
                
			return ('\nTemperature = '+str(ccdtemp)+unichr(176).encode("UTF-8") + 'C'+'\n'
				'Cooling status = '+str(tempstatus)+'\n'
				'PreAmpGain = '+str(preamp)+'\n'
				'Exposure Time = '+str(exptime)+' sec'+'\n'
				'Acquisition mode = '+str(acmode)+'\n'
				'Camera status = '+str(sta)+'\n'
				'Binning (H/V) = '+str(hbin)+'/'+str(vbin)+'\n'
				'Read Mode = '+str(rmode)+'\n'
				'HSSpeed = '+str(hss)+'\n'
				'High Capacity = '+str(hcap)+'\n'
				'Image size (hstart/hend/vstart/vend) = '+str(hstart)+'/'+str(hend)+'/'+str(vstart)+'/'+str(vend)+'\n')
        
