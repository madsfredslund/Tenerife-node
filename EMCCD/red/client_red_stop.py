#!/usr/bin/python
'''
Created on Feb 24, 2010

@author: madsfa
When called this will shutdown the camera properly and disconnect the daemon.
'''
import xmlrpclib, sys, os
from signal import SIGKILL
import time
sys.path.append("/home/madsfa/subversion/trunk/common/") 
import master_config as m_conf
import red_ccd_config as conf

#attempt connection to server
server = xmlrpclib.ServerProxy('http://%s:%s' % (conf.serverhost, conf.port))

if len(sys.argv) > 1:
   if sys.argv[1] == '-h' or sys.argv[1] == '--help':
      print '   This function does not need parameters.'
      print '   When called this will turn of the camera properly and terminate the Camera Daemon.'
      sys.exit()
   elif sys.argv[1] == '--total':
        try:
           print("Shutting down the camera...")
           server.shutdown_camera()
        
           print("Turning off the power on outlet 2 on the APC...")
           setpower = server.poweronapc(2,2)
           print setpower
        
           print 'Closing Camera Daemon...'
           server.stop_server()
        except Exception, e:
           print 'Could not connect to the camera daemon!'
           print e
   elif sys.argv[1] == '--force':
        try:
           pidfile = open('/home/madsfa/SONG_programs/logs/song_camera.pid', 'r')
           pidnumber = int(pidfile.read().strip())
           pidfile.close()
           print 'Killing the process with pidnumber: ', pidnumber
        except IOError, e:
           print e
           pid = None
         
           if not pidnumber:
              message = "pidfile %s does not exist. Daemon not running?\n"
              sys.stderr.write(message % '/home/madsfa/SONG_programs/logs/song_camera.pid')

        try:
            commandkill = 0
            while commandkill != None:
                os.kill(pidnumber, SIGKILL) # SIGTERM is replaced by SIGKILL to make sure to kill the daemon
                commandkill = os.kill(pidnumber, SIGKILL) # SIGTERM is replaced by SIGKILL to make sure to kill the daemon
                time.sleep(0.1)
                
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
               if os.path.exists('/home/madsfa/SONG_programs/logs/song_camera.pid'):
                  os.remove('/home/madsfa/SONG_programs/logs/song_camera.pid')
               else:
                  print str(err)
                  sys.exit(1)
        
        try:
             os.remove('/home/madsfa/SONG_programs/logs/song_camera.pid')
        except Exception, e:
            print e
            
   else:
      sys.exit('   This function does not need parameters.\nType -h or --help to see functionality.')
else:
	#This makes sure that there will be no stress on the CCD because of temperature changes.
	try:
	   print("Shutting down the camera...") 
	   server.shutdown_camera()
	
	   #now stop the server. Otherwise it might run forever
	   print 'Closing Camera Daemon...'
	   server.stop_server()
	except Exception, e:
	   print 'Could not connect to the camera daemon!'
	   print e

