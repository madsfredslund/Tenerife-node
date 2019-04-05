from ctypes import *
import sys

ERROR_CODE = {
    20001: "DRV_ERROR_CODES",
    20002: "DRV_SUCCESS",
    20003: "DRV_VXNOTINSTALLED",
    20006: "DRV_ERROR_FILELOAD",
    20007: "DRV_ERROR_VXD_INIT",
    20010: "DRV_ERROR_PAGELOCK",
    20011: "DRV_ERROR_PAGE_UNLOCK",
    20013: "DRV_ERROR_ACK",
    20024: "DRV_NO_NEW_DATA",
    20026: "DRV_SPOOLERROR",
    20034: "DRV_TEMP_OFF",
    20035: "DRV_TEMP_NOT_STABILIZED",
    20036: "DRV_TEMP_STABILIZED",
    20037: "DRV_TEMP_NOT_REACHED",
    20038: "DRV_TEMP_OUT_RANGE",
    20039: "DRV_TEMP_NOT_SUPPORTED",
    20040: "DRV_TEMP_DRIFT",
    20050: "DRV_COF_NOTLOADED",
    20053: "DRV_FLEXERROR",
    20066: "DRV_P1INVALID",
    20067: "DRV_P2INVALID",
    20068: "DRV_P3INVALID",
    20069: "DRV_P4INVALID",
    20070: "DRV_INIERROR",
    20071: "DRV_COERROR",
    20072: "DRV_ACQUIRING",
    20073: "DRV_IDLE",
    20074: "DRV_TEMPCYCLE",
    20075: "DRV_NOT_INITIALIZED",
    20076: "DRV_P5INVALID",
    20077: "DRV_P6INVALID",
    20083: "P7_INVALID",
    20089: "DRV_USBERROR",
    20091: "DRV_NOT_SUPPORTED",
    20099: "DRV_BINNING_ERROR",
    20990: "DRV_NOCAMERA",
    20991: "DRV_NOT_SUPPORTED",
    20992: "DRV_NOT_AVAILABLE"
}

class Andor:
	def __init__(self):
		self.dll = CDLL("/usr/local/lib/libandor.so")
		error = self.dll.Initialize("/usr/local/etc/andor/")

		cw = c_int()
		ch = c_int()
		self.dll.GetDetector(byref(cw), byref(ch))

		self.width       = cw.value
		self.height      = ch.value
		self.temp_int    = None
		self.temp_float  = None
		self.set_T       = None
		self.gain        = None
		self.gainRange   = None
		self.status      = ERROR_CODE[error]
		self.verbosity   = True
		self.preampgain  = None
		self.channel     = None
		self.outamp      = None
		self.hsspeed     = None
		self.vsspeed     = None
		self.serial      = None
		self.exposure    = None
		self.accumulate  = None
		self.kinetic     = None
		self.highcap     = None
		self.exptime     = None
		self.ac_mode     = None
		self.hbin        = None
		self.vbin        = None
		self.readmode    = None
		self.hstart      = None
		self.hend        = None
		self.vstart      = None
		self.vend        = None
		self.abort       = None
		self.trigger	 = None
		self.head	 = "DZ936_BV"
		self.readtime	 = None

	def __del__(self):
		error = self.dll.ShutDown()

	def AbortAcquisition(self):
		self.abort = 1
		error = self.dll.AbortAcquisition()
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	def CancelWait(self):
		error = self.dll.CancelWait()
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	def CoolerON(self):
		error = self.dll.CoolerON()
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	def CoolerOFF(self):
		error = self.dll.CoolerOFF()
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def GetAcquiredData(self,imageArray):
		self.GetReadOutTime()
		dim = self.width * self.height
		cimageArray = c_int * dim
		cimage = cimageArray()
		error = self.dll.GetAcquiredData(pointer(cimage),dim)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)

		for i in range(len(cimage)):
		    imageArray.append(cimage[i])

		self.imageArray = imageArray[:]
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	def GetAcquisitionTimings(self):
		exposure   = c_float()
		accumulate = c_float()
		kinetic    = c_float()
		error = self.dll.GetAcquisitionTimings(byref(exposure),byref(accumulate),byref(kinetic))
		self.exposure = exposure.value
		self.accumulate = accumulate.value
		self.kinetic = kinetic.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	def GetCameraSerialNumber(self):
		serial = c_int()
		error = self.dll.GetCameraSerialNumber(byref(serial))
		self.serial = serial.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	 #   def GetHeadModel(self):
	 #       head = c_char()
	 #       error = self.dll.GetHeadModel(byref(head))
	 #       self.head = head.value
	 #       self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
	 #       return ERROR_CODE[error]
	    
	def GetHSSpeed(self):
		HSSpeed = c_float()
		error = self.dll.GetHSSpeed(self.channel, self.outamp, self.hsspeed ,byref(HSSpeed))
		self.HSSpeed = HSSpeed.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def GetHSSpeeds(self):
		HSSpeed = c_float()
		self.HSSpeeds = []
		for i in range(self.noHSSpeeds):
		    error = self.dll.GetHSSpeed(byref(HSSpeed))
		    self.dll.GetHSSpeed(self.channel, self.outamp, i, byref(HSSpeed))
		    self.HSSpeeds.append(HSSpeed.value)
		return ERROR_CODE[error]

	def GetNumberADChannels(self):
		noADChannels = c_int()
		error = self.dll.GetNumberADChannels(byref(noADChannels))
		self.noADChannels = noADChannels.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def GetNumberAmp(self):
		numberamp = c_int()
		error = self.dll.GetNumberAmp(byref(numberamp))
		self.numberamp = numberamp.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def GetNumberHSSpeeds(self):
		noHSSpeeds = c_int()
		error = self.dll.GetNumberHSSpeeds(self.channel, self.outamp, byref(noHSSpeeds))
		self.noHSSpeeds = noHSSpeeds.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def GetNumberPreAmpGains(self):
		noGains = c_int()
		error = self.dll.GetNumberPreAmpGains(byref(noGains))
		self.noGains = noGains.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def GetNumberVSSpeeds(self):
		noVSSpeeds = c_int()
		error = self.dll.GetNumberVSSpeeds(byref(noVSSpeeds))
		self.noVSSpeeds = noVSSpeeds.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def GetPreAmpGain(self):
		gain = c_float()
		self.preAmpGain = []
		for i in range(self.noGains):
		    self.dll.GetPreAmpGain(i,byref(gain))
		    self.preAmpGain.append(gain.value)

	def GetReadOutTime(self):
		readtime = c_int()
		error = self.dll.GetReadOutTime(byref(readtime))
		self.readtime = readtime.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
		    
	def GetSeriesProgress(self):
		acc = c_long()
		series = c_long()
		error = self.dll.GetAcquisitionProgress(byref(acc),byref(series))
		if ERROR_CODE[error] == "DRV_SUCCESS":
		    return series.value
		else:
		    return None
		
	def GetSpoolProgress(self):
		progress = c_long()
		error = self.dll.GetAcquisitionProgress(byref(progress))
		if ERROR_CODE[error] == "DRV_SUCCESS":
		   return progress.value
		else:
		   return None
	       
	def GetStatus(self):
		status = c_int()
		error = self.dll.GetStatus(byref(status))
		self.status = ERROR_CODE[status.value]
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	       
	def GetTemperature(self):
		ctemp_int = c_int()
		error = self.dll.GetTemperature(byref(ctemp_int))
		self.temp_int = ctemp_int.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def GetTemperatureF(self):
		ctemp_float = c_float()
		error = self.dll.GetTemperatureF(byref(ctemp_float))
		self.temp_float = ctemp_float.value
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def GetVSSpeed(self):
		VSSpeed = c_float()
		self.VSSpeeds = []
		for i in range(self.noVSSpeeds):
		    self.dll.GetVSSpeed(i,byref(VSSpeed))
		    self.VSSpeeds.append(VSSpeed.value)
	    
	def Initialize(self):
		error = self.dll.Initialize("/usr/local/etc/andor/")
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
		    
	def IsCoolerOn(self):
		iCoolerStatus = c_int()
		error = self.dll.IsCoolerOn(byref(iCoolerStatus))
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return iCoolerStatus.value
	    
	def SaveAsBmp(self, path):
		im=Image.new("RGB",(512,512),"white")
		pix = im.load()

		for i in range(len(self.imageArray)):
		    (row, col) = divmod(i,self.width)
		    picvalue = int(round(self.imageArray[i]*255.0/65535))
		    pix[row,col] = (picvalue,picvalue,picvalue)

		im.save(path,"BMP")
		
	def SaveAsBmpNormalised(self, path):

		im=Image.new("RGB",(512,512),"white")
		pix = im.load()

		maxIntensity = max(self.imageArray)

		for i in range(len(self.imageArray)):
		    (row, col) = divmod(i,self.width)
		    picvalue = int(round(self.imageArray[i]*255.0/maxIntensity))
		    pix[row,col] = (picvalue,picvalue,picvalue)

		im.save(path,"BMP")
		
	def SaveAsFITS(self, filename, data_type):
		error = self.dll.SaveAsFITS(filename, data_type)
	#	error = self.dll.SaveAsFITS(c_char_p(filename), c_int(data_type))
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	#    def SaveAsFITS_TEST(self, filename):
	#	self.GetAcquiredData([])
	#	data = numpy.empty((self.height,self.width),dtype='uint16')
	#	data[:,:] = numpy.reshape(self.imageArray,(self.height,self.width))
	#        hdu = pyfits.PrimaryHDU(data)
	#        hdulist = pyfits.HDUList([hdu])
	#        hdulist.writeto(filename,clobber=True)
	#	return "DRV_SUCCESS"
	    
	#    def SaveAsFITSdummy(self,file,type):
	#        error = self.dll.SaveAsFITS(file,type)
	#        #self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
	#        return ERROR_CODE[error]  
		
	def SaveAsTxt(self, path):
		file = open(path, 'w')

		for line in self.imageArray:
		    file.write("%g\n" % line)

		file.close()

	def SetAcquisitionMode(self, mode):
		ac_mode = c_int()
		error = self.dll.SetAcquisitionMode(mode)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		self.ac_mode = mode
		return ERROR_CODE[error]
	    
	def SetADChannel(self, index):
		error = self.dll.SetADChannel(index)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		self.channel = index
		return ERROR_CODE[error] 
	    
	def SetCoolerMode(self, mode):
		error = self.dll.SetCoolerMode(mode)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def SetExposureTime(self, time):
		exptime = c_float()
		error = self.dll.SetExposureTime(c_float(time))
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		self.exptime = time
		return ERROR_CODE[error]

	def SetFanMode(self, mode):
		error = self.dll.SetFanMode(mode)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def SetHighCapacity(self,state):
		error = self.dll.SetHighCapacity(state)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		self.highcap = state
		return ERROR_CODE[error]
	    
	def SetHSSpeed(self, mode, index):
		error = self.dll.SetHSSpeed(mode,index)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		self.hsspeed = index
		self.mode = mode
		return ERROR_CODE[error]
	    
	def SetImage(self,hbin,vbin,hstart,hend,vstart,vend):
		error = self.dll.SetImage(hbin,vbin,hstart,hend,vstart,vend)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		self.hbin = hbin
		self.vbin = vbin
		self.hstart = hstart
		self.hend = hend
		self.vstart = vstart
		self.vend = vend
		return ERROR_CODE[error]
	    
	def SetImageRotate(self, iRotate):
		error = self.dll.SetImageRotate(iRotate)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		
	def SetImageFlip(self,iHFlip,iVFlip):
		error = self.dll.SetImageFlip(iHFlip,iVFlip)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def SetPreAmpGain(self, index):
		error = self.dll.SetPreAmpGain(index)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		self.preampgain = index
		return ERROR_CODE[error]
	    
	def SetReadMode(self, mode):
		error = self.dll.SetReadMode(mode)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		self.readmode = mode
		return ERROR_CODE[error]

	def SetShutter(self,typ,mode,closingtime,openingtime):
		error = self.dll.SetShutter(typ,mode,closingtime,openingtime)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def SetShutterEx(self, typ, mode, closingtime, openingtime, extmode):
		error = self.dll.SetShutterEx(typ, mode, closingtime, openingtime, extmode)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	def SetSingleScan(self):
		self.SetReadMode(4)
		self.SetAcquisitionMode(1)
		#self.SetImage(1,1,1,self.width,1,self.height)
		
	def SetSingleTrack(self, h_off, track_h): # h_off is offset in hight on CCD in pixels and track_h is the hight of the track
		error = self.dll.SetSingleTrack(h_off, track_h)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	def SetSpool(self, active, method, path, framebuffersize):
		error = self.dll.SetSpool(active, method, c_char_p(path), framebuffersize)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
		 
	def SetTemperature(self,temperature):
		#ctemperature = c_int(temperature)
		#error = self.dll.SetTemperature(byref(ctemperature))
		error = self.dll.SetTemperature(temperature)
		self.set_T = temperature
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
	    
	def SetTriggerMode(self, mode):
		error = self.dll.SetTriggerMode(mode)
		self.trigger = mode
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
		
	def SetVerbose(self, state=True):
		self.verbose = state
		
	def SetVSSpeed(self, index):
		error = self.dll.SetVSSpeed(index)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		self.vsspeed = index
		return ERROR_CODE[error] 

	def ShutDown(self):
		error = self.dll.ShutDown()
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	def StartAcquisition(self):
		self.abort = 0
		error = self.dll.StartAcquisition()
		#self.dll.WaitForAcquisition()
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

	def verbose(self, error, function=''):
		if self.verbosity is True:
		    print "[%s]: %s" %(function, error)

	def WaitForAcquisition(self):
		error = self.dll.WaitForAcquisition()
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

#handle = Andor()
#exptime = 1.0

#handle.SetAcquisitionMode(1)
#handle.SetHighCapacity(0)
#handle.SetTriggerMode(0)
#handle.SetShutter(1,0,50,50)
#handle.SetHSSpeed(0,1)
#handle.SetPreAmpGain(0)
#handle.SetImage(1,1,1,handle.width,1,handle.height)
#handle.SetReadMode(4)
#handle.SetExposureTime(exptime)
#handle.StartAcquisition()
#handle.GetStatus()
#handle.WaitForAcquisition()
#handle.GetStatus()
#handle.SaveAsFITS("/tmp/test_andor_1.fits",0)


