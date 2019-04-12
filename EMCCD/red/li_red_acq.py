#!/usr/bin/python
from multiprocessing import Process
import sys
import time
from optparse import OptionParser
import xmlrpclib
import red_ccd_config

parser = OptionParser()
parser.add_option("-f", "--file", 	dest="filename", default="mfa.fits", help="The name of the file. ex. -ftest.fits", type="string")
parser.add_option("-e", "--exptime", 	type="float", dest="exptime", default=0, help="Set exposure time in seconds: ex. --exptime=2.5 or -e2.5")
parser.add_option("-o", "--object", 	default='', dest="object", help="Set object name")     
parser.add_option("-n", "--nframes", 	default=0, dest="nframes", help="Set number of frames")
parser.add_option("-g", "--emgain", 	default=0, dest="emgain", help="EM gain to use in LI mode")

                                                                                                               
(options, args) = parser.parse_args()

try:
	server = xmlrpclib.ServerProxy('http://%s:%s' % (red_ccd_config.serverhost, red_ccd_config.port))
except Exception, e:
	print e

if float(options.exptime) > 0.3 and int(options.conv) == 0 and int(options.emgain) > 1:
	sys.exit("The EMGain and Exposure time was not in agreement!\nTry shorter exposure time!")	

if int(options.emgain) > 1000:
	sys.exit("The EMGain was too high!")	

if options.object != '':
	print 'Target:           ', options.object
	print 'Number of frames: ', int(options.nframes)
	print 'EM gain: ', options.emgain
	print 'Exposure time: ', options.exptime
	f_name = server.Spool(int(options.nframes), options.object, int(options.emgain), float(options.exptime))

	print "A fits cube was created: ", f_name

elif int(options.conv) == 0 and options.object == '':
	sys.exit("No images were acquired.\nYou MUST specify an object name!!!")


