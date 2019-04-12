#!/usr/bin/python
'''
Created on Feb 24, 2010

@author: madsfa
 
'''
import xmlrpclib
import sys
sys.path.append("/home/madsfa/subversion/trunk/common/")
import master_config as m_conf
import red_ccd_config as conf

#attempt connection to server
server = xmlrpclib.ServerProxy('http://%s:%s' % (conf.serverhost, conf.port))

value = ''

if len(sys.argv) > 1:
    id = sys.argv[1]
    if id == 'temp' or id == 'preamp' or id =='exptime' or id =='ac_mode' or id =='status' or id =='binning' or id =='readmode' or id =='hsspeed' or id =='highcap' or id =='imsize' or id == '-h' or id == '--help' or id == 'all' or id=='a' or id=='t':
       if sys.argv[1] == '-h' or sys.argv[1] == '--help':
			print 'This is the help for GetSettings for CCD camera.' 
			print 'Posible parameters is:' 
			print 'temp:        returns the current temperature of the CCD'
			print 'preamp:      returns the current setting for Pre Amplifier Gain'
			print 'exptime:     returns the current setting for the exposure time'
			print 'ac_mode:     returns the current setting for Acquisition Mode'
			print 'status:      returns the current status of the CCD camera'
			print 'binning:     returns the current settings for vertical and horizontal binnning'
			print 'readmode:    returns the current setting for the Cameras read mode'
			print 'hsspeed:     returns the current setting for Horizontal Shift Speed (Readout speed)'
			print 'highcap:     returns the current setting for High Capacity mode'
			print 'imsize:      returns the current settings for image size'
			print 'all:         returns all the current settings for the camera' 
       else:
            try:
                value = server.get_settings(id)
                print value
            except Exception, e:
                print 'Could not connect to the camera.'
                print e	 
    else:		      
    	print 'Wrong parameter. Type -h or --help to see parameters.'

else:
    print 'Please specify a parameter'

