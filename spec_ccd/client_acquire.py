#!/usr/bin/python
'''
Created on Feb 24, 2010

@author: madsfa
'''
import xmlrpclib
import sys, time
import master_config as m_conf

#attempt connection to server
server = xmlrpclib.ServerProxy('http://%s:%s' % (m_conf.ccd_server, m_conf.ccd_port))

filename = '/scratch/test.fits'
exptime = 1.0
hsspeed = 0
pregain = 0
highcap = 0
hbin = 1
vbin = 1
acmode = 1
hstart = 1
hend = 2048
vstart = 1
vend = 2048
#hstart = 1
#hend = 2088
#vstart = 1
#vend = 2048
req_no = ''
imagetyp = "STAR"
comment = ""

print 'Acquiring...'
try:
	value = server.acquire_an_image(filename,req_no,exptime,hsspeed,pregain,highcap,hbin,vbin,acmode,hstart,hend,vstart,vend,imagetyp,comment)
	if value != '':
		print value
except Exception,e:
	print 'Could not connect to the camera!'
	print 'Check if the Daemon is running!'
	print e

############################ THIS IS TO SHOW THE IMAGE AND HEADER###################################################
if len(sys.argv) == 3:
	show = sys.argv[1]
	option = sys.argv[2]
	
	if show == '-s' or show == '--show':
		if option == '--all':	
		
			import pyfits
			import matplotlib
			from matplotlib import *
			import matplotlib.pyplot as plt
			import numpy
			
			im, hdr = pyfits.getdata('/scratch/test.fits', header=True)
			
			plt.figure(figsize=(5, 5),facecolor='w', edgecolor='k')
			plt.subplots_adjust(left=0.0, bottom=0.0, right=1.0, top=1.0,wspace=0.2, hspace=0.2)
			plt.gray()
			plt.imshow(im, origin=[0,0]) # Log scaled
			
			plt.figure(figsize=(5.0, 11),facecolor='w', edgecolor='k')
			plt.subplots_adjust(left=0.0, bottom=0.0, right=1.0, top=0.97,wspace=0.2, hspace=0.2)
			plt.text(0.03,0.005,hdr,fontsize=8,bbox=dict(facecolor='green', alpha=1.0))
			plt.title('HEADER')
	
			plt.show()
		
		elif option == '-h':

			import pyfits
			import matplotlib
			from matplotlib import *
			import matplotlib.pyplot as plt
			import numpy
			
			im, hdr = pyfits.getdata('/scratch/test.fits', header=True)
			
			plt.figure(figsize=(5.0, 11),facecolor='w', edgecolor='k')
			plt.subplots_adjust(left=0.0, bottom=0.0, right=1.0, top=0.97,wspace=0.2, hspace=0.2)
			plt.text(0.03,0.005,hdr,fontsize=8,bbox=dict(facecolor='green', alpha=1.0))
			plt.title('HEADER')
	
			plt.show()
	
		elif option == '-i':
			import pyfits
			import matplotlib
			#from matplotlib import *
			import matplotlib.pyplot as plt
			import numpy
			
			im, hdr = pyfits.getdata('/scratch/test.fits', header=True)

			plt.figure(figsize=(2, 2),facecolor='w', edgecolor='k')
			plt.subplots_adjust(left=0.0, bottom=0.0, right=1.0, top=1.0,wspace=0.2, hspace=0.2)
			#plt.gray()
			#plt.bone()
			plt.copper()
			#plt.hot()
			#plt.jet()
			#plt.pink()
			
			plt.imshow(im, origin=[0,0]) # Log scaled
			
			plt.show()
		
		else:
			print 'Image was required but option was not valid!\nMust be: -i, -h or --all'
	
	else:
		print 'Image was required but show-option was not valid!\nMust be: -s or --show'
		
elif len(sys.argv) == 2:
	show = sys.argv[1]
	
	if show == '-s' or show == '--show':	
		############################ THIS IS TO SHOW THE IMAGE ###################################################
		import pyfits
		import matplotlib
		from matplotlib import *
		import matplotlib.pyplot as plt
		import numpy
		
		im, hdr = pyfits.getdata('/scratch/test.fits', header=True)
		
		plt.figure(figsize=(5, 5),facecolor='w', edgecolor='k')
		plt.subplots_adjust(left=0.0, bottom=0.0, right=1.0, top=1.0,wspace=0.2, hspace=0.2)
		plt.gray()
		plt.imshow(im, origin=[0,0]) # Log scaled
		
		plt.figure(figsize=(5.0, 11),facecolor='w', edgecolor='k')
		plt.subplots_adjust(left=0.0, bottom=0.0, right=1.0, top=0.97,wspace=0.2, hspace=0.2)
		plt.text(0.03,0.005,hdr,fontsize=8,bbox=dict(facecolor='green', alpha=1.0))
		plt.title('HEADER')

		plt.show()
	
	else:
		print 'Image was required but show option was not valid!\nMust be: -s or --show'	
		
		
		
		
		
