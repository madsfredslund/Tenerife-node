#!/usr/bin/python
'''
Created on Oct. 10, 2011

@author: Mads Fredslund Andersen
'''
import xmlrpclib
import sys
import comm2tcs_read
import comm2tcs_write
import time
import psycopg2
import master_config as m_conf
import os

gettsi = comm2tcs_read.GET_TSI()
settsi = comm2tcs_write.SET_TSI()


# Database values:
#db_central = "192.168.64.65"	# Central db machine
#db_host = "192.168.66.65"	# Tenerife machine
#db_user = "postgres"
#db_password = ""
#db = "db_song"
#db_table = "obs_request_1"
#st_db = "db_tenerife"
#st_table = "obs_request_status_1"

db_central = m_conf.db_c_host	# Central db machine
db_host =  m_conf.db_host	# Tenerife machine
db_user =  m_conf.db_user
db_password =  m_conf.db_password
db =  m_conf.or_db
db_table = m_conf.or_table
st_db =  m_conf.data_db
st_table =  m_conf.or_status_table


def update_or(parameters="", ins_values="", table_id="req_no", req_no=""):
	"""
	@brief:		    
	@param: 
	
	"""
	stmt_up = "UPDATE obs_request_1 SET (%s) = (%s) WHERE %s = %s" % (str(parameters), str(ins_values), str(table_id), str(req_no))

	try:
		conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s' connect_timeout=3" % (db_central, db, db_user, db_password))
	except Exception,e:
		print clock.timename(), e
		print clock.timename(), "The update function has timed out"
		return 0

	curr = conn.cursor()		

	try:
	    curr.execute(stmt_up)
	except Exception as e:
	    conn.rollback()
	    print clock.timename(), "Could not create status in the database. Changes to the status-data has been rolled back."
	    print clock.timename(), e

	conn.commit()
	curr.close()
     	conn.close()  
	return 1


def update_or_status(status, obs_req_nr):
	"""
	@brief Update the status.
	Updates the status in the database. Since the req_no is locked to the instance of the ObservationStatus object, all you need to supply here is the new status. The ins_at-field in the database will be updated as well.
	    
	@param status The new value for the status.
	@exception AssertionError Bad value of status provided.
	
	"""
	if obs_req_nr == "":
		return 0	

	conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, st_db, db_user, db_password))

	if status not in list(['wait', 'exec', 'done', 'abort', 'unknown']):
	    raise AssertionError("Could not update status. The values '%s' is not among the allowed values." % (status))
	curr = conn.cursor()
	try:
	    stmt = "UPDATE %s SET status='%s', ins_at='%s' WHERE req_no=%s" % (st_table, status, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), obs_req_nr)
	    curr.execute(stmt)
	except Exception as e:
	    conn.rollback()
	    print("Could not create status in the database. Changes to the status-data has been rolled back.")
	    raise e

	conn.commit()
	curr.close()
     	conn.close()  
	return 1

if len(sys.argv) > 1:
	try:
		obs_req_nr = int(sys.argv[1])
		print "Obs request number was: ", obs_req_nr
	except Exception,e:
		print "The request number was not correct"
		sys.exit("You must give the request number of the OR you want to abort!")
else:
	sys.exit("You must give the request number of the OR you want to abort!")
	#print "No request number was given and the script will only send an abort command to the CCD camera."


#attempt connection to server
server2 = xmlrpclib.ServerProxy('http://%s:%s' % (m_conf.ccd_server, m_conf.ccd_abort_port))
e = None
print 'Aborting CCD acquisition...'
try:
	value = server2.abort_function()
except Exception ,e:
	print 'Could not connect to the camera.'
	print e
   
if e == None:
	print value

print "Now stopping the telescope if it is tracking."

try:
	track_value = gettsi.get_pointing_track(sender="Observer")
	motion_state = gettsi.get_telescope_motion_state(sender="Observer") 
	print "The motion state of the telescope is currently: ", motion_state

	if float(track_value) == float(1.0) or float(motion_state) != 0.0:
		print "Stop tracking..."
		track_state = settsi.set_pointing_track(param=0,sender="Observer")

	motion_state = gettsi.get_telescope_motion_state(sender="Observer") 
	print "The motion state of the telescope is now: ", motion_state
except Exception,e:
	print "Could not stop the telescope"
	print e

print "Now updating the OR status to abort"

try:
	update_or_status("abort", obs_req_nr)
	update_or("constraint_4", "'Manually aborted'", "req_no", obs_req_nr)
except Exception,e:
	print "Could not update the OR status"
	print e

#### Checking for running obs scripts:
print "Now trying to clean up after you..."
pros = os.popen("ps -ef | grep OR_script.py").readlines()
for proc_line in pros:
	print proc_line
	if "/home/madsfa/subversion/trunk/obs_scripts/SONG_obs/OR_script.py" in proc_line:
		pid = proc_line.split()[1]
		print "Trying to kill process with PID number: ", pid
		try:
			pid = int(pid)
		except Exception,e:
			print "Could not get PID of process"
		else:
			print "Trying to kill the process..."
			os.popen("kill -9 %i" % pid)

print "Done!"






