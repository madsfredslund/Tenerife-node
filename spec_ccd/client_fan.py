#!/usr/bin/python
'''
Created on Mar 3, 2010

@author: madsfa
This can be called to switch the mode of the cooling fan
'''
import xmlrpclib
import sys
import master_config as m_conf

#attempt connection to server
server = xmlrpclib.ServerProxy('http://%s:%s' % (m_conf.ccd_server, m_conf.ccd_port))

mode = None
e = None

if len(sys.argv) > 1:
    if sys.argv[1] == '-h' or sys.argv[1] == '--help':
       print '   Please specify a mode (0,1,2) = (high,low,off) for the cooling fan'
       print '   Example: ./client_fan 1'
       sys.exit("   Please specify a mode for the fan!")
    else:
       mode = sys.argv[1]
       if int(mode) not in [0,1,2]:
          print '  The mode value must be 0,1,2 [high,low,off]'
          sys.exit("  Wrong value for state!")
else:
    print '  Please specify a mode for the fan'
    sys.exit("  No mode has been given!")

print 'Changing the mode of the fan...'
try:
   print server.set_fan(int(mode))
except Exception ,e:
   print 'Could not connect to the camera.'
   print e
   
if e == None:
  print 'Fan mode has changed!'

