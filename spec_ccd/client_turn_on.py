#!/usr/bin/python
'''
Created on Feb 24, 2010

@author: madsfa
'''
import xmlrpclib
import sys
import master_config as m_conf

#attempt connection to server
server = xmlrpclib.ServerProxy('http://%s:%s' % (m_conf.ccd_server, m_conf.ccd_port))

if len(sys.argv) > 1:
   if sys.argv[1] == '-h' or sys.argv[1] == '--help':
      print '  This function will initialize the CCD camera after shutdown.'
      sys.exit('  No parameters is required for this function')
   else:
      sys.exit('  No parameters is required for this function\nType -h or --help to see functionality') 
else:
   try:
      server.turnon_camera()
      print 'The Camera is now turned on!'
   except Exception, e:
      print 'Could not connect to the camera.'
      print e
