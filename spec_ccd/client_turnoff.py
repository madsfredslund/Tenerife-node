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

e = None

if len(sys.argv) > 1:
   if sys.argv[1] == '-h' or sys.argv[1] == '--help':
      print '  This function will turn off the CCD camera.'
      sys.exit('  No parameters is required for this function')
   else:
      sys.exit('  No parameters is required for this function\nType -h or --help to see functionality') 
else:
   try:
      server.shutdown_camera()
   except Exception, e:
      print 'Could not connect to the camera.'
      print e

if e == None:
   print 'The Camera has now been turned off!'


