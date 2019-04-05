#!/usr/bin/python
'''
Created on Mar 3, 2010

@author: madsfa
when this is called the temperature for the camera will be set and it waits until the temperature has been stabilized.
'''
import xmlrpclib
import sys
import master_config as m_conf

#attempt connection to server
server = xmlrpclib.ServerProxy('http://%s:%s' % (m_conf.ccd_server, m_conf.ccd_port))

e = None

if len(sys.argv) > 1:
    if sys.argv[1] == '-h' or sys.argv[1] == '--help':
       print '   Please specify a temperature in the range -10'+ unichr(176).encode("UTF-8") + 'C'+' to -120'+ unichr(176).encode("UTF-8") + 'C!'
       print '   Example: ./client_settemp -80'
       sys.exit("   No valid temperature has been defined!")
    else:
       cam_temp = sys.argv[1]
       if int(cam_temp) > -10 or int(cam_temp) < -120:
          print '  The temperature must be set to a value in the range {-10,-11,...,-119,-120}'
          sys.exit("  Wrong value for CCD temperature!")
else:
    print '  Please specify a temperature in the range -10'+ unichr(176).encode("UTF-8") + 'C'+' to -120'+ unichr(176).encode("UTF-8") + 'C!'
    sys.exit("  No temperature has been defined!")

print 'Setting temperature...'
try:
   server.set_temp(cam_temp)
except Exception ,e:
   print 'Could not connect to the camera.'
   print e
   
if e == None:
  print 'Temperature stabilized!'

