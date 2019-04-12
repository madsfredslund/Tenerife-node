"""
   Created on Aug 21, 2010

   @author: madsfa
"""

import sys
import andor
import song_timeclass
import string

clock = song_timeclass.TimeClass()	

class wrapper(object):
   """
      @brief: This class checks the parameters send to the camera and says OKAY if they are valid
   """
   def value_checker(self,cam,filename,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend):
      """
         @brief: This function checks all the given parameters to see if they fulfill given criterias. 
 
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
      """
        
      error_value = 1
      if cam.width == 0:
         print '\nerror: The camera is not turned on!!!\n'
         error_value += 1
           
      if filename == None or filename == '':
         print '\nerror at: ',clock.whattime()
         print 'error '+str(error_value)+': No filename was given!'
         error_value += 1
        
      if exptime != None and exptime != '':
         if exptime < 0.0 or exptime > 100000.0:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': The exposuretime was not set correct!'
            error_value += 1
      else:
         exptime = ''
            
      if hsspeed != None and hsspeed != '' :
         if hsspeed != 0 and hsspeed != 1 and hsspeed != 2 and hsspeed != 3:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': hsspeed must be one of {0,1,2,3}'
            error_value += 1
      else:
         hsspeed = ''
            
      if pregain != None and pregain != '':
         if pregain != 0 and pregain != 1 and pregain != 2:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': pregain must be one of {0,1,2}'
            error_value += 1
      else:
         pregain = ''
            
      if highcap != None and highcap != '':
         if highcap != 0 and highcap != 1:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': highcap must be one of {0,1}'
            error_value += 1
      else:
         highcap = ''
        
      if hbin != None and hbin != '':
         if hbin < 1 or hbin > 20:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': hbin must be one of {1,2...19,20}'
            error_value += 1
      else:
         hbin = ''
            
      if vbin != None and vbin != '':
         if vbin < 1 or vbin > 20:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': vbin must be one of {1,2...19,20}'
            error_value += 1
      else:
         vbin = ''
        
      if acmode != None and acmode != '':
         if acmode != 1 and acmode != 2 and acmode != 3 and acmode != 4 and acmode != 5:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': acmode must be one of {1,2,3,4,5}'
            error_value += 1
      else:
         acmode = ''
        
      if hstart != None and hstart != '':
         if hstart < 1 or hstart > cam.width:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': hstart must be in the range from 1 to '+str(cam.width)
            error_value += 1
      else:
         hstart = ''
            
      if hend != None and hend != '':
         if hend < 1 or hend > cam.width:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': hend must be in the range from 1 to '+str(cam.width)
            error_value += 1
      else:
         hend = ''
            
      if vstart != None and vstart != '':
         if vstart < 1 or vstart > cam.height:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': vstart must be in the range from 1 to '+str(cam.height)
            error_value += 1
      else:
         vstart = ''
            
      if vend != None and vend != '':
         if vend < 1 or vend > cam.height:
            print '\nerror at: ',clock.whattime()
            print 'error '+str(error_value)+': vend must be in the range from 1 to '+str(cam.height)
            error_value += 1
      else:
         vend = ''
            
      if error_value != 1:
         return -1
      else:
         return 1
