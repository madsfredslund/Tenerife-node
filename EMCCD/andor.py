#   pyAndor - A Python wrapper for Andor's scientific cameras
#   Copyright (C) 2009  Hamid Ohadi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

#####   Changes from original version has been made by Mads Fredslund Andersen #####

from ctypes import *
import time
from PIL import Image
import sys
import andorsetup
import datetime
import Queue
import numpy

"""Andor class which is meant to provide the Python version of the same
   functions that are defined in the Andor's SDK. Since Python does not
   have pass by reference for immutable variables, some of these variables
   are actually stored in the class instance. For example the temperature,
   gain, gainRange, status etc. are stored in the class. """

class CameraError(Exception): 
    '''Exception raised when something exceptional happended related to the camera'''
    pass

class SaturationError(CameraError):
    '''Exception raised when saturation has been detected'''
    pass

class InitError(CameraError):
    '''Exception raised when init failed'''
    pass

class AbortError(CameraError):
    '''Exception raised when abort or timeout occured'''
    pass

class CoolingError(CameraError):
    '''Exception raised when cooling could not be enabled'''
    pass

class GainError(CameraError):
    '''Exception raised when gain could not be set'''
    pass

class RPCError(CameraError):
    '''Exception raised when there is problems with the xmlrpc server'''
    pass

class Andor:
    def __init__(self):
        #cdll.LoadLibrary("/usr/local/lib/libandor.so")
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
	
	print self.width, self.height

	self.dim = self.width * self.height

	self.GetNumberADChannels()
	self.GetBitDepth()

	self.SetADChannel(0)
	self.SetOutputAmplifier(0)

	self.GetNumberPreAmpGains()
	self.GetNumberHSSpeeds()
	self.GetHSSpeeds()
	self.GetNumberVSSpeeds()
	self.GetVSSpeed()
	self.GetPreAmpGain()
	self.GetCameraSerialNumber()

	#Setup camera
	self.SetImage(1,1,1,self.width,1,self.height)
	self.SetFrameTransferMode(1)
	self.SetHSSpeed(0)
	self.SetPreAmpGain(0)
	self.SetEMGainMode(3)	# Real EM gain
	self.SetVSSpeed(3)
	self.SetEMCCDGain(0)
	self.SetReadMode(4)
	self.SetHighCapacity(0)
	self.SetExposureTime(1.0)
	self.SetAcquisitionMode(1)
	#self.SetTemperature(0)
	#self.SetFanMode(0)

	self.oldestImage = numpy.zeros(self.dim,dtype='<u2')
	self.imageArray  = numpy.zeros(self.dim,dtype='<u2')

	self.GetDataFun = self.dll.GetAcquiredData16
	self.GetDataFun.argtypes = [numpy.ctypeslib.ndpointer(dtype='<u2',ndim=1, shape=(self.dim),flags='CONTIGUOUS,C'),c_ulong]

	self.GetOldestFun = self.dll.GetOldestImage16
	self.GetOldestFun.argtypes = [numpy.ctypeslib.ndpointer(dtype='<u2',ndim=1, shape=(self.dim),flags='CONTIGUOUS,C'),c_ulong]

	self.GetMostRecentFun = self.dll.GetMostRecentImage16
	self.GetMostRecentFun.argtypes = [numpy.ctypeslib.ndpointer(dtype='<u2',ndim=1,	shape=(self.dim),flags='CONTIGUOUS,C'),c_ulong]

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
            error = self.dll.GetVSSpeed(i,byref(VSSpeed))
            self.VSSpeeds.append(VSSpeed.value)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
    
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
        
    def SaveAsFITS(self, filename, type):
        error = self.dll.SaveAsFITS(filename, type)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
    
    def SaveAsFITSdummy(self,file,type):
        error = self.dll.SaveAsFITS(file,type)
        #self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]  
        
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
    
    def SetHSSpeed(self, index):
        error = self.dll.SetHSSpeed(self.outamp, index)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        if ERROR_CODE[error] == "DRV_SUCCESS":
            self.hsspeed = index
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

############################################ NOT USED FOR SONG iKON CCD CAMERA ########################################
        
    def SetNumberKinetics(self,numKin):
		error = self.dll.SetNumberKinetics(numKin)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
        
    def SetNumberAccumulations(self,number):
		error = self.dll.SetNumberAccumulations(number)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
        
    def SetAccumulationCycleTime(self,time):
		error = self.dll.SetAccumulationCycleTime(c_float(time))
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]
        
    def SetKineticCycleTime(self,time):
		error = self.dll.SetKineticCycleTime(c_float(time))
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

    def GetEMCCDGain(self):
        gain = c_int()
        error = self.dll.GetEMCCDGain(byref(gain))
        self.gain = gain.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
     
    def SetEMGainMode(self, gainMode):
        error = self.dll.SetEMGainMode(gainMode)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]   
        
    def SetEMCCDGain(self, gain):
        error = self.dll.SetEMCCDGain(gain)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
        
    def SetEMAdvanced(self, gainAdvanced):
		error = self.dll.SetEMAdvanced(gainAdvanced)
		self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
		return ERROR_CODE[error]

    def GetEMGainRange(self):
        low = c_int()
        high = c_int()
        error = self.dll.GetEMGainRange(byref(low),byref(high))
        self.gainRange = (low.value, high.value)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
  
    def GetBitDepth(self):
        bitDepth = c_int()

        self.bitDepths = []

        for i in range(self.noADChannels):
            self.dll.GetBitDepth(i,byref(bitDepth))
            self.bitDepths.append(bitDepth.value)
        
    def SetOutputAmplifier(self, index):
        error = self.dll.SetOutputAmplifier(index)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        self.outamp = index
        return ERROR_CODE[error]
 
    def GetAccumulationProgress(self):
		 acc = c_long()
		 series = c_long()
		 error = self.dll.GetAcquisitionProgress(byref(acc),byref(series))
		 if ERROR_CODE[error] == "DRV_SUCCESS":
			return acc.value
		 else:
			return None
        
    def SetFrameTransferMode(self, frameTransfer):
        error = self.dll.SetFrameTransferMode(frameTransfer)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def SetBaselineOffset(self, baseline_level):
        error = self.dll.SetBaselineOffset(c_int(baseline_level))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def GetNumberNewImages(self):
        first = c_long()
        last  = c_long()
        error = self.dll.GetNumberNewImages(byref(first),byref(last))
        first = first.value
        last  = last.value
      #  self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error], first, last

    def GetOldestImage(self):
        error = self.GetOldestFun(self.oldestImage,self.dim,self.dim)
    #    self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def GetOldestImage16(self,pixel_size):
#        dim = self.width * self.height
#	print self.width, self.height
#	print pixel_size, dim
#        cimageArray = c_int * dim
#        cimage = cimageArray()
	cimage = numpy.ctypeslib.ndpointer(dtype='<u2',ndim=1, shape=(self.dim),flags='CONTIGUOUS,C')
        error = self.dll.GetOldestImage16(cimage, c_ulong(pixel_size))
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        for i in range(len(cimage)):
#            imageArray.append(cimage[i])
#        self.imageArray = imageArray[:]
        return ERROR_CODE[error], cimage

    def GetImages16(self):
        error, first, last = self.GetNumberNewImages()
        if error == "DRV_SUCCESS":
            nImages = (last-first + 1)
            image = numpy.zeros(self.dim*nImages,dtype='<i2')
            validfirst = c_long()
            validlast  = c_long()
            error = self.dll.GetImages16(first, last, image,c_ulong(self.dim*nImages), byref(validfirst),byref(validlast))
            self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
            return ERROR_CODE[error], numpy.reshape(image, (self.height, self.width,nImages)),validfirst.value, validlast.value
        else:
            return ERROR_CODE[error], None, None, None	

    def SpoolToArray(self, exposureNumber, exposureTime):
	    '''Spools a small array from the camera. Syntax: 
	    SpoolToArray('number of exposures','exposure time'). Returns
	    completion state, 3D array, time of first frame, seconds since Unix
	    epoch UTC.'''
	
	    spool_time_start = time.time()	
            data = numpy.empty((exposureNumber,self.height,self.width),dtype='<i2')
            # Skip the first image due to bug (check if this is still true)
            index = 0 #-1     
	    tstart = time.time()       
 #           tempArr = numpy.empty(self.height*self.width,dtype='<u2')
 
            error = self.StartAcquisition()

            if error != "DRV_SUCCESS":
                raise CameraError('CamError:'+str(error))  

	    loopstart = time.time() 
            while (True):
                while True:
                    res,availimage,imageidx= self.GetNumberNewImages()
                    if res == "DRV_SUCCESS":
                        if ((imageidx-availimage) >= 0 ) and (imageidx != 0):
			    break
		    time.sleep(0.001)

                error = self.GetOldestImage()
#                error, tempArr = self.GetOldestImage16(self.width * self.height)
#                error, tempArr = self.GetOldestFun(tempArr,self.dim,self.dim)

#		print "Lenght of arry: ", len(self.oldestImage)
#		tempArr = numpy.array(tempArr)

		
		
                if error == "DRV_SUCCESS":

                 #   e=numpy.copy(tempArr)

                    data[index,:,:] = numpy.reshape(self.oldestImage,(self.height,self.width))
		    
	#	    print "Shape of data array: ", data[index,:,:].shape

                    if index == 0:
                        if numpy.mean(data[0,...]) > 50000:
                            self.AbortAcquisition()
                            print('CamError:Saturation')  
			    break 
			elif numpy.mean(data[0,...]) == 0: 
                            self.AbortAcquisition()
                            print('DataError; No data stored')  
			    break 
                    index += 1
                    if index == exposureNumber:
                        self.AbortAcquisition()	
			print('SpoolToArrayEnd')		
			loopstop = time.time()		
			return data, tstart
                else:
                    print error
                    self.AbortAcquisition()
                    print('SpoolToArrayAborted')
		    loopstop = time.time()
                    raise AbortError('CamError:Abort') 
		    break
	
 	    spool_time_stop = time.time()

	    print "Overhead time in this call: ", (spool_time_stop - spool_time_start) - (loopstop - loopstart)
            print "Frame time in loop: ", (loopstop - loopstart) / float(exposureNumber)

	    return data, tstart
 
    def GatherHeaderData(self):
        setupDict = {}
        self.GetTemperature()
        self.GetAcquisitionTimings()
        setupDict["TEMP"]      =  self.temp_float
        setupDict["SETTEMP"]   =  self.set_T
        setupDict["EM_GAIN"]   =  self.gain
        setupDict["PRE_AMP"]   =  self.preampgain
        #setupDict["BITDEPTH"]  =  self.channel
        setupDict["OUT_AMP"]   =  self.outamp
        #setupDict["HS_SPEED"]  =  self.hsspeed
        setupDict["VS_SPEED"]  =  self.vsspeed
        setupDict["SERIAL"]    =  self.serial
        setupDict["EXP_TIME"]  =  self.exposure
        setupDict["ACC_TIME"]  =  self.accumulate
        setupDict["KIN_CY"]    =  self.kinetic
        return setupDict

    def GetMJDUTC(self):
        '''Calculats modified julian days  with respect to UTC'''
        return (time.time())/86400+2440587.5 - 2400000.5

    def SetupSpool(self, exposureTime):
	print "Setup tool called"
	self.SetFrameTransferMode(1)		# FrameTransfer On
        self.SetAcquisitionMode(5)		# Run till abort
        self.SetExposureTime(float(exposureTime))
	self.SetKineticCycleTime(0.0)
	print "Acq Timing: ", self.GetAcquisitionTimings()
	return 1

    def SetGainValue(self,gain):
        '''Does not directly set the gain of the camera, 
        set an internal variable,
        which is activated with the UseGain method'''
        #with self.internallock:
        self.gainValue = int(gain)
        print('gainValue:'+str(self.gainValue))
        print ">>>>>>>>>>>>>>>SetGainValue:", self.gainValue

    def SetGain(self,number):
        print "SetGain / RPCSetEMCCDGain:", number
        '''Sets the EM gain directly, will set EMAdvanced 
        if required. 
        Be ware to to set the EM gain to high'''
        if number > 300:
            self.SetEMAdvanced(1)
            self.SetEMCCDGain(number)
        else:
            self.SetEMAdvanced(0)
            self.SetEMCCDGain(number)

	return 1

    def UseGain(self,value):
        print "UseGain: %i / SetEMCCDGain: %i" % (value, self.gainValue)
        '''Convenience function for enabling 
        and disabling the EM gain'''
        #with self.internallock:
        if value:
            error = self.SetEMCCDGain(self.gainValue)
            if error != "DRV_SUCCESS":
                pass
                #raise GainError('CamError:'+str(error))
        else:
            error = self.SetEMCCDGain(0) 
            if error != "DRV_SUCCESS":
                #pass
                raise GainError('CamError:'+str(error))

	return 1

    def Acquire(self, outputQue, target, exposureNumber, exposureTime):
        '''Spools a series of images to the multiprocessing que outPutQue,
        call signature: Acquire(self,outputQue,target,exposureNumber,exposureTime)
        The exposures are made 100 at a time (defined by andorsetup.subExposure) 
        using the SpoolToArray method. When a block of 100 images has been acquired, 
        it is put into the outputQue and then 100 more is acquired and so on. 
        Information on the camera setup to the fits header is also put into 
        the outputQue. When the acquisition is done, outputQue is closed.'''
        returnVal = 0
	subExposure = andorsetup.subExposure
	numberFullExpo = exposureNumber / subExposure
	if numberFullExpo == 0:
		numberFullExpo = 1            

	self.SetupSpool(exposureTime)
	self.UseGain(1)

	firstRun = True
	spool_time_start = 0 
	spool_time_stop = 0 
	tstart = time.time()

#	print "Number ", numberFullExpo
	for i in range(numberFullExpo):
		if firstRun:
		    configuration = self.GatherHeaderData()
		    configuration['TYPE'] = 'Science'
		    configuration['UTSTART'] =  datetime.datetime.utcnow().isoformat()[:-3]
		    configuration['BLK_SIZE'] = subExposure
		    configuration['OBJECT'] = target
		    outputQue.put(configuration)
		    firstRun = False
		try:
		    data, timestart = self.SpoolToArray(subExposure,exposureTime)
		    outputQue.put((data, timestart),10)
		except SaturationError:
		    print('Camera saturated')
		    returnVal = -1
		    break
		except AbortError:
		    print('Acqucition was aborted')
		    returnVal = -2
		    break
		except Queue.Full:
		    print('Output Queue Full, Timeout')
		    returnVal = -3
		    break
		except CameraError:
		    print('Unspecified camera error')
		    returnVal = -4
		    break
#		if self.abortEvent.is_set():
#		    print('Abort event was set')
#		    returnVal = -2
#		    break
	tstop = time.time()

	#self.SetShutter(0,2,0,0)
	outputQue.put(('Done',self.GetMJDUTC()))
	print('OK to move telescope!!!')
	outputQue.close()


	print "Acquisition time in total: ", tstop - tstart
	print "Time per frame: ", (tstop - tstart) / (float(exposureNumber))
	print "Overhead time in seconds per frame: ", (tstop - tstart) / (float(exposureNumber)) - float(self.exposure)
	print "Overhead time in seconds in total: ", ((tstop - tstart) / (float(exposureNumber)) - float(self.exposure)) * float(exposureNumber)
	print 'Number of images:', exposureNumber
	print "Cube is done at: ", time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime())

	self.UseGain(0)

        return returnVal

    
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
