#!/usr/bin/python

import sys
import os
import time
import send_song_mail
import song_timeclass
import slit_module
import pupil_module
import psycopg2
import datetime
import master_config as m_conf
import subprocess
import xmlrpclib
sys.path.append("/home/obs/programs/DMC")
import pst
import lamp
import Set_M8
import get_db_values
import pdu_module
import song_star_checker
import song_checker
import comm2tcs_write
import comm2tcs_read

ccd_server = xmlrpclib.ServerProxy('http://%s:%s' % (m_conf.ccd_server, m_conf.ccd_port))

sigu = slit_module.SIGU()
pugu = pupil_module.PUGU()
sun_handle = song_star_checker.sun_pos(m_conf.song_site)
checker_handle = song_checker.Checker()

clock = song_timeclass.TimeClass()
pdu_handle = pdu_module.APC()



def update_or_status(status, obs_req_nr):
	"""
	@brief Update the status.
	Updates the status in the database. Since the req_no is locked to the instance of the ObservationStatus object, all you need to supply here is the new status. The ins_at-field in the database will be updated as well.
	    
	@param status The new value for the status.
	@exception AssertionError Bad value of status provided.
	
	"""
	if obs_req_nr == "":
		return 0	

	conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s' connect_timeout=5" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))

	if status not in list(['wait', 'exec', 'done', 'abort', 'unknown']):
	    raise AssertionError("Could not update status. The values '%s' is not among the allowed values." % (status))
	curr = conn.cursor()
	try:
	    stmt = "UPDATE %s SET status='%s', ins_at='%s' WHERE req_no=%s" % (m_conf.or_status_table, status, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), obs_req_nr)
	    curr.execute(stmt)
	except Exception as e:
	    conn.rollback()
	    print clock.timename(), "Could not create status in the database. Changes to the status-data has been rolled back."
	    raise e

	conn.commit()
	curr.close()
     	conn.close()  
	return 1

def update_or(parameters="", ins_values="", table_id="req_no", req_no=""):
	"""
	@brief:		    
	@param: 
	
	"""
	stmt_up = "UPDATE obs_request_1 SET (%s) = (%s) WHERE %s = %s" % (str(parameters), str(ins_values), str(table_id), str(req_no))

	try:
		conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s' connect_timeout=5" % (m_conf.db_c_host, m_conf.or_db, m_conf.db_user, m_conf.db_password))
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

def get_or_values(table_name, fields=[], req_no=""):
	"""
	 @brief: This function collects data from given table in database to a specific observation request.
	 @param req_no: The observation request number.
	"""

	conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.or_db, m_conf.db_user, m_conf.db_password))
	curr = conn.cursor()

	field_str = ''
	for field in fields:
		field_str += field
		field_str += ','
	field_str = field_str[0:-1]

	stmt = 'SELECT %s FROM %s WHERE req_no = %s' % (field_str, table_name, req_no)
	curr.execute(stmt)
	results = curr.fetchone()
	curr.close()
	conn.close()

	res_dict = {}
	if results != None:
		for i in range(len(results)):
			res_dict[fields[i]] = results[i]
		return res_dict
	else:
		return None

#def restart_sigu():
#	try:
#		os.popen("python /home/obs/programs/guiders/slit/slit_guider.py -t", "w")
#	except Exception, e:
#		print clock.timename(), "Something went wrong when trying to stop slit guider!"
#		print clock.timename(), e
#
#	time.sleep(2)
#
#	try:
#		os.popen("python /home/obs/programs/guiders/slit/slit_guider.py -s", "w")
#	except Exception, e:
#		print clock.timename(), "Something went wrong when trying to start slit guider!"
#		print clock.timename(), e
#
#	time.sleep(2)
#
#	return 1

def restart_pugu():

	try:
		os.popen("python /home/obs/programs/guiders/pupil/pupil_guider.py -t", "w")
	except Exception, e:
		print clock.timename(), "Something went wrong when trying to stop pupil guider!"
		print clock.timename(), e

	time.sleep(2)

	try:
		os.popen("python /home/obs/programs/guiders/pupil/pupil_guider.py -s", "w")
	except Exception, e:
		print clock.timename(), "Something went wrong when trying to start pupil guider!"
		print clock.timename(), e

	time.sleep(2)

	return 1

def starting_up():

	sigu_texp = "0.002"
	pugu_texp = "0.001"

	val = sigu.exec_action("texp", [sigu_texp])
	val = pugu.exec_action("texp", [pugu_texp])
	val = pugu.exec_action("pause")	
	#val = pugu.exec_action("start")	
	val = sigu.exec_action("pause")	
	#val = sigu.exec_action("start")	

	return 1

def stop_sigu_pugu():

	val = pugu.exec_action("stop")	
	val = sigu.exec_action("stop")	

	return 1	


def move_motors(imagetype="", obs_mode="", iodine_cell=3):

	### Check which obs mode the OR defines and move motors...

	# Check if motors are moving:
	output = get_db_values.db_connection().get_fields_site01("coude_unit", fields=["calib_mirror_pos", "iodine_pos", "filter_pos", "mirror_slide", "spectrograph_foc", "slit_pos"])

	timeout = time.time() + 20
	for motor in output:
		if float(output[motor]) == 0.0:
			time.sleep(1)
			output_motor = get_db_values.db_connection().get_fields_site01("coude_unit", fields=[motor])
			while float(output_motor[motor]) == 0.0:
				time.sleep(1)
				output_motor = get_db_values.db_connection().get_fields_site01("coude_unit", fields=[motor])
				if time.time() > timeout:
					break

	try:

		if imagetype.lower() == 'thar':
			try:
				lamp.Lamp(lamp='thar').set_on()	# Might change Lamp to LAMP at some point
				lamp.Lamp(lamp='halo').set_off()	# Might change Lamp to LAMP at some point
			except Exception,e:
				print clock.timename(), "One of the lamps was not switched correctly"
			pst.PST().move(3,2) 			# Move IODINE cell out of path
			pst.PST().move(4,3) 			# Move Calibration mirror to ThAr position

		elif imagetype.lower() == 'moon':
			try:
				lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point
				lamp.Lamp(lamp='halo').set_off()	# Might change Lamp to LAMP at some point
			except Exception,e:
				print clock.timename(), "One of the lamps was not switched correctly"
			pst.PST().move(3,2) 			# Move IODINE cell out of path
			pst.PST().move(4,1) 			# Move Calibration slide to telescope position

		elif imagetype.lower() == 'mooni2':
			try:
				lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point
				lamp.Lamp(lamp='halo').set_off()	# Might change Lamp to LAMP at some point
			except Exception,e:
				print clock.timename(), "One of the lamps was not switched correctly"
			pst.PST().move(3,iodine_cell) 			# Move IODINE cell into light path
			pst.PST().move(4,1) 			# Move Calibration mirror to telescope position


		### These are the same for all types of observations...
		pst.PST().move(1,4) 				# Move Filter wheel to position 4 (Free)
		pst.PST().move(6,8) 				# Move slit to right position


		Set_M8.set_m8_pos()

	except Exception, e:
		print clock.timename(), "An error occured when trying to move the motors: ", e
		return e

	return 'done'


def EXECUTE_OR(obs_req_nr=""):

	if obs_req_nr != "":
		obs_req_values = get_or_values("obs_request_1", ["right_ascension", "declination", "ra_pm", "dec_pm", "object_name", "imagetype", "observer", "exp_time", "x_bin", "y_bin", "x_begin", "y_begin", "x_end", "y_end", "no_exp", "no_target_exp", "no_thar_exp", "amp_gain", "readoutmode", "iodine_cell", "obs_mode", "slit", "start_window", "stop_window", "project_name", "ang_rot_offset", "adc_mode", "epoch", "site", "project_id", "req_prio", "req_chain_previous", "req_chain_next", "magnitude"], obs_req_nr)


	#### To not saturate the skycam1:
	os.system("python /home/madsfa/subversion/trunk/skycam/skycam_code/acq_skycam_im.py -m stop")

	try:
		stop_sigu_pugu()
	except Exception,e:
		print clock.timename(), e
		print clock.timename(), "sigu pugu failure!"


	print clock.timename(), "Stopping the telescope..."	
	value = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")
	print ""
	print clock.timename(), " PLEASE MOVE TELESCOPE TO THE MOON NOW!!!"
	print ""
	sys.stdout.flush()


	comm2tcs_write.SET_TSI().set_position_instrumental_az_offset(param=0.0,sender="Observer")
	comm2tcs_write.SET_TSI().set_position_instrumental_zd_offset(param=0.0,sender="Observer")

	# SETTING THE TELESCOPE TO POINT TO THE MOON:
	value = comm2tcs_write.SET_TSI().set_object_solarsystem_object(param=3,sender="Observer")	# Set Object to Earth
	value = comm2tcs_write.SET_TSI().set_object_solarsystem_moon(param=1,sender="Observer")		# Set moon to Moon	

	# Setting the telescope to point to and track the moon:
	value = comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Observer")	# start to track the Moon


	track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")

	timeout = time.time() + 120	# Timeout after n minutes.
	close_to = False

	time_out = time.time() + 120
	while str(track_value) not in ['11', '11.0']:
		time.sleep(1.0)
		track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
		print clock.timename(), "The telescope motion state value was: ", track_value

		if time.time() > time_out:
			break
	t1 = time.time() + 120
	print "Please move telescope manually to the Moon or fix the issues!"
	while time.time < t1:
		print "You have %i seconds left to be tracking the Moon" % (int(t1-time.time()))



	if obs_req_values["obs_mode"].lower() == "thar" or obs_req_values["obs_mode"].lower() == "none-iodine":

		return_val = move_motors(imagetype="thar")
		if return_val != 'done':
			print clock.timename(), "The motors were not moved!"
			print clock.timename(), "The observations were cancelled due to the above..."
			sys.exit()
		else:
			print clock.timename(), "The motors have moved mirrors into position!"

		sys.stdout.flush()

		os.system("python /home/madsfa/subversion/trunk/skycam/skycam_code/acq_skycam_im.py -mstart -e0.001 --mt=5")
	
########### DO THAR before
		for i in range(int(obs_req_values["no_thar_exp"])):
			ccd_value = ccd_server.acquire_an_or_image("mfa.fits", obs_req_nr, float(m_conf.thar_exptime), 1, 2, '', 1, 1, '', 1, 2088, 1, 2048, "THAR", "Moon", "00:00:00", "00:00:00", 'moon',"")
			print clock.timename(), "ThAr spectre number: %i of %i was acquired" % (i+1, int(obs_req_values["no_thar_exp"]))
			sys.stdout.flush()

		return_val = move_motors(imagetype="moon")
		if return_val != 'done':
			print clock.timename(), "The motors were not moved!"
			print clock.timename(), "The observations were cancelled due to the above..."
			sys.exit()
		else:
			print clock.timename(), "The motors have moved mirrors into position!"
		sys.stdout.flush()	


########## Be sure we are tracking the Moon
		track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
		timeout = time.time() + 120	# Timeout after 120 seconds
		break_out = False
		while str(track_value) not in ['11', '11.0'] and break_out == False:
			time.sleep(1.0)
			track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
			print clock.timename(), "The telescope motion state value was: ", track_value
			if time.time() > timeout:
				value = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")				
				print clock.timename(), "The timeout was reached at: %s" % (clock.obstimeUT())
				break_out == True
			

		print ""
		print clock.timename(), "Starting to acquire spectra..."
		print ""	
		sys.stdout.flush()
########## Acquire moon spectras!
		sigu.exec_action("texp", ["0.1"])
		sigu.exec_action("pause")			
		sigu.exec_action("start")
		sigu.exec_action("moveto", ["60","40"])	

		for i in range(int(obs_req_values["no_exp"])):
			ccd_value = ccd_server.acquire_an_or_image("mfa.fits", obs_req_nr, float(obs_req_values["exp_time"]), 1, 2, '', 1, 1, '', 1, 2088, 1, 2048, "STAR", "Moon", "00:00:00", "00:00:00", 'moon',"")
			print clock.timename(), "Moon spectre number: %i of %i was acquired" % (i+1, int(obs_req_values["no_exp"]))
			sys.stdout.flush()
			
			#### Repoint telescope

			print clock.timename(), "Setting -track- to the telescope to repoint"
			value = comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Observer")	# start to track the Moon
			time.sleep(5)

			#value = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")	
			#time.sleep(1)
			#value = comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Observer")
			#track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
			#timeout = time.time() + 30	# Timeout after 30 seconds
			#while str(track_value) not in ['11', '11.0']:
			#	time.sleep(1.0)
			#	track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
			#	print clock.timename(), "The telescope motion state value was: ", track_value
			#	if time.time() > timeout:
			#		value = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")				
			#		print clock.timename(), "The timeout was reached at: %s" % (clock.obstimeUT())
			#		update_or_status("abort", req_no)
			#		update_or("constraint_4", "'Tracking timeout'", "req_no", req_no)
			#		sys.exit()

########### DO THAR after

		return_val = move_motors(imagetype="thar")
		if return_val != 'done':
			print clock.timename(), "The motors were not moved!"
			print clock.timename(), "The observations were cancelled due to the above..."
			sys.exit()
		else:
			print clock.timename(), "The motors have moved mirrors into position!"
		sys.stdout.flush()


		stop_window_time = datetime.datetime.strptime(str(obs_req_values["stop_window"]), "%Y-%m-%d %H:%M:%S")
		# Acquire THAR spectras!	
		for i in range(int(obs_req_values["no_thar_exp"])):

			obs_time_diff = stop_window_time - (datetime.datetime.utcnow() + datetime.timedelta(seconds=obs_req_values["exp_time"]))
			if (float(obs_time_diff.days)*24*3600. + float(obs_time_diff.seconds)) < -10.0:
				print clock.timename(), "Stop window end time was reached!"
				break

			ccd_value = ccd_server.acquire_an_or_image("mfa.fits", obs_req_nr, float(m_conf.thar_exptime), 1, 2, '', 1, 1, '', 1, 2088, 1, 2048, "THAR", "Sun", "00:00:00", "00:00:00", 'moon',"")
			print clock.timename(), "ThAr spectre number: %i of %i was acquired" % (i+1, int(obs_req_values["no_thar_exp"]))
			sys.stdout.flush()

		print clock.timename(), "Power off ThAr lamp..."
		lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point


	elif obs_req_values["obs_mode"].lower() == "iodine":
		return_val = move_motors(imagetype="suni2", iodine_cell=int(obs_req_values["iodine_cell"]))
		if return_val != 'done':
			print clock.timename(), "The motors were not moved!"
			print clock.timename(), "The observations were cancelled due to the above..."
			sys.exit()
		else:
			print clock.timename(), "The motors have moved mirrors into position!"
		sys.stdout.flush()
		stop_window_time = datetime.datetime.strptime(str(obs_req_values["stop_window"]), "%Y-%m-%d %H:%M:%S")
		# Acquire suni2 spectras!	
		for i in range(int(obs_req_values["no_exp"])):

			obs_time_diff = stop_window_time - (datetime.datetime.utcnow() + datetime.timedelta(seconds=obs_req_values["exp_time"]))
			if (float(obs_time_diff.days)*24*3600. + float(obs_time_diff.seconds)) < 0.0:
				print clock.timename(), "Stop window end time was reached!"
				break

			ccd_value = ccd_server.acquire_an_or_image("mfa.fits", obs_req_nr, float(obs_req_values["exp_time"]), 1, 2, '', 1, 1, '', 1, 2088, 1, 2048, "SUN", "Sun", "00:00:00", "00:00:00", 'sun',"Using fibre")
			print clock.timename(), "Sun spectre number: %i of %i was acquired" % (i+1, int(obs_req_values["no_exp"]))
			sys.stdout.flush()
	
	### Update OR with number of acquired spectres:
	if obs_req_values["obs_mode"].lower() == "iodine":
		try:
			update_or("constraint_2", int(i), "req_no", obs_req_nr)
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), "Could not update OR with number of acquire images!"

	elif obs_req_values["obs_mode"].lower() == "thar" or obs_req_values["obs_mode"].lower() == "none-iodine":
		try:
			update_or("constraint_2", int(i), "req_no", obs_req_nr)
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), "Could not update OR with number of acquire images!"

	try:
		os.popen("python /home/obs/programs/guiders/pupil/pupil_guider.py -t", "w")
	except Exception, e:
		print clock.timename(), "Something went wrong when trying to stop pupil guider!"
		print clock.timename(), e

	sys.stdout.flush()
	#sys.exit()
	os.system("python /home/madsfa/subversion/trunk/skycam/skycam_code/acq_skycam_im.py -m stop")
	try:
		update_or_status("done", obs_req_nr)
	except Excpetion,e:
		print e
		print clock.timename(), "Could not update OR status!"



if __name__ == "__main__":
	obs_req_nr = int(sys.argv[1])   
	EXECUTE_OR(obs_req_nr)



