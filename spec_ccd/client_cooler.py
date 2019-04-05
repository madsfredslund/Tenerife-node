#!/usr/bin/python
'''
Created on Mar 3, 2010

@author: madsfa
This can be called to switch the cooler on or off
'''
import xmlrpclib
import sys
import master_config as m_conf

#attempt connection to server
server = xmlrpclib.ServerProxy('http://%s:%s' % (m_conf.ccd_server, m_conf.ccd_port))

state = None
e = None

if len(sys.argv) > 1:
    if sys.argv[1] == '-h' or sys.argv[1] == '--help':
       print '   Please specify a state (on/off) for the cooler'
       print '   Example: ./client_cooler on'
       sys.exit("   Please specify a state for the cooler!")
    else:
       state = sys.argv[1]
       if str(state) != 'on' and str(state) != 'off':
          print '  The state must be on or off'
          sys.exit("  Wrong value for state!")
else:
    print '  Please specify a state for the cooler'
    sys.exit("  No state has been given!")

print 'Changing the state of the cooler...'
try:
   server.cooler(state)
except Exception ,e:
   print 'Could not connect to the camera.'
   print e
   
if e == None:
  print 'Cooler status has changed!'

