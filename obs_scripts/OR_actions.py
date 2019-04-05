import sys
import os
import time
import xmlrpclib
import psycopg2
import get_db_values
import datetime
import comm2tcs_read
import comm2tcs_write
import song_timeclass
import numpy
import song_convert_coor
import slit_module
import pupil_module
import Set_M8
import datetime
import song_star_checker
import thread
import threading
import pyfits
import mfa
import image_smoother
import update_song_database
import song_checker_config
import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
import mfa_exposure
import set_ao
import OR_script_config as conf
import song_checker
import master_config as m_conf
import math
import read_value_db
import multiprocessing
import scipy.ndimage as ndim
import send_song_mail

cleaner = image_smoother.SMOOTH()

clock = song_timeclass.TimeClass()
coor_handle = song_convert_coor.COOR_CONVERTER()

sigu = slit_module.SIGU()
pugu = pupil_module.PUGU()
sun_handle = song_star_checker.sun_pos(m_conf.song_site)
checker_handle = song_checker.Checker()

########################################################################
########## TO BE SURE THAT PATHS ARE CORRECT ###########################

DMC_PATH =  "/home/obs/programs/DMC/"
ANDOR_PATH = "/home/madsfa/subversion/trunk/spec_ccd/"

ccd_server = xmlrpclib.ServerProxy('http://%s:%s' % (m_conf.ccd_server, m_conf.ccd_port))

########################################################################
########################################################################
sys.path.append(DMC_PATH) 
import pst		
import lamp
import nas
########################################################################

# Database values:
db_central = m_conf.db_c_host	# Central db machine
db_host =  m_conf.db_host	# Tenerife machine
db_user =  m_conf.db_user
db_password =  m_conf.db_password
db =  m_conf.or_db
db_table = m_conf.or_table
st_db =  m_conf.data_db
st_table =  m_conf.or_status_table

class DO_SOMETHING():
	def __init__(self, obs_req_nr):	
		self.obs_request_number = obs_req_nr
		self.number = 0

		# Create mask for determining the pupil flux:
		self.pugu_center_X = 110.0	# 110.0
		self.pugu_center_Y = 109.0	# 109.0

		self.base_focus_offset = 0.8

		radius_big = 64.0
		raidus_small = 15.0

		self.slewing = 0
		self.motors_moving = 0

		### size of binned images are: 216x216
		self.pugu_mask = numpy.zeros((216, 216)).astype('int')

		for x in range(self.pugu_mask.shape[0]):
			for y in range(self.pugu_mask.shape[0]):
				r = numpy.sqrt((x - self.pugu_center_X)**2.0 + (y - self.pugu_center_Y)**2.0)
				if r < radius_big and r > raidus_small:
					self.pugu_mask[x,y] = 1

		try:
			self.obs_req_values = self.get_or_values("obs_request_1", ["right_ascension", "declination", "ra_pm", "dec_pm", "object_name", "imagetype", "observer", "exp_time", "x_bin", "y_bin", "x_begin", "y_begin", "x_end", "y_end", "no_exp", "no_target_exp", "no_thar_exp", "amp_gain", "readoutmode", "iodine_cell", "obs_mode", "slit", "start_window", "stop_window", "project_name", "ang_rot_offset", "adc_mode", "epoch", "site", "project_id", "req_prio", "req_chain_previous", "req_chain_next", "magnitude", "constraint_2", "constraint_4", "constraint_5"], self.obs_request_number)
		except Exception, e:
			print clock.timename(), e
			time.sleep(10)	

			try:
				self.obs_req_values = self.get_or_values("obs_request_1", ["right_ascension", "declination", "ra_pm", "dec_pm", "object_name", "imagetype", "observer", "exp_time", "x_bin", "y_bin", "x_begin", "y_begin", "x_end", "y_end", "no_exp", "no_target_exp", "no_thar_exp", "amp_gain", "readoutmode", "iodine_cell", "obs_mode", "slit", "start_window", "stop_window", "project_name", "ang_rot_offset", "adc_mode", "epoch", "site", "project_id", "req_prio", "req_chain_previous", "req_chain_next", "magnitude", "constraint_2", "constraint_4", "constraint_5"], self.obs_request_number)		
			except Exception, e:
				print clock.timename(), e
				print clock.timename(), "Could not read OR values from database...."

		self.time_to_complete = float(self.obs_req_values["exp_time"])


	def read_o_star(self, o_star_name):
		try:
			sys.path.append(conf.o_star_dir)		
			template_conf = __import__(str(o_star_name) + "_o-star")

			self.time_to_complete = float(self.obs_req_values["no_exp"]) * float(self.obs_req_values["exp_time"]) + float(template_conf.ostar_num_exp) * float(template_conf.ostar_exptime_spec)

			self.obs_req_values["right_ascension"] = template_conf.ostar_ra_hours
			self.obs_req_values["declination"] = template_conf.ostar_dec_degrees
			self.obs_req_values["ra_pm"] = template_conf.ostar_pmra
			self.obs_req_values["dec_pm"] = template_conf.ostar_pmdec
			self.primary_target = self.obs_req_values["object_name"]
			self.obs_req_values["object_name"] = template_conf.ostar_name
			self.obs_req_values["exp_time"] = template_conf.ostar_exptime_spec
			self.obs_req_values["no_exp"] = template_conf.ostar_num_exp
			self.obs_req_values["magnitude"] = template_conf.ostar_vmagnitude

			if ":" in self.obs_req_values["right_ascension"]:
				self.obs_req_values["right_ascension"] = coor_handle.convert_ra(self.obs_req_values["right_ascension"],24)

			if ":" in self.obs_req_values["declination"]:
				self.obs_req_values["declination"] = coor_handle.convert_dec(self.obs_req_values["declination"])

		except Exception, e:
			print clock.timename(), e
			return 0

		return 1


	def re_read_or(self):
		try:
			self.obs_req_values = self.get_or_values("obs_request_1", ["right_ascension", "declination", "ra_pm", "dec_pm", "object_name", "imagetype", "observer", "exp_time", "x_bin", "y_bin", "x_begin", "y_begin", "x_end", "y_end", "no_exp", "no_target_exp", "no_thar_exp", "amp_gain", "readoutmode", "iodine_cell", "obs_mode", "slit", "start_window", "stop_window", "project_name", "ang_rot_offset", "adc_mode", "epoch", "site", "project_id", "req_prio", "req_chain_previous", "req_chain_next", "magnitude", "constraint_2", "constraint_4"], self.obs_request_number)
		except Exception, e:
			print clock.timename(), e
			time.sleep(10)	

			try:
				self.obs_req_values = self.get_or_values("obs_request_1", ["right_ascension", "declination", "ra_pm", "dec_pm", "object_name", "imagetype", "observer", "exp_time", "x_bin", "y_bin", "x_begin", "y_begin", "x_end", "y_end", "no_exp", "no_target_exp", "no_thar_exp", "amp_gain", "readoutmode", "iodine_cell", "obs_mode", "slit", "start_window", "stop_window", "project_name", "ang_rot_offset", "adc_mode", "epoch", "site", "project_id", "req_prio", "req_chain_previous", "req_chain_next", "magnitude", "constraint_2", "constraint_4"], self.obs_request_number)		
			except Exception, e:
				print clock.timename(), e
				print clock.timename(), "Could not read OR values from database...."

		self.obs_req_values["constraint_2"] = 0
		self.time_to_complete = float(self.obs_req_values["no_exp"]) * float(self.obs_req_values["exp_time"])

		return 1


	def get_db_values(self, table_name, fields=[]):
		conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, st_db, db_user, db_password))
		curr = conn.cursor()
		try:
			return_value = get_db_values.db_connection().get_fields(curr, table_name, fields)
		except Exception as e:
			conn.rollback()
			return_value = e
		curr.close()
	     	conn.close() 
		return return_value

	def get_or_values(self, table_name, fields=[], obs_req_nr=""):
		"""
		 @brief: This function collects data from given table in database to a specific observation request.
		 @param req_no: The observation request number.
		"""

		#conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, db, db_user, db_password))
		conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s' connect_timeout=5" % (db_host, db, db_user, db_password))	#has worked for a long time with "central"

		curr = conn.cursor()

		field_str = ''
		for field in fields:
			field_str += field
			field_str += ','
		field_str = field_str[0:-1]

		stmt = 'SELECT %s FROM %s WHERE req_no = %s' % (field_str, table_name, obs_req_nr)
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

	def get_or_status(self, req_no=""):
		"""
		 @brief: This function collects data from given table in database to a specific observation request.
		 @param req_no: The observation request number.
		"""
		conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s' connect_timeout=5" % (db_host, st_db, db_user, db_password))
		curr = conn.cursor()

		stmt = 'SELECT status FROM obs_request_status_1 WHERE req_no = %s' % (req_no)
		curr.execute(stmt)
		results = curr.fetchone()
		curr.close()
		conn.close()

		return results[0]

	def update_or_status(self, status, obs_req_nr):
		"""
		@brief Update the status.
		Updates the status in the database. Since the req_no is locked to the instance of the ObservationStatus object, all you need to supply here is the new status. The ins_at-field in the database will be updated as well.
		    
		@param status The new value for the status.
		@exception AssertionError Bad value of status provided.
		
		"""
		if obs_req_nr == "":
			return 0	

		conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s' connect_timeout=5" % (db_host, st_db, db_user, db_password))

		if status not in list(['wait', 'exec', 'done', 'abort', 'unknown']):
		    raise AssertionError("Could not update status. The values '%s' is not among the allowed values." % (status))
		curr = conn.cursor()
		try:
		    stmt = "UPDATE %s SET status='%s', ins_at='%s' WHERE req_no=%s" % (st_table, status, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), obs_req_nr)
		    curr.execute(stmt)
		except Exception as e:
		    conn.rollback()
		    print clock.timename(), "Could not create status in the database. Changes to the status-data has been rolled back."
		    raise e

		conn.commit()
		curr.close()
	     	conn.close()  
		return 1

	def update_or(self, parameters="", ins_values="", table_id="req_no", req_no=""):
		"""
		@brief:		    
		@param: 
		
		"""
		if req_no == "":
			stmt_up = "UPDATE obs_request_1 SET (%s) = (%s) WHERE %s = (SELECT max(%s) FROM obs_request_1)" % (str(parameters), str(ins_values), str(table_id), str(table_id))
		else:
			stmt_up = "UPDATE obs_request_1 SET (%s) = (%s) WHERE %s = %s" % (str(parameters), str(ins_values), str(table_id), str(req_no))

		try:
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s' connect_timeout=5" % (db_central, db, db_user, db_password))
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

	def insert_obs_request_status(self, obs_req_nr):
		"""
		@brief: Insert the status of the newly inserted OR.
		
		"""
		or_status_values = "( %i, '%s', '%s' )" % (obs_req_nr, "wait", time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))


		conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s' connect_timeout=5" % (db_host, st_db, db_user, db_password))
		curr = conn.cursor()

		params = '(req_no, status, ins_at)'

		try:
			stmt = "INSERT INTO obs_request_status_1 %s VALUES %s" % (params, or_status_values)
			curr.execute(stmt)
		except Exception as e:
			conn.rollback()
			return_value = e
	 		print clock.timename(), "Could not create status in the database. Changes to the status-data has been rolled back."
			raise e
		else:
			return_value = 'done'
		  

		conn.commit()
		curr.close()
	     	conn.close()  
		return return_value


	########################################################################

	def check_parameters(self, obs_req_nr):

		return_string = ''
		if self.obs_req_values["exp_time"] < 0.0 or self.obs_req_values["exp_time"] > 3600.0:
			return_string = return_string + " The exposure time was not in the range: 0-3600 seconds"
	
		if self.obs_req_values["readoutmode"] not in [0,1,2,3]:
			return_string = return_string + " The readout mode was not one of: 0,1,2,3"

		if self.obs_req_values["amp_gain"] not in [0,1,2]:
			return_string = return_string + " The pre amplifier gang mode was not one of: 0,1,2"
	
		if self.obs_req_values["x_bin"] not in [1,2,4,8,16]:
			return_string = return_string + " The horizontal (x) binning was not one of: 1,2,4,8,16"
	
		if self.obs_req_values["y_bin"] not in [1,2,4,8,16]:
			return_string = return_string + " The vertical (y) binning was not one of: 1,2,4,8,16"

		if self.obs_req_values["x_begin"] <= 0 or self.obs_req_values["x_begin"] > 2087:
			return_string = return_string + " The horizontal start pixel must be in the range: 1-2087"

		if self.obs_req_values["x_end"] <= 1 or self.obs_req_values["x_end"] > 2088:
			return_string = return_string + " The horizontal end pixel must be in the range: 2-2088"

		if self.obs_req_values["y_begin"] <= 0 or self.obs_req_values["y_begin"] > 2047:
			return_string = return_string + " The vertical start pixel must be in the range: 1-2047"

		if self.obs_req_values["y_end"] <= 1 or self.obs_req_values["y_end"] > 2048:
			return_string = return_string + " The vertical end pixel must be in the range: 2-2048"

		if self.obs_req_values["imagetype"].lower() not in ["bias","dark","flat","flati2","test","star","thar","sun", "suni2"]:
			return_string = return_string + " The imagetype must be one of: [Bias, Dark, Flat, Flati2, Test, Star, ThAr, Sun, Suni2]"
	
		if float(self.obs_req_values["right_ascension"]) < 0.0 or float(self.obs_req_values["right_ascension"]) > 24.0:
			return_string = return_string + " The right ascension was not in the range: 0-24"
	
		if float(self.obs_req_values["declination"]) < -90.0 or float(self.obs_req_values["declination"]) > 90.0:
			return_string = return_string + " The declination was not in the range: -90-90"

		if self.obs_req_values["magnitude"] > 15.0:
			return_string = return_string + " The object is too faint. The magnitude must be in brighter than 15."

		print clock.timename(), "Object name = ", self.obs_req_values["object_name"]
		if self.obs_req_values["object_name"] == None:
			return_string = return_string + " No object name was specified."

		#print "Observer = ", self.obs_req_values["observer"]
		if self.obs_req_values["observer"] == None:
			return_string = return_string + " No observer name was specified."

		#print "Project name = ", self.obs_req_values["project_name"]
		if self.obs_req_values["project_name"] == None:
			return_string = return_string + " No project name was specified."

		if self.obs_req_values["project_id"] < 0:
			return_string = return_string + " The project id must be a positive integer."

		if self.obs_req_values["no_exp"] < 1 or self.obs_req_values["no_exp"] > 1000:
			return_string = return_string + " The number of exposures must be in the range 1-1000"

		if self.obs_req_values["no_target_exp"] < 0 or self.obs_req_values["no_target_exp"] > 1000:
			return_string = return_string + " The number of target exposures must be in the range 0-1000"

		if self.obs_req_values["no_thar_exp"] < 0 or self.obs_req_values["no_thar_exp"] > 1000:
			return_string = return_string + " The number of ThAr exposures must be in the range 0-1000"

		if self.obs_req_values["iodine_cell"] not in [1,2,3]:
			return_string = return_string + " The iodine cell must be on of [1: dummy, 2: Free, 3: iodine]"

		if self.obs_req_values["slit"] not in [1,2,3,4,5,6,7,8,9]:
			return_string = return_string + " The slit number must be on of [1,2,3,4,5,6,7,8,9]"

		if self.obs_req_values["obs_mode"].lower() not in ["iodine", "none-iodine", "template"]:
			return_string = return_string + " The obs mode must be on of [iodine, none-iodine, template]"

		if self.obs_req_values["ang_rot_offset"] < 0 or self.obs_req_values["ang_rot_offset"] > 360:
			return_string = return_string + " The rotation angle offset must be in the range 0-360"

		if self.obs_req_values["adc_mode"].lower() not in ["false", "true"]:
			return_string = return_string + " The adc mode must be on of [false, true]"

		if self.obs_req_values["epoch"] <= 1999 or self.obs_req_values["epoch"] >= 2100:
			return_string = return_string + " The epoch must be in the range 2000-2100"

		if self.obs_req_values["site"] not in [0,1,2,3,4,5,6,7,8]:
			return_string = return_string + " The site must be in the range 0-8"

		if self.obs_req_values["req_prio"] < 0 or self.obs_req_values["req_prio"] > 100:
			return_string = return_string + " The priority must be in the range 0-100"

		try:
			tmp_time_str1 = datetime.datetime.strptime(str(self.obs_req_values["start_window"]), "%Y-%m-%d %H:%M:%S")
		except Exception, e:
			print clock.timename(), self.obs_req_values["start_window"]
			return_string = return_string + " The observation window start time was not in the format 'yyyy-mm-dd HH:MM:SS'!"
			self.update_or("constraint_4", "'Wrong time format in OR'", "req_no", self.obs_request_number)
		try:
			tmp_time_str2 = datetime.datetime.strptime(str(self.obs_req_values["stop_window"]), "%Y-%m-%d %H:%M:%S")
			time_diff = tmp_time_str2-datetime.datetime.utcnow()-datetime.timedelta(seconds=float(self.obs_req_values['exp_time']))
		except Exception, e:
			print clock.timename(), self.obs_req_values["stop_window"]
			return_string = return_string + " The observation window stop time was not in the format 'yyyy-mm-dd HH:MM:SS'!"
			self.update_or("constraint_4", "'Wrong time format in OR'", "req_no", self.obs_request_number)
		else:
			time_diff_in_hours = (int(time_diff.days) + time_diff.seconds / (24.*3600.)) * (24.)
			print clock.timename(), "Time after first exposure to end of obs window: %02i:%02i" % (numpy.floor(time_diff_in_hours), round(float(time_diff_in_hours - numpy.floor(time_diff_in_hours) )*60.))
			if (int(time_diff.days) + time_diff.seconds / (24.*3600.)) < 0:
				return_string = return_string + " The observation window has past!"
				self.update_or("constraint_4", "'Insufficient time'", "req_no", self.obs_request_number)

		time_error = ''
		try:
			time_window = datetime.datetime.strptime(self.obs_req_values["stop_window"], "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(self.obs_request_config.start_window, "%Y-%m-%d %H:%M:%S")
		except Exception, e:
			time_error = e
		if time_error == '':
			if time_window.days < 0:
				return_string = return_string + " The observation window start time was later than the stop time!"	
		
		if type(self.obs_req_values["req_chain_previous"]) is not int:
			return_string = return_string + " The request chain previous value must be an integer"

		if type(self.obs_req_values["req_chain_next"]) is not int:
			return_string = return_string + " The request chain next value must be an integer"


		#### Check if wind is too high coming from the stars position:
		#object_az = song_star_checker.star_pos(site=1).star_az(star_ra=self.obs_req_values["right_ascension"], star_dec=self.obs_req_values["declination"])
		#object_az = float(str(object_az).split(":")[0])
		#print "The star is located at azimuth: ", object_az
		
		#try:
		#	weather_output = self.get_db_values("weather_station", ["ins_at", "wxt520_wind_speed", "wxt520_wind_direction", "wxt520_wind_avg", "wxt520_wind_avgdir"])
		#except Exception, e:
		#	print "Error: ", e		

		#if float(weather_output["wxt520_wind_avg"]) > song_checker_config.max_w_speed_into and numpy.abs(object_az - float(weather_output["wxt520_wind_avgdir"])) < song_checker_config.angle_into:
		#	print "The wind speed was too high in the observing direction..."
		#	return_string = return_string + " Wind speed too high in direction of star!\n"

		return return_string


	def check_obs_window(self, req_no):
		# Check if the time is inside the obs window.	

		if datetime.datetime.utcnow() >= self.obs_req_values["start_window"] and datetime.datetime.utcnow() < self.obs_req_values["stop_window"]:
			return 'go'
		else:
			return 'no_go'

	def pst_motor(self, m, p):
		pst.PST().move(int(m),int(p))
		return 1

	def calib_lamp(self, lamp_name, switch):
		if switch == "on":
			try:
				lamp.Lamp(lamp=lamp_name).set_on()	
			except Exception,e:
				print clock.timename(), "One of the lamps was not switched correctly"
		elif switch == "off":
			try:
				lamp.Lamp(lamp=lamp_name).set_off()	
			except Exception,e:
				print clock.timename(), "One of the lamps was not switched correctly"

	def move_motors_star(self,tel_acq="no"):

		### Check which obs mode the OR defines and move motors...

		self.motors_moving = 1

		try:
			if conf.use_sigu == 1:
				val = sigu.exec_action("pause")	
				if val != "done":
					return "no_go"
			if conf.use_pugu == 1:
				val = pugu.exec_action("pause")	
				if val != "done":
					return "no_go"
		except Exception, e:
			print clock.timename(), "An error occured when trying to move the motors: ", e
			return e

		try:
			thar_lamp = threading.Thread(target=self.calib_lamp, args=("thar", "off")) # Move Calibration mirror out of the path
			thar_lamp.start()

			halo_lamp = threading.Thread(target=self.calib_lamp, args=("halo", "off")) # Move Calibration mirror out of the path
			halo_lamp.start()

			#lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point
			#lamp.Lamp(lamp='halo').set_off()	# Might change Lamp to LAMP at some point
		except Exception,e:
			print clock.timename(), "One of the lamps was not switched correctly"

	#	pst.PST().move(4,1) 			# Move Calibration mirror out of the path
		calib_s = threading.Thread(target=self.pst_motor, args=(4,1)) # Move Calibration mirror out of the path
		calib_s.start()

		if self.obs_req_values["obs_mode"] == 'iodine':
		#	pst.PST().move(3,int(self.obs_req_values["iodine_cell"])) 			# Move IODINE cell into the light path
			iodine_s = threading.Thread(target=self.pst_motor, args=(3,int(self.obs_req_values["iodine_cell"]))) # Move Iodine cell into light path
			iodine_s.start()
		if self.obs_req_values["obs_mode"] == 'none-iodine' or self.obs_req_values["obs_mode"] == 'template':
		#	pst.PST().move(3,2) 			# Move IODINE cell out of the light path
			iodine_s = threading.Thread(target=self.pst_motor, args=(3,2)) # Move Iodine cell out of light path
			iodine_s.start()

		### These are the same for all types of observations...
	#	pst.PST().move(1,4) 					# Move Filter wheel to position 4 (Free)
		filter_w = threading.Thread(target=self.pst_motor, args=(1,4)) # Move filter
		filter_w.start()	

	#	pst.PST().move(6,int(self.obs_req_values["slit"])) 				# Move slit to right position
		slit_s = threading.Thread(target=self.pst_motor, args=(6,int(self.obs_req_values["slit"]))) # Move slit
		slit_s.start()

		if tel_acq != "yes":
		#	pst.PST().move(2,3) 					# Move Mirror slide to Beam Splitter cube position				
			beam_s = threading.Thread(target=self.pst_motor, args=(2,3)) # Move Mirror slide to Beam Splitter cube position
			beam_s.start()	
		else:
		#	pst.PST().move(2,3) 					# Move Mirror slide to Beam Splitter cube position				
			beam_s = threading.Thread(target=self.pst_motor, args=(2,2)) # Move Mirror slide to Beam Splitter cube position
			beam_s.start()	

		while threading.activeCount() > 1:
			time.sleep(1)
			print clock.timename(), "Still moving motors... ", threading.activeCount()
			sys.stdout.flush()

		print clock.timename(), "Number of threads: ", threading.activeCount()			

		self.motors_moving = 0
		return 'done'


	def move_motors(self, imagetype="", obs_mode="", tel_acq=""):
	
		### Check which obs mode the OR defines and move motors...
		self.motors_moving = 1

		try:
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
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), "Could not check status of motors from database..."


		try:

			iodine_cell = int(self.obs_req_values["iodine_cell"])			# Position of the iodine cell (In/Out/Dummy)
			slit = self.obs_req_values["slit"] 					# Which slit number to use
			if imagetype == "":
				imagetype = self.obs_req_values["imagetype"] 			# Type of image to be observed	 
			if obs_mode == "":
				obs_mode = self.obs_req_values["obs_mode"] 			# Observation mode (iodine or none-iodine)

			if conf.use_sigu == 1:
				val = sigu.exec_action("pause")	
				if val != "done":
					return "no_go"
			if conf.use_pugu == 1:
				val = pugu.exec_action("pause")	
				if val != "done":
					return "no_go"

			if imagetype.lower() == 'bias':
				try:
					### Then it does not matter which positions the motors are in...
					# The lamps are just turned off to be sure...
					lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point
					lamp.Lamp(lamp='halo').set_off()	# Might change Lamp to LAMP at some point
				except Exception,e:
					print clock.timename(), "One of the lamps was not switched correctly"
	
			elif imagetype.lower() == 'flat':
				try:
					lamp.Lamp(lamp='halo').set_on()		# Might change Lamp to LAMP at some point
					lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point
				except Exception,e:
					print clock.timename(), "One of the lamps was not switched correctly"
				pst.PST().move(3,2) 			# Move IODINE cell out of path
				pst.PST().move(4,1) 			# Move Calibration mirror out of the path

			elif imagetype.lower() == 'flati2':
				try:
					lamp.Lamp(lamp='halo').set_on()		# Might change Lamp to LAMP at some point
					lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point
				except Exception,e:
					print clock.timename(), "One of the lamps was not switched correctly"
				pst.PST().move(3,iodine_cell) 			# Move IODINE cell into light path
				pst.PST().move(4,1) 			# Move Calibration mirror out of the path

			elif imagetype.lower() == 'star':
				try:
					lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point
					lamp.Lamp(lamp='halo').set_off()	# Might change Lamp to LAMP at some point
				except Exception,e:
					print clock.timename(), "One of the lamps was not switched correctly"

				pst.PST().move(4,1) 			# Move Calibration mirror out of the path

				if obs_mode == 'iodine':
					pst.PST().move(3,iodine_cell) 			# Move IODINE cell into the light path
				if obs_mode == 'none-iodine':
					pst.PST().move(3,2) 			# Move IODINE cell out of the light path
				if obs_mode == 'template':
					pst.PST().move(3,2) 			# Move IODINE cell out of the light path

			elif imagetype.lower() == 'thar':
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
				pst.PST().move(4,4) 			# Move Calibration mirror to Sun Fiber position

			elif imagetype.lower() == 'suni2':
				try:
					lamp.Lamp(lamp='thar').set_off()	# Might change Lamp to LAMP at some point
					lamp.Lamp(lamp='halo').set_off()	# Might change Lamp to LAMP at some point
				except Exception,e:
					print clock.timename(), "One of the lamps was not switched correctly"
				pst.PST().move(3,iodine_cell) 			# Move IODINE cell into light path
				pst.PST().move(4,4) 			# Move Calibration mirror to Sun Fiber position

			elif imagetype.lower() == 'test':
				# Do not move anything. 
				print clock.timename(), "Manual mode was desired and no motors were moved!"

############ NOT NEEDED ANY MORE AFTER MOVING THE NASMYTH BOX #############################
#			try:
#				nas.Nasmyth().move(3,2) 				# Move beamselector in nasmyth box to send light through coude.
#			except Exception,e:
#				print clock.timename(), "Could not connect to the nasmyth server"
#				print clock.timename(), "We will continue and hope that the light goes to the coude if not the acquisition will stop the observations"

			### These are the same for all types of observations...
			pst.PST().move(1,4) 					# Move Filter wheel to position 4 (Free)
			if tel_acq != "yes":
				pst.PST().move(2,3) 					# Move Mirror slide to Beam Splitter cube position
			else:
				pst.PST().move(2,2) 					# Move Mirror slide to Beam Splitter cube position				
			
			### These are defined by the user...

			pst.PST().move(6,int(slit)) 				# Move slit to right position


			if str(self.obs_req_values["object_name"]).lower() == "sun" and imagetype.lower() == 'star':

				print clock.timename(), "Setting sigu for the Sun in move motors function"
				try:
					sigu.exec_action("moveto", [str(conf.m8_pos_x), str(conf.m8_pos_y)])					
					sigu.exec_action("texp", [str(conf.sigu_texp_sun)])
					pugu.exec_action("texp", [str(conf.pugu_texp_sun)])
				except Exception,e:
					print e
					print "Could not move sigu to sun postion"

			else:
				Set_M8.set_m8_pos()

		except Exception, e:
			print clock.timename(), "An error occured when trying to move the motors: ", e
			return e
		self.motors_moving = 0
		return 'done'


	def move_motors_thar(self):

		print clock.timename(), "Stopping guiders while doing a ThAr spectrum"

		if conf.use_sigu == 1:
			val = sigu.exec_action("pause")	
			if val != "done":
				return "no_go"

			val = sigu.exec_action("stop")	
			if val != "done":
				return "no_go"

		if conf.use_pugu == 1:
			val = pugu.exec_action("pause")	
			if val != "done":
				return "no_go"

			val = pugu.exec_action("stop")	
			if val != "done":
				return "no_go"

		print clock.timename(), "Guiders should now be stopped"

		try:
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
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), "Could not check status of motors from database in ThAr function..."
	
	#	try:
	#		lamp.Lamp(lamp='thar').set_on()	# Might change Lamp to LAMP at some point
	#		lamp.Lamp(lamp='halo').set_off()	# Might change Lamp to LAMP at some point
	#	except Exception,e:
	#		print clock.timename(), "One of the lamps was not switched correctly" 

		thar_lamp = threading.Thread(target=self.calib_lamp, args=("thar", "on")) # Move Calibration mirror out of the path
		thar_lamp.start()

		halo_lamp = threading.Thread(target=self.calib_lamp, args=("halo", "off")) # Move Calibration mirror out of the path
		halo_lamp.start()

		iod_cell = threading.Thread(target=self.pst_motor, args=(3,2)) # Move Iodine cell out of light path
		iod_cell.start()	

		calib_slide = threading.Thread(target=self.pst_motor, args=(4,3)) # Move Calibration mirror to ThAr position
		calib_slide.start()

		filter_wheel = threading.Thread(target=self.pst_motor, args=(1,4)) # Move Filter wheel to position 4 (Free)
		filter_wheel.start()

		beam_slide = threading.Thread(target=self.pst_motor, args=(2,3)) # Move Mirror slide to Beam Splitter cube position
		beam_slide.start()

		slit_slide = threading.Thread(target=self.pst_motor, args=(6,int(self.obs_req_values["slit"] ))) # Move to slit
		slit_slide.start()	

		while threading.activeCount() > 1:
			time.sleep(1)
			print clock.timename(), "Still moving motors thar... ", threading.activeCount()
			sys.stdout.flush()

		if str(self.obs_req_values["object_name"]).lower() == "sun":
			print clock.timename(), "Setting sigu for the Sun in ThAr function"
			try:
				sigu.exec_action("moveto", [str(conf.m8_pos_x), str(conf.m8_pos_y)])					
				sigu.exec_action("texp", [str(conf.sigu_texp_sun)])
				pugu.exec_action("texp", [str(conf.pugu_texp_sun)])
			except Exception,e:
				print e
				print "Could not move sigu to sun postion"
		else:
			M8_val = Set_M8.set_m8_pos()

		print clock.timename(), "Number of threads: ", threading.activeCount()

		print clock.timename(), "The mirrors are in position for ThAr spectrum"
		
#		time.sleep(5)

		return 1

	def move_motors_for_acq(self):

		print clock.timename(), "Moving to star light"
		try: 
			pst.PST().move(4,1) 	# Move to star light
		except Exception, e:
			return "no_go"

		print clock.timename(), "Moving acquisition mirror into position"
		try: 
			pst.PST().move(2,2) 
		except Exception, e:
			return "no_go"

		return "go"

	def tel_acquisition(self):
		### Sets the beam on the slit.
	
		if self.obs_req_values["magnitude"] <= 1.0:
			texp = "0.01"
		elif self.obs_req_values["magnitude"] > 1.0 and self.obs_req_values["magnitude"] <= 2.0:
			texp = "0.05"
		elif self.obs_req_values["magnitude"] > 2.0 and self.obs_req_values["magnitude"] <= 3.0:
			texp = "0.08"
		elif self.obs_req_values["magnitude"] > 3.0 and self.obs_req_values["magnitude"] <= 4.0:
			texp = "0.1"
		elif self.obs_req_values["magnitude"] > 4.0 and self.obs_req_values["magnitude"] <= 5.0:
			texp = "0.3"
		elif self.obs_req_values["magnitude"] > 5.0 and self.obs_req_values["magnitude"] <= 6.0:
			texp = "0.5"
		elif self.obs_req_values["magnitude"] > 6.0 and self.obs_req_values["magnitude"] <= 8.0:
			texp = "1.0"
		elif self.obs_req_values["magnitude"] > 8.0:
			texp = "2.0"
	
		val = sigu.exec_action("texp", [texp])	
		if val != "done":
			print clock.timename(), " SIGU failed to set the exposure time"
			return "no_go"


		val = sigu.exec_action("moveto", ["idle"])
	
		if val != "done":
			print clock.timename(), " SIGU failed to moveto idle"
			return "no_go"


		val = pugu.exec_action("moveto", ["idle"])	
#		if val != "done":
#			return "no_go"

		print clock.timename(), "Moving acquisition mirror into position"
		try: 
			pst.PST().move(2,2) 
		except Exception, e:
			return "no_go"
		

		print clock.timename(), "Acquiring a snapshot of sigu just before sigu acquire"
		try: 
			self.snap_sigu()
		except Exception, e:
			return "no_go"
		

		print clock.timename(), "Sigu start acquire..."
		val = sigu.exec_action("acquire")	
		print clock.timename(), val
		if val != "succes":
			print clock.timename(), "Sigu acquire again..."
			val = sigu.exec_action("acquire")	
			print clock.timename(), val	
			if val != "succes":
				return "no_go"

#		time.sleep(10)	# sleeps to make sure it is done

		print clock.timename(), "Acquiring a snapshot of sigu just after sigu acquire"
		try: 
			self.snap_sigu()
		except Exception, e:
			return "no_go"

		print clock.timename(), "Moving beamsplitter into light path"
		try: 
			pst.PST().move(2,3) 
		except Exception, e:
			return "no_go"

#		time.sleep(5)	# sleeps to make sure it is done


#		try:
#			val = sigu.exec_action("pointing", ["disable"])	
#		except Exception,e:
#			print e
#			print "pointing disabled failed."	

		return "go"


	def track_object(self, req_no):
		#########################################################
		########   Here some initial checks will be made  #######
		#########################################################

		self.slewing = 1
		
		site_value = m_conf.song_site

		ra_object = self.obs_req_values["right_ascension"]
		dec_object = self.obs_req_values["declination"]
		ra_pm = self.obs_req_values["ra_pm"]
		dec_pm = self.obs_req_values["dec_pm"]
	

		print clock.timename(), "RA PM from database: ", ra_pm
		print clock.timename(), "DEC PM from database: ", dec_pm

		#obj_right_ascension = coor_handle.convert_ra(self.obs_request_config.right_ascension,24) # Convert coordinates to decimal hours
		#obj_declination = coor_handle.convert_dec(self.obs_request_config.declination)# Convert coorinates to decimal degrees

		#ra_object = obj_right_ascension		
		#dec_object = obj_declination		

		moon_handle = song_star_checker.moon_pos(site=site_value)
		sun_handle = song_star_checker.sun_pos(site=site_value)
		star_handle = song_star_checker.star_pos(site=site_value)

		moon_alt = moon_handle.moon_alt()
		print clock.timename(), "The altitude of the Moon: ", moon_alt
		moon_phase = moon_handle.moon_phase()
		print clock.timename(), "The phase of the Moon: ", moon_phase

		object_alt = star_handle.star_alt(ra_object,dec_object)
		print clock.timename(), "Objects altitude: ", object_alt
		moon_dist = moon_handle.moon_dist(ra_object,dec_object)
		print clock.timename(), "Distance from Moon to Object: ", moon_dist
		sun_dist = sun_handle.sun_dist(ra_object,dec_object)
		print clock.timename(), "Distance between Sun and Object: ", sun_dist

		sun_alt = sun_handle.sun_alt()
		print clock.timename(), "Suns altitude: ", sun_alt
		if float(str(object_alt).split(":")[0]) < m_conf.telescope_min_altitude:
			self.update_or("constraint_4", "'Object too low'", "req_no", req_no)
			return "no_go"

		if float(str(moon_dist).split(":")[0]) < m_conf.tel_dist_to_moon:
			self.update_or("constraint_4", "'Moon too close'", "req_no", req_no)
			return "no_go"

		if float(str(sun_dist).split(":")[0]) < m_conf.tel_dist_to_sun:
			self.update_or("constraint_4", "'Sun too close'", "req_no", req_no)
			return "no_go"

		print clock.timename(), "The object is observable!!!"

		#### Test if the telescope is currently tracking. 
		track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Observer")
		motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer") 
		print clock.timename(), "The motion state of the telescope is currently: ", motion_state

		if float(track_value) == float(1.0):
			print clock.timename(), "Stop tracking..."
			track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")

		# Make sure focus sync mode is set:
		print clock.timename(), "Setting focus syncmode to 67"
		comm2tcs_write.SET_TSI().set_pointing_setup_focus_syncmode(param=67, sender="Observer")


		# Set ZD and AZ offsets to zero:
		current_az_offset = float(comm2tcs_read.GET_TSI().get_position_instrumental_az_offset(sender="Observer"))
		current_zd_offset = float(comm2tcs_read.GET_TSI().get_position_instrumental_zd_offset(sender="Observer"))

#### Offsets are set in the config file. When everything is fine these offsets should be 0.0
		comm2tcs_write.SET_TSI().set_position_instrumental_az_offset(param=float(conf.tel_az_offset),sender="Observer")
		comm2tcs_write.SET_TSI().set_position_instrumental_zd_offset(param=float(conf.tel_zd_offset),sender="Observer")

		print clock.timename(), "Zenith distance and Azimuth offsets has been set!"

		print clock.timename(), "Setting M3 to coude port"
		comm2tcs_write.SET_TSI().set_pointing_setup_use_port(param=conf.m3_position,sender="Observer")	

		sync_mode = ["Off", "Fixed position", "Sync discrete", "Sync discret + offset", "Continues sync", "Continues sync + offset"]
		dome_sync_mode_pre = int(comm2tcs_read.GET_TSI().get_pointing_setup_dome_syncmode())
		print clock.timename(), "The dome sync mode was set to: [ %s ]" % (sync_mode[dome_sync_mode_pre])
		if dome_sync_mode_pre != int(conf.dome_syncmode_value):
			print clock.timename(), "Now setting the dome to sync mode: [ %s ]" % (str(sync_mode[conf.dome_syncmode_value]))
			comm2tcs_write.SET_TSI().set_pointing_setup_dome_syncmode(param=conf.dome_syncmode_value, sender="Observer")

		try:
			print clock.timename(), "Setting dome offsets to 0.0"			# Added 2016-01-11
			comm2tcs_write.SET_TSI().set_pointing_setup_dome_offset(param=0.0,sender="Observer")	# Added 2016-01-11
			print clock.timename(), "Setting dome deviation to maximum 5.0 degrees"			# Added 2016-01-12
			comm2tcs_write.SET_TSI().set_pointing_setup_dome_max_deviation(param=conf.dome_max_deviation,sender="Observer")	# Added 2016-01-12
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), "Could not set parameters for the dome sync..."

	######################################    
	###### RA PROPER MOTION CONVERTION #######
	######################################
		#print "Setting RA Proper motion..."		
		ra_pm = (float(ra_pm) / (1000. * 3600. * 15. ))
		comm2tcs_write.SET_TSI().set_object_equatorial_ra_pm(param=0.0, sender="Observer")
	######################################
	###### DEC PROPER MOTION CONVERTION #######
	######################################
		#print "Setting DEC Proper motion..."
		dec_pm = (float(dec_pm) / (1000. * 3600.))
		comm2tcs_write.SET_TSI().set_object_equatorial_dec_pm(param=0.0, sender="Observer")	
	######################################

		###### Difference in time from epoch 2000 to now
		start_date = datetime.datetime(2000, 1, 1, 0, 0)
		end_date = datetime.datetime.utcnow()
		difference  = end_date - start_date
		difference_in_years = (difference.days + difference.seconds/86400.)/365.2425

		print clock.timename(), "PM difference in years: ", difference_in_years

		### Add pm to coorinates.... ??? Maybe the telescope wants that...???
		print clock.timename(), "RA PM applied: ", float(ra_pm) * float(difference_in_years)
		print clock.timename(), "DEC PM applied: ", float(dec_pm) * float(difference_in_years)

		ra_object = float(ra_object) + (float(ra_pm) * float(difference_in_years))
		dec_object = float(dec_object) + (float(dec_pm) * float(difference_in_years))

		print clock.timename(), "Setting RA... to %f" % ra_object
		print clock.timename(), "Setting RA... to %s" % coor_handle.convert_ra(ra_object,24)
		comm2tcs_write.SET_TSI().set_object_equatorial_ra(param=float(ra_object),sender="Observer")		
		print clock.timename(), "Setting DEC... to %f" % dec_object
		print clock.timename(), "Setting DEC... to %s" % coor_handle.convert_dec(dec_object)
		comm2tcs_write.SET_TSI().set_object_equatorial_dec(param=float(dec_object),sender="Observer")

		print clock.timename(), "Now the telescope will slew to the coordinates and start tracking"
		value = comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Observer")
		if value != "done":
			self.update_or("constraint_4", "'Tracking problem'", "req_no", req_no)
			return "no_go"

############################################################################################################################
#		self.ao_and_focus_adjusted = 0
#		################ Adjust AO and Focus while slewing ################################
#		def adjust_ao_and_focus(obj_alt):
#			self.ao_and_focus_adjusted = 2
#			ao_ret_val = set_ao.main(value = obj_alt)
#			if ao_ret_val == "done":
#				print  clock.timename(), "AO and focus is now adjusted in thread..."
#				self.ao_and_focus_adjusted = 1
#			else:
#				print  clock.timename(), "AO and focus was NOT adjusted in thread..."
#				self.ao_and_focus_adjusted = 0
		####################################################################################

#		if conf.ao_settings == "manual":
#			obj_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.
#			try:
#				print  clock.timename(), "Adjusting AO and focus in thread..."
#				thread_value = thread.start_new_thread(adjust_ao_and_focus, (obj_alt,))
#			except Exception,e:
#				print clock.timename(), e
#				print clock.timename(), "Could not set the AO and focus while slewing"	
#				self.ao_and_focus_adjusted = 0	
############################################################################################################################

		track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")

		timeout = time.time() + conf.tracking_timeout	# Timeout after n minutes.
		close_to = False

		while str(track_value) not in ['11', '11.0'] and close_to == False:
			time.sleep(1.0)
			track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
			print clock.timename(), "The telescope motion state value was: ", track_value

			tel_point_dec = comm2tcs_read.GET_TSI().get_position_equatorial_dec_j2000()
			tel_point_ra = comm2tcs_read.GET_TSI().get_position_equatorial_ra_j2000()
			tel_point_alt = comm2tcs_read.GET_TSI().get_position_horizontal_alt()

			dist_to_obj_ra = (numpy.abs(float(tel_point_ra) - float(ra_object))) * 3600.
			dist_to_obj_dec = (numpy.abs(float(tel_point_dec) - float(dec_object))) * 3600.

			print clock.timename(), "Distance to object from telescope: (RA = %s, DEC = %s) arcseconds" % (str(round(dist_to_obj_ra,2)), str(round(dist_to_obj_dec,2)))

		### If we are pointing close to zenith the telescope might report slewing even though it is tracking due to fast az movements. 
		### If pointing is closer than about 2 arcseconds of the object and altitude of the telescope is above 83 degrees:
			if (dist_to_obj_ra < conf.pointing_dist) and (dist_to_obj_dec < conf.pointing_dist):
				print clock.timename(), "The telescope is pointing within %f arcsec of the object and is not reporting slewing yet!" % conf.pointing_dist
				print clock.timename(), "I assume we are there and continue to observe!"
				close_to = True
			elif time.time() > timeout:
				value = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")				
				print clock.timename(), "The timeout of %i minutes was reached at: %s" % (int(conf.tracking_timeout / 60),clock.obstimeUT())
				self.update_or_status("wait", req_no)
				self.update_or("constraint_4", "'Tracking timeout'", "req_no", req_no)
				return 'soso_go'

			#sys.stdout.flush()

#		print clock.timename(), "The telescope is now tracking!"
		
		tel_point_dec = comm2tcs_read.GET_TSI().get_position_equatorial_dec_j2000()
		tel_point_ra = comm2tcs_read.GET_TSI().get_position_equatorial_ra_j2000()
		dist_to_obj_ra = (numpy.abs(float(tel_point_ra) - float(ra_object))) * 3600.
		dist_to_obj_dec = (numpy.abs(float(tel_point_dec) - float(dec_object))) * 3600.
		print clock.timename(), "Distance to object from telescope: (RA = %s, DEC = %s) arcseconds" % (str(round(dist_to_obj_ra,2)), str(round(dist_to_obj_dec,2)))


		try:
			temp_values = read_value_db.get_fields("tenerife_tel_temps", ["m1_temp", "m2_temp", "m3_temp", "tel_temp"])
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), "Could not get telescope temperatures from database"


		if m_conf.use_temp_from == "m1":
	#		used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m1(sender="monitor"))
			used_temp = float(temp_values["m1_temp"])
		elif m_conf.use_temp_from == "m2":
	#		used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m2(sender="monitor"))
			used_temp = float(temp_values["m2_temp"])
		elif m_conf.use_temp_from == "m3":
	#		used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m3(sender="monitor"))
			used_temp = float(temp_values["m3_temp"])
		elif m_conf.use_temp_from == "tt":
	#		used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_ttelescope(sender="monitor"))
			used_temp = float(temp_values["tel_temp"])
		elif m_conf.use_temp_from == "out":	
			try:
				weather_output = self.get_db_values("weather_station", ["wxt520_temp1"])
				used_temp = float(weather_output["wxt520_temp1"])
			except Exception, e:
				print clock.timename(), "Error: ", e	
				print clock.timename(), "Using M2 temperature in stead of outside temperature"
				used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m1(sender="monitor"))	

		print clock.timename(), "Temperature used for focus guess: ", used_temp

#				telescope_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor"))
		obj_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.
		print clock.timename(), "Telescope altitude used for focus guess: ", obj_alt


		#### SETTING A FOCUS OFFSET #### --- Setting  
		curr_focus_offset = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_z_offset()
		focus_realpos = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_z_realpos()
		focus_currpos = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_z_currpos()

		focus_guess = m_conf.tel_focus_function_values[0] + (m_conf.tel_focus_function_values[1] * used_temp) + (m_conf.tel_focus_function_values[2] / obj_alt) + m_conf.tel_focus_function_values[3] * float(self.obs_req_values['magnitude'])
		print clock.timename(), "Focus guess is: ", curr_focus_offset

		print clock.timename(), "Real focus position was: ", focus_realpos
		print clock.timename(), "Current focus position without offsets was: ", focus_currpos

		try:
			if float(focus_currpos) < 0.1:
				print clock.timename(), "For some reason the focus position was not set. Will set to 1.9 now"
				comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_z_targetpos(param=1.9,sender="Observer")
		except Exception,e:
			print clock.timename(), "Could not set the focus target position"

#		if float(curr_focus_offset) > 0.7 and float(curr_focus_offset) < 1.0:
#			print clock.timename(), "Focus offset was already set to: ", curr_focus_offset
		if numpy.abs(float(curr_focus_offset)-focus_guess) < 0.3:
			print clock.timename(), "Focus offset was already set to: ", curr_focus_offset
		else:
			print clock.timename(), "The focus offset will be set to: ", focus_guess
			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_z_offset(param=focus_guess, sender="Observer")

		focus_realpos = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_z_realpos()

		self.base_focus_offset = float(comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_z_offset())


	#	ao_timeout = time.time() + 20	#Timeout after additional 10 seconds.
	#	while self.ao_and_focus_adjusted == 2:
	#		print clock.timename(), "The AO adjustment and focusing where not completed yet!"
	#		time.sleep(1)		
	#		if time.time() > ao_timeout:
	#			print clock.timename(), "The AO adjustment and focusing was timed out...!"
	#			break

	#	if self.ao_and_focus_adjusted != 1:		
	#		try:
	#			obj_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.
	#			#telescope_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor"))
	#			set_ao.main(value=obj_alt)
	#		except Exception,e:
	#			print clock.timename(), "Error: ", e	
	#			print clock.timename(), "AO and Focus guess was not applied correctly... Now trying old way:"		

	#			try:
	#				temp_values = read_value_db.get_fields("tenerife_tel_temps", ["m1_temp", "m2_temp", "m3_temp", "tel_temp"])
	#			except Exception,e:
	#				print clock.timename(), e
	#				print clock.timename(), "Could not get telescope temperatures from database"

	#			if m_conf.use_temp_from == "m1":
	#		#		used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m1(sender="monitor"))
	#				used_temp = float(temp_values["m1_temp"])
	#			elif m_conf.use_temp_from == "m2":
	#		#		used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m2(sender="monitor"))
	#				used_temp = float(temp_values["m2_temp"])
	#			elif m_conf.use_temp_from == "m3":
	#		#		used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m3(sender="monitor"))
	#				used_temp = float(temp_values["m3_temp"])
	#			elif m_conf.use_temp_from == "tt":
	#		#		used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_ttelescope(sender="monitor"))
	#				used_temp = float(temp_values["tel_temp"])
	#			elif m_conf.use_temp_from == "out":	
	#				try:
	#					weather_output = self.get_db_values("weather_station", ["wxt520_temp1"])
	#					used_temp = float(weather_output["wxt520_temp1"])
	#				except Exception, e:
	#					print clock.timename(), "Error: ", e	
	#					print clock.timename(), "Using M2 temperature in stead of outside temperature"
	#					used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m1(sender="monitor"))	

	#			print clock.timename(), "Temperature used for focus guess: ", used_temp

#	#			telescope_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor"))
	#			obj_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.
	#			print clock.timename(), "Telescope altitude used for focus guess: ", obj_alt

	#	#		focus_guess = m_conf.tel_focus_function_values[0] + (m_conf.tel_focus_function_values[1] * used_temp) + (m_conf.tel_focus_function_values[2] / telescope_alt)
	#			try:
	#	#			focus_guess = m_conf.tel_focus_function_values[0] + (m_conf.tel_focus_function_values[1] * used_temp) + (m_conf.tel_focus_function_values[2] / telescope_alt**2) + m_conf.tel_focus_function_values[3] / float(self.obs_req_values['magnitude'])
	#				focus_guess = m_conf.tel_focus_function_values[0] + (m_conf.tel_focus_function_values[1] * used_temp) + (m_conf.tel_focus_function_values[2] / obj_alt) + m_conf.tel_focus_function_values[3] * float(self.obs_req_values['magnitude'])
	#			except Exception,e:
	#				print clock.timename(), "Using old function for guess"
	#				focus_guess = m_conf.old_tel_focus_function_values[0] + (m_conf.old_tel_focus_function_values[1] * used_temp) + (m_conf.old_tel_focus_function_values[2] / obj_alt)

	#			if focus_guess > conf.focus_min and focus_guess < conf.focus_max:
	#				print clock.timename(), "Now setting focus offset of telescope to %s" % focus_guess
	#				print clock.timename(), "and setting focus position of telescope to 0.0"
	#				comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_z_targetpos(param=0.0,sender="Observer")
	#				comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_z_offset(param=focus_guess, sender="Observer")
	#			else:
	#				print clock.timename(), "Focus guess was too large or too small. The guess was:", focus_guess


		#### 2018-09-11: Using the determined offsets from the daily calibrations to set a up to date guide target:
		slit_offsets = ""
		if int(self.obs_req_values["slit"]) == 5:
			slit_offsets = ["extra_value_1", "extra_value_2"]
		elif int(self.obs_req_values["slit"]) == 6:
			slit_offsets = ["extra_value_3", "extra_value_4"]
		elif int(self.obs_req_values["slit"]) == 8:
			slit_offsets = ["extra_value_5", "extra_value_6"]
		else:
			try:
				print clock.timename(), "Setting guide target of sigu to X=%s, Y=%s" % (str(conf.guide_targets[int(self.obs_req_values["slit"])][0]),str(conf.guide_targets[int(self.obs_req_values["slit"])][1]))
				sigu.exec_action(action="guide_target", args=[str(conf.guide_targets[int(self.obs_req_values["slit"])][0]),str(conf.guide_targets[int(self.obs_req_values["slit"])][1])])	
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "Problem in setting the sigu guide target"

		if slit_offsets != 0:	
			try:	
				conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, st_db, db_user, db_password))
				curr = conn.cursor()
				stmt = "SELECT %s, %s FROM maintenance WHERE extra_value_1 != 99.0 and ins_at > (current_timestamp - INTERVAL '2 days') ORDER BY maintenance_id DESC LIMIT 1" % (slit_offsets[0], slit_offsets[1])
				curr.execute(stmt)		
				output = curr.fetchall()
				curr.close()
	
				slit_x_offset = float(output[0][0])
				slit_y_offset = float(output[0][1])

				if numpy.abs(slit_x_offset) > 50. or numpy.abs(slit_y_offset) > 50.:
					slit_x_offset = 0.0
					slit_y_offset = 0.0
					print clock.timename(), " The slit locations offsets were way off..!"
					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Wrong slit offsets detected!",message="The offsets determined from the daily calibration routines were larger than the limit of 50 pixels. The values determined for slit %i were x=%s and y=%s.\n\nSend at: %s\n\n" % (int(self.obs_req_values["slit"]), str(slit_x_offset), str(slit_y_offset), clock.obstimeUT()))

			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "Problem in setting the sigu guide target"			
			try:
				print clock.timename(), "Setting guide target of sigu to X=%s, Y=%s" % (str(conf.guide_targets[int(self.obs_req_values["slit"])][0] + slit_x_offset),str(conf.guide_targets[int(self.obs_req_values["slit"])][1] + slit_y_offset))
				sigu.exec_action(action="guide_target", args=[str(conf.guide_targets[int(self.obs_req_values["slit"])][0] + slit_x_offset),str(conf.guide_targets[int(self.obs_req_values["slit"])][1] + slit_y_offset)])	
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "Problem in setting the sigu guide target"		


		print clock.timename(), "Setting the track value again to make sure the command was understood!"
		value = comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Observer")

		self.slewing = 0

		return "go"


	def acquire_one_thar(self, req_no, obs_end):

		#obs_req_values = self.get_or_values("obs_request_1", ["exp_time", "readoutmode", "amp_gain", "x_bin", "y_bin", "x_begin", "y_begin", "x_end", "y_end", "imagetype", "object_name", "right_ascension", "declination", "no_exp"], req_no)

		#### Move motors to fit ThAr spectrum:
		self.move_motors_thar()
		thar_exptime = m_conf.thar_exptime
		thar_imagetype = "THAR"
		ra = "00:00:00"
		dec = "00:00:00"
		
		if str(self.obs_req_values["obs_mode"]).lower() == "template":
			comment = 'TemplateObs_' + str(self.obs_req_values["object_name"])
			obj_name = "THAR"
		else:
			obj_name = str(self.obs_req_values["object_name"])
			comment = "Comment"
		
		##### Acquire ONE Thorium Argon spectrum ########
		ccd_value = ccd_server.acquire_an_or_image("mfa.fits", int(req_no), float(thar_exptime), int(self.obs_req_values["readoutmode"]), int(self.obs_req_values["amp_gain"]), '', int(self.obs_req_values["x_bin"]), int(self.obs_req_values["y_bin"]), '', int(self.obs_req_values["x_begin"]), int(self.obs_req_values["x_end"]), int(self.obs_req_values["y_begin"]), int(self.obs_req_values["y_end"]), str(thar_imagetype), obj_name, ra, dec, 'night',comment)

		if ccd_value == 1: # The ccd_server.acquire_an_image() 
			print clock.timename(), "The request was aborted"
			# Write "abort" to the status table in the database.
			self.update_or_status("abort", req_no)
			return_val = "abort"

		elif ccd_value == 0:
			print clock.timename(), "A ThAr spectrum was acquired"
			return_val = "done"
		else:
			print clock.timename(), "Something went wrong when acquiring a ThAr spectrum"
			print clock.timename(), ccd_value
			self.update_or_status("unknown", req_no)
			return_val = "error"
		sys.stdout.flush()

		#### Move motors to fit Star spectrum:
		print clock.timename(), "Now motors are being moved again!"
		sys.stdout.flush()

		if obs_end == "yes":
			#self.move_motors_star(tel_acq="no")
			os.popen("python /home/obs/programs/DMC/pst.py move -m 4 -p 1 & disown")	# Moving to star light 
			return return_val
		elif obs_end == "no":
			self.move_motors_star(tel_acq="no")
		elif obs_end == "acq":
			self.move_motors_star(tel_acq="yes")

#		print clock.timename(), "Now waiting 5 seconds for sigu and pugu to do its thing!"
#		sys.stdout.flush()
#		time.sleep(5)

		if conf.use_pugu == 1:
			val = pugu.exec_action("start")	
			if val != "done":
				return "no_go"

			if str(self.obs_req_values["object_name"]).lower() != "sun":
				val = pugu.exec_action("unpause")	
				if val != "done":
					return "no_go"

		if conf.use_sigu == 1:
			val = sigu.exec_action("start")	
			if val != "done":
				return "no_go"

			if str(self.obs_req_values["object_name"]).lower() != "sun":
				val = sigu.exec_action("unpause")	
				if val != "done":
					return "no_go"
			else:
				sigu.exec_action("moveto", [str(conf.m8_pos_x), str(conf.m8_pos_y)])			

		print clock.timename(), "The guiders are now activated!"

#		print clock.timename(), "Now waiting 5 seconds for sigu and pugu to do its thing!"
#		sys.stdout.flush()
#		time.sleep(5)

		return return_val


	def acquire_template_flats(self, req_no):

		print clock.timename(), "Moving things for Flat field spectres "
		sys.stdout.flush()

		value = lamp.Lamp(lamp="halo").set_on()                  # Turn on ThAr lamp
		value = pst.PST().move(2,3)                              # Beamsplitter cube
		value = pst.PST().move(3,int(self.obs_req_values["iodine_cell"]))                              # Move in the iodine cell
		value = pst.PST().move(4,2)                              # Light from the flat field lamp
		value = pst.PST().move(6,int(self.obs_req_values["slit"]))    # move slit into position
		Set_M8.set_m8_pos()

		print clock.timename(), "Starting to acquire Flat field spectres "
		sys.stdout.flush()

		# ------------------------------------------------------------------------------------
		exptime     = m_conf.halo_exptime
		imagetype   = 'FLATI2'
		objectname  = 'FLATI2'
		num_exp     = 20
		ra 	    = "00:00:00"
		dec	    = "00:00:00"
		comment = 'TemplateObs_' + str(self.obs_req_values["object_name"])

		for i in range(num_exp):

			##### Acquire FLAT through iodine ########
			ccd_value = ccd_server.acquire_an_or_image("mfa.fits", int(req_no), float(exptime), int(self.obs_req_values["readoutmode"]), int(self.obs_req_values["amp_gain"]), '', int(self.obs_req_values["x_bin"]), int(self.obs_req_values["y_bin"]), '', int(self.obs_req_values["x_begin"]), int(self.obs_req_values["x_end"]), int(self.obs_req_values["y_begin"]), int(self.obs_req_values["y_end"]), str(imagetype), str(objectname), ra, dec, 'night',comment)

			if ccd_value == 1:
				print clock.timename(), "The request was aborted"
				# Write "abort" to the status table in the database.
				self.update_or_status("abort", req_no)
				return_val = "abort"

			elif ccd_value == 0:
				print clock.timename(), "A ThAr spectrum was acquired"
				return_val = "done"
			else:
				print clock.timename(), "Something went wrong when acquiring a ThAr spectrum"
				print clock.timename(), ccd_value
				self.update_or_status("unknown", req_no)
				return_val = "error"
			# ------------------------------------------------------------------------------------

		value = lamp.Lamp(lamp="halo").set_off()  # Turn on Halogen lamp

		value = pst.PST().move(4,1)                               # Move to light from telescope
		value = pst.PST().move(3,2)                               # Remove the iodine cell

		return return_val

	def acquire_images(self, req_no):

		#obs_req_values = self.get_or_values("obs_request_1", ["exp_time", "readoutmode", "amp_gain", "x_bin", "y_bin", "x_begin", "y_begin", "x_end", "y_end", "imagetype", "object_name", "right_ascension", "declination", "no_exp", "obs_mode", "no_target_exp", "constraint_2"], req_no)

		if str(self.obs_req_values["object_name"]).lower() != "sun" and conf.use_sigu == 1:
			val = sigu.exec_action("unpause")

		### Allow more than 1000 spectre:
		if int(self.obs_req_values["req_chain_next"]) > 0:
			self.obs_req_values["no_exp"] = int(self.obs_req_values["req_chain_next"]) * int(self.obs_req_values["no_exp"])

		return_val = 'error'
		################ Save sigu and pugu images and adjusting AO every 30 seconds:#########################
		global RUNNING
		RUNNING = True
		def start_side_process(req_no):
			global RUNNING
			while RUNNING == True:
				print clock.timename(), "Number of threads: ", threading.activeCount()
				try:

					az_off = float(comm2tcs_read.GET_TSI().get_position_instrumental_az_offset(sender="Observer")) * 3600.
					zd_off = float(comm2tcs_read.GET_TSI().get_position_instrumental_zd_offset(sender="Observer")) * 3600.
					focus_off = float(comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_z_offset())
					####### Print telescope AZ og ALT offsets to log file:
					print clock.timename(), "Telescope AZ offset: %f arcseconds" % (az_off)
					print clock.timename(), "Telescope ZD offset: %f arcseconds" % (zd_off)
					print clock.timename(), "Telescope Focus offset: %f mm" % (focus_off)
				except Exception,e:
					print  clock.timename(), e
				else:
					if numpy.abs(zd_off) > conf.zd_offset_limit or numpy.abs(focus_off-self.base_focus_offset) > conf.focus_offset_limit or numpy.abs(az_off) > conf.az_offset_limit:
						print clock.timename(), "Telescope offsets are going crazy!"

				if (conf.use_sigu == 1 or conf.use_pugu == 1):
					try:
						self.snap_sigu_pugu()
					except Exception,e:
						print  clock.timename(), e
						print  clock.timename(), "Could not save sigu and pugu image in tread"

				obs_state_values = self.get_db_values(table_name='tel_dome', fields=["extra_param_1", "tel_motion_state"])

				if conf.ao_settings == "manual" and float(obs_state_values["extra_param_1"]) == float(0.0) and str(obs_state_values["tel_motion_state"]) in ["11", "11.0"]:
					try:
						try:
							object_alt = song_star_checker.star_pos(site=m_conf.song_site).star_alt(star_ra=self.obs_req_values["right_ascension"], star_dec=self.obs_req_values["declination"])
							tel_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.
						except Exception,e:
							print clock.timename(), "Could not use self values insie side process"
							tel_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt())

						#print clock.timename(), "Telescope altitude sent to AO function: ", tel_alt
						####### reapply ao and focus corrections:
						#ao_ret_val = set_ao.main(value = tel_alt)
					except Exception,e:
						print clock.timename(), e
						print clock.timename(), "Could not apply AO corrections..."

				### Check OR status...
				try:
					tmp_status = self.get_or_status(req_no)
				except Exception,e:
					print clock.timename(), e
					print clock.timename(), "Could not get OR status"
				else:
					if tmp_status == "abort":
						RUNNING = False
						try:
							self.side_p.terminate()
						except Exception,e:
							pass	

				time.sleep(30)

		if (conf.use_sigu == 1 or conf.use_pugu == 1 or conf.ao_settings == "manual") and str(self.obs_req_values["object_name"]).lower() != "sun":
			try:
				self.side_p = multiprocessing.Process(target=start_side_process, args=(req_no,))
				self.side_p.start()
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "The multiprocess way did not work"
				thread_value = thread.start_new_thread(start_side_process, (req_no,))
		####################################################################################


		if int(self.obs_req_values["constraint_2"]) == 0:
			self.number = 1
		else:
			self.number = int(self.obs_req_values["constraint_2"])

		if self.obs_req_values["obs_mode"] == "template":
			self.number = 1

		print clock.timename(), "Number of threads: ", threading.activeCount()
		print clock.timename(), "Should start at exposure number: %i" % self.number

		ccd_value = 0
		old_over_all_obs_state = '0'

		try:
			stop_window_time = datetime.datetime.strptime(str(self.obs_req_values["stop_window"]), "%Y-%m-%d %H:%M:%S")
		except Exception, e:
			print clock.timename(), e
			print clock.timename(), "Could not get the stop window time"

		try:
			obs_stop_time = datetime.datetime.strptime(str(sun_handle.obs_stop_next(m_conf.obs_sun_alt)), "%Y/%m/%d %H:%M:%S")
		except Exception, e:
			print clock.timename(), e
			print clock.timename(), "Could not get the obs stop time from star checker"


		overhead = 60	# overhead of one minute.... time between last observation and stop_window...
		total_spectres = 0

		if conf.ao_settings == "auto" or conf.ao_settings == "lookup":
			adjust_ao_time = time.time()
			old_tel_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt())

		print clock.timename(),"Timeout will happen at: %s" % (datetime.datetime.utcnow() + datetime.timedelta(seconds=int(self.time_to_complete)) + datetime.timedelta(seconds=overhead))

		for i in range(self.number, int(self.obs_req_values["no_exp"])+1):

			print clock.timename(), "Exposure number: %i" % self.number

			### IF now time plus exposure time plus overhead is later than stop_window... break
			if self.obs_req_values["obs_mode"] == "template":
				self.time_to_complete = (float(self.obs_req_values["no_exp"]) - (self.number-1)) * float(self.obs_req_values["exp_time"])
				print clock.timename(),"We are observing in TEMPLATE mode and the -time-to-complete- is: ", self.time_to_complete
				print clock.timename(),"Timeout will happen at: %s" % (datetime.datetime.utcnow() + datetime.timedelta(seconds=int(self.time_to_complete)) + datetime.timedelta(seconds=overhead))
			if (datetime.datetime.utcnow() + datetime.timedelta(seconds=int(self.time_to_complete)) + datetime.timedelta(seconds=overhead)) >= stop_window_time:
				RUNNING = False	# This should stop the save guide images thread
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				print clock.timename(), "Stop window reached in new timeout idea!"
				print clock.timename(), "Image number %i was about to be acquired!" % self.number 	
				self.update_or("constraint_4", "'Stop window reached'", "req_no", req_no)
				if self.number <= 1:
					self.update_or_status("abort", req_no)
					return "abort"
				else:
					return "done"	 
			###		

			sun_alt = sun_handle.sun_alt()
			sun_alt_d = float(str(sun_alt).split(":")[0]) - float(str(sun_alt).split(":")[1])/60.0 - float(str(sun_alt).split(":")[2])/3600.0
			#### IF time until obs time ends is less than now time plus exposure time -> stop observing!
			obs_time_diff = obs_stop_time - (datetime.datetime.utcnow() + datetime.timedelta(seconds=self.obs_req_values["exp_time"]))
			if (float(obs_time_diff.days)*24*3600. + float(obs_time_diff.seconds)) < -300.0 and str(self.obs_req_values["object_name"]).lower() != "sun":		### Allow to run 5 minutes more before sunrise
				print clock.timename(), "The observation could not finish before end of night. Difference in seconds: %f" % (float(obs_time_diff.days)*24*3600. + float(obs_time_diff.seconds))
				print clock.timename(), "End of night reached!"
				print clock.timename(), "Image number %i was about to be acquired!" % self.number 				
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				self.update_or("constraint_4", "'End of night reached'", "req_no", req_no)
				if self.number <= 1:
					self.update_or_status("abort", req_no)
					return "abort"
				else:
					return "done"		
			elif sun_alt_d > m_conf.obs_sun_alt + 2.0 and str(self.obs_req_values["object_name"]).lower() != "sun":			### Allow observations until Sun is at -4 degrees.
				print clock.timename(), "Sun is rising - end of night reached!"
				print clock.timename(), "Image number %i was about to be acquired!" % self.number 	
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				self.update_or("constraint_4", "'End of night reached'", "req_no", req_no)
				if self.number <= 1:
					self.update_or_status("abort", req_no)
					return "abort"
				else:
					return "done"	

			object_alt = song_star_checker.star_pos(site=m_conf.song_site).star_alt(star_ra=self.obs_req_values["right_ascension"], star_dec=self.obs_req_values["declination"])
			object_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.
			if object_alt < float(m_conf.telescope_min_altitude) and str(self.obs_req_values["object_name"]).lower() != "sun":
				print clock.timename(), "The altitude of the object was: ", object_alt
				print clock.timename(), "The OR was stopped due to low object #1"
				print clock.timename(), "Image number %i about to be acquired!" % self.number 	
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				self.update_or("constraint_4", "'Object too low'", "req_no", req_no)
				if self.number <= 1:
					self.update_or_status("abort", req_no)
					return "abort"
				else:
					return "done"	
			elif object_alt >= float(m_conf.max_alt_auto) and str(self.obs_req_values["object_name"]).lower() != "sun":
				print clock.timename(), "The altitude of the object was: ", object_alt
				print clock.timename(), "The OR was stopped due to object close to zenith"
				print clock.timename(), "Image number %i about to be acquired!" % self.number 	
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				self.update_or("constraint_4", "'Object close to zenith'", "req_no", req_no)
				if self.number <= 1:
					self.update_or_status("abort", req_no)
					return "abort"
				else:
					return "done"	

			### Check if telescope is at the right position:

			try:
				tel_point_dec = comm2tcs_read.GET_TSI().get_position_equatorial_dec_j2000()
				tel_point_ra = comm2tcs_read.GET_TSI().get_position_equatorial_ra_j2000()

				dist_to_obj_ra = (numpy.abs(float(tel_point_ra) - float(self.obs_req_values["right_ascension"]))) * 3600.
				dist_to_obj_dec = (numpy.abs(float(tel_point_dec) - float(self.obs_req_values["declination"]))) * 3600.

				print clock.timename(), "Distance to calculated object position from telescope: (RA = %s, DEC = %s) degrees" % (str(dist_to_obj_ra / 3600. ), str(dist_to_obj_dec / 3600. ))

				if ((dist_to_obj_ra / 3600.) > 1.0 or (dist_to_obj_dec / 3600.) > 1.0) and str(self.obs_req_values["object_name"]).lower() != "sun":	# If telescope points more than one degree away from the object in RA or DEC the OR will stop.
					RUNNING = False
					try:
						self.side_p.terminate()
					except Exception,e:
						pass
					print clock.timename(), "Telescope did not point at the object!!"
					self.update_or("constraint_4", "'Pointing away'", "req_no", req_no)
					self.update_or_status("wait", req_no)
					self.stop_tracking()
					return "wait"	
			except Exception,e:
				print  clock.timename(), e	
				print  clock.timename(), "Failed to check distance to object..."			

			try:
				zd_off = float(comm2tcs_read.GET_TSI().get_position_instrumental_zd_offset(sender="Observer")) * 3600.
				az_off = float(comm2tcs_read.GET_TSI().get_position_instrumental_az_offset(sender="Observer")) * 3600.
				focus_off = float(comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_z_offset())
			except Exception,e:
				print  clock.timename(), e
			else:
				if (numpy.abs(zd_off) > conf.zd_offset_limit or numpy.abs(focus_off-self.base_focus_offset) > conf.focus_offset_limit or numpy.abs(az_off) > conf.az_offset_limit) and str(self.obs_req_values["object_name"]).lower() != "sun":
					RUNNING = False
					try:
						self.side_p.terminate()
					except Exception,e:
						pass
					print clock.timename(), "Telescope offsets are going crazy! Now stopping the observation..."
					self.update_or("constraint_4", "'Telescope ZD drifting'", "req_no", req_no)
					self.update_or_status("wait", req_no)
					self.stop_tracking()
					return "wait"	




	#		tel_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt())

			####### reapply ao and focus corrections:

	#		if conf.ao_settings == "manual":
	#			if time.time() > adjust_ao_time + 300:
	#			ao_ret_val = set_ao.main(value = tel_alt)
	#				adjust_ao_time = time.time()
			if conf.ao_settings == "auto":
				if time.time() > adjust_ao_time + 600:	# checks every 10 minutes. 
					if tel_alt > 65.0 and tel_alt < 67.0 and (tel_alt - old_tel_alt) > 0.0: 
						print clock.timename(), "Applying focus and AO corrections according to altitude: ", tel_alt
						self.apply_focus_and_ao()
						adjust_ao_time = time.time()
					elif tel_alt > 55.0 and tel_alt < 57.0 and (tel_alt - old_tel_alt) > 0.0: 
						print clock.timename(), "Applying focus and AO corrections according to altitude: ", tel_alt
						self.apply_focus_and_ao()
						adjust_ao_time = time.time()	
					elif tel_alt > 49.0 and tel_alt < 51.0 and (tel_alt - old_tel_alt) > 0.0: 
						print clock.timename(), "Applying focus and AO corrections according to altitude: ", tel_alt
						self.apply_focus_and_ao()
						adjust_ao_time = time.time()	
					elif tel_alt > 45.0 and tel_alt < 47.0 and (tel_alt - old_tel_alt) > 0.0: 
						print clock.timename(), "Applying focus and AO corrections according to altitude: ", tel_alt
						self.apply_focus_and_ao()
						adjust_ao_time = time.time()	
					elif tel_alt > 37.0 and tel_alt < 39.0 and (tel_alt - old_tel_alt) > 0.0: 
						print clock.timename(), "Applying focus and AO corrections according to altitude: ", tel_alt
						self.apply_focus_and_ao()
						adjust_ao_time = time.time()	

					if tel_alt > 63.0 and tel_alt < 65.0 and (tel_alt - old_tel_alt) < 0.0: 
						print clock.timename(), "Applying focus and AO corrections according to altitude: ", tel_alt
						self.apply_focus_and_ao()
						adjust_ao_time = time.time()
					elif tel_alt > 53.0 and tel_alt < 55.0 and (tel_alt - old_tel_alt) < 0.0: 
						print clock.timename(), "Applying focus and AO corrections according to altitude: ", tel_alt
						self.apply_focus_and_ao()
						adjust_ao_time = time.time()	
					elif tel_alt > 47.0 and tel_alt < 49.0 and (tel_alt - old_tel_alt) < 0.0: 
						print clock.timename(), "Applying focus and AO corrections according to altitude: ", tel_alt
						self.apply_focus_and_ao()
						adjust_ao_time = time.time()	
					elif tel_alt > 42.0 and tel_alt < 44.0 and (tel_alt - old_tel_alt) < 0.0: 
						print clock.timename(), "Applying focus and AO corrections according to altitude: ", tel_alt
						self.apply_focus_and_ao()
						adjust_ao_time = time.time()	
					elif tel_alt > 35.0 and tel_alt < 37.0 and (tel_alt - old_tel_alt) < 0.0: 
						print clock.timename(), "Applying focus and AO corrections according to altitude: ", tel_alt
						self.apply_focus_and_ao()
						adjust_ao_time = time.time()	

					old_tel_alt = tel_alt

			elif conf.ao_settings == "lookup":
				if time.time() > adjust_ao_time + 600:	# checks every 10 minutes. 
					self.apply_focus_and_ao()
					adjust_ao_time = time.time()	

			
			over_all_obs_state = self.get_db_values(table_name='tel_dome', fields=['extra_param_1'])

			### Calling the telescope to ask it to track the object. This might help on the dome problem when it does not follow the telescope....
			if (float(self.obs_req_values["exp_time"]) >= 120 or self.number == 1) and str(self.obs_req_values["object_name"]).lower() != "sun":
				print clock.timename(), "Setting the track value again...!"
				value = comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Observer")
			elif float(self.obs_req_values["exp_time"]) < 120 and (self.number % 6) == 0 and str(self.obs_req_values["object_name"]).lower() != "sun":
				print clock.timename(), "Setting the track value again...!"
				value = comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Observer")

			try:
				print clock.timename(), "The over all obs state is: %s " % (str(over_all_obs_state['extra_param_1']))
			except Exception,e:
				pass
			
			sys.stdout.flush()
			if str(over_all_obs_state['extra_param_1']) == '0' or old_over_all_obs_state == '0' or str(self.obs_req_values["object_name"]).lower() == "sun":

				if self.obs_req_values["obs_mode"] == "none-iodine":	
					if checker_handle.check_last_thar_spectrum() == 1:				
						#### Acquire ONE Thorium Argon spectrum
						thar_value = self.acquire_one_thar(req_no, "no")
					
					#### Acquire no_target_exp star spectres
					for k in range(int(self.obs_req_values["no_target_exp"])):

						over_all_obs_state = self.get_db_values(table_name='tel_dome', fields=['extra_param_1'])
						print clock.timename(), "The over all obs state is: %s " % (str(over_all_obs_state['extra_param_1']))
						sys.stdout.flush()

						### IF now time plus exposure time is later than stop_window... break... If the script gets to this point it should neglect the overhead...
						if (datetime.datetime.utcnow() + datetime.timedelta(seconds=self.obs_req_values["exp_time"])) >= stop_window_time:
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							print clock.timename(), "Stop window reached in new timeout idea!"
							if self.number > 1:
								print clock.timename(), "Acquirering a ThAr before stopping"
								thar_value = self.acquire_one_thar(req_no, "yes")
								self.update_or("constraint_4", "'Stop window reached'", "req_no", req_no)
								return "done"	 
							else:
								self.update_or("constraint_4", "'Stop window reached'", "req_no", req_no)
								self.update_or_status("abort", req_no)
								return "abort"
						###	

						#### IF time until obs time ends is less than now time plus exposure time -> stop observing!
						obs_time_diff = obs_stop_time - (datetime.datetime.utcnow() + datetime.timedelta(seconds=self.obs_req_values["exp_time"]))
						if (float(obs_time_diff.days)*24*3600. + float(obs_time_diff.seconds)) < -300.0 and str(self.obs_req_values["object_name"]).lower() != "sun": ### Allow to run 5 minutes more before sunrise
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							print clock.timename(), "End of night reached - ThAr!"
							print clock.timename(), "Image number %i was about to be acquired!" % self.number 
							if self.number <= 1:
								self.update_or("constraint_4", "'End of night reached'", "req_no", req_no)
								self.update_or_status("abort", req_no)
								return "abort"
							else:
								return "done"		
						if str(self.obs_req_values["object_name"]).lower() != "sun":
							ccd_value = ccd_server.acquire_an_or_image("mfa.fits", int(req_no), float(self.obs_req_values["exp_time"]), int(self.obs_req_values["readoutmode"]), int(self.obs_req_values["amp_gain"]), '', int(self.obs_req_values["x_bin"]), int(self.obs_req_values["y_bin"]), '', int(self.obs_req_values["x_begin"]), int(self.obs_req_values["x_end"]), int(self.obs_req_values["y_begin"]), int(self.obs_req_values["y_end"]), str(self.obs_req_values["imagetype"]), str(self.obs_req_values["object_name"]), float(self.obs_req_values["right_ascension"]), float(self.obs_req_values["declination"]), 'night',"Comment")
						else:
							ccd_value = ccd_server.acquire_an_or_image("mfa.fits", int(req_no), float(self.obs_req_values["exp_time"]), int(self.obs_req_values["readoutmode"]), int(self.obs_req_values["amp_gain"]), '', int(self.obs_req_values["x_bin"]), int(self.obs_req_values["y_bin"]), '', int(self.obs_req_values["x_begin"]), int(self.obs_req_values["x_end"]), int(self.obs_req_values["y_begin"]), int(self.obs_req_values["y_end"]), str(self.obs_req_values["imagetype"]), str(self.obs_req_values["object_name"]), float(self.obs_req_values["right_ascension"]), float(self.obs_req_values["declination"]), 'night',"Blue sky")


						if ccd_value == 1: # The ccd_server.acquire_an_image() 
							print clock.timename(), "The request was aborted in ThAr with a AbortAcquisition command"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							# Write "abort" to the status table in the database.
							self.update_or_status("abort", req_no)
							self.update_or("constraint_4", "'Forced stop'", "req_no", req_no)
							return_val = "abort"
							return return_val

						elif ccd_value == 0:
							print clock.timename(), "Image number %s out of %i was acquired" % (self.number, int(self.obs_req_values["no_exp"]))

							try:
								self.update_or("constraint_2", self.number, "req_no", req_no)
							except Exception,e:
								print clock.timename(), "Could not update OR with number of acquire images!"

							self.number += 1
							return_val = "done"
						else:
							print clock.timename(), "Something went wrong in ThAr"
							print clock.timename(), ccd_value
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or_status("unknown", req_no)
							self.update_or("constraint_4", "'Unknown'", "req_no", req_no)
							return_val = "error"
							return return_val

						#################################################################################################
						#### IF FOR SOME REASON THE OBSERVATIONS ARE SUPPOSED TO STOP INSIDE THE LOOP:

						over_all_obs_state = self.get_db_values(table_name='tel_dome', fields=['extra_param_1'])

						if str(over_all_obs_state['extra_param_1']) != '0' and k > 3 and str(self.obs_req_values["object_name"]).lower() != "sun":
							thar_value = self.acquire_one_thar(req_no, "yes")

#						if str(over_all_obs_state['extra_param_1']) != '0':
						# Check the object coordinates (altitude)
						object_alt = song_star_checker.star_pos(site=m_conf.song_site).star_alt(star_ra=self.obs_req_values["right_ascension"], star_dec=self.obs_req_values["declination"])
						object_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.0
						if object_alt < float(m_conf.telescope_min_altitude) and str(self.obs_req_values["object_name"]).lower() != "sun":
							print clock.timename(), "The altitude of the object was: ", object_alt
							print clock.timename(), "The request was stopped due to low object #2"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or("constraint_4", "'Object too low'", "req_no", req_no)
							return_val = "done"
							return return_val	

						elif object_alt >= float(m_conf.max_alt_auto) and str(self.obs_req_values["object_name"]).lower() != "sun":
							print clock.timename(), "The altitude of the object was: ", object_alt
							print clock.timename(), "The request was stopped due to object close to zenith #2"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or("constraint_4", "'Object close to zenith'", "req_no", req_no)
							return_val = "done"
							return return_val			


						if str(over_all_obs_state['extra_param_1']) == '1' or old_over_all_obs_state == '1':
							print clock.timename(), "The request was stopped due to bad weather"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							###### SETTING status to 'wait' will make it stat again when weather turns good!
							self.update_or_status("wait", req_no)
							self.update_or("constraint_4", "'Weather'", "req_no", req_no)
							return_val = "abort"
							return return_val

						elif (str(over_all_obs_state['extra_param_1']) == '2' or old_over_all_obs_state == '2') and str(self.obs_req_values["object_name"]).lower() != "sun":
							print clock.timename(), "The request was aborted due to daylight"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or_status("abort", req_no)
							self.update_or("constraint_4", "'Daylight'", "req_no", req_no)
							return_val = "abort"
							return return_val

						elif str(over_all_obs_state['extra_param_1']) == '3' or old_over_all_obs_state == '3':
							print clock.timename(), "The request was aborted due to db error"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or_status("abort", req_no)
							self.update_or("constraint_4", "'DB error'", "req_no", req_no)
							return_val = "abort"
							return return_val

						elif str(over_all_obs_state['extra_param_1']) == '5' or old_over_all_obs_state == '5':
							print clock.timename(), "The request was set to wait due to dome slit not open"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or_status("wait", req_no)
							self.update_or("constraint_4", "'Closed dome'", "req_no", req_no)
							return_val = "wait"
							return return_val

						elif str(over_all_obs_state['extra_param_1']) == '6' or old_over_all_obs_state == '6':
							print clock.timename(), "The request was aborted due to mirror covers not open"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or_status("abort", req_no)
							self.update_or("constraint_4", "'Closed mirror covers'", "req_no", req_no)
							return_val = "abort"
							return return_val	
		
						elif (str(over_all_obs_state['extra_param_1']) == '7' or old_over_all_obs_state == '7') and str(self.obs_req_values["object_name"]).lower() != "sun":
							print clock.timename(), "The request was aborted due to objects altitude too low #3"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or_status("abort", req_no)
							self.update_or("constraint_4", "'Low object'", "req_no", req_no)
							return_val = "abort"
							return return_val

						elif str(over_all_obs_state['extra_param_1']) == '4' and old_over_all_obs_state == '4' and str(self.obs_req_values["object_name"]).lower() != "sun":
							#print "\nThe telescope was not tracking. Now trying to set it to track again at: ", clock.obstimeUT()
							#print comm2tcs_write.SET_TSI().set_pointing_track(param=1)
							print clock.timename(), "The request was set to wait due to telescope not tracking. The OR will be put on hold for 20 minutes"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass

							try:
								print clock.timename(), "Setting the ins_at to: -%s- and delay to -%s-" % (time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), conf.on_hold_wind_time)
								self.update_or("constraint_3, ins_at, constraint_4", "%i, '%s', '%s'" % (conf.on_hold_wind_time, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "On hold"), "req_no", req_no)
								self.update_or_status("wait", req_no)
								print clock.timename(), "Sleeping 10 seconds to make sure the OR values are copied from central to the site"
								time.sleep(10)
							except Exception,e:
								print e
								print clock.timename(), "The OR could not be put on hold since database was not updated."

							return_val = "wait"
							return return_val

						elif str(over_all_obs_state['extra_param_1']) == '9':
							print clock.timename(), "The request was set to wait due to telescope starting up"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or_status("wait", req_no)
							self.update_or("constraint_4", "'Starting up'", "req_no", req_no)
							return_val = "wait"
							return return_val

						elif str(over_all_obs_state['extra_param_1']) == '10':

							weather_output = checker_handle.weather_check()
							if weather_output[0] > 0:
								print clock.timename(), "Weather value was: ", weather_output
								print clock.timename(), "The request was set to wait due to bad weather"
								RUNNING = False
								try:
									self.side_p.terminate()
								except Exception,e:
									pass
								self.update_or_status("wait", req_no)
								self.update_or("constraint_4", "'Bad weather'", "req_no", req_no)
								return_val = "wait"
								return return_val
							else:
								print clock.timename(), "The request was set to wait due to telescope shutting down"
								RUNNING = False
								try:
									self.side_p.terminate()
								except Exception,e:
									pass
								self.update_or_status("wait", req_no)
								self.update_or("constraint_4", "'Shutting down'", "req_no", req_no)
								return_val = "wait"
								return return_val

						elif str(over_all_obs_state['extra_param_1']) == '10' and old_over_all_obs_state == '1':
							print clock.timename(), "The request was set to wait due to bad weather and shutting down"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or_status("wait", req_no)
							self.update_or("constraint_4", "'Bad weather'", "req_no", req_no)
							return_val = "wait"
							return return_val
						#else:
						#	print "The request was aborted for some strange reason... at: ", clock.obstimeUT()
						#	self.update_or_status("unknown", req_no)
						#	self.update_or("constraint_4", "'Unknown'", "req_no", req_no)
						#	return_val = "abort"
						#	return return_val

						sys.stdout.flush()
			
						old_over_all_obs_state = str(over_all_obs_state['extra_param_1'])
						#################################################################################################

						#### If last star spectrum is acquire end with a ThAr.
						if (self.number-1) == int(self.obs_req_values["no_exp"]):						
							thar_value = self.acquire_one_thar(req_no, "yes")
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							return_val = "done"
							return return_val
						sys.stdout.flush()

						### Check OR status...
						try:
							tmp_status = self.get_or_status(req_no)
						except Exception,e:
							print clock.timename(), e
							print clock.timename(), "Could not get OR status"
						else:
							if tmp_status == "abort":
								self.update_or("constraint_4", "'Nicely stopped'", "req_no", req_no)
								RUNNING = False
								try:
									self.side_p.terminate()
								except Exception,e:
									pass
								return "abort"	


						# Check if we still point towards the object
						tel_point_dec = comm2tcs_read.GET_TSI().get_position_equatorial_dec_j2000()
						tel_point_ra = comm2tcs_read.GET_TSI().get_position_equatorial_ra_j2000()

						dist_to_obj_ra = (numpy.abs(float(tel_point_ra) - float(self.obs_req_values["right_ascension"]))) * 3600.
						dist_to_obj_dec = (numpy.abs(float(tel_point_dec) - float(self.obs_req_values["declination"]))) * 3600.

						print clock.timename(), "Distance to calculated object position from telescope: (RA = %s, DEC = %s) degrees" % (str(dist_to_obj_ra / 3600. ), str(dist_to_obj_dec / 3600. ))

						if ((dist_to_obj_ra / 3600.) > 1.0 or (dist_to_obj_dec / 3600.) > 1.0) and str(self.obs_req_values["object_name"]).lower() != "sun":	# If telescope points more than one degree away from the object in RA or DEC the OR will stop.
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							print clock.timename(), "Telescope did not point at the object!!"
							self.update_or("constraint_3, ins_at, constraint_4", "%i, '%s', '%s'" % (conf.on_hold_wind_time, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "On hold"), "req_no", req_no)
							self.update_or_status("wait", req_no)
							self.stop_tracking()
							return "wait"	
	

				elif self.obs_req_values["obs_mode"].lower() == "template":
					comment_prefix = 'TemplateObs_'

					ra_for_makeheader = coor_handle.convert_ra(self.obs_req_values["right_ascension"])
					dec_for_makeheader = coor_handle.convert_dec(self.obs_req_values["declination"])

					ccd_value = ccd_server.acquire_an_or_image("mfa.fits", int(req_no), float(self.obs_req_values["exp_time"]), int(self.obs_req_values["readoutmode"]), int(self.obs_req_values["amp_gain"]), '', int(self.obs_req_values["x_bin"]), int(self.obs_req_values["y_bin"]), '', int(self.obs_req_values["x_begin"]), int(self.obs_req_values["x_end"]), int(self.obs_req_values["y_begin"]), int(self.obs_req_values["y_end"]), str(self.obs_req_values["imagetype"]), str(self.obs_req_values["object_name"]), ra_for_makeheader, dec_for_makeheader, 'night', comment_prefix + str(self.primary_target))


					if ccd_value == 1: # The ccd_server.acquire_an_image() 
						print clock.timename(), "The request was aborted by a AbortAcquisition command"	
						RUNNING = False
						try:
							self.side_p.terminate()
						except Exception,e:
							pass
						# Write "abort" to the status table in the database.
						self.update_or_status("abort", req_no)
						self.update_or("constraint_4", "'Forced stop'", "req_no", req_no)
						return_val = "abort"
						return return_val

					elif ccd_value == 0:
						print clock.timename(), "Image number %s out of %i was acquired" % (self.number, int(self.obs_req_values["no_exp"]))
						try:
							self.update_or("constraint_2", self.number, "req_no", req_no)
						except Exception,e:
							print clock.timename(), "Could not update OR with number of acquire images!"
						self.number +=1
						return_val = "done"

					else:
						print clock.timename(), "Something went wrong"
						print clock.timename(), ccd_value
						RUNNING = False
						try:
							self.side_p.terminate()
						except Exception,e:
							pass
						self.update_or_status("unknown", req_no)
						self.update_or("constraint_4", "'Unknown'", "req_no", req_no)
						return_val = "error"
						return return_val
					sys.stdout.flush()

					object_alt = song_star_checker.star_pos(site=m_conf.song_site).star_alt(star_ra=self.obs_req_values["right_ascension"], star_dec=self.obs_req_values["declination"])
					object_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.0

					if object_alt < float(m_conf.telescope_min_altitude):
						print clock.timename(), "The altitude of the object was: ", object_alt
						print clock.timename(), "The request was stopped due to low object #4"
						RUNNING = False
						try:
							self.side_p.terminate()
						except Exception,e:
							pass
						self.update_or("constraint_4", "'Object too low'", "req_no", req_no)
						return_val = "done"
						return return_val
					elif object_alt >= float(m_conf.max_alt_auto):
						print clock.timename(), "The altitude of the object was: ", object_alt
						print clock.timename(), "The request was stopped due to object close to zenith #4"
						RUNNING = False
						try:
							self.side_p.terminate()
						except Exception,e:
							pass
						self.update_or("constraint_4", "'Object close to zenith'", "req_no", req_no)
						return_val = "done"
						return return_val

					if str(over_all_obs_state['extra_param_1']) != '0':
						# Check the object coordinates (altitude)
						object_alt = song_star_checker.star_pos(site=m_conf.song_site).star_alt(star_ra=self.obs_req_values["right_ascension"], star_dec=self.obs_req_values["declination"])
						object_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.0
						weather_output = checker_handle.weather_check()

						if object_alt < float(m_conf.telescope_min_altitude) + 0.1:
							print clock.timename(), "The altitude of the object was: ", object_alt
							print clock.timename(), "The request was stopped due to low object #5"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or("constraint_4", "'Object too low'", "req_no", req_no)
							return_val = "done"
							return return_val	
						elif object_alt >= float(m_conf.max_alt_auto):
							print clock.timename(), "The altitude of the object was: ", object_alt
							print clock.timename(), "The request was stopped due to object close to zenith #5"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or("constraint_4", "'Object close to zenith'", "req_no", req_no)
							return_val = "done"
							return return_val							
									
						elif weather_output[0] > 0:
							print clock.timename(), "Weather value was: ", weather_output
							print clock.timename(), "The request was set to wait due to bad weather"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or_status("wait", req_no)
							self.update_or("constraint_4", "'Bad weather'", "req_no", req_no)
							return_val = "abort"
							return return_val

				else:

					if str(self.obs_req_values["object_name"]).lower() != "sun":
						ccd_value = ccd_server.acquire_an_or_image("mfa.fits", int(req_no), float(self.obs_req_values["exp_time"]), int(self.obs_req_values["readoutmode"]), int(self.obs_req_values["amp_gain"]), '', int(self.obs_req_values["x_bin"]), int(self.obs_req_values["y_bin"]), '', int(self.obs_req_values["x_begin"]), int(self.obs_req_values["x_end"]), int(self.obs_req_values["y_begin"]), int(self.obs_req_values["y_end"]), str(self.obs_req_values["imagetype"]), str(self.obs_req_values["object_name"]), float(self.obs_req_values["right_ascension"]), float(self.obs_req_values["declination"]), 'night',"Comment")
					else:
						ccd_value = ccd_server.acquire_an_or_image("mfa.fits", int(req_no), float(self.obs_req_values["exp_time"]), int(self.obs_req_values["readoutmode"]), int(self.obs_req_values["amp_gain"]), '', int(self.obs_req_values["x_bin"]), int(self.obs_req_values["y_bin"]), '', int(self.obs_req_values["x_begin"]), int(self.obs_req_values["x_end"]), int(self.obs_req_values["y_begin"]), int(self.obs_req_values["y_end"]), str(self.obs_req_values["imagetype"]), str(self.obs_req_values["object_name"]), float(self.obs_req_values["right_ascension"]), float(self.obs_req_values["declination"]), 'night',"Blue sky")


					if ccd_value == 1: # The ccd_server.acquire_an_image() 
						print clock.timename(), "The request was aborted by a AbortAcquisition command"	
						RUNNING = False
						try:
							self.side_p.terminate()
						except Exception,e:
							pass
						# Write "abort" to the status table in the database.
						self.update_or_status("abort", req_no)
						self.update_or("constraint_4", "'Forced stop'", "req_no", req_no)
						return_val = "abort"
						return return_val

					elif ccd_value == 0:
						print clock.timename(), "Image number %s out of %i was acquired" % (self.number, int(self.obs_req_values["no_exp"]))
						try:
							self.update_or("constraint_2", self.number, "req_no", req_no)
						except Exception,e:
							print clock.timename(), "Could not update OR with number of acquire images!"
						self.number +=1
						return_val = "done"

					else:
						print clock.timename(), "Something went wrong"
						print clock.timename(), ccd_value
						RUNNING = False
						try:
							self.side_p.terminate()
						except Exception,e:
							pass
						self.update_or_status("unknown", req_no)
						self.update_or("constraint_4", "'Unknown'", "req_no", req_no)
						return_val = "error"
						return return_val
					sys.stdout.flush()

					object_alt = song_star_checker.star_pos(site=m_conf.song_site).star_alt(star_ra=self.obs_req_values["right_ascension"], star_dec=self.obs_req_values["declination"])
					object_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.0

					if object_alt < float(m_conf.telescope_min_altitude) and str(self.obs_req_values["object_name"]).lower() != "sun":
						print clock.timename(), "The altitude of the object was: ", object_alt
						print clock.timename(), "The request was stopped due to low object #4"
						RUNNING = False
						try:
							self.side_p.terminate()
						except Exception,e:
							pass
						self.update_or("constraint_4", "'Object too low'", "req_no", req_no)
						return_val = "done"
						return return_val
					elif object_alt >= float(m_conf.max_alt_auto) and str(self.obs_req_values["object_name"]).lower() != "sun":
						print clock.timename(), "The altitude of the object was: ", object_alt
						print clock.timename(), "The request was stopped due to object close to zenith #4"
						RUNNING = False
						try:
							self.side_p.terminate()
						except Exception,e:
							pass
						self.update_or("constraint_4", "'Object close to zenith'", "req_no", req_no)
						return_val = "done"
						return return_val

					if str(over_all_obs_state['extra_param_1']) != '0':
						# Check the object coordinates (altitude)
						object_alt = song_star_checker.star_pos(site=m_conf.song_site).star_alt(star_ra=self.obs_req_values["right_ascension"], star_dec=self.obs_req_values["declination"])
						object_alt = float(str(object_alt).split(":")[0]) + float(str(object_alt).split(":")[1]) / 60.0
						weather_output = checker_handle.weather_check()

						if object_alt < float(m_conf.telescope_min_altitude) + 0.1  and str(self.obs_req_values["object_name"]).lower() != "sun":
							print clock.timename(), "The altitude of the object was: ", object_alt
							print clock.timename(), "The request was stopped due to low object #5"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or("constraint_4", "'Object too low'", "req_no", req_no)
							return_val = "done"
							return return_val

						elif object_alt >= float(m_conf.max_alt_auto) and str(self.obs_req_values["object_name"]).lower() != "sun":
							print clock.timename(), "The altitude of the object was: ", object_alt
							print clock.timename(), "The request was stopped due to object close to zenith #5"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or("constraint_4", "'Object close to zenith'", "req_no", req_no)
							return_val = "done"
							return return_val								
									
						elif weather_output[0] > 0:
							print clock.timename(), "Weather value was: ", weather_output
							print clock.timename(), "The request was set to wait due to bad weather"
							RUNNING = False
							try:
								self.side_p.terminate()
							except Exception,e:
								pass
							self.update_or_status("wait", req_no)
							self.update_or("constraint_4", "'Bad weather'", "req_no", req_no)
							return_val = "abort"
							return return_val

			elif str(over_all_obs_state['extra_param_1']) == '1' or old_over_all_obs_state == '1':
				print clock.timename(), "The request was stopped due to bad weather"
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				###### SETTING status to 'wait' will make it stat again when weather turns good!
				self.update_or_status("wait", req_no)
				self.update_or("constraint_4", "'Bad weather'", "req_no", req_no)
				return_val = "abort"
				return return_val

			elif (str(over_all_obs_state['extra_param_1']) == '2' or old_over_all_obs_state == '2') and str(self.obs_req_values["object_name"]).lower() != "sun":
				print clock.timename(), "The request was aborted due to daylight"
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				self.update_or_status("abort", req_no)
				self.update_or("constraint_4", "'Daylight'", "req_no", req_no)
				return_val = "abort"
				return return_val

			elif str(over_all_obs_state['extra_param_1']) == '3' or old_over_all_obs_state == '3':
				print clock.timename(), "The request was aborted due to db error"
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				self.update_or_status("abort", req_no)
				self.update_or("constraint_4", "'DB error'", "req_no", req_no)
				return_val = "abort"
				return return_val

			elif str(over_all_obs_state['extra_param_1']) == '5' or old_over_all_obs_state == '5':
				print clock.timename(), "The request was aborted due to dome slit not open"
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				self.update_or_status("wait", req_no)
				self.update_or("constraint_4", "'Closed dome'", "req_no", req_no)
				return_val = "wait"
				return return_val

			elif str(over_all_obs_state['extra_param_1']) == '6' or old_over_all_obs_state == '6':
				print clock.timename(), "The request was aborted due to mirror covers not open"
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				self.update_or_status("abort", req_no)
				self.update_or("constraint_4", "'Closed mirror covers'", "req_no", req_no)
				return_val = "abort"
				return return_val	
		
			elif (str(over_all_obs_state['extra_param_1']) == '7' or old_over_all_obs_state == '7') and str(self.obs_req_values["object_name"]).lower() != "sun":
				print clock.timename(), "The request was aborted due to objects altitude too low #6"
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				self.update_or_status("abort", req_no)
				self.update_or("constraint_4", "'Low object'", "req_no", req_no)
				return_val = "abort"
				return return_val

			elif str(over_all_obs_state['extra_param_1']) == '4' and old_over_all_obs_state == '4' and str(self.obs_req_values["object_name"]).lower() != "sun":
				#print "\nThe telescope was not tracking. Now trying to set it to track again at: ", clock.obstimeUT()
				#print comm2tcs_write.SET_TSI().set_pointing_track(param=1)
				print clock.timename(), "The request was set to wait due to telescope not tracking"
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass

				try:
					print clock.timename(), "Setting the ins_at to: -%s- and delay to -%s-" % (time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), conf.on_hold_wind_time)
					self.update_or("constraint_3, ins_at, constraint_4", "%i, '%s', '%s'" % (conf.on_hold_wind_time, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "On hold"), "req_no", req_no)
					self.update_or_status("wait", req_no)
					print clock.timename(), "Sleeping 10 seconds to make sure the OR values are copied from central to the site"
					time.sleep(10)
				except Exception,e:
					print e
					print clock.timename(), "The OR could not be put on hold since database was not updated."

		#		self.update_or_status("wait", req_no)
		#		self.update_or("constraint_4", "'Not tracking'", "req_no", req_no)
				return_val = "wait"
				return return_val

			elif str(over_all_obs_state['extra_param_1']) == '10':

				weather_output = checker_handle.weather_check()
				if weather_output[0] > 0:
					print clock.timename(), "Weather value was: ", weather_output
					print clock.timename(), "The request was set to wait due to bad weather"
					RUNNING = False
					try:
						self.side_p.terminate()
					except Exception,e:
						pass
					self.update_or_status("wait", req_no)
					self.update_or("constraint_4", "'Bad weather'", "req_no", req_no)
					return_val = "wait"
					return return_val
				else:
					print clock.timename(), "The request was set to wait due to telescope shutting down"
					RUNNING = False
					try:
						self.side_p.terminate()
					except Exception,e:
						pass
					self.update_or_status("wait", req_no)
					self.update_or("constraint_4", "'Shutting down'", "req_no", req_no)
					return_val = "wait"
					return return_val

			else:
				print clock.timename(), "The request was aborted for some strange reason"
				RUNNING = False
				try:
					self.side_p.terminate()
				except Exception,e:
					pass
				self.update_or_status("unknown", req_no)
				self.update_or("constraint_4", "'Unknown'", "req_no", req_no)
				return_val = "abort"
#				return_val = "timeout"
				return return_val

			sys.stdout.flush()		

			### Check OR status...
			try:
				tmp_status = self.get_or_status(req_no)
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "Could not get OR status"
			else:
				if tmp_status == "abort":
					print clock.timename(), "Stopping nicely..."
					self.update_or("constraint_4", "'Nicely stopped'", "req_no", req_no)
					RUNNING = False
					try:
						self.side_p.terminate()
					except Exception,e:
						pass
					return "abort"					

			old_over_all_obs_state = str(over_all_obs_state['extra_param_1'])

		RUNNING = False
		try:
			self.side_p.terminate()
		except Exception,e:
			pass
	
		return return_val

	def start_guiding(self):
		"""
			@brief: This function sets sigu and pugu to pause
		"""

		print clock.timename(), "Now trying to start sigu and pugu"
		if conf.use_sigu == 1:
#			thread_value1 = thread.start_new_thread(send_stop_to_sigu, ("Sending stop to sigu",))
			val = sigu.exec_action("unpause")
			val = sigu.exec_action("start")	
#			val = sigu.exec_action("moveto", ["idle"])

		if conf.use_pugu == 1:
#			thread_value2 = thread.start_new_thread(send_stop_to_pugu, ("Sending stop to pugu",))
			val = pugu.exec_action("unpause")	
			val = pugu.exec_action("start")	
#			val = pugu.exec_action("moveto", ["idle"])

		print clock.timename(), "Sigu and pugu should be started again"

		return 1

	def finishing_off(self):
		"""
			@brief: This function sets sigu and pugu to pause
		"""
		global RUNNING
		RUNNING = False
		try:
			self.side_p.terminate()
		except Exception,e:
			pass	

		def send_stop_to_sigu(msg):
			print clock.timename(), msg
			val = sigu.exec_action("pause")	
			val = sigu.exec_action("stop")	
			print clock.timename(), "Sigu was stopped!"
			return 1
		def send_stop_to_pugu(msg):
			print clock.timename(), msg
			val = pugu.exec_action("pause")	
			val = pugu.exec_action("stop")		
			print clock.timename(), "Pugu was stopped!"
			return 1	

		print clock.timename(), "Now trying to stop sigu and pugu"
		if conf.use_sigu == 1:
#			thread_value1 = thread.start_new_thread(send_stop_to_sigu, ("Sending stop to sigu",))
			#val = sigu.exec_action("pause")
			#val = sigu.exec_action("stop")	
			os.popen("python /home/obs/programs/guiders/slit/sigu.py stop")
#			val = sigu.exec_action("moveto", ["idle"])

		if conf.use_pugu == 1:
#			thread_value2 = thread.start_new_thread(send_stop_to_pugu, ("Sending stop to pugu",))
			#val = pugu.exec_action("pause")	
			#val = pugu.exec_action("stop")	
			os.popen("python /home/obs/programs/guiders/pupil/pugu.py stop")
#			val = pugu.exec_action("moveto", ["idle"])

#		print clock.timename(), "Sigu and pugu should be stopped"

#		#### Test if the telescope is currently tracking. 
#		track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Observer")
#		motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer") 
#		print clock.timename(), "The motion state of the telescope is currently: ", motion_state
#
#		if float(track_value) != float(0.0):
#			print clock.timename(), "Stop tracking..."
#			track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")

		# Set ZD and AZ offsets to zero:
#		current_az_offset = float(comm2tcs_read.GET_TSI().get_position_instrumental_az_offset(sender="Observer"))
#		current_zd_offset = float(comm2tcs_read.GET_TSI().get_position_instrumental_zd_offset(sender="Observer"))
#		if current_az_offset != float(0.0):
#			comm2tcs_write.SET_TSI().set_position_instrumental_az_offset(param=float(0.0),sender="Observer")
#		if current_zd_offset != float(0.0):
#			comm2tcs_write.SET_TSI().set_position_instrumental_zd_offset(param=float(0.0),sender="Observer")
#		print clock.timename(), "Zenith distance and Azimuth offsets has been set to zero!"
		
		return 1

	def starting_up(self):
		"""
			@brief: This function sets sigu and pugu to unpause
		"""

		if self.obs_req_values["magnitude"] <= 1.0:
			sigu_texp = "0.2"
			pugu_texp = "0.5"
		elif self.obs_req_values["magnitude"] > 1.0 and self.obs_req_values["magnitude"] <= 2.0:
			sigu_texp = "0.5"
			pugu_texp = "1.0"
		elif self.obs_req_values["magnitude"] > 2.0 and self.obs_req_values["magnitude"] <= 4.0:
			sigu_texp = "1.0"
			pugu_texp = "2.5"
		elif self.obs_req_values["magnitude"] > 4.0 and self.obs_req_values["magnitude"] <= 5.0:
			sigu_texp = "2.0"
			pugu_texp = "6.0"
		elif self.obs_req_values["magnitude"] > 5.0 and self.obs_req_values["magnitude"] <= 6.0:
			sigu_texp = "3.0"
			pugu_texp = "7.0"
		elif self.obs_req_values["magnitude"] > 6.0 and self.obs_req_values["magnitude"] <= 7.0:
			sigu_texp = "4.0"
			pugu_texp = "8.0"
		elif self.obs_req_values["magnitude"] > 7.0 and self.obs_req_values["magnitude"] <= 8.0:
			sigu_texp = "5.0"
			pugu_texp = "10.0"
		elif self.obs_req_values["magnitude"] > 8.0:
			sigu_texp = "6.0"
			pugu_texp = "12.0"

#		sigu_texp = str(self.obs_req_values["magnitude"] * 0.7)

		pugu_texp = str(0.1 * 10.0**(0.4 * float(self.obs_req_values["magnitude"])))
		sigu_texp = str(0.03 * 10.0**(0.4 * float(self.obs_req_values["magnitude"])))

		if float(sigu_texp) > 10.0:
			sigu_texp = "10.0"
		if float(pugu_texp) > 12.0:
			pugu_texp = "12.0"	

		val = sigu.exec_action("texp", [sigu_texp])	
		if val != "done":
			return "no_go"

		val = pugu.exec_action("texp", [pugu_texp])	
		if val != "done":
			return "no_go"

		if self.obs_req_values["magnitude"] <= 10.0 and str(self.obs_req_values["object_name"]).lower() != "sun":

			if conf.use_pugu == 1:
				val = pugu.exec_action("start")	
				if val != "done":
					return "no_go"

				val = pugu.exec_action("unpause")	
				if val != "done":
					return "no_go"

			if conf.use_sigu == 1:
				val = sigu.exec_action("start")	
				if val != "done":
					return "no_go"

				val = sigu.exec_action("unpause")	
				if val != "done":
					return "no_go"

			#time.sleep(10)	# wait for sigu and pugu to have corrected things.

		elif str(self.obs_req_values["object_name"]).lower() == "sun":
			if conf.use_pugu == 1:
				val = pugu.exec_action("pause")	
				if val != "done":
					return "no_go"

				val = pugu.exec_action("texp", [str(conf.pugu_texp_sun)])
				if val != "done":
					return "no_go"

				val = pugu.exec_action("start")	
				if val != "done":
					return "no_go"

			if conf.use_sigu == 1:
				val = sigu.exec_action("pause")	
				if val != "done":
					return "no_go"

				val = sigu.exec_action("texp", [str(conf.sigu_texp_sun)])
				if val != "done":
					return "no_go"

				val = sigu.exec_action("start")	
				if val != "done":
					return "no_go"		

		else:
			if conf.use_pugu == 1:
				val = pugu.exec_action("pause")	
				if val != "done":
					return "no_go"

				val = pugu.exec_action("start")	
				if val != "done":
					return "no_go"

			if conf.use_sigu == 1:
				val = sigu.exec_action("pause")	
				if val != "done":
					return "no_go"

				val = sigu.exec_action("moveto", ["idle"])
				if val != "done":
					return "no_go"

				val = sigu.exec_action("start")	
				if val != "done":
					return "no_go"

		print clock.timename(), "The guiders have been started!"

		return 1


	def restart_sigu(self):
		if conf.use_sigu_on_sstenerife != "yes":
			try:
				os.popen("python /home/obs/programs/guiders/slit/slit_guider.py -t", "w")
			except Exception, e:
				print clock.timename(), "Something went wrong when trying to stop slit guider!"
				print clock.timename(), e

			time.sleep(2)

			try:
				os.popen("python /home/obs/programs/guiders/slit/slit_guider.py -s", "w")
			except Exception, e:
				print clock.timename(), "Something went wrong when trying to start slit guider!"
				print clock.timename(), e

			time.sleep(2)

		return 1

	def restart_pugu(self):

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


	def snap_sigu_pugu(self):

		#print "Snapping a sigu and a pugu image at: ", clock.obstimeUT()
		############# Creating the directory to store the snapshots if they do not already exist #########		
		sun_alt = sun_handle.sun_alt()
		sun_alt_d = float(str(sun_alt).split(":")[0]) - float(str(sun_alt).split(":")[1])/60.0 - float(str(sun_alt).split(":")[2])/3600.0

		now_hour = time.strftime("%H", time.localtime())
		now_date = time.strftime("%Y%m%d", time.localtime())

		if float(sun_alt) < 0.0 and float(now_hour) < float(12.0):
			yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
			folder_date = yesterday.strftime('%Y%m%d')
		else:
			folder_date = now_date

		use_dir = "/scratch/star_spec/"

		IMAGE_DIR_PATH = use_dir + folder_date + "/guide_images/"
		IMAGE_DIR_PATH1 = use_dir + folder_date

		e = ''
		if not os.path.exists(IMAGE_DIR_PATH):
			print clock.timename(), "The directory did not exist!"

			if os.path.exists(IMAGE_DIR_PATH1):
				try:	
					os.mkdir(IMAGE_DIR_PATH)
				except OSError, e:
					print clock.timename(), e
					print clock.timename(), "Could not make image path 1"
			else:
				try:	
					os.mkdir(IMAGE_DIR_PATH1)
					os.mkdir(IMAGE_DIR_PATH)
				except OSError, e:
					print clock.timename(), e
					print clock.timename(), "Could not make image path 2"

			if os.path.exists(IMAGE_DIR_PATH) and e == '':
				print clock.timename(), "The directory was created!"

		sigu_snap_name = IMAGE_DIR_PATH + time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime()) + "_" + self.obs_req_values['object_name'] + "_sigu" + ".fits"
		pugu_snap_name = IMAGE_DIR_PATH + time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime()) + "_" + self.obs_req_values['object_name'] + "_pugu" + ".fits"

		if conf.use_sigu == 1:
			try:
				sigu.exec_action("snap", [sigu_snap_name])	
			except Exception, e:
				print clock.timename(), e
				print clock.timename(), "Could not take a snapshot of sigu "

			### Determine seeing value and insert value to database
			try:
				self.seeing_from_sigu(sigu_snap_name)
			except Exception, e:
				pass
				#print e
				#print "Could not determine seeing from sigu image ", clock.obstimeUT()	

		if conf.use_pugu == 1:
			try:
				pugu.exec_action("snap", [pugu_snap_name])	
			except Exception, e:
				print clock.timename(), e
				print clock.timename(), "Could not take a snapshot of pugu "

			### Determine flux level and insert value to database
			try:
				self.flux_from_pugu(pugu_snap_name)
			except Exception, e:
				pass
				#print e
				#print "Could not determine flux level from pugu image ", clock.obstimeUT()


		#print "Converting and cleaning sigu image to png ", clock.obstimeUT()
		if conf.use_sigu == 1:
			try:
				sigu_im2 = pyfits.getdata(sigu_snap_name)
				#sigu_im2 = cleaner.clean_im_array(sigu_im,1)
				#sigu_im2 = ndim.filters.median_filter(sigu_im, 3)
				fig = plt.figure()
				fig.set_size_inches(4, 3)
				ax = plt.Axes(fig, [0., 0., 1., 1.])
				ax.set_axis_off()
				fig.add_axes(ax)
				ax.imshow(sigu_im2, cmap='gray', interpolation="nearest", vmin=0, vmax=300)
				plt.savefig(sigu_snap_name.split('.fits')[0] +".png")
				plt.close()
			except Exception,e:
				pass
				#print e

		#try:
		#	exec_str = "scp %s madsfa@srf:/var/www/new_web_site/images/guide_images/slit_display.png" % (sigu_snap_name.split('.fits')[0] +".png")
		#	os.popen(exec_str)
		#except Exception, e:
		#	print e

		#print "Converting and cleaning pugu image to png ", clock.obstimeUT()
		if conf.use_pugu == 1:
			try:
				pugu_im2 = pyfits.getdata(pugu_snap_name)
				#pugu_im2 = cleaner.clean_im_array(pugu_im,1)
				#pugu_im2 = ndim.filters.median_filter(pugu_im, 3)
				fig = plt.figure()
				fig.set_size_inches(3, 3)
				ax = plt.Axes(fig, [0., 0., 1., 1.])
				ax.set_axis_off()
				fig.add_axes(ax)
				ax.imshow(pugu_im2, cmap='gray', interpolation="nearest", vmin=0, vmax=150)
				plt.savefig(pugu_snap_name.split('.fits')[0] +".png")
				plt.close()
			except Exception,e:
				pass
				#print e

		#try:
		#	exec_str = "scp %s madsfa@srf:/var/www/new_web_site/images/guide_images/pupil_display.png" % (pugu_snap_name.split('.fits')[0] +".png")
		#	os.popen(exec_str)
		#except Exception, e:
		#	print e
		
		#print "Done snapping sigu and pugu images at: ", clock.obstimeUT()
	
		### CONVERT TO jpg:
		#try:
		#	os.popen("convert %s -normalize %s" % (sigu_snap_name, sigu_snap_name.split('.fits')[0] +".jpg"))
		#	os.popen("convert %s -normalize %s" % (pugu_snap_name, pugu_snap_name.split('.fits')[0] +".jpg"))
		#except Exception, e:
		#	print e
		#	print "Could not take a snapshot of pugu ", clock.obstimeUT()	

		return 1


	def snap_sigu(self):
		#print "Snapping a sigu image at: ", clock.obstimeUT()
		############# Creating the directory to store the snapshots if they do not already exist #########		
		sun_alt = sun_handle.sun_alt()
		sun_alt_d = float(str(sun_alt).split(":")[0]) - float(str(sun_alt).split(":")[1])/60.0 - float(str(sun_alt).split(":")[2])/3600.0

		now_hour = time.strftime("%H", time.localtime())
		now_date = time.strftime("%Y%m%d", time.localtime())

		if float(sun_alt) < 0.0 and float(now_hour) < float(12.0):
			yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
			folder_date = yesterday.strftime('%Y%m%d')
		else:
			folder_date = now_date

		use_dir = "/scratch/star_spec/"

		IMAGE_DIR_PATH = use_dir + folder_date + "/guide_images/"
		IMAGE_DIR_PATH1 = use_dir + folder_date

		e = ''
		if not os.path.exists(IMAGE_DIR_PATH):
			print clock.timename(), "The directory did not exist!"

			if os.path.exists(IMAGE_DIR_PATH1):
				try:	
					os.mkdir(IMAGE_DIR_PATH)
				except OSError, e:
					print clock.timename(), e
					print clock.timename(), "Could not make image path 1"
			else:
				try:	
					os.mkdir(IMAGE_DIR_PATH1)
					os.mkdir(IMAGE_DIR_PATH)
				except OSError, e:
					print clock.timename(), e
					print clock.timename(), "Could not make image path 2"

			if os.path.exists(IMAGE_DIR_PATH) and e == '':
				print clock.timename(), "The directory was created!"

		sigu_snap_name = IMAGE_DIR_PATH + self.obs_req_values['object_name'] + "_sigu_" + time.strftime("%H-%M-%S", time.gmtime()) + ".fits"

		try:
			sigu.exec_action("snap", [sigu_snap_name])	
		except Exception, e:
			print clock.timename(), e
			print clock.timename(), "Could not take a snapshot of sigu "	


		try:
			sigu_im2 = pyfits.getdata(sigu_snap_name)
			#sigu_im2 = cleaner.clean_im_array(sigu_im,1)
			#sigu_im2 = ndim.filters.median_filter(sigu_im, 3)
			fig = plt.figure()
			fig.set_size_inches(4, 3)
			ax = plt.Axes(fig, [0., 0., 1., 1.])
			ax.set_axis_off()
			fig.add_axes(ax)
			ax.imshow(sigu_im2, cmap='gray', interpolation="nearest", vmin=0, vmax=300)
			plt.savefig(sigu_snap_name.split('.fits')[0] +".png")
			plt.close()
		except Exception,e:
			pass
			#print e

		#try:
		#	exec_str = "scp %s madsfa@srf:/var/www/new_web_site/images/guide_images/slit_display.png" % (sigu_snap_name.split('.fits')[0] +".png")
		#	os.popen(exec_str)
		#except Exception, e:
		#	print e

		#print "Done snapping sigu at: ", clock.obstimeUT()


		### CONVERT TO jpg:
		#try:
		#	os.popen("convert %s -normalize %s" % (sigu_snap_name, sigu_snap_name.split('.fits')[0] +".jpg"))
		#except Exception, e:
		#	print e
		#	print "Could not take a snapshot of pugu ", clock.obstimeUT()	

		return 1


	def seeing_from_sigu(self, sigu_file_name):

		#print "Trying to determine the seeing from a sigu image at: ", clock.obstimeUT()
		sys.stdout.flush()

		new_im, tmp_hdr = pyfits.getdata(sigu_file_name, header=True)
		new_im = cleaner.clean_im_array(new_im, 1)

		try:
			y1,x1,y2,x2 = self.determine_spots(new_im)
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), "Could not get the coorindates of the two sigu guide spots"

			x1 = 252
			y1 = 136

			x2 = 68
			y2 = 138

#		x1 = 252
#		y1 = 136

#		x2 = 68
#		y2 = 138

	#	print y1,x1,y2,x2

		e = ""
		param1 = 0
		#print "Calculating first gauss at: ", clock.obstimeUT()

		fwhm1 = 0
		fwhm2 = 0
		fwhm3 = 0
		fwhm4 = 0
		param1 = 0
		try:
			param1 = mfa.fit_gauss_circular([y1-30,x1-30],new_im[y1-30:y1+30, x1-30:x1+30])
		except Exception,e:
			pass
			#print e

		if e == "" and param1 != 0:
			#print "X-Pos: ", param[4]
			#print "Y-Pos: ", param[3]
	#		print "Gaus FWHM 1: ", param1[5] * 0.117 * (37./41.) # 0.24 = pixel scale of 0.12 and 2x2 binning - Used for old Prosilica guider, 0.117 is pixel scale for new 
			fwhm1 = param1[5] * 0.24 * (37./41.)

		param2 = 0
		#print "Calculating second gauss at: ", clock.obstimeUT()
		try:
			param2 = mfa.fit_gauss_circular([y2-30,x2-30],new_im[y2-30:y2+30, x2-30:x2+30])
		except Exception,e:
			pass
			#print e

		if e == "" and param2 != 0:
			#print "X-Pos: ", param[4]
			#print "Y-Pos: ", param[3]
	#		print "Gaus FWHM 2: ", param2[5] * 0.117 * (37./41.) # 0.24 = pixel scale of 0.12 and 2x2 binning - Used for old Prosilica guider, 0.117 is pixel scale for new 
			fwhm2 = param2[5] * 0.24 * (37./41.)

		param3 = 0
		try:
			coeffs = [param1[2], 30, 1.0]
			param3 = mfa.fit_with_2d_gauss(range(60),new_im[param1[3],param1[4]-30:param1[4]+30] + new_im[param1[3]-30:param1[3]+30,param1[4]] - numpy.median(new_im), coeffi = coeffs)
		except Exception,e:
			pass
			#print e


		try:
			X3 = numpy.array(range(600)) / 10.
			Y3 = param3[3]*numpy.exp(-(X3-param3[2])**2/(2.*param3[4]**2))
			fwhm3 = 2.3548 * numpy.abs(param3[4]) * 0.117 * (37./41.) # 0.24 = pixel scale of 0.12 and 2x2 binning - Used for old Prosilica guider, 0.117 is pixel scale for new 
	#		print "FWHM 3 from 2D gauss: ",fwhm3
		except Exception,e:
			pass
			#print e

		param4 = 0
		try:
			coeffs = [param2[2], 30, 1.0]
			param4 = mfa.fit_with_2d_gauss(range(60),new_im[param2[3],param2[4]-30:param2[4]+30] + new_im[param2[3]-30:param2[3]+30,param2[4]] - numpy.median(new_im), coeffi = coeffs)
		except Exception,e:
			pass
			#print e


		try:
			X4 = numpy.array(range(600)) / 10.
			Y4 = param4[3]*numpy.exp(-(X4-param4[2])**2/(2.*param4[4]**2))
			fwhm4 = 2.3548 * numpy.abs(param4[4]) * 0.117 * (37./41.)	# 0.24 = pixel scale of 0.12 and 2x2 binning - Used for old Prosilica guider, 0.117 is pixel scale for new 
	#		print "FWHM 4 from 2D gauss: ",fwhm4
		except Exception,e:
			pass
			#print e

		try:
			fwhm_array = []
			if round(fwhm1,1) in (numpy.array(range(3,50)) / 10.):
				fwhm_array.append(fwhm1)
			if round(fwhm2,1) in (numpy.array(range(3,50)) / 10.):
				fwhm_array.append(fwhm2)
			if round(fwhm3,1) in (numpy.array(range(3,50)) / 10.):
				fwhm_array.append(fwhm3)
			if round(fwhm4,1) in (numpy.array(range(3,50)) / 10.):
				fwhm_array.append(fwhm4)

			if len(fwhm_array) >=1:
				seeing_value = numpy.min(fwhm_array)
				seeing_index = numpy.where(numpy.array(fwhm_array) == numpy.min(fwhm_array))[0]

				seeing_bad_value = numpy.max(fwhm_array)
				seeing_bad_index = numpy.where(numpy.array(fwhm_array) == numpy.max(fwhm_array))[0]
	
				#print "Using FWHM: ", seeing_value 
			else:
				seeing_value = 0	
		except Exception,e:
			pass
			#print e
			seeing_value = 0	

		create_sigu_info_plot = "no"
		if create_sigu_info_plot == "yes":
			try:
				#print "Try to make information sigu seeing plot", clock.obstimeUT()

				try:
					img_eq = mfa_exposure.equalize_hist(new_im / numpy.max(new_im))
					im_to_disp = img_eq
					im_to_disp[0:80,:] = 0
					im_to_disp[-50:-1,:] = 0
					v_max = numpy.max(im_to_disp)
				except Exception,e:
					#print e
					#print "Could not make it eq hist"
					im_to_disp = new_im
					v_max = 300

				fig = plt.figure(figsize=(3.0, 3.0 * new_im.shape[0] / new_im.shape[1]), frameon=False)
				ax = plt.Axes(fig, [0., 0., 1., 1.])
				ax.set_axis_off()
				fig.add_axes(ax)
		
		#		ax.imshow(new_im, cmap='gray', interpolation="nearest", vmin=0, vmax=300, origin="lower", aspect='normal')
				im = ax.imshow(im_to_disp, origin="lower", vmin=0, vmax=v_max)
				im.set_cmap('bone')

				limits = ax.axis()

				try:
					scale_factor = numpy.max([param3[3], param4[3]]) * (1./ 70.)

					ax.plot(numpy.array(range(60))+param1[4]-30, (new_im[param1[3], param1[4]-30:param1[4]+30] + new_im[param1[3]-30:param1[3]+30,param1[4]] - 2 * numpy.median(new_im)) / scale_factor, "g-", linewidth=3)
					ax.plot(numpy.array(range(60))+param2[4]-30, (new_im[param2[3], param2[4]-30:param2[4]+30] + new_im[param2[3]-30:param2[3]+30,param2[4]] - 2 * numpy.median(new_im)) / scale_factor, "y-", linewidth=3)
					ax.plot(X3+param1[4]-30,Y3 / scale_factor, "w--", linewidth=2)
					ax.plot(X4+param2[4]-30,Y4 / scale_factor, "m--", linewidth=2)
				except Exception,e:
					pass
					#print e
					#print "Could not make gauss plots"

				try:
					circ = plt.Circle((param1[4],param1[3]), radius=param1[5] / 2.0, alpha =.7, color='r')
					circ2 = plt.Circle((param2[4],param2[3]), radius=param2[5] / 2.0, alpha =.7, color='b')

					ax.axis(limits)

					ax.add_patch(circ)
					ax.add_patch(circ2)
				except Exception,e:
					pass
					#print e
					#print "Could not make gauss circle plots"

				try:
					ax.text(new_im.shape[1] / 2, new_im.shape[0]-15, "Best Seeing%s = %s''" % (seeing_index+1, numpy.round(seeing_value,2)), size=10, horizontalalignment='center', verticalalignment='center', color="yellow")
					ax.text(new_im.shape[1] / 2, new_im.shape[0]-30, "Worst Seeing%s = %s''" % (seeing_bad_index+1, numpy.round(seeing_bad_value,2)), size=8, horizontalalignment='center', verticalalignment='center', color="yellow")

					ax.text(param1[4],param1[3]+30, "1", size=10, horizontalalignment='center', verticalalignment='center', color="red", fontweight='bold')
					ax.text(param2[4],param2[3]+30, "2", size=10, horizontalalignment='center', verticalalignment='center', color="blue", fontweight='bold')
					ax.text(param1[4]+30, 30, "3", size=10, horizontalalignment='center', verticalalignment='center', color="white", fontweight='bold')
					ax.text(param2[4]-30, 30, "4", size=10, horizontalalignment='center', verticalalignment='center', color="magenta", fontweight='bold')
				except Exception,e:
					pass
					#print e
					#print "Could not make draw test on plot"

				plt.savefig(sigu_file_name.split('.fits')[0] +"_info.png")
				plt.close()

				try:
					exec_str = "scp %s madsfa@srf:/var/www/new_web_site/images/guide_images/slit_display.png" % (sigu_file_name.split('.fits')[0] +"_info.png")
					os.popen(exec_str)
				except Exception, e:
					pass
					#print e

				#print "Done creating a sigu info plot", clock.obstimeUT()

			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "Could not create sigu info plot", clock.obstimeUT()



		

#		if fwhm1 * 0.22 > 0.3 and fwhm1 * 0.22 < 5.0 and fwhm2 * 0.22 > 0.3 and fwhm2 * 0.22 < 5.0:
#			print "Using both FWHMs"
#			seeing_value = numpy.min([fwhm1,fwhm2])
			#seeing_value = (fwhm1 + fwhm2) / 2.0  * 0.24 * (37./41.)
#		elif fwhm1 * 0.22 > 0.3 and fwhm1 * 0.22 < 5.0 and (fwhm2 * 0.22 < 0.3 or fwhm2 * 0.22 > 5.0):	
#			print "Using FWHM1 only"		
#			seeing_value = fwhm1 * 0.24 * (37./41.)
#		elif (fwhm1 * 0.22 < 0.3 or fwhm1 * 0.22 > 5.0) and fwhm2 * 0.22 > 0.3 and fwhm2 * 0.22 < 5.0:		
#			print "Using FWHM2 only"	
#			seeing_value = fwhm2 * 0.24 * (37./41.)
#		else:
#			seeing_value = 0

#		print "Seeing value was: %f at %s " % (seeing_value, clock.obstimeUT())
		sys.stdout.flush()

		# Update weather_station table in database (ACC HAIL VALUE = wxt520_hail_acc:
		#print "Now trying to collect seeing from last 5 minutes at: ", clock.obstimeUT()
		try:
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, st_db, db_user, db_password))
			curr = conn.cursor()
			stmt = "SELECT extra_param_1 FROM tenerife_tel_temps WHERE extra_param_1 > 0.5 and extra_param_1 < 5.0 and ins_at > (current_timestamp - INTERVAL '5 minutes')"
			curr.execute(stmt)		
			output = curr.fetchall()
			curr.close()
		except Exception, e:
			print clock.timename(), "Could not collect data from the database: ", e
		#print "Done collecting seeing data from db at: ", clock.obstimeUT()

		seeing_values = []
		#print len(output)
		for line in output:
			seeing_values.append(line[0])
		seeing_values.append(seeing_value)

		median_value = numpy.median(seeing_values)
		ii = numpy.where(numpy.array(seeing_values) < median_value + 1.0)
		seeing_values = numpy.array(seeing_values)[ii[0]]
		jj = numpy.where(numpy.array(seeing_values) > median_value - 1.0)
		mean_value = numpy.mean(seeing_values[jj[0]])

		run_mean_seeing = mean_value
	#	run_mean_seeing = numpy.mean(seeing_values)

		if math.isnan(run_mean_seeing):
			run_mean_seeing = seeing_value

		if seeing_value > 0.3 and seeing_value < 5.0 and math.isnan(run_mean_seeing) == False:
			#print "Now updating the database with seeing data at: ", clock.obstimeUT()
			sys.stdout.flush()

			insert_to_database = True
			if insert_to_database == True:

				try:
					conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, st_db, db_user, db_password))
					curr = conn.cursor()
					stmt = "UPDATE tenerife_tel_temps SET (extra_param_1, extra_param_2) = (%s, %s) WHERE ins_at = (SELECT max(ins_at) FROM tenerife_tel_temps)" % (seeing_value, run_mean_seeing)
					curr.execute(stmt)		
					conn.commit()
					curr.close()
				except Exception, e:
					print clock.timename(), "Could not update the database: ", e	

				try:
					conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, st_db, db_user, db_password))
					curr = conn.cursor()
					stmt = "UPDATE ccd_header SET (seeing_curr, seeing_mean, ins_at) = (%s, %s, '%s') WHERE ccd_header_id = (SELECT max(ccd_header_id) FROM ccd_header)" % (seeing_value, run_mean_seeing, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
					curr.execute(stmt)		
					conn.commit()
					curr.close()
				except Exception, e:
					print clock.timename(), "Could not update the database: ", e

		#print "Done determining the seeing at: ", clock.obstimeUT()


	def determine_spots(self, cleaned_sigu_array):
		"""
			@breif: This function determines the to highest values in each side of a image array and returns the coordinates in the image of those two points.
		"""

		data = cleaned_sigu_array

#		im_part_1 = data[50:,:149]
#		im_part_2 = data[50:,150:]
		im_part_1 = data[50:,:300]
		im_part_2 = data[50:,300:]

		spot1 = numpy.where(data == numpy.max(im_part_1))
		spot2 = numpy.where(data == numpy.max(im_part_2))

		x1 = 0
		y1 = 0
		mean1 = 0
		x2 = 0
		y2 = 0
		mean2 = 0

		#### First spot:
		if len(spot1[0]) == 1:
			x1 = spot1[0][0]
			y1 = spot1[1][0]
		else:
			for i1 in range(len(spot1)):
				x = spot1[0][i1]
				y = spot1[1][i1]
	
				try:
					mean_surr = numpy.mean([data[x + 1, y], data[x, y + 1], data[x, y - 1], data[x - 1, y], data[x - 1, y - 1], data[x + 1, y + 1], data[x + 1, y - 1], data[x - 1, y + 1]])
				except Exception,e:
					print e
				else:
					if mean_surr > mean1 and y < 300:
						x1 = x
						y1 = y

						mean1 = mean_surr	
	
		#### Seconds spot:
		if len(spot2[0]) == 1:
			x2 = spot2[0][0]
			y2 = spot2[1][0]
		else:
			for i1 in range(len(spot2)):
				x = spot2[0][i1]
				y = spot2[1][i1]	
				try:
					mean_surr = numpy.mean([data[x + 1, y], data[x, y + 1], data[x, y - 1], data[x - 1, y], data[x - 1, y - 1], data[x + 1, y + 1], data[x + 1, y - 1], data[x - 1, y + 1]])
				except Exception,e:
					print e
				else:
					if mean_surr > mean2 and y > 300:
						x2 = x
						y2 = y

						mean2 = mean_surr

		return x1,y1,x2,y2


	def flux_from_pugu(self, pugu_file_name):

		if ".fits" in pugu_file_name and "pugu" in pugu_file_name:

			#print "Trying to determine flux level from: %s, at: %s" % (pugu_file_name, clock.obstimeUT())

			try:
				new_im, tmp_hdr = pyfits.getdata(pugu_file_name, header=True)

				new_im = cleaner.clean_im_array(new_im, 1)

				background_mean = numpy.mean(new_im[:,0:40])

				pugu_im = new_im * self.pugu_mask

				hh = numpy.where(numpy.array(pugu_im) > 0.0)	
				all_mean = numpy.mean(pugu_im[hh])

				pugu_im1 = pugu_im[:,0:self.pugu_center_X]
				pugu_im2 = pugu_im[:,self.pugu_center_X:-1]
		
				ii = numpy.where(numpy.array(pugu_im1) > 0.0)
				jj = numpy.where(numpy.array(pugu_im2) > 0.0)

				mean_value = numpy.mean(pugu_im1[ii]) - background_mean
				mean_value2 = numpy.mean(pugu_im2[jj]) - background_mean

				if mean_value > 3.0 and mean_value2 > 3.0 and mean_value < 500.0 and mean_value2 < 500.0:
					#print "Now updating the database with pupil flux data at: ", clock.obstimeUT()
					sys.stdout.flush()
					try:
						conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, st_db, db_user, db_password))
						curr = conn.cursor()
						stmt = "UPDATE tenerife_tel_temps SET (extra_param_3, extra_param_4) = (%s, %s) WHERE ins_at = (SELECT max(ins_at) FROM tenerife_tel_temps)" % (mean_value, mean_value2)
						curr.execute(stmt)		
						conn.commit()
						curr.close()
					except Exception, e:
						print clock.timename(), "Could not update the database: ", e		

					try:
						conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, st_db, db_user, db_password))
						curr = conn.cursor()
						stmt = "UPDATE ccd_header SET (pupil_flux_left, pupil_flux_right, ins_at) = (%s, %s, '%s') WHERE ccd_header_id = (SELECT max(ccd_header_id) FROM ccd_header)" % (mean_value, mean_value2, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
						curr.execute(stmt)		
						conn.commit()
						curr.close()
					except Exception, e:
						print clock.timename(), "Could not update the database: ", e	

				#print "Done determining flux level of pugu image at: %s" % (clock.obstimeUT())	

			except Exception,e:
				print clock.timename(), e
				#print "Could not determine flux level of pugu image at: ", clock.obstimeUT()

		return 1	


	def repoint_with_skycam(self, req_no):
		print clock.timename(), "Now trying to repoint to coordinates determined by skycam..."
		sys.stdout.flush()
		e = ''

		try:
			server = xmlrpclib.ServerProxy('http://hw.prv:8035')	
		except Exception, e:
			print clock.timename(), "Could not update the database: ", e	

		try:
			value = server.acquire_and_solve("",10)
		except Exception, e:
			print clock.timename(), "Could not update the database: ", e	

		if e == '' and type(value) != int:
			if len(value) == 2:
				if value[0] == 1:
					print clock.timename(), "An image was acquired to: ", value[1]
				elif value[0] == 2:
					print clock.timename(), "An image was acquired to: ", value[1], " but the image was not solved!"
					return 0
				else:
					return 0

			else:
				return 0
		else:
			return 0

		try:
			tmp_im, tmp_hdr = pyfits.getdata(value[1], header=True)
		except Exception, e:
			print clock.timename(), "Could not update the database: ", e
			return 0

		### Reads pointing coordinates from header.
		ra_object = song_convert_coor.COOR_CONVERTER().convert_ra(tmp_hdr["TEL_RA"])
		dec_object = song_convert_coor.COOR_CONVERTER().convert_dec(tmp_hdr["TEL_DEC"])

		print clock.timename(), "Skycam header coordinates ra: ", tmp_hdr["TEL_RA"]
		print clock.timename(), "Repoint to new coordinates ra: ", ra_object
		print clock.timename(), "Skycam header coordinates dec: ", tmp_hdr["TEL_DEC"]
		print clock.timename(), "Repoint to new coordinates dec: ", dec_object
		
		moon_handle = song_star_checker.moon_pos(site=m_conf.song_site)
		sun_handle = song_star_checker.sun_pos(site=m_conf.song_site)
		star_handle = song_star_checker.star_pos(site=m_conf.song_site)

		moon_alt = moon_handle.moon_alt()
		moon_phase = moon_handle.moon_phase()

		object_alt = star_handle.star_alt(ra_object,dec_object)
		moon_dist = moon_handle.moon_dist(ra_object,dec_object)
		sun_dist = sun_handle.sun_dist(ra_object,dec_object)

		sun_alt = sun_handle.sun_alt()
		if float(str(object_alt).split(":")[0]) < m_conf.telescope_min_altitude:
			self.update_or("constraint_4", "'Object too low'", "req_no", req_no)
			return 0

		if float(str(moon_dist).split(":")[0]) < m_conf.tel_dist_to_moon:
			self.update_or("constraint_4", "'Moon too close'", "req_no", req_no)
			return 0

		if float(str(sun_dist).split(":")[0]) < m_conf.tel_dist_to_sun:
			self.update_or("constraint_4", "'Sun too close'", "req_no", req_no)
			return 0

		sys.stdout.flush()

		#### Test if the telescope is currently tracking. 
		track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Observer")
		motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer") 
		print clock.timename(), "The motion state of the telescope is currently: ", motion_state

		if float(track_value) == float(1.0):
			print clock.timename(), "Stop tracking..."
			track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Observer")

		# Set ZD and AZ offsets to zero:
		current_az_offset = float(comm2tcs_read.GET_TSI().get_position_instrumental_az_offset(sender="Observer"))
		current_zd_offset = float(comm2tcs_read.GET_TSI().get_position_instrumental_zd_offset(sender="Observer"))
		if current_az_offset != float(0.0):
			comm2tcs_write.SET_TSI().set_position_instrumental_az_offset(param=float(0.0),sender="Observer")
		if current_zd_offset != float(0.0):
			comm2tcs_write.SET_TSI().set_position_instrumental_zd_offset(param=float(0.0),sender="Observer")

		print clock.timename(), "Zenith distance and Azimuth offsets has been set to zero!"
		sys.stdout.flush()

		print clock.timename(), "Setting RA... to %f" % ra_object
		print clock.timename(), "Setting RA... to %s" % coor_handle.convert_ra(ra_object,24)
		comm2tcs_write.SET_TSI().set_object_equatorial_ra(param=float(ra_object),sender="Observer")		
		print clock.timename(), "Setting DEC... to %f" % dec_object
		print clock.timename(), "Setting DEC... to %s" % coor_handle.convert_dec(dec_object)
		comm2tcs_write.SET_TSI().set_object_equatorial_dec(param=float(dec_object),sender="Observer")

		print clock.timename(), "Now the telescope will slew to the coordinates and start tracking"
		value = comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Observer")
		if value != "done":
			return 0
		self.slewing = 1
		sys.stdout.flush()
		track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")

		close_to = False
		while str(track_value) not in ['11', '11.0'] and close_to == False:
			time.sleep(1.0)
			track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
			
			tel_point_dec = comm2tcs_read.GET_TSI().get_position_equatorial_dec_j2000()
			tel_point_ra = comm2tcs_read.GET_TSI().get_position_equatorial_ra_j2000()
			tel_point_alt = comm2tcs_read.GET_TSI().get_position_horizontal_alt()

			dist_to_obj_ra = (numpy.abs(float(tel_point_ra) - float(ra_object))) * 3600.
			dist_to_obj_dec = (numpy.abs(float(tel_point_dec) - float(dec_object))) * 3600.

			print clock.timename(), "Distance to object from telescope: (RA = %s, DEC = %s) arcseconds" % (str(round(dist_to_obj_ra,2)), str(round(dist_to_obj_dec,2)))

		### If we are pointing close to zenith the telescope might report slewing even though it is tracking due to fast az movements. 
		### If pointing is closer than about 2 arcseconds of the object and altitude of the telescope is above 83 degrees:
			if (dist_to_obj_ra < conf.pointing_dist) and (dist_to_obj_dec < conf.pointing_dist):
				print clock.timename(), "The telescope is pointing within %f arcsec of the object and is not reporting slewing yet!" % conf.pointing_dist
				print clock.timename(), "I assume we are there and continue to observe!"
				close_to = True

			sys.stdout.flush()

		self.slewing = 0
		print clock.timename(), "The telescope is now tracking!"
		sys.stdout.flush()

		try:
			telescope_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor"))
		#	set_ao.main(value=telescope_alt)
		except Exception,e:
			print clock.timename(), "Error: ", e	
			print clock.timename(), "AO and Focus guess was not applied correctly... Now trying old way:"		



	#		focus_guess = 2.0 + 0.04 * float(comm2tcs_read.GET_TSI().get_auxiliary_ttelescope(sender="monitor")) + 5.0 / float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor"))
	#		focus_guess = 2.1 + 0.04 * float(comm2tcs_read.GET_TSI().get_auxiliary_ttelescope(sender="monitor")) + 5.0 / float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor"))

			if m_conf.use_temp_from == "m1":
				used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m1(sender="monitor"))
			elif m_conf.use_temp_from == "m2":
				used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m2(sender="monitor"))
			elif m_conf.use_temp_from == "m3":
				used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m3(sender="monitor"))
			elif m_conf.use_temp_from == "tt":
				used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_ttelescope(sender="monitor"))
			elif m_conf.use_temp_from == "out":	
				try:
					weather_output = self.get_db_values("weather_station", ["wxt520_temp1"])
					used_temp = float(weather_output["wxt520_temp1"])
				except Exception, e:
					print clock.timename(), "Error: ", e	
					print clock.timename(), "Using M2 temperature in stead of outside temperature"
					used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m1(sender="monitor"))					

			print clock.timename(), "Temperature used for focus guess: ", used_temp

			telescope_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor"))

			print clock.timename(), "Telescope altitude used for focus guess: ", telescope_alt

			try:
	#			focus_guess = m_conf.tel_focus_function_values[0] + (m_conf.tel_focus_function_values[1] * used_temp) + (m_conf.tel_focus_function_values[2] / telescope_alt**2) + m_conf.tel_focus_function_values[3] / float(self.obs_req_values['magnitude'])
				focus_guess = m_conf.tel_focus_function_values[0] + (m_conf.tel_focus_function_values[1] * used_temp) + (m_conf.tel_focus_function_values[2] / telescope_alt) + m_conf.tel_focus_function_values[3] * float(self.obs_req_values['magnitude'])
			except Exception,e:
				print clock.timename(), "Using old function for guess"
				focus_guess = m_conf.old_tel_focus_function_values[0] + (m_conf.old_tel_focus_function_values[1] * used_temp) + (m_conf.old_tel_focus_function_values[2] / telescope_alt)

			if focus_guess > 1.8 and focus_guess < 3.8:
				print clock.timename(), "Now setting focus offset of telescope to %s" % focus_guess
				print clock.timename(), "and setting focus position of telescope to 0.0"
				comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_z_targetpos(param=0.0,sender="Observer")
				comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_z_offset(param=focus_guess, sender="Observer")
			else:
				print clock.timename(), "Focus guess was too large or too small. The guess was:", focus_guess

		return 1

	def apply_focus_and_ao(self):
		re_ao_er = 0

		if conf.tel_focus_table == 1:
			try:
				print clock.timename(), "Trying to apply focus correction according to altitude"
				comm2tcs_write.SET_TSI().set_pointing_track(param=4)
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "Could not set pointing track to 4"	
				re_ao_er = 1

		if conf.m1_ao_table == 1:
			try:
				print clock.timename(), "Trying to apply AO correction according to altitude"
				comm2tcs_write.SET_TSI().set_pointing_track(param=8)
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "Could not set pointing track to 8"	
				re_ao_er = re_ao_er + 2

##		if re_ao_er == 0:
##			time.sleep(10)
##		elif re_ao_er == 1:				
##			time.sleep(2)
##		elif re_ao_er == 2:				
##			time.sleep(10)

##		focus_guess = 2.0 + 0.04 * float(comm2tcs_read.GET_TSI().get_auxiliary_ttelescope(sender="monitor")) + 5.0 / float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor"))
##		focus_guess = 2.1 + 0.04 * float(comm2tcs_read.GET_TSI().get_auxiliary_ttelescope(sender="monitor")) + 5.0 / float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor"))
#		if m_conf.use_temp_from == "m1":
#			used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m1(sender="monitor"))
#		elif m_conf.use_temp_from == "m2":
#			used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m2(sender="monitor"))
#		elif m_conf.use_temp_from == "m3":
#			used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m3(sender="monitor"))
#		elif m_conf.use_temp_from == "tt":
#			used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_ttelescope(sender="monitor"))
#		elif m_conf.use_temp_from == "out":	
#			try:
#				weather_output = self.get_db_values("weather_station", ["wxt520_temp1"])
#				used_temp = float(weather_output["wxt520_temp1"])
#			except Exception, e:
#				print clock.timename(), "Error: ", e	
#				print clock.timename(), "Using M2 temperature in stead of outside temperature"
#				used_temp = float(comm2tcs_read.GET_TSI().get_auxiliary_temp_m1(sender="monitor"))					

#		print clock.timename(), "Temperature used for focus guess: ", used_temp

#		telescope_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor"))

#		print clock.timename(), "Telescope altitude used for focus guess: ", telescope_alt

#		try:
##			focus_guess = m_conf.tel_focus_function_values[0] + (m_conf.tel_focus_function_values[1] * used_temp) + (m_conf.tel_focus_function_values[2] / telescope_alt**2) + m_conf.tel_focus_function_values[3] / float(self.obs_req_values['magnitude'])
#			focus_guess = m_conf.tel_focus_function_values[0] + (m_conf.tel_focus_function_values[1] * used_temp) + (m_conf.tel_focus_function_values[2] / telescope_alt) + m_conf.tel_focus_function_values[3] * float(self.obs_req_values['magnitude'])
#		except Exception,e:
#			print clock.timename(), "Using old function for guess"
#			focus_guess = m_conf.old_tel_focus_function_values[0] + (m_conf.old_tel_focus_function_values[1] * used_temp) + (m_conf.old_tel_focus_function_values[2] / telescope_alt)

#		if focus_guess > 1.8 and focus_guess < 3.8:
#			print clock.timename(), "Now setting focus offset of telescope to %s" % focus_guess
#			print clock.timename(), "and setting focus position of telescope to 0.0"
#			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_z_targetpos(param=0.0,sender="Observer")
#			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_z_offset(param=focus_guess, sender="Observer")
#		else:
#			print clock.timename(), "Focus guess was too large or too small. The guess was:", focus_guess

		return re_ao_er	

	def set_hexapod(self):

#		hexapod_x = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_x_realpos(sender="Observer")
#		hexapod_y = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_y_realpos(sender="Observer")
#		hexapod_u = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_u_realpos(sender="Observer")
#		hexapod_v = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_v_realpos(sender="Observer")

#		if hexapod_x == hexapod_y and hexapod_y	== hexapod_u and hexapod_u == hexapod_v:
		try:
			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_x_targetpos(param=conf.hexapod_x, sender="Observer")
			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_y_targetpos(param=conf.hexapod_y, sender="Observer")
			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_u_targetpos(param=conf.hexapod_u, sender="Observer")
			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_v_targetpos(param=conf.hexapod_v, sender="Observer")
			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_w_targetpos(param=conf.hexapod_w, sender="Observer")

			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_x_offset(param=0.0, sender="Observer")
			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_y_offset(param=0.0, sender="Observer")
			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_u_offset(param=0.0, sender="Observer")
			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_v_offset(param=0.0, sender="Observer")
			comm2tcs_write.SET_TSI().set_position_instrumental_hexapod_w_offset(param=0.0, sender="Observer")
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), "Could not get the hexapod values"
			return "error"
		else:
			print clock.timename(), "Hexapod values are now set"	
			return "done"


	def check_hexapod(self):

		hexapod_x = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_x_realpos(sender="Observer")
		hexapod_y = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_y_realpos(sender="Observer")
		hexapod_u = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_u_realpos(sender="Observer")
		hexapod_v = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_v_realpos(sender="Observer")

		if numpy.abs(float(hexapod_x) - conf.hexapod_x) > 0.01 or numpy.abs(float(hexapod_y) - conf.hexapod_y) > 0.01 or numpy.abs(float(hexapod_u) - conf.hexapod_u) > 0.01 or numpy.abs(float(hexapod_v) - conf.hexapod_v) > 0.01:

			print clock.timename(), "Hexapod values were not set!!!!"
			print clock.timename(), "Will now try to do so."
			ret_val = self.set_hexapod()

		return "done"

	def stop_tracking(self):

		error = 0
		try:
			#val = sigu.exec_action("stop")	
			os.popen("python /home/obs/programs/guiders/pupil/pugu.py stop")
		except Exception,e:
			print clock.timename(), e
		try:
			track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Monitor")
			motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Monitor")
		except Exception, e:
			print clock.timename(), " Could not collect telescope data" 
			motion_state = "error"
			error = "error"
			return "error"
		
		print clock.timename(), " The motion state of the telescope is currently: ", motion_state

		if float(track_value) != float(0.0) and error == 0:
			print clock.timename(), " Stop tracking..."
			track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")

		return 1


	def shut_down_telescope(self):

		"""
			@brief: Shuts down the telescope.
		"""	
		error = 0

		print clock.timename(), " The obs script will now shut down the telescope..."

		# Test if the telescope is powered on:
		try:
			telescope_state = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor")
		except Exception, e:
			print clock.timename(), " Could not collect telescope data" 
			telescope_state = -1
			error = "error"
			return "error"	

		#Setting status flag in database about telescope shutdown. VALUE to 2.0
		try:
			update_song_database.update("tel_dome", ["extra_param_2"], [2.0], "tel_dome_id")
		except Exception,e:
			print clock.timename(), " Problem setting the status value of shutdown in database: ", e
		else:
			print clock.timename(), " Status flag was set to 2.0 in database"

		if float(telescope_state) == float(0.0): 
			print clock.timename(), " The telescope was not powered on and nothing will be done"
			return error
		else:

			### Test if the telescope is currently tracking. 
			try:
				track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Monitor")
				motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not collect telescope data" 
				motion_state = "error"
				error = "error"
				return "error"

			
			print clock.timename(), " The motion state of the telescope is currently: ", motion_state

			if float(track_value) != float(0.0) and error == 0:
				print clock.timename(), " Stop tracking..."
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")

			##### SET OFFSETS TO ZERO #######
			print "Now setting the Telescope Focus offset to 0.0"
			focus_offset = comm2tcs_read.GET_TSI().get_position_instrumental_focus_offset(sender="Observer") # Asks what the focus offset is.
			if float(focus_offset) != float(0.0) and error == 0:
				focus_cmd_status = comm2tcs_write.SET_TSI().set_position_instrumental_focus_offset(param=0.0,sender="Observer") # Sets the focus offset to 0.0

			print "Now setting the AZ offset to 0.0"
			az_offset = comm2tcs_read.GET_TSI().get_position_instrumental_az_offset(sender="Observer")
			if float(az_offset) != float(0.0):
				az_status = comm2tcs_write.SET_TSI().set_position_instrumental_az_offset(param=0.0,sender="Observer")	# Sets telescope azimuth offset to 0.0

			print "Now setting the ZD offset to 0.0"
			zd_offset = comm2tcs_read.GET_TSI().get_position_instrumental_zd_offset(sender="Observer")
			if float(zd_offset) != float(0.0):
				zd_status = comm2tcs_write.SET_TSI().set_position_instrumental_zd_offset(param=0.0,sender="Observer")	# Sets telescope azimuth offset to 0.0



	##### ALL open parts will be closed in the right order:

			mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
			if float(mirror_cover_state) != float(0.0):
				print clock.timename(), " The mirror covers will now be closed"
				comm2tcs_write.SET_TSI().set_auxiliary_cover_targetpos(param=0,sender="Monitor") # This will open the mirror covers.
				time_out = time.time() + 120.0
				while float(mirror_cover_state) != float(0.0):
					mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
					time.sleep(5)
					if time.time() > time_out:
						print clock.timename(), " The while loop has timed out and the mirror covers are most likely closed!"
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Mirror cover closing timeout!",message="The telescope was shut down and the mirror covers should be closed. The while loop timed out and the mirror covers might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						break
				print clock.timename(), " The mirror covers are now closed"

			flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
			if float(flap_state) != float(0.0):
				print clock.timename(), " The flap will now be closed"
				comm2tcs_write.SET_TSI().set_position_instrumental_dome_flap_targetpos(param=0,sender="Monitor") # This will open the mirror covers.
				time_out = time.time() + 180.0
				while float(flap_state) != float(0.0):
					err_value = comm2tcs_read.GET_TSI().get_telescope_status_global(sender="Observer")
					error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()	
					if int(err_value) == 2 and "timeout" in error_list.lower():						
						print clock.timename(), " The dome did not finish the movement before timeout"
						print clock.timename(), error_list
						print clock.timename(), " The error will now be acknowledged"							
						tel_error_state = comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Observer")	

					flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
					time.sleep(5)
					if time.time() > time_out:
						print clock.timename(), " The while loop has timed out and the flap are most likely closed!"
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Flap closing timeout!",message="The telescope was shut down and the dome flap should be closed. The while loop timed out and the dome flap might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome flap was not closed corretly... Please check")
						send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Flap closing timeout!",message="The telescope was shut down and the dome flap should be closed. The while loop timed out and the dome flap might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						break
				print clock.timename(), " The flap is now closed"


			slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")
			if float(slit_state) != float(0.0):
				print clock.timename(), " The slit will now be closed"
				comm2tcs_write.SET_TSI().set_position_instrumental_dome_slit_targetpos(param=0,sender="Monitor") # This will open the mirror covers.
				time_out = time.time() + 180.0
				while float(slit_state) != float(0.0):
					err_value = comm2tcs_read.GET_TSI().get_telescope_status_global(sender="Observer")
					error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()	
					if int(err_value) == "2" and "timeout" in errorlist.lower():						
						print clock.timename(), " The dome did not finish the movement before timeout"
						print clock.timename(), error_list
						print clock.timename(), " The error will now be acknowledged"							
						tel_error_state = comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Observer")	

					slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")
					time.sleep(5)
					if time.time() > time_out:
						print clock.timename(), " The while loop has timed out and the dome slit are most likely closed!"
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Slit closing timeout!",message="The telescope was shut down and the dome slit should be closed. The while loop timed out and the dome slit might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome slit was not closed corretly... Please check")
						send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Slit closing timeout!",message="The telescope was shut down and the dome slit should be closed. The while loop timed out and the dome slit might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						
						break
				print clock.timename(), " The slit is now closed"


			print clock.timename(), " The telescope will now be parked!"

			error = 0

			# Test if the telescope is powered on:
			try:
				telescope_state = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not collect telescope data" 
				telescope_state = -1
				error = "error"
				return "error"	

			if float(telescope_state) != float(1.0): 
				print clock.timename(), " The telescope was not powered on and nothing will be done"
				return error

			else:
				try:
					track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Monitor")
					motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Monitor")
				except Exception, e:
					print clock.timename(), " Could not collect telescope data" 
					motion_state = "error"
					error = "error"
					return "error"

				print clock.timename(), " The motion state of the telescope is currently: ", motion_state

				if float(track_value) != float(0.0) and error == 0:
					print clock.timename(), " Stop tracking..."
					track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")

				print clock.timename(), " The telescope should have stopped tracking"
				print clock.timename(), " Now the telescope will be parked"
		
				try:
					comm2tcs_write.SET_TSI().set_object_horizontal_alt(param=m_conf.tel_park_alt, sender="Monitor")
					comm2tcs_write.SET_TSI().set_object_horizontal_az(param=m_conf.tel_park_az, sender="Monitor")
				except Exception, e:
					print clock.timename(), " Could not collect telescope data" 
					motion_state = "error"
					error = "error"
					return "error"

		
				print clock.timename(), " The telescope will now move to AZ=%s and ALT=%s" % (str(m_conf.tel_park_az), str(m_conf.tel_park_alt))
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=2,sender="Monitor")
				time.sleep(10)
				track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Monitor")
				warn_time = time.time()
				stop_param = 0
				while str(track_value) not in ['0', '0.0']:
					time.sleep(1.0)
					track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Monitor")
				
					tel_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="Monitor"))
					tel_az = float(comm2tcs_read.GET_TSI().get_position_horizontal_az(sender="Monitor"))
			
					if numpy.abs(tel_alt - m_conf.tel_park_alt) < 1.0 and numpy.abs(tel_az - m_conf.tel_park_az) < 1.0 and str(track_value) not in ['0', '0.0']:
						print clock.timename(), " The telescope is now at the parking position but it is not reporting stopped, Track value: ", str(track_value)
						print clock.timename(), " It will now be asked to stop and continue with whatever!"
						comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")
						return "done"

					if time.time() > warn_time + 120:	# If the telescope has not reached its parking position after 2 minutes....
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS",subject="Telescope park fail!",message="The telescope was asked to park but did not!\n\nSend at: %s\n\n" % clock.obstimeUT())	
						send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The telescope was not parked correctly! Send at: %s" % clock.obstimeUT())
						send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Telescope park fail!",message="The telescope was asked to park but did not!\n\nSend at: %s\n\n" % clock.obstimeUT())	
		
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")

				if track_state != "done":
					print clock.timename(), " The telescope did not park correctly!!!"
					error = 1
				else:
					print clock.timename(), " The telescope is now parked!"

				if error == 0:
					return "done"
				elif error != 0:
					return "error"
				else:
					return "what"


			err_value = comm2tcs_read.GET_TSI().get_telescope_status_global(sender="Monitor") # This checks if there is any errors.
			if str(err_value) != "0":
				print clock.timename(), " Some errors had occured. These will now be fixed (hopefully)"
				error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()	
				print ""
				print clock.timename(), error_list
				print ""
				tel_error_state = comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor") # This will fix the errors/warnings on the telescope if there is any.

			tel_state = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor") # This tells the current state of the telescope ( 0 = powered off, 1 = powered on)
			print clock.timename(), " The status of the telescope is: ", tel_state

			if str(tel_state) != "0.0" and float(slit_state) == float(0.0) and float(flap_state) == float(0.0):
				print clock.timename(), " The telescope will now be powered off."
				tel_ready_state = comm2tcs_write.SET_TSI().set_telescope_ready(param=0,sender="Monitor") # This will power on the telescope.

				shutdown_timeout = time.time() + 120
				while str(tel_state) != "0.0":
					print clock.timename(), " The telescope was not powered off yet!"
					tel_state = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor")
					print clock.timename(), " The telescope state was: ", tel_state
					time.sleep(5)
					if time.time() > shutdown_timeout:
						print clock.timename(), " Telescope shutdown timeout...!"
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS",subject="Telescope shutdown failure!",message="The telescope was asked to shut down but did not!\n\nSend at: %s\n\n" % clock.obstimeUT())	
						send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The telescope was not shut down correctly! Send at: %s" % clock.obstimeUT())
						break

				if str(tel_ready_state) == "done":
					print ""
					print clock.timename(), " The telescope has now been powered off"	
				else:
					print ""
					print clock.timename(), " The telescope did not powered off correctly"
					error = 1
			elif float(slit_state) != float(0.0) or float(flap_state) != float(0.0):
				print ""
				print clock.timename(), " The telescope was not closed correctly and will stay turned on!"				
				error = 1				

			#Setting status flag in database about telescope shutdown. VALUE back to 0.0
			try:
				update_song_database.update("tel_dome", ["extra_param_2"], [0.0], "tel_dome_id")
			except Exception,e:
				print clock.timename(), " Problem setting the status value of shutdown done in database: ", e
			else:
				print clock.timename(), " Status flag was set to 0.0 in database"

			if error == 0:
				return "done"
			elif error != 0:
				return "error"
			else:
				return "what"


	def thread_slew(self):
		self.slewing = 1
		return 1


	def test_function(self):
		slit_offsets = ""
		if int(self.obs_req_values["slit"]) == 5:
			slit_offsets = ["extra_value_1", "extra_value_2"]
		elif int(self.obs_req_values["slit"]) == 6:
			slit_offsets = ["extra_value_3", "extra_value_4"]
		elif int(self.obs_req_values["slit"]) == 8:
			slit_offsets = ["extra_value_5", "extra_value_6"]
		else:
			try:
				print clock.timename(), "Setting guide target of sigu to X=%s, Y=%s" % (str(conf.guide_targets[int(self.obs_req_values["slit"])][0]),str(conf.guide_targets[int(self.obs_req_values["slit"])][1]))
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "Problem in setting the sigu guide target"

		if slit_offsets != 0:	
			try:	
				conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, st_db, db_user, db_password))
				curr = conn.cursor()
				stmt = "SELECT %s, %s FROM maintenance WHERE extra_value_1 != 99.0 and ins_at > (current_timestamp - INTERVAL '2 days') ORDER BY maintenance_id DESC LIMIT 1" % (slit_offsets[0], slit_offsets[1])
				curr.execute(stmt)		
				output = curr.fetchall()
				curr.close()
	
				slit_x_offset = float(output[0][0])
				slit_y_offset = float(output[0][1])

			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "Problem in setting the sigu guide target"			
			try:
				print clock.timename(), "Setting guide target of sigu to X=%s, Y=%s" % (str(conf.guide_targets[int(self.obs_req_values["slit"])][0] + slit_x_offset),str(conf.guide_targets[int(self.obs_req_values["slit"])][1] + slit_y_offset))
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), "Problem in setting the sigu guide target"	




