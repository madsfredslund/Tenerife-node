#!/usr/bin/python
'''
Created on Feb 24, 2010

@author: madsfa
'''
import xmlrpclib
import sys
from optparse import OptionParser
import time
import vis_ccd_config

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename", default="mfa.fits",
                  help="The name of the file. ex. -ftest.fits", type="string")
parser.add_option("-e", "--exptime", type="float", dest="exptime", default=1.0,
                  help="Set exposure time in seconds: ex. --exptime=2.5 or -e2.5")
parser.add_option("-r", "--readout", type="int", dest="readout", default=0,
                  help="Set HSSpeed (readoutspeed) {0,1,2,3} = [5.0,3.0,1.0,0.05]MHz: ex. --readout=1 or -r1")
parser.add_option("-p", "--pregain", type="int", dest="pregain", default=0,
                  help="Set PreAmpGain {0,1,2} = [1.0, 2.0, 4.0]: ex. --pregain=2 or -p2")
parser.add_option("-c", "--highcap", type="int", dest="highcap", default=0,
                  help="Set High Capacity {0,1} = [Off, On]: ex. --highcap=1 or -c1")
parser.add_option("--vb", "--vbinning", type="int", dest="vbin", default=1,
                  help="Set Vertical binning {1,2,4,8,16}: ex. --vbinning=2 or --vb=2")
parser.add_option("--hb", "--hbinning", type="int", dest="hbin", default=1,
                  help="Set Horizontal binning {1,2,4,8,16}: ex. --hbinning=2 or --hb=2")
parser.add_option("-a", "--acmode", type="int", dest="acmode", default=1,
                  help="Set Acquisition mode {1,2,3,4,5} = [Single scan,Accumulate,Kinetic Series,Run Till Abort,Fast Kinetics]: ex. --acmode=2 or -a2")
parser.add_option("--ihs", "--imhstart", type="int", dest="hstart", 
                  help="Set image horizontal start value: ex. --imhstart=250 or --ihs=250")
parser.add_option("--ihe", "--imhend", type="int", dest="hend",
                  help="Set image horizontal end value: ex. --imhend=1250 or --ihs=1250")
parser.add_option("--ivs", "--imvstart", type="int", dest="vstart",
                  help="Set image vertical start value: ex. --imvstart=250 or --ivs=250")
parser.add_option("--ive", "--imvend", type="int", dest="vend",
                  help="Set image vertical end value: ex. --imvend=1250 or --ive=1250")
parser.add_option("--obj_ra", "--object_right_ascension", default='00:00:00', dest="obj_ra",
                  help="Set object right ascension: format: xx:xx:xx, hours, minutes, seconds") 
parser.add_option("--obj_dec", "--object_declination", default='00:00:00', dest="obj_dec",
                  help="Set object declination: format: xx:xx:xx, degrees, arcminutes, arcseconds")   
parser.add_option("-t", "--imagetype", default='STAR', dest="imagetyp",
                  help="Set image type")    
parser.add_option("-o", "--object", default='', dest="object",
                  help="Set object name")     
parser.add_option("--daynight", "--day_or_night_folder", default='', dest="daynight",
                  help="Set day or night data folder: Ex: --daynight='night' or --daynight='day'")     
parser.add_option("--req_no", "--request_number", default='', dest="req_no",
                  help="Set request number")    
parser.add_option("--com", "--comment", default='', dest="comment",
                  help="Set a comment")                                                                                                                          
(options, args) = parser.parse_args()


#attempt connection to server
server = xmlrpclib.ServerProxy('http://%s:%s' % (vis_ccd_config.serverhost, vis_ccd_config.port))

if options.exptime != None:
	exptime = options.exptime
else:
	exptime = ''
	
if options.readout != None:
    hsspeed = options.readout
    if hsspeed != 0 and hsspeed != 1 and hsspeed != 2 and hsspeed != 3:
       print 'hsspeed must be one of {0,1,2,3}'
       sys.exit("Wrong settings for HSSpeed!")
else:
 	hsspeed = ''


if options.pregain != None:
    pregain = options.pregain
    if pregain != 0 and pregain != 1 and pregain != 2:
       print 'pregain must be one of {0,1,2}'
       sys.exit("Wrong settings for PreAmpGain!")
else:
	pregain = ''

if options.highcap != None:
    highcap = options.highcap
    if highcap != 0 and highcap != 1:
       print 'highcap must be one of {0,1}'
       sys.exit("Wrong settings for HighCap!")
else:
	highcap = ''
	
if options.hbin != None:
	hbin = options.hbin
	if hbin != 1 and hbin != 2 and hbin != 4 and hbin != 8 and hbin != 16:
		print 'hbin must be one of {1,2,4,8,16}'
		sys.exit("Wrong settings for Horizontal Binning!")
else:
	hbin = ''
	
if options.vbin != None:
	vbin = options.vbin
	if vbin != 1 and vbin != 2 and vbin != 4 and vbin != 8 and vbin != 16:
		print 'vbin must be one of {1,2,4,8,16}'
		sys.exit("Wrong settings for Vertical Binning!")
else:
	vbin = ''

if options.acmode != None:
	acmode = options.acmode
	if acmode != 1 and acmode != 2 and acmode != 3 and acmode != 4 and acmode != 5:
		print 'acmode must be one of {1,2,3,4,5}'
		sys.exit("Wrong settings for Acquisition mode!")
else:
	acmode = ''

if options.hstart != None and options.hstart not in range(1,2088):
	print 'hstart must be in range {1,2,...,2087,2088}'
	sys.exit("Wrong settings for Image Horizontal Start!")
elif options.hstart != None and options.hstart in range(1,2088):
	hstart = options.hstart
else:
	hstart = ''

if options.hend != None and options.hend not in range(1,2088):
	print 'hend must be in range {1,2,...,2087,2088}'
	sys.exit("Wrong settings for Image Horizontal End!")
elif options.hend != None and options.hend in range(1,2088):
	hend = options.hend
else:
	hend = ''

if options.vstart != None and options.vstart not in range(1,2048):
	print 'vstart must be in range {1,2,...,2047,2048}'
	sys.exit("Wrong settings for Image Vertical Start!")
elif options.vstart != None and options.vstart in range(1,2048):
	vstart = options.vstart
else:
	vstart = ''

if  options.vend != None and options.vend not in range(1,2048):
	print 'vend must be in range {1,2,...,2047,2048}'
	sys.exit("Wrong settings for Image Vertical End!")
elif options.vend != None and options.vend in range(1,2048):
	vend = options.vend
else:
	vend = ''

print 'Acquiring...'
e = None
value = ""
try:
	value = server.acquire_an_image(options.filename, options.req_no, exptime, hsspeed, pregain, highcap, hbin, vbin, acmode, hstart, hend, vstart, vend, options.imagetyp, options.object, options.obj_ra, options.obj_dec, options.daynight, options.comment, "vis")
except Exception, e:
	print 'error'
if e != None:
	print e
	print "String returned: ", value
elif value == 2:
	print "Something was wrong!\nCheck if directory permissions are OKAY!"
else:
	print "An image was saved to: ", value

