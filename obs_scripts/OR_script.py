#!/usr/bin/python

import sys
import comm2tcs_read
import comm2tcs_write
import song_checker
import song_star_checker
import os
import time
import send_song_mail
import OR_actions
import get_db_values
import song_timeclass
import slit_module
import pupil_module
import psycopg2
import datetime
import OR_script_config as conf
import master_config as m_conf
import subprocess
import threading
import xmlrpclib

sigu = slit_module.SIGU()
pugu = pupil_module.PUGU()

collect_db_values = get_db_values.db_connection()
clock = song_timeclass.TimeClass()

# Database values:
#db_host = "192.168.66.65"	# Tenerife machine
#db_user = "postgres"
#db_password = ""
#db = "db_song"
#db_table = "obs_request_1"
#st_db = "db_tenerife"
#st_table = "obs_request_status_1"
# Database values:
db_host =  m_conf.db_host	# Tenerife machine
db_user =  m_conf.db_user
db_password =  m_conf.db_password
db =  m_conf.or_db
db_table = m_conf.or_table
st_db =  m_conf.data_db
st_table =  m_conf.or_status_table


def get_or_values(table_name, fields=[], req_no=""):
	"""
	 @brief: This function collects data from given table in database to a specific observation request.
	 @param req_no: The observation request number.
	"""

	#conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, db, db_user, db_password))
	conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, db, db_user, db_password))

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

def get_or_status(req_no=""):
	"""
	 @brief: This function collects data from given table in database to a specific observation request.
	 @param req_no: The observation request number.
	"""
	conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, st_db, db_user, db_password))
	curr = conn.cursor()

	stmt = 'SELECT status FROM obs_request_status_1 WHERE req_no = %s' % (req_no)
	curr.execute(stmt)
	results = curr.fetchone()
	curr.close()
	conn.close()

	return results[0]

def acquire_skycam2_image(exp_time):
	try:
		server = xmlrpclib.ServerProxy('http://luckycam1.prv:8110')
		server.acquire_im_thread("", exp_time, 1, 1, "usb", 1, "", 0, 0, 3358, 2536)
	except Exception,e:
		print e
	return 1

def acquire_skycam2_phot(exp_time,numberofimages,req_no, xbegin, ybegin, width, height):
	try:
		server = xmlrpclib.ServerProxy('http://luckycam1.prv:8110')
		server.acquire_im_thread("", exp_time, 1, int(numberofimages), "usb", 1, req_no, xbegin, ybegin, width, height)
	except Exception,e:
		print e
	return 1

def set_skycam2_filter(filterpos):
	try:
		server = xmlrpclib.ServerProxy('http://luckycam1.prv:8110')
		server.change_filter(int(filterpos))
	except Exception,e:
		print e
	return 1

def start_skycam2_derot():
	try:
		server = xmlrpclib.ServerProxy('http://luckycam1.prv:8110')
		cur_pos = server.start_derotator()
	except Exception,e:
		print e
	return cur_pos

def stop_skycam2_derot():
	try:
		server = xmlrpclib.ServerProxy('http://luckycam1.prv:8110')
		server.stop_derotator()
	except Exception,e:
		print e
	return 1

def set_skycam2_derot_goto(pos):
	try:
		server = xmlrpclib.ServerProxy('http://luckycam1.prv:8110')
		server.derotator_go_to(pos)
	except Exception,e:
		print e
	return 1

def EXECUTE_OR(obs_req_nr):
	do_action = OR_actions.DO_SOMETHING(obs_req_nr=obs_req_nr)

	#####   Outline of script #####

	# 1:	Check observing conditions (weather, time of day)
	# 2:	Check if the telescope daemon is running and if the telescope is powered on
	# 3: 	Check if sigu and pugu are running
	# 4:	Check observing window and object coordinates
	### redo # 1
	# 5: 	Set status of OR to "exec" for executing
	# 6:	Check if Dome and mirror covers are open. If not then open them.
	# 7:	Move motors to correct position on PST and in Spectrograph.
	# 8:	Slew to object and start to track. 
	# 9:	do acquisition
	# 10:	Start to acquire images/spectres until some condition are not fulfilled.
	# 11:	Change status of OR to "done" if completed with no problems.

	###############################

	def call_to_track():
		if conf.track_object == 1:
			# This should be turned into a function which can be run in a thread.
			returned_val = do_action.track_object(obs_req_nr)
			if returned_val == 'no_go':
				print clock.timename(), "The object could not be tracked!"
				print clock.timename(), "The observations were cancelled due to the above..."

				if conf.finish_off == 1:
					print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
					do_action.finishing_off()

				do_action.update_or_status("abort", obs_req_nr)
	#			do_action.update_or("constraint_4", "'Tracking problem'", "req_no", obs_req_nr)
				sys.exit()
			elif returned_val == 'soso_go':
				print clock.timename(), "The OR will be stopped and set to wait and might be started again."

				if conf.finish_off == 1:
					print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
					do_action.finishing_off()

				sys.exit()
			elif returned_val == 'go':
				print clock.timename(), "The object are being tracked!"
			sys.stdout.flush()

		try:
			if conf.set_hexapod == 1:
				print clock.timename(), "Setting the hexapod values!"
				returned_val = do_action.set_hexapod()
		except Exception,e:
			print clock.timename(), e 
			print clock.timename(), "Problem in setting the hexapod values!"

		try:
			if conf.check_hexapod == "yes":
				print clock.timename(), "Checking the hexapod values!"
				returned_val = do_action.check_hexapod()
		except Exception,e:
			print clock.timename(), e 
			print clock.timename(), "Problem in setting the hexapod values!"

		return 1

	def check_weather():
		weather_value = song_checker.Checker().weather_check()
		print clock.timename(), "Weather value was: ", weather_value[0]
		if str(weather_value[0]) != "0":
			print clock.timename(), "The weather was not good for observing!\n"
			do_action.update_or_status("wait", obs_req_nr)
			do_action.update_or("constraint_4", "'Bad weather'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")  
		sys.stdout.flush()

	def check_daytime():
		day_value = song_checker.Checker().day_check()
		if str(day_value) == "4" and obs_req_values["object_name"].lower() != "sun":
			print clock.timename(), "The Sun has not set yet!"
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'It was daytime'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!") 
		elif str(day_value) != "4" and obs_req_values["object_name"].lower() != "sun":
			night_values = ["Night","","Astronomical twilight", "Nautical twilight", "Civil twilight", "Day"]
			print clock.timename(), "The Suns position means that it is: ", night_values[int(day_value)+1]
		elif  str(day_value) != "4" and obs_req_values["object_name"].lower() == "sun":
			print clock.timename(), "The Sun has set so it can not be observed!"
			sys.exit("The execution of the OR was cancelled!")
		sys.stdout.flush()

	def check_telescope():
		try:
			tcs_ready = comm2tcs_read.GET_TSI().get_telescope_state(sender="observer")
		except Exception,e:
			print clock.timename(), "The tcs comm daemon was not running\nOr the ASTELCO tsi script was not running on the ASTELCO PC!\nOr there were no power on the Telescope."
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'TCS problem'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")

		print clock.timename(), "The telescope state was: ", tcs_ready
		if str(tcs_ready) == "1.0":
			print clock.timename(), "The telescope is powered on and ready to observe!"
		elif str(tcs_ready) == "0.0":
			print clock.timename(), "The telescope is powered off and needs to be started!"
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'Telescope off'", "req_no", obs_req_nr)
			sys.exit()
		sys.stdout.flush()

	def check_guiders():
		if conf.use_sigu == 1:
			sigu_er = 0
			if conf.use_sigu_on_sstenerife != "yes":
				try:
					sigu_pid = os.popen("cat /tmp/slit_guider.pid").readlines()[0].strip()
				except Exception,e:
					print clock.timename(), "/tmp/slit_guider.pid did not exist!"
					sigu_pid = 0
					sigu_er = 1

				if int(sigu_pid) > 0:
					print clock.timename(), "sigu is running"
				else:
					try:
						do_action.restart_sigu()
					except Exception,e:
						print clock.timename(), "Sigu did not get started!"
						do_action.update_or_status("abort", obs_req_nr)
						do_action.update_or("constraint_4", "'Slit guider problem'", "req_no", obs_req_nr)
						sys.exit("The execution of the OR was cancelled!")	
			sys.stdout.flush()

		if conf.use_pugu == 1:
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
					do_action.restart_pugu()
				except Exception,e:
					print clock.timename(), "Pugu did not get started!"
					do_action.update_or_status("abort", obs_req_nr)
					do_action.update_or("constraint_4", "'Pupil guider problem'", "req_no", obs_req_nr)
					sys.exit("The execution of the OR was cancelled!")	
			sys.stdout.flush()

	def check_or_values():
		pass_value = do_action.check_parameters(obs_req_nr)
		if pass_value != '':
			print clock.timename(), pass_value
			print clock.timename(), "The observations were cancelled due to the above..."
			print clock.timename(), "Please correct the config file and try again!"
			do_action.update_or_status("abort", obs_req_nr)
			sys.exit()
		sys.stdout.flush()

	def check_obs_window():
		returned_val = do_action.check_obs_window(obs_req_nr)
		if returned_val == 'no_go':
			print clock.timename(), "The time of execution was not inside the observing window!"
			print clock.timename(), "The observations were cancelled due to the above..."
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'Window past'", "req_no", obs_req_nr)
			sys.exit()
		sys.stdout.flush()

	def check_object():
		object_value = song_checker.Checker().object_check(obs_req_values["right_ascension"],obs_req_values["declination"])
		if object_value == 1:
			print clock.timename(), "The object was not above %f degrees" % (m_conf.telescope_min_altitude)
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'Too low object'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")  
		elif object_value == 2:
			print clock.timename(), "The wind speed was too high in direction of the object\n"
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'High wind speed'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")  
		elif object_value == 3:
			print clock.timename(), "The object was not above %f degrees and wind speed in that direction was too high" % (m_conf.telescope_min_altitude)
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'Low object'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")  
		elif object_value == 0:
			print clock.timename(), "The object was observable"
		sys.stdout.flush()	

	def check_dome():
		slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="observer")
		if str(slit_state) != '1.0':
			print clock.timename(), "Monitor had not opened the dome! "
			do_action.update_or_status("wait", obs_req_nr)
			do_action.update_or("constraint_4", "'Dome was closed'", "req_no", obs_req_nr)
			sys.exit()
		else:
			print clock.timename(), "The dome was open "
		sys.stdout.flush()


#######################################
#######################################
#######################################

	obs_req_values = get_or_values("obs_request_1", ["right_ascension", "declination", "ra_pm", "dec_pm", "object_name", "imagetype", "observer", "exp_time", "x_bin", "y_bin", "x_begin", "y_begin", "x_end", "y_end", "no_exp", "no_target_exp", "no_thar_exp", "amp_gain", "readoutmode", "iodine_cell", "obs_mode", "slit", "start_window", "stop_window", "project_name", "ang_rot_offset", "adc_mode", "epoch", "site", "project_id", "req_prio", "req_chain_previous", "req_chain_next", "magnitude"], obs_req_nr)

	same_as_last_OR = "not_same"
	try:
		same_as_last_OR = song_checker.Checker().check_last_observed_target(next_object=obs_req_nr)
	except Exception,e:
		print clock.timename(), e
		print clock.timename(), "Could not check if the same object was to be observed again."					

	if same_as_last_OR == "not_same":
		if conf.finish_off == 1:
			print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
			try:
				do_action.finishing_off()
				do_action.thread_slew()		# Setting the self.slewing variable to one to make sure image acquisition will not happen premature.
			except Exception,e:
				print clock.timename(), e
	else:
		print clock.timename(), "Now starting the guiders..."
		try:
			do_action.start_guiding()		
		except Exception,e:
			print clock.timename(), e		

	#Check the weather conditions:
	if conf.check_weather == 1:
#		wc = threading.Thread(target=check_weather, args=()) # Move Calibration mirror out of the path
#		wc.start()

		weather_value = song_checker.Checker().weather_check()
		print clock.timename(), "Weather value was: ", weather_value[0]
		if str(weather_value[0]) != "0":
			print clock.timename(), "The weather was not good for observing!\n"
			do_action.update_or_status("wait", obs_req_nr)
			do_action.update_or("constraint_4", "'Bad weather'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")  
		sys.stdout.flush()

	#Check the time of the day conditions:
	if conf.check_daytime == 1:
#		dc = threading.Thread(target=check_daytime, args=()) # Move Calibration mirror out of the path
#		dc.start()

		day_value = song_checker.Checker().day_check()
		if str(day_value) == "4" and obs_req_values["object_name"].lower() != "sun":
			print clock.timename(), "The Sun has not set yet!"
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'It was daytime'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!") 
		elif str(day_value) != "4" and obs_req_values["object_name"].lower() != "sun":
			night_values = ["Night","","Astronomical twilight", "Nautical twilight", "Civil twilight", "Day"]
			print clock.timename(), "The Suns position means that it is: ", night_values[int(day_value)+1]
		elif  str(day_value) != "4" and obs_req_values["object_name"].lower() == "sun":
			print clock.timename(), "The Sun has set so it can not be observed!"
			sys.exit("The execution of the OR was cancelled!")
		sys.stdout.flush()

	# Check if there is a connection to the tcs comm daemon:
	if conf.check_telescope == 1:
#		ct = threading.Thread(target=check_telescope, args=()) # Move Calibration mirror out of the path
#		ct.start()

		try:
			tcs_ready = comm2tcs_read.GET_TSI().get_telescope_state(sender="observer")
		except Exception,e:
			print clock.timename(), "The tcs comm daemon was not running\nOr the ASTELCO tsi script was not running on the ASTELCO PC!\nOr there were no power on the Telescope."
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'TCS problem'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")

		print clock.timename(), "The telescope state was: ", tcs_ready
		if str(tcs_ready) == "1.0":
			print clock.timename(), "The telescope is powered on and ready to observe!"
		elif str(tcs_ready) == "0.0":
			print clock.timename(), "The telescope is powered off and needs to be started!"
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'Telescope off'", "req_no", obs_req_nr)
			sys.exit()
		sys.stdout.flush()


#	cg = threading.Thread(target=check_guiders, args=()) # Move Calibration mirror out of the path
#	cg.start()

	# Check if sigu and pugu are running:
	if conf.use_sigu == 1:
		sigu_er = 0
		if conf.use_sigu_on_sstenerife != "yes":
			try:
				sigu_pid = os.popen("cat /tmp/slit_guider.pid").readlines()[0].strip()
			except Exception,e:
				print clock.timename(), "/tmp/slit_guider.pid did not exist!"
				sigu_pid = 0
				sigu_er = 1

			if int(sigu_pid) > 0:
				print clock.timename(), "sigu is running"
			else:
				try:
					do_action.restart_sigu()
				except Exception,e:
					print clock.timename(), "Sigu did not get started!"
					do_action.update_or_status("abort", obs_req_nr)
					do_action.update_or("constraint_4", "'Slit guider problem'", "req_no", obs_req_nr)
					sys.exit("The execution of the OR was cancelled!")	
		sys.stdout.flush()

	if conf.use_pugu == 1:
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
				do_action.restart_pugu()
			except Exception,e:
				print clock.timename(), "Pugu did not get started!"
				do_action.update_or_status("abort", obs_req_nr)
				do_action.update_or("constraint_4", "'Pupil guider problem'", "req_no", obs_req_nr)
				sys.exit("The execution of the OR was cancelled!")	
		sys.stdout.flush()



	# Check the observing window
	if conf.check_obs_window == 1:
#		cbw = threading.Thread(target=check_obs_window, args=()) # Move Calibration mirror out of the path
#		cbw.start()

		returned_val = do_action.check_obs_window(obs_req_nr)
		if returned_val == 'no_go':
			print clock.timename(), "The time of execution was not inside the observing window!"
			print clock.timename(), "The observations were cancelled due to the above..."
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'Window past'", "req_no", obs_req_nr)
			sys.exit()
		sys.stdout.flush()

	# Check if parameters in the config file are valid...
	if conf.check_or_values == 1:
#		corv = threading.Thread(target=check_or_values, args=()) # Move Calibration mirror out of the path
#		corv.start()

		pass_value = do_action.check_parameters(obs_req_nr)
		if pass_value != '':
			print clock.timename(), pass_value
			print clock.timename(), "The observations were cancelled due to the above..."
			print clock.timename(), "Please correct the config file and try again!"
			do_action.update_or_status("abort", obs_req_nr)
			sys.exit()
		sys.stdout.flush()

	#Check the object conditions:
	if conf.check_object == 1:
#		co = threading.Thread(target=check_object, args=()) # Move Calibration mirror out of the path
#		co.start()

		object_value = song_checker.Checker().object_check(obs_req_values["right_ascension"],obs_req_values["declination"])
		if object_value == 1:
			print clock.timename(), "The object was not above %f degrees" % (m_conf.telescope_min_altitude)
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'Too low object'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")  
		elif object_value == 2:
			print clock.timename(), "The wind speed was too high in direction of the object\n"
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'High wind speed'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")  
		elif object_value == 3:
			print clock.timename(), "The object was not above %f degrees and wind speed in that direction was too high" % (m_conf.telescope_min_altitude)
			do_action.update_or_status("abort", obs_req_nr)
			do_action.update_or("constraint_4", "'Low object'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")  
		elif object_value == 0:
			print clock.timename(), "The object was observable"
		sys.stdout.flush()
	

	#Check the weather conditions:
	if conf.check_weather == 1:
#		wc = threading.Thread(target=check_weather, args=()) # Move Calibration mirror out of the path
#		wc.start()

		weather_value = song_checker.Checker().weather_check()
		if str(weather_value[0]) != "0":
			print clock.timename(), "The weather was not good for observing!\n"
			do_action.update_or_status("wait", obs_req_nr)
			do_action.update_or("constraint_4", "'Bad weather'", "req_no", obs_req_nr)
			sys.exit("The execution of the OR was cancelled!")  
		sys.stdout.flush()

	# Check if dome is open:
	if conf.check_dome == 1:
#		cd = threading.Thread(target=check_dome, args=()) # Move Calibration mirror out of the path
#		cd.start()
	
		slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="observer")
		if str(slit_state) != '1.0':
			print clock.timename(), "Monitor had not opened the dome! "
			do_action.update_or_status("wait", obs_req_nr)
			do_action.update_or("constraint_4", "'Dome was closed'", "req_no", obs_req_nr)
			sys.exit()
		else:
			print clock.timename(), "The dome was open "
		sys.stdout.flush()

#	thread_count = 0
#	while threading.activeCount() > 1:
#		time.sleep(0.1)
#		print clock.timename(), "Still checking things... ", threading.activeCount()

	if conf.check_mirror_covers == 1:	
		mir_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="observer")
		if float(mir_cover_state) == 0.0:
			comm2tcs_write.SET_TSI().set_auxiliary_cover_targetpos(param=1, sender="observer")
			print clock.timename(), "Now trying to open the mirror covers... "
			sys.stdout.flush()
			time_out = time.time() + 180.0
			while mir_cover_state != '1.0':
				mir_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="observer")
				time.sleep(5)
				if time.time() > time_out:
					print clock.timename(), "The while loop has timed out and the mirror covers are most likely open!"
					if conf.send_notifications == 1:
						print send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Mirror cover opening timeout!",message="The mirror cover loop timed out in the beginning of the observing script.\n\nSend at: %s\n\n" % clock.obstimeUT())
					break
				elif mir_cover_state == '1.0':
					print clock.timename(), "The mirror covers are now open"
		sys.stdout.flush()

	### CHECK IF THAR and do one if needed!
#	do_thar = 0
#	if obs_req_values["obs_mode"] == "none-iodine" and song_checker.Checker().check_last_thar_spectrum() == 1:				
#		#### Acquire ONE Thorium Argon spectrum
#		acq_thar = threading.Thread(target=do_action.acquire_one_thar, args=(obs_req_nr, "acq")) # Acquire a Thorium Argon spectre while slewing...
#		acq_thar.start()
#		do_thar = 1


	print clock.timename(), "Number of threads: ", threading.activeCount()

	tel_move_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
	if same_as_last_OR != "same" or float(tel_move_state) != 11.0:
		# Set the telescope to go to object and start tracking:
		if conf.track_object == 1:
			# This should be turned into a function which can be run in a thread.
			returned_val = do_action.track_object(obs_req_nr)
			if returned_val == 'no_go':
				print clock.timename(), "The object could not be tracked!"
				print clock.timename(), "The observations were cancelled due to the above..."

				if conf.finish_off == 1:
					print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
					do_action.finishing_off()

				do_action.update_or_status("abort", obs_req_nr)
	#			do_action.update_or("constraint_4", "'Tracking problem'", "req_no", obs_req_nr)
				sys.exit()
			elif returned_val == 'soso_go':
				print clock.timename(), "The OR will be stopped and set to wait and might be started again."

				if conf.finish_off == 1:
					print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
					do_action.finishing_off()

				sys.exit()
			elif returned_val == 'go':
				print clock.timename(), "The object are being tracked!"
			sys.stdout.flush()

		try:
			if conf.set_hexapod == 1:
				print clock.timename(), "Setting the hexapod values!"
				returned_val = do_action.set_hexapod()
		except Exception,e:
			print clock.timename(), e 
			print clock.timename(), "Problem in setting the hexapod values!"

		try:
			if conf.check_hexapod == "yes":
				print clock.timename(), "Checking the hexapod values!"
				returned_val = do_action.check_hexapod()
		except Exception,e:
			print clock.timename(), e 
			print clock.timename(), "Problem in setting the hexapod values!"

#		if obs_req_values["obs_mode"] == "none-iodine" and do_thar == 1:
#			while threading.activeCount() > 2:
#				time.sleep(1)
#				print clock.timename(), "Not done with the ThAr yet.. ", threading.activeCount()
#				sys.stdout.flush()			

		if conf.move_motors == 1 and conf.do_acquisition == 1 or obs_req_values["obs_mode"] == "template":	
			if conf.move_new_motors == 1:
				return_val = do_action.move_motors_star(tel_acq="yes")
			else:
				return_val = do_action.move_motors(tel_acq="yes")
			if return_val != 'done':
				print clock.timename(), "The motors were not moved!"
				print clock.timename(), "The observations were cancelled due to the above..."

				if conf.finish_off == 1:
					print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
					do_action.finishing_off()

				do_action.update_or_status("abort", obs_req_nr)
				do_action.update_or("constraint_4", "'DMC problem'", "req_no", obs_req_nr)


				if conf.tel_shut_down == 1:
					print clock.timename(), "Now closing telescope and power of untill problem is fixed..."

					try:
						do_action.shut_down_telescope()
					except Exception,e:
						print clock.timename(), "Failed to shut down telescope"
						
						send_song_mail.send_mail().send_sms(receiver=["Mads"], message="The telescope was not shut down correctly after DMC or guider failure! Send at: %s" % clock.obstimeUT())
					else:
						send_song_mail.send_mail().send_sms(receiver=["Mads"], message="The telescope was shut down caused by DMC or guider failure!")

				sys.exit()
			else:
				print clock.timename(), "The motors have moved mirrors into position!"
			sys.stdout.flush()

	#		time.sleep(5)

		print clock.timename(), "Number of threads: ", threading.activeCount()

		## Do acquisition to put the beam on the slit:
		if conf.do_acquisition == 1 and conf.use_sigu == 1 or obs_req_values["obs_mode"] == "template":
			returned_val = do_action.tel_acquisition()
			print clock.timename(), returned_val
			if returned_val == 'no_go':

				#send_song_mail.send_mail().send_sms(receiver=["jens"], message="The acquisition did not go well. You got mail!")

				print clock.timename(), "The object could not be located with sigu/pugu!"

				ret_val = ""
				if conf.use_skycam == 1:
					print clock.timename(), "Now trying to repoint using skycam..."
					sys.stdout.flush()				

					try:
						ret_val = do_action.repoint_with_skycam(obs_req_nr)
					except Exception,e:
						print clock.timename(), e
						print clock.timename(), "An error occurred while repointing using skycam"					

				if ret_val == 1:
					print clock.timename(), "Telescope has now repointed to object close by..."
					print clock.timename(), "Now trying to do sigu acquire again"
					sys.stdout.flush()
					returned_val = do_action.tel_acquisition()
					if returned_val == 'go':
						print clock.timename(), "The object is now on the slit!"	
					else:
						ret_val = 0
					sys.stdout.flush()

				if ret_val != 1:
					### The acquisition procedure could not put the star on the slit. 
					### Maybe because of clouds. 
					### The script will now sleep a little while and try again. 
					### The sleep time will be determined by the observing window and exposure time. 

					###### NEW THING:
					### The OR will be set on hold for x minutes before it can be selected again by the scheduler
					try:
						print clock.timename(), "Putting the OR - %i - on hold for %i minutes..." % (obs_req_nr,conf.on_hold_time)
						print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
					except Exception,e:
						print e
						print clock.timename(), "Text could not be written to the log."

					do_action.finishing_off()

					try:
						print clock.timename(), "Stopping the telescope..."
						value = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")					
					except Exception,e:
						print e
						print clock.timename(), "Could not stop the telescope"

					try:
						#### Maybe change ins_at time on status in stead... and add 3 minutes to that time...
						print clock.timename(), "Setting the ins_at to: -%s- and delay to -%s-" % (time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), conf.on_hold_time)
						do_action.update_or("constraint_3, ins_at, constraint_4", "%i, '%s', '%s'" % (conf.on_hold_time, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "On hold"), "req_no", obs_req_nr)
						do_action.update_or_status("wait", obs_req_nr)
					except Exception,e:
						print e
						print clock.timename(), "The OR could not be put on hold since database was not updated."

	#				try:
	#					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Acquisition failed!",message="The robot was not able to grap the star in OR: %i \n\nThe OR will now be put on hold for at least 3 minutes from: %s...\n\nIf something else is in the que the robot will try that!!!" % (int(obs_req_nr), time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))
	#				except Exception,e:
	#					print e
	#					print clock.timename(), "The e-mail could not be send out."

					time.sleep(5)

					sys.exit()

			elif returned_val == 'go':
				print clock.timename(), "The object is now on the slit!"


		elif conf.do_acquisition != 1 and conf.move_motors == 1:	
			if conf.move_new_motors == 1:
				return_val = do_action.move_motors_star(tel_acq="no")
			else:
				return_val = do_action.move_motors(tel_acq="no")
			if return_val != 'done':
				print clock.timename(), "The motors were not moved!"
				print clock.timename(), "The observations were cancelled due to the above..."

				if conf.finish_off == 1:
					print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
					do_action.finishing_off()

				do_action.update_or_status("abort", obs_req_nr)
				do_action.update_or("constraint_4", "'DMC problem'", "req_no", obs_req_nr)
				sys.exit()
			else:
				print clock.timename(), "The motors have moved mirrors into position!"
			sys.stdout.flush()


	#				# Set the telescope to go to object and start tracking:
	#				returned_val = do_action.track_object(obs_req_nr)
	#				if returned_val == 'go':
	#					print clock.timename(), "The object are being tracked!"
	#				sys.stdout.flush()
	#
	#				try:
	#					tmp_time_str2 = datetime.datetime.strptime(str(obs_req_values["stop_window"]), "%Y-%m-%d %H:%M:%S")
	#					time_diff = tmp_time_str2 - datetime.datetime.utcnow()
	#				except Exception, e:
	#					print clock.timename(), e
	#					print clock.timename(), obs_req_values["stop_window"]
	#					lenght_ow = 0
	#				else:
	#					# Time until stop window is reached in seconds
	#					lenght_ow = int(time_diff.days) * (24.*3600.) + time_diff.seconds
	#
	#				end_time = time.time() + lenght_ow - float(obs_req_values["exp_time"]) - 180		# End time is now + lenght of observing window - the exposure time - overhead of three minutes. 
	#				print clock.timename(), "Time until script will stop trying to do acquisition: %s seconds" % (end_time - time.time())
	#				print clock.timename(), "End of start time is set to: ", datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
	#				sys.stdout.flush()
	#
	#				m3_reset = 0
	#				#if end_time - time.time() > float(obs_req_values["exp_time"]) + 180 + 180:		# sleeps for 180 seconds and an overhead of three minutes. 
	#				if end_time - time.time() > 200.0:		# sleeps for 200 seconds and an overhead of three minutes. 
	#					while time.time() < end_time:	
	#						if m3_reset == 0:
	#							# Rotate M3 to check if it was not located perfectly.
	#							try:
	#								comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")
	#								comm2tcs_write.SET_TSI().set_pointing_setup_use_port(param=1, sender="Observer")
	#								comm2tcs_write.SET_TSI().set_pointing_track(param=2,sender="Observer")					
	#								track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
	#								timeout = time.time() + 60
	#								while str(track_value) not in ['0', '0.0']:
	#									time.sleep(1.0)
	#									track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
	#									if time.time() > timeout:
	#										print clock.obstimeUT(), "The M3 movement has timed out..."
	#										break
	#								print clock.obstimeUT(), "Moved M3 to port: 1"
	#							except Exception,e:
	#								print clock.timename(), e
	#								print clock.timename(), "Could not rotate M3 to Nasmyth 2..."
	#							try:
	#								comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")
	#								comm2tcs_write.SET_TSI().set_pointing_setup_use_port(param=conf.m3_position, sender="Observer")
	#								comm2tcs_write.SET_TSI().set_pointing_track(param=2,sender="Observer")					
	#								track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
	#								timeout = time.time() + 60
	#								while str(track_value) not in ['0', '0.0']:
	#									time.sleep(1.0)
	#									track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
	#									if time.time() > timeout:
	#										print clock.obstimeUT(), "The M3 movement has timed out..."
	#										break
	#								print clock.obstimeUT(), "Moved M3 to port: ", conf.m3_position
	#							except Exception,e:
	#								print clock.timename(), e
	#								print clock.timename(), "Could not rotate M3 back to Nasmyth 1..."
	#
	#							# Start tracking the star again:
	#							try:
	#								comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Observer")
	#							except Exception,e:
	#								print clock.timename(), e
	#								print clock.timename(), "Could not start tracking the star again..."
	#
	#							m3_reset = 1
	#
	#						# Check if the object is too low:
	#
	#						object_altitude = song_star_checker.star_pos(site=m_conf.song_site).star_alt(star_ra=obs_req_values["right_ascension"], star_dec=obs_req_values["declination"])
	#						tel_pointing_alt = float(str(object_altitude).split(":")[0]) + float(str(object_altitude).split(":")[1]) / 60.
	#
	#						if tel_pointing_alt < 16.0:
	#							print clock.timename(), "The telescope was pointing too low: ", tel_pointing_alt
	#							if conf.finish_off == 1:
	#								print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
	#								do_action.finishing_off()
	#								do_action.update_or_status("abort", obs_req_nr)
	#								do_action.update_or("constraint_4", "'Insufficient time'", "req_no", obs_req_nr)
	#							sys.exit()	
	#
	#						# Check if the OR has been aborted:						
	#						try:
	#							or_status_now = get_or_status(obs_req_nr)
	#						except Exception,e:
	#							print clock.timename(), "Could not get or status..."
	#							print clock.timename(), e
	#						if or_status_now != "exec":
	#							print clock.timename(), "The OR has been aborted from elsewhere...!"
	#
	#							if conf.finish_off == 1:
	#								print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
	#								do_action.finishing_off()
	#
	#							sys.exit()													
	#
	#						print clock.timename(), "The script will sleep for 3 minutes and try again"
	#						sys.stdout.flush()
	#						time.sleep(180)
	#						print clock.timename(), "The telescope will now repoint to coordinates..."
	#						returned_val = do_action.track_object(obs_req_nr)
	#						if returned_val == 'go':
	#							print clock.timename(), "The object are being tracked!"
	#						sys.stdout.flush()
	#						returned_val = do_action.tel_acquisition()
	#						if returned_val == 'go':
	#							break
	#				else:
	#					print clock.timename(), "The observations were cancelled due to too little time to perform the observation..."
	#
	#					if conf.finish_off == 1:
	#						print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
	#						do_action.finishing_off()
	#
	#					do_action.update_or_status("abort", obs_req_nr)
	#					do_action.update_or("constraint_4", "'Insufficient time'", "req_no", obs_req_nr)
	#					sys.exit()					
	#
	#				if returned_val != 'go':
	#					print clock.timename(), "Acquisition failed!"
	#
	#					#send_song_mail.send_mail().sending_an_email(reciever=["jens","mads", "ditte", "vichi", "frank"],sender="SONG_MS",subject="Acquisition failed!",message="The robot was not able to grap the star and put it on the slit!\n\nMaybe the pointing model was bad in that area. It will now try to use the SkyCam to repoint.\n\nIf this does not help either maybe there are some clouds OR it could be a strange thing like the worng pointing model which is loaded.\nIf you can determine that there is no clouds (look at skycam image) and it could be the pointing model which is wrong do this: Log on to hw as obs. Type:\nsong_monitor -t\ntcs_comm_daemon -t	(You are sure, type Y)\ntcs_comm_daemon -s\nsong_monitor -s\n\nThis will restart the telescope communication deamen which loads the correct pointing model, if a wrong one was loaded before. Restarting the monitor will send an sms to the entire duty team.\n\nThe script will try this a couple of times and then abort the OR if it does not succeed.\n\nIf wind speeds are high and near the limit for observing (see web page) the reason for failing might be that the telescope was moved away from the pointing direction...")
	#					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Acquisition failed!",message="The robot was not able to grap the star and put it on the slit!\n\n")		
	#
	#					print clock.timename(), "The observations were cancelled due to the above..."
	#
	#					if conf.finish_off == 1:
	#						print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
	#						do_action.finishing_off()
	#
	#					do_action.update_or_status("abort", obs_req_nr)
	#					do_action.update_or("constraint_4", "'Acquisition failure'", "req_no", obs_req_nr)
	#					sys.exit()	


		try:
			do_action.starting_up()
		except Exception,e:
			print clock.timename(), "Sigu and Pugu did not get started!"

			if conf.finish_off == 1:
				print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
				do_action.finishing_off()

			sys.exit("The execution of the OR was cancelled!")
		sys.stdout.flush()

#	try:
#		do_action.snap_sigu_pugu()
#	except Exception, e:
#		print clock.timename(), e
#		print clock.timename(), "No sigu and pugu snapshots were acquired"

	else:
		if conf.move_motors == 1:	
			if conf.move_new_motors == 1:
				return_val = do_action.move_motors_star(tel_acq="no")
			else:
				return_val = do_action.move_motors(tel_acq="no")
			if return_val != 'done':
				print clock.timename(), "The motors were not moved!"
				print clock.timename(), "The observations were cancelled due to the above..."

				if conf.finish_off == 1:
					print clock.timename(), "Now doing stuff like stopping sigu and pugu and stopping telescope..."
					do_action.finishing_off()

				do_action.update_or_status("abort", obs_req_nr)
				do_action.update_or("constraint_4", "'DMC problem'", "req_no", obs_req_nr)
				sys.exit()
			else:
				print clock.timename(), "The motors have moved mirrors into position!"
			sys.stdout.flush()

	#		time.sleep(5)


	while do_action.slewing != 0 or do_action.motors_moving != 0:
		time.sleep(1.0)
		print clock.timename(), "Telescope and/or motors not ready yet..!"

	print clock.timename(), "Number of threads: ", threading.activeCount()	

	skycam2_derot_active = False
	try:
		t_left = obs_req_values["stop_window"] - datetime.datetime.utcnow()

		print clock.timename(), "Acquiring a SkyCam-2 image..."
	#	exptime = 0.003 * 10.0**(0.4 * float(obs_req_values["magnitude"]))		

		if obs_req_values["object_name"].lower() in conf.phot_stars:

			try:
				bla = set_skycam2_filter(int(conf.phot_stars[obs_req_values["object_name"].lower()]["filterpos"]))
			except Exception,e:
				print e

			if conf.phot_stars[obs_req_values["object_name"].lower()]["derot"] == True:
				try:
					skycam2_derot_start_pos = start_skycam2_derot()
				except Exception,e:
					print e	
				skycam2_derot_active = True
		
		#	et = 0.005 * 10.0**(0.4 * float(obs_req_values["magnitude"]))
			try:
				et = float(conf.phot_stars[obs_req_values["object_name"].lower()]["exptime"])	
			except Exception,e:
				print e
				et = 5		

			numberofimages = float(t_left.seconds) / (et + 3) # overhead 3 seconds
			print clock.timename(), "Number of SkyCam2 images to acquire: ", numberofimages

			xbegin = conf.phot_stars[obs_req_values["object_name"].lower()]["sub_im"][0]
			ybegin = conf.phot_stars[obs_req_values["object_name"].lower()]["sub_im"][1]
			width = conf.phot_stars[obs_req_values["object_name"].lower()]["sub_im"][2]
			height = conf.phot_stars[obs_req_values["object_name"].lower()]["sub_im"][3]

			bla = acquire_skycam2_phot(et, numberofimages, obs_req_nr, xbegin, ybegin, width, height)

		elif obs_req_values["object_name"].lower() != "moon":
			exptime = 10.
			bla = acquire_skycam2_image(exptime)

	except Exception,e:
		print e

	# Acquire spectras!
	if conf.acq_spectres == 1:
		try:
			returned_val = do_action.acquire_images(obs_req_nr)
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), "Error in acquire images function..."
			try:
				do_action.finishing_off()
			except Exception,e:					
				pass
			else:
				print clock.timename(), "Stopped the guider loop thread and finishing the script."
		else:
			if returned_val != 'done':
				print clock.timename(), "The observations were stopped due to the above..."
				#do_action.update_or_status("abort", obs_req_nr)
			else:
				print clock.timename(), "The observation request was completed correctly!"
				ret_val = do_action.update_or_status("done", obs_req_nr)
				if ret_val == 0:
					print clock.timename(), "Trying to update the status database again..."
					ret_val = do_action.update_or_status("done", obs_req_nr)

		sys.stdout.flush()


	### Here a check on what is next in the line could be inserted to optimize the code even further...
	### If we just observed in ThAr mode it might not be needed to do another ThAr at once again. 
	### If the object is the same and just inserted more than once - tracking and guiding should continue. 
	### If next OR is with another slit it could be set in motion here. 
	### If just finished OR was with Iodine and next is ThAr the Iodine cell could be set in motion here and ThAr lamp could be turned on.




##### The things below were commented out after implementation of letting the telescope track at ended observations to optimize when same object is observed after each other.

#	try:
#		child = subprocess.Popen("python /home/obs/programs/DMC/pst.py move -m2 -p2 ", shell=True) 
#	except Exception,e:
#		print clock.timename(), "Were not able to move to the acquisition mirror"
#		print clock.timename(), e


	if conf.finish_off == 1:
		print clock.timename(), "Now doing stuff like stopping sigu and pugu..."
		do_action.finishing_off()

	if skycam2_derot_active == True:
		bla = stop_skycam2_derot()
		bla = set_skycam2_derot_goto(skycam2_derot_start_pos)


	sys.stdout.flush()
	sys.exit()

if __name__ == "__main__":
	obs_req_nr = int(sys.argv[1])   
	EXECUTE_OR(obs_req_nr)



