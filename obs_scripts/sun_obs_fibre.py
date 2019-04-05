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

def stopping():

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

		elif imagetype.lower() == 'sun':
			try:
				lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point
				lamp.Lamp(lamp='halo').set_off()	# Might change Lamp to LAMP at some point
			except Exception,e:
				print clock.timename(), "One of the lamps was not switched correctly"
			pst.PST().move(3,2) 			# Move IODINE cell out of path
			pst.PST().move(4,4) 			# Move Calibration slide to Sun Fibre position

		elif imagetype.lower() == 'suni2':
			try:
				lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point
				lamp.Lamp(lamp='halo').set_off()	# Might change Lamp to LAMP at some point
			except Exception,e:
				print clock.timename(), "One of the lamps was not switched correctly"
			pst.PST().move(3,iodine_cell) 			# Move IODINE cell into light path
			pst.PST().move(4,4) 			# Move Calibration mirror to Sun Fiber position


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

	### Check for clouds:
	weather_value = checker_handle.weather_check(deduced=1)
	print clock.timename(), weather_value
	if 16 in weather_value[0] or 32 in weather_value[0]:
		#send_song_mail.send_mail().sending_an_email(reciever=['mads'],sender="SONG_MS",subject="Sun fibre observations - aborted!",message="The sun fibre script aborted because of rain or clouds. Please check!\n\nSend at: %s\n\n" % clock.obstimeUT())
		try:
			update_or("constraint_3, ins_at, constraint_4", "%i, '%s', '%s'" % (5, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "On hold"), "req_no", obs_req_nr)
			update_or_status("wait", obs_req_nr)
			#update_or_status("abort", obs_req_nr)
		except Excpetion,e:
			print e
			print clock.timename(), "Could not update OR status!"	
		else:
			print clock.timename(), "OR (%i) put on hold" % (int(obs_req_nr))
			time.sleep(5)

		sys.exit()

	# If high cadence solar observations are needed:
	if int(obs_req_values["req_chain_next"]) != 0:
		obs_req_values["no_exp"] = int(obs_req_values["req_chain_next"]) * int(obs_req_values["no_exp"])

	#####
	# Make sure the SONG solar shutter is active:				
	# Changing to Solar shutter by power ON outlet 13:
	if obs_req_values["obs_mode"].lower() == "iodine" and int(obs_req_values["no_exp"]) > 50:
		print clock.timename(), "Switching to SOLAR shutter..."
		try:
			pdu_handle.SetPower("container", 13, 1)
		except Exception,e:
			print e
			print clock.timename(), "Could not activate Solar shutter"
		else:
			print clock.timename(), "SOLAR shutter is now activated!"
			solar_shutter_active = 1
	else:
		solar_shutter_active = 0


	try:
		pugu_pid = os.popen("cat /tmp/pupil_guider.pid").readlines()[0].strip()
	except Exception,e:
		print clock.timename(), "/tmp/pupil_guider.pid did not exist!"
		pugu_er = 1
		pugu_pid = 0

	if int(pugu_pid) > 0:
		print clock.timename(), "pugu is running"
	else:
		try:
			restart_pugu()
		except Exception,e:
			print clock.timename(), "Pugu did not get started!"
			sys.exit("The execution of the OR was cancelled!")	
	sys.stdout.flush()

	try:
		starting_up()
	except Exception,e:
		print clock.timename(), "Sigu and Pugu did not get started!"
		sys.exit("The execution of the OR was cancelled!")
	sys.stdout.flush()


	try:
		stop_window_time = datetime.datetime.strptime(str(obs_req_values["stop_window"]), "%Y-%m-%d %H:%M:%S")
	except Exception, e:
		print clock.timename(), e
		print clock.timename(), "Could not get the stop window time"

	try:
		obs_stop_time = datetime.datetime.strptime(str(sun_handle.obs_stop_next(m_conf.obs_sun_alt)), "%Y/%m/%d %H:%M:%S")
	except Exception, e:
		print clock.timename(), e
		print clock.timename(), "Could not get the obs stop time from star checker"


	if obs_req_values["obs_mode"].lower() == "thar" or obs_req_values["obs_mode"].lower() == "none-iodine":

		return_val = move_motors(imagetype="thar")
		if return_val != 'done':
			print clock.timename(), "The motors were not moved!"
			print clock.timename(), "The observations were cancelled due to the above..."
			sys.exit()
		else:
			print clock.timename(), "The motors have moved mirrors into position!"
		sys.stdout.flush()

		for j in range(int(obs_req_values["no_exp"])/int(obs_req_values["no_target_exp"])):
			# Acquire THAR spectras!	
			for i in range(int(obs_req_values["no_thar_exp"])):
				ccd_value = ccd_server.acquire_an_or_image("mfa.fits", obs_req_nr, float(m_conf.thar_exptime), 1, 2, '', 1, 1, '', 1, 2088, 1, 2048, "THAR", "Sun", "00:00:00", "00:00:00", 'sun',"Using fibre")
				print clock.timename(), "ThAr spectre number: %i of %i was acquired" % (i+1, int(obs_req_values["no_thar_exp"]))
				sys.stdout.flush()

			return_val = move_motors(imagetype="sun")
			if return_val != 'done':
				print clock.timename(), "The motors were not moved!"
				print clock.timename(), "The observations were cancelled due to the above..."
				sys.exit()
			else:
				print clock.timename(), "The motors have moved mirrors into position!"
			sys.stdout.flush()	

			# Acquire sun spectras!	
			for i in range(int(obs_req_values["no_target_exp"])):
				ccd_value = ccd_server.acquire_an_or_image("mfa.fits", obs_req_nr, float(obs_req_values["exp_time"]), 1, 2, '', 1, 1, '', 1, 2088, 1, 2048, "SUN", "Sun", "00:00:00", "00:00:00", 'sun',"Using fibre")
				print clock.timename(), "Sun spectre number: %i of %i was acquired" % (i+1, int(obs_req_values["no_target_exp"]))
				sys.stdout.flush()

			return_val = move_motors(imagetype="thar")
			if return_val != 'done':
				print clock.timename(), "The motors were not moved!"
				print clock.timename(), "The observations were cancelled due to the above..."
				sys.exit()
			else:
				print clock.timename(), "The motors have moved mirrors into position!"
			sys.stdout.flush()

			# Acquire THAR spectras!	
			for i in range(int(obs_req_values["no_thar_exp"])):

				obs_time_diff = stop_window_time - (datetime.datetime.utcnow() + datetime.timedelta(seconds=obs_req_values["exp_time"]))
				if (float(obs_time_diff.days)*24*3600. + float(obs_time_diff.seconds)) < -10.0:
					print clock.timename(), "Stop window end time was reached!"
					break

				ccd_value = ccd_server.acquire_an_or_image("mfa.fits", obs_req_nr, float(m_conf.thar_exptime), 1, 2, '', 1, 1, '', 1, 2088, 1, 2048, "THAR", "Sun", "00:00:00", "00:00:00", 'sun',"Using fibre")
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
			update_or("constraint_2", int(j*i), "req_no", obs_req_nr)
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), "Could not update OR with number of acquire images!"

	try:
		stopping()
	except Exception, e:
		print clock.timename(), "Something went wrong when trying to stop the guiders!"
		print clock.timename(), e

	try:
		os.popen("python /home/obs/programs/guiders/pupil/pupil_guider.py -t", "w")
	except Exception, e:
		print clock.timename(), "Something went wrong when trying to stop pupil guider!"
		print clock.timename(), e

	sys.stdout.flush()
	#sys.exit()


	#####
	# Make sure the SONG Stellar shutter is active:				
	# Changing to Stellar shutter by power OFF outlet 13:

	if solar_shutter_active == 1:
		print clock.timename(), "Switching to STELLAR shutter..."
		try:
			pdu_handle.SetPower("container", 13, 2)
		except Exception,e:
			print clock.timename(), "Could not activate Stellar shutter"
		else:
			print clock.timename(), "STELLAR shutter is now activated!"			

	try:
		update_or_status("done", obs_req_nr)
	except Excpetion,e:
		print e
		print clock.timename(), "Could not update OR status!"



if __name__ == "__main__":
	obs_req_nr = int(sys.argv[1])   
	EXECUTE_OR(obs_req_nr)



