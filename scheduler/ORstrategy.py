"""
Strategies for handling ORs
"""

import ConfigParser
import subprocess
import time
import shlex
import logging
import psycopg2 as psql
import song_checker
import ORUtils
import scheduler_config
import datetime
import master_config as m_conf
import comm2tcs_read
import song_timeclass
#import scheduling_module
import thread
import sys

clock = song_timeclass.TimeClass()
gettsi = comm2tcs_read.GET_TSI()
#schedule_handle = scheduling_module.Scheduling()

class defStrat(object):
	"""
	Default strategy.
	"""
	
	def __init__(self):
		"""
		Initialise object. This is done primarily through a configuration file.
		@param config_file: Filename or -handle from which configuration options are read.
		@throws: ConfigParser.Error, ConfigParser.NoSectionError, ConfigParser.NoOptionError
		@return: None
		"""

		self.cfg = scheduler_config

		#logging related options
		loglevels = {'debug': logging.DEBUG, 'info': logging.INFO, 'critical': logging.CRITICAL, 'error': logging.ERROR, 'warning': logging.WARNING}
		self.loglevel = loglevels[self.cfg.level]
		self.loglocation = self.cfg.outstream
		logging.basicConfig(filename=self.loglocation, level=self.loglevel, format='%(levelname)s:(%(asctime)s): %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
	
		#site-specific information
		self.site_num = self.cfg.site_num

		#number of entries to read out at a time, when determining the next OR to execute
		self.readout_lim = self.cfg.readout_lim

		#add three sorting parameters to self.sort_params. they are added in correct order
		self.sort_params = []
		self.sort_params.append(self.cfg.sort_param1)
		#self.sort_params.append(self.cfg.sort_param2)
		#self.sort_params.append(self.cfg.sort_param3)

		self.mode = self.cfg.scheduler_mode

		#connection and table information on the OR-part of the database
		self.ORdb= {}
		self.ORdb['host'] = m_conf.db_host
		self.ORdb['db'] = m_conf.or_db
		self.ORdb['table'] = m_conf.or_table
		self.ORdb['user'] = m_conf.db_user
		self.ORdb['password'] = m_conf.db_password

		self.ORcdb= {}
		self.ORcdb['host'] = m_conf.db_c_host
		self.ORcdb['db'] = m_conf.or_db
		self.ORcdb['table'] = m_conf.or_table
		self.ORcdb['user'] = m_conf.db_user
		self.ORcdb['password'] = m_conf.db_password

		#connection and table information on the status-part of the database
		self.statusdb = {}
		self.statusdb['host'] = m_conf.db_host
		self.statusdb['db'] = m_conf.data_db
		self.statusdb['table'] = m_conf.or_status_table
		self.statusdb['user'] = m_conf.db_user
		self.statusdb['password'] = m_conf.db_password
		
		#script related options
		self.script = {}
		self.script['timeout_overhead'] = self.cfg.timeout_overhead
		self.script['or_script_name'] = self.cfg.or_script_name
		self.script['template_script_name'] = self.cfg.template_script_name
		self.script['sun_script_name'] = self.cfg.sun_script_name
		self.script['sun_fibre_script'] = self.cfg.sun_fibre_script
		self.script['moon_script'] = self.cfg.moon_script

		#checker related options
		self.checker_values = {}
		self.checker = song_checker.Checker()
		
		#allowed values for the weather checker
		if('all' in self.cfg.weather_allowed_values):
			self.checker_values['weather'] = range(128)			
		else:
			self.checker_values['weather'] = [int(a) for a in self.cfg.weather_allowed_values]

		logging.debug('weather-checker values: ' + str(self.checker_values['weather']))
		logging.info('weather-checker values: ' + str(self.checker_values['weather']))
		
		#allowed values for the day-checker
		if('all' in self.cfg.day_allowed_values):
			self.checker_values['day'] = [-1, 1, 0, 2, 3, 4]
		else:
			self.checker_values['day'] = self.cfg.day_allowed_values

		logging.debug('day-checker values: '+str(self.checker_values['day']))
		logging.info('day-checker values: '+str(self.checker_values['day']))
		
		#whether to check if object is observable
		if(self.cfg.object_check == False):
			self.checker_values['object'] = [0, 1]
		else:
			self.checker_values['object'] = [0, ]
		logging.debug('object-checker values: '+str(self.checker_values['object']))
		logging.info('object-checker values: '+str(self.checker_values['object']))

		### Starting the real-time-scheduling thread:
		if self.mode == "advanced":
			self.real_time_scheduling()

		logging.info('Scheduler initialized.')	

	def get_or_values(self, table_name, fields=[], obs_req_nr=""):
		"""
		 @brief: This function collects data from given table in database to a specific observation request.
		 @param req_no: The observation request number.
		"""

		conn = self.connect(self.ORdb)
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

	def update_or(self, parameters="", ins_values="", table_id="req_no", req_no=""):
		"""
		@brief:		    
		@param: 
		
		"""
		if req_no == "":
			stmt_up = "UPDATE obs_request_1 SET (%s) = (%s) WHERE %s = (SELECT max(%s) FROM obs_request_1)" % (str(parameters), str(ins_values), str(table_id), str(table_id))
		else:
			stmt_up = "UPDATE obs_request_1 SET (%s) = (%s) WHERE %s = %s" % (str(parameters), str(ins_values), str(table_id), str(req_no))

		conn = self.connect(self.ORcdb)
		curr = conn.cursor()	

		try:
		    curr.execute(stmt_up)
		except Exception as e:
		    conn.rollback()
		    print("Could not create status in the database. Changes to the status-data has been rolled back.")
		    print e

		conn.commit()
		curr.close()
	     	conn.close()  
		return 1

	def connect(self, conn_dict):
		"""
		Return a psql connection-object constructed using information from conn_dict.
		@param conn_dict: A dictionary containing the (string) entries 'host', 'db', 'user', 'password' used to define the connection
		@return: An alive psql connection object.
		@TODO: Handle connection-problems in a sensible way. Perhaps throwing or catching an exception.
		"""
		#logging.debug('Opening connection to database %s at host %s' % (conn_dict['db'], conn_dict['host']))
		conn = psql.connect("host='%s' dbname='%s' user='%s' password='%s'" % (conn_dict['host'], conn_dict['db'], conn_dict['user'], conn_dict['password']))
		return conn

	def check_status_of_script(self,req_no):
		"""
		This will check the database to see if status has changed of the OR script.
		"""
		conn = self.connect(self.statusdb)
		curr = conn.cursor()
		stmt = 'SELECT status FROM %s WHERE req_no=%s' % (self.statusdb['table'], req_no)
		curr.execute(stmt)
		cur_status = curr.fetchone()
		curr.close()
		conn.close()
		return cur_status

	def check_status_of_ors(self):
		"""
		This will check the database to see if any ORs are executing.
		"""
		conn = self.connect(self.statusdb)
		curr = conn.cursor()
		stmt = "SELECT req_no FROM %s WHERE status='exec'" % (self.statusdb['table'])
		curr.execute(stmt)
		cur_status = curr.fetchone()
		curr.close()
		conn.close()
		return cur_status


	def determine_next(self):
		"""
		Determine what OR is next in line to be executed. Return OR-id, or -1 if none is available.
		@return: ID of next OR to be executed.
		"""

		conn = self.connect(self.statusdb)
		curr = conn.cursor()
		stmt = "SELECT req_no FROM %s WHERE status='wait'" % (self.statusdb['table'], )
		curr.execute(stmt)
		or_list = curr.fetchall()
		list_of_waiting = self.format_list(or_list)
		curr.close()
		conn.close()

		logging.info(or_list)

		conn = self.connect(self.ORdb)
		curr = conn.cursor()
		OR_id = None
		write_val = 0
		
		##### THIS IS WHERE THE SCHEDULER NEEDS TO THINK #######
		if self.cfg.use_main_spec == "yes" and self.cfg.use_blue_spec != "yes":
			stmt = "SELECT req_no, right_ascension, declination, obs_mode, constraint_5, constraint_3, ins_at, object_name, constraint_4 FROM %s WHERE start_window < CURRENT_TIMESTAMP AT TIME ZONE 'UTC-0' AND stop_window > CURRENT_TIMESTAMP AT TIME ZONE 'UTC-0' AND (site=%i OR site=0) AND req_no IN %s ORDER BY %s desc" % (self.ORdb['table'], self.site_num, list_of_waiting, self.sort_params[0]) # New line modified by Mads

		elif self.cfg.use_main_spec == "yes" and self.cfg.use_blue_spec == "yes":
			stmt = "SELECT req_no, right_ascension, declination, obs_mode, constraint_5, constraint_3, ins_at, object_name, constraint_4 FROM %s WHERE start_window < CURRENT_TIMESTAMP AT TIME ZONE 'UTC-0' AND stop_window > CURRENT_TIMESTAMP AT TIME ZONE 'UTC-0' AND (site=%i OR site=0) AND req_no IN %s ORDER BY %s desc" % (self.ORdb['table'], self.site_num, list_of_waiting, self.sort_params[0])


		curr.execute(stmt)

		#########################

		for OR in curr.fetchall():

			good = True
			logging.debug('Checking req_no='+str(OR[0]))

			if OR[8] == "sun-fibre":
				logging.debug('Sun fibre observations will start regardless of other conditions...')		
				if( self.check_status_of_ors() != None and good):
					good = False
					logging.debug('Another OR is executing: OR number: '+str(self.check_status_of_ors()[0]))
					return None
			else:		

				logging.info(str(OR[6] + datetime.timedelta(seconds=int(OR[5])* 60)))

				if self.checker.weather_check()[0] not in self.checker_values['weather']:
					good = False
					logging.debug('Weather too bad for observation. Value of check: '+str(self.checker.weather_check()[0]))
					#logging.info('Weather too bad for observation. Value of check: '+str(self.checker.weather_check()[0]))

				elif(OR[6] + datetime.timedelta(seconds=int(OR[5])* 60) > datetime.datetime.utcnow()):				
					good = False
					try:
						time_diff = (OR[6] + datetime.timedelta(seconds=int(OR[5])* 60)) - datetime.datetime.utcnow()
						logging.info('Request number - %i - is on hold. Will be released in: %s seconds' % (OR[0], str(time_diff.seconds)))
					except Exception,e:
						logging.info('Error when printing the time diff for the OR on hold: %s' % (e))

				elif self.checker.day_check() not in self.checker_values['day'] and good and str(OR[7]).lower() != "sun":
					good = False
					logging.debug('Daytime prevents observation. Value of check: '+str(self.checker.day_check()))
					return None

				elif self.checker.object_check(OR[1], OR[2]) not in self.checker_values['object'] and good and str(OR[7]).lower() != "sun" and str(OR[7]).lower() != "moon" :
					good = False
					logging.debug('Object is not observable. Value of check: '+str(self.checker.object_check(OR[1], OR[2])))
					#logging.info('Object is not observable. Value of check: '+str(self.checker.object_check(OR[1], OR[2])))

				elif( self.check_status_of_ors() != None and good):
					good = False
					logging.debug('Another OR is executing: OR number: '+str(self.check_status_of_ors()[0]))
					#logging.info('Another OR is executing: OR number: '+str(self.check_status_of_ors()[0]))
					return None

				elif( self.checker.check_for_or_start() != 0 and good):
					if self.checker.check_for_or_start() == "[Telescope still tracking]":
						same = self.checker.check_last_observed_target(next_object=OR[0])
						if same == "same":
							print clock.timename(), "The same object is to be observed again..."
						else:
							print clock.timename(), "A -new- object is to be observed..."
	#						bla = settsi.set_pointing_track(param=0, sender="Observer")
	#						track_value = gettsi.get_pointing_track(sender="Observer")
	#						motion_state = gettsi.get_telescope_motion_state(sender="Observer") 
	#						print clock.timename(), "The motion state of the telescope is currently: ", motion_state
	#						if float(track_value) != float(0.0) or str(track_value) in ['11', '11.0']:
	#							good = False
	#							logging.debug('The telescope was still tracking!')
	#							logging.info('The telescope was still tracking!')
	#							return None	
	#						else:
	#							OR_id = OR[0]
	#							break					

					else:
						good = False
						logging.debug('The monitor had not prepared the telescope. Value of check: '+str(self.checker.check_for_or_start()))
						#logging.info('The monitor had not prepared the telescope. Value of check: '+str(self.checker.check_for_or_start()))
						return None

			if (str(OR[3]).lower() == "template"):
				if (self.checker.check_o_star(o_star_name=OR[4], site=1) not in self.checker_values['object'] and good):
					good = False
					logging.debug('O-star is not observable. Value of check: '+str(self.checker.object_check(OR[1], OR[2])))
					#logging.info('Object is not observable. Value of check: '+str(self.checker.object_check(OR[1], OR[2])))

			if(good):	
				OR_id = OR[0]
				break
		
		sys.stdout.flush()	
		curr.close()
		conn.close()

		return OR_id

	def execute(self, OR_id):
		"""
		Execute OR by calling script.
		@param OR_id: ID of OR to execute. This will be passed to the script executed.
		@TODO: Executing script. Catching timed out script. 
		"""

		#### timeout should be something calculated from exptime and number of exposures.....
		#### or observing window...
		or_output = self.get_or_values("obs_request_1", ["stop_window", "constraint_5", "obs_mode", "object_name", "exp_time", "constraint_4"], OR_id)		
		
		conn = self.connect(self.statusdb)
		status = ORUtils.ObservationStatus(table_name=self.statusdb['table'], req_no=OR_id, conn=conn)
		status.update('exec')
		conn.close()

		if or_output['object_name'].lower() == "sun" and or_output['constraint_4'].lower() == "sun-fibre":
			exec_str = 'python %s %i' % (self.script['sun_fibre_script'], OR_id)
			print "\n", clock.timename(), "EXECUTING Sun fibre observations: '%s'" % exec_str
			#exec_str = 'python %s %i' % (self.script['sun_script_name'], OR_id)
			#print "\n", clock.timename(), "EXECUTING Blue Sky observations: '%s'" % exec_str	
		elif or_output['object_name'].lower() == "sun" and or_output['constraint_4'].lower() != "sun-fibre":
			exec_str = 'python %s %i' % (self.script['sun_script_name'], OR_id)
			print "\n", clock.timename(), "EXECUTING Blue Sky observations: '%s'" % exec_str
		elif or_output['obs_mode'].lower() == "template":
			exec_str = 'python %s %i' % (self.script['template_script_name'], OR_id)
			print "\n", clock.timename(), "EXECUTING Template: '%s'" % exec_str
		elif or_output['object_name'].lower() == "moon":
			exec_str = 'python %s %i' % (self.script['moon_script'], OR_id)
			print "\n", clock.timename(), "EXECUTING Moon script: '%s'" % exec_str			
		else:
			exec_str = 'python %s %i' % (self.script['or_script_name'], OR_id)
			print "\n", clock.timename(), "Executing OR = %i" % (OR_id)

		try:
			tmp_time_str2 = datetime.datetime.strptime(str(or_output["stop_window"]), "%Y-%m-%d %H:%M:%S")
			time_diff = tmp_time_str2-datetime.datetime.utcnow()
		except Exception, e:
			print clock.timename(), or_output["stop_window"]
		else:
			lenght_ow = int(time_diff.days) * (24.*3600.) + time_diff.seconds
			print clock.timename(), "Lenght of observing window: ", int(lenght_ow), " seconds or ", int(lenght_ow) / 3600., " hours"
		sys.stdout.flush()
		if or_output['obs_mode'].lower() == "none-iodine":
			overhead = 120
			if int(lenght_ow) - int(or_output['exp_time']) - overhead < 0.0:
				print clock.timename(), "Theres not enough time for the observation to finish in time"
				conn = self.connect(self.statusdb)
				status = ORUtils.ObservationStatus(table_name=self.statusdb['table'], req_no=OR_id, conn=conn)
				status.update('abort')
				conn.close()	
				self.update_or("constraint_4", "'Window past'", "req_no", OR_id)
				return 1

		elif or_output['obs_mode'].lower() == "iodine":
			overhead = 60
			if int(lenght_ow) - int(or_output['exp_time']) - overhead < 0.0:
				print clock.timename(), "Theres not enough time for the observation to finish in time"
				conn = self.connect(self.statusdb)
				status = ORUtils.ObservationStatus(table_name=self.statusdb['table'], req_no=OR_id, conn=conn)
				status.update('abort')
				conn.close()	
				self.update_or("constraint_4", "'Window past'", "req_no", OR_id)
				return 1
				
		#proc = subprocess.Popen(shlex.split(exec_str))

		thr = ORUtils.ExtCommand(shlex.split(exec_str))
#		returncode = thr.run(timeout=self.script['timeout'])
		if or_output['obs_mode'].lower() == "template":
			try:
				returncode = thr.run(timeout=int(3 * 3600))	# If template not finised after 3 hours do something. 
			except Exception, e:
				print clock.timename(), "Error in thread which controls the timeout...."
				print clock.timename(), e
				returncode = 1
		else:
			try:
				returncode = thr.run(timeout=int(lenght_ow)+self.script['timeout_overhead'])
			except Exception, e:
				print clock.timename(), "Error in thread which controls the timeout...."
				print clock.timename(), e
				returncode = 1

		logging.info("Returncode: %s" % (str(returncode)))
		sys.stdout.flush()

		or_status = self.check_status_of_script(OR_id)
		logging.info("Status of OR was: %s" % str(or_status[0]))
	######################################## This was changed by Mads on Oct. 13. 2011 #########################################
		if(returncode == -1):
			logging.warning('Execution of req_no=%i was terminated due to timeout of %i seconds reached.' % (OR_id, int(lenght_ow)))
			print clock.timename(), "This should actually never happen!"
			conn = self.connect(self.statusdb)
			status = ORUtils.ObservationStatus(table_name=self.statusdb['table'], req_no=OR_id, conn=conn)
			status.update('unknown')
			conn.close()

		elif(returncode == 0):
			logging.info('Obs. script was finished before timeout.')
			if or_status[0].strip() == "exec":
				conn = self.connect(self.statusdb)
				status = ORUtils.ObservationStatus(table_name=self.statusdb['table'], req_no=OR_id, conn=conn)
				status.update('unknown')
				conn.close()

		elif (returncode == 1) and or_status[0].strip() == "exec":
			conn = self.connect(self.statusdb)
			status = ORUtils.ObservationStatus(table_name=self.statusdb['table'], req_no=OR_id, conn=conn)
			status.update('unknown')
			conn.close()

		else:
			logging.warning('Execution of req_no=%i completed with an unrecognized returncode: %i' % (OR_id, returncode))
			conn = self.connect(self.statusdb)
			status = ORUtils.ObservationStatus(table_name=self.statusdb['table'], req_no=OR_id, conn=conn)
			status.update('unknown')
			conn.close()
	############################################################################################################################

		del(status)
		sys.stdout.flush()

		
	def handle_next(self):
		"""
		Determine what OR is next in line to be executed, and take appropriate action to execute it.

		"""
#		logging.info('Updating db...')
		self.update_db()
#		logging.info('Aborting past ORs...')
		self.abort_past_req()
#		logging.info('Determine next...')
		OR_id = self.determine_next()
		if(OR_id != None):
			logging.info('Executing OR...')
			self.execute(OR_id)
			logging.info('Done executing OR!')

	def format_list(self, sqlist):
		"""
		Return a string representation of a list of OR-ID's to be used in SQL-queries.
		@example: [[1,], [2,], [3,]] -> '(1,2,3)'
		@param sqlist: Any list of the form [[(number), ], [number(), ]...]
		@return: A string represention of the sqlist of the form '(number, number...)'.
		"""
		if(not sqlist):
			sqlist = [[-1, ]]
		lstr = str(sqlist)
                lstr = lstr.replace("[", "")
                lstr = lstr.replace("]", "")
                lstr = lstr.replace("(", "")
                lstr = lstr.replace(")", "")
		lstr = lstr.replace(",,", ",")
		lstr = lstr.rstrip(",")
                lstr = "("+lstr+")"
		return lstr

	def update_db(self):
		"""
		Update the status-db 
		@return: None
		"""

                #connection and cursor to status-database
                conn = self.connect(self.statusdb)
                curr = conn.cursor()
                curr.execute("SELECT req_no FROM %s WHERE req_no > ((SELECT req_no FROM obs_request_status_1 ORDER BY req_no desc LIMIT 1) - 200) ORDER BY req_no desc" % (self.statusdb['table'], ))
	#	print curr.rowcount
                if(curr.rowcount > 0):
			reqlist = curr.fetchall()
			reqstr = self.format_list(reqlist)
			reqstr =  "AND req_no NOT IN %s" % (reqstr)
                else:
                    reqstr = ""
                    logging.info('Status-table was empty.')
                
		curr.close()
		conn.close()

	#	print reqlist[-1][0], reqlist[0][0]

		conn = self.connect(self.ORdb)
		curr = conn.cursor()
		stmt = "SELECT req_no FROM %s WHERE (site=1) %s AND req_no >= %s" % (self.ORdb['table'], reqstr, reqlist[-1][0])
                curr.execute(stmt)
		new_entries = curr.fetchall()
		curr.close()
		conn.close()
		
	        for req_no in new_entries:
			conn = self.connect(self.statusdb)
			stat = ORUtils.ObservationStatus(self.statusdb['table'], req_no[0], conn)
			logging.info('Inserting status-entry for req_no=%i' % (req_no[0]))
			del(stat)
			conn.close()

	def abort_past_req(self):
		"""
		Set the status of requests with stop_window in the past to aborted. Use ObservationStatus-object to interact and change status-entries in the database.
		@return: None
		"""
		
		#fetch list of overdue requests
		conn = self.connect(self.ORdb)
		curr = conn.cursor()
		#stmt = 'SELECT req_no FROM %s WHERE stop_window<CURRENT_TIMESTAMP' % (self.ORdb['table']) # Original line made by Jonas
		stmt = "SELECT req_no FROM %s WHERE stop_window<CURRENT_TIMESTAMP AT TIME ZONE 'UTC-0'" % (self.ORdb['table']) # New line modified by Mads
		curr.execute(stmt)
		overdue = curr.fetchall()
		conn.close()
		

		#fetch list of requests with status 'wait'
		conn = self.connect(self.statusdb)
		curr = conn.cursor()
		stmt = "SELECT req_no FROM %s WHERE status='wait'" % (self.statusdb['table'])
		curr.execute(stmt)
		waiting = curr.fetchall()

		#go through lists and find numbers OR-IDs that are in both list
                #use a ObservationStatus object to make actual changes. These are committed in a correct way
		for req_no in waiting:
			if req_no in overdue:
				stat = ORUtils.ObservationStatus(self.statusdb['table'], req_no[0], conn)
				stat.update('abort')
				try:
					self.update_or("constraint_4", "'Window past'", "req_no", req_no[0])
				except Exception,e:
					print "Could not update the OR on central..."
					print e
				logging.info('Aborted request %i: Window exceeded!' % (req_no[0]))
				del(stat)

		conn.close()


	def __str__(self):
		"""
		Write out information on object.
		@return: String representation of the object (useful for debugging purposes)
		"""
		s = 'defStrat object\n'
#		s += 'sort_params: \n'
#		s += '\t %s\n' % (str(self.sort_params))
		s += '\t %s' % (str(self.__dict__))
		return s

	def real_time_scheduling(self):
		def check_for_good_object():
			while True:
				self.optimum_obj = schedule_handle.determine_next()
				print clock.timename(), "The optimum object is now: %s" % (self.optimum_obj[6])
				time.sleep(60)
		
		thread.start_new_thread(check_for_good_object, ())

	def insert_backup_OR(self,target_id):
		### Collect all relevant paramters from the project database:
		try:
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.or_db, m_conf.db_user, m_conf.db_password))
			curr = conn.cursor()
			curr.execute("SELECT project_id, right_ascencion, declination, exp_time, obs_mode, no_exp, no_thar_exp, no_target_exp, observer, ra_pm, dec_pm, project_name, magnitude, object_name FROM %s WHERE target_id = %i FROM %s)" % (table, target_id, table))
			project_data = curr.fetchone()
			curr.close()
			conn.close()
		except Exception, e:
			print clock.timename(), " Error: ", e

		if "i2" in project_data[4]:
			obs_request_config.obs_mode = "iodine"
			obs_request_config.no_target_exp = 0
			obs_request_config.no_thar_exp = 0
			obs_request_config.iodine_cell = 3
		elif "i3" in project_data[4]:
			obs_request_config.obs_mode = "iodine"
			obs_request_config.no_target_exp = 0
			obs_request_config.no_thar_exp = 0
			obs_request_config.iodine_cell = 1		#### New iodine cell for testing
		elif "none-iodine" in project_data[4]:
			obs_request_config.obs_mode = "none-iodine"			
			obs_request_config.iodine_cell = 2

		#### Standard values:
		obs_request_config.imagetype		= "STAR"			# Type of image: FLAT, FLATI2, BIAS, THAR, STAR, TEST, ...
		obs_request_config.start_window		= str(datetime.datetime.utcnow())# The fist possible UT-time when observation could start.
		timeout_in = (int(project_data[5]) * int(project_data[3])) + 600 + (int(project_data[6]) * 120)
		obs_request_config.stop_window		= str(datetime.datetime.utcnow() + datetime.timedelta(seconds=timeout_in))		# The last possible UT-time when observation should end.
		obs_request_config.req_prio		= 99				# Request priority in percentage
		obs_request_config.amp_gain		= 2				# Pre amplifying gain value: 0,1,2
		obs_request_config.ang_rot_offset	= 0				# Derotator angle offset.
		obs_request_config.adc_mode		= "false" 			# Atmospheric dispersion corrector on/off (true/false).
		obs_request_config.x_bin		= 1				# Binning on the x axis
		obs_request_config.y_bin		= 1				# Binning on the y axis	
		obs_request_config.x_begin		= 1				# The first pixel on the image on the x axis
		obs_request_config.y_begin		= 1				# The first pixel on the image on the y axis
		obs_request_config.x_end		= 2088				# The last pixel on the image on the x axis
		obs_request_config.y_end		= 2048				# The last pixel on the image on the y axis
		obs_request_config.epoch		= 2000				# Epoch used for object coordinates
		obs_request_config.constraint_1		= 0				# Not in use. Signed integer
		obs_request_config.constraint_2		= 0				# Number of acq spectres
		obs_request_config.constraint_3 	= 0				# Time delay in minutes when acquisition fails
		obs_request_config.constraint_4		= ""				# Error msg
		obs_request_config.constraint_5 	= ""				# Used for template obs
		obs_request_config.site			= 1				# 0 = all, 1 = tenerife
		obs_request_config.req_chain_previous	= 0				# Value to make OR linked to another OR.
		obs_request_config.req_chain_next	= 0				# Value to make OR linked to another OR.
		obs_request_config.no_exp 		= project_data[5]
		obs_request_config.no_target_exp 	= project_data[7]
		obs_request_config.no_thar_exp 		= project_data[6]
		obs_request_config.observer 		= project_data[8]
		obs_request_config.right_ascension	= project_data[1]
		obs_request_config.declination		= project_data[2]
		obs_request_config.ra_pm		= project_data[9]
		obs_request_config.dec_pm		= project_data[10]
		obs_request_config.magnitude		= project_data[12]
		obs_request_config.object_name		= project_data[13]
		obs_request_config.project_name		= project_data[11]
		obs_request_config.project_id		= project_data[0]
		obs_request_config.exp_time		= project_data[3]

		or_values = "( %i, %i, %i, %f, %f, %f, %f, %i, %f, '%s', '%s', '%s', '%s', %i, %f, %i, %i, %i, %i, %i, %i, %i, %i, %i, %i, %i, %i, '%s', %i, '%s', %i, '%s', '%s', %f, %i, %f, '%s', '%s', %i, '%s' )" % (obs_request_config.req_prio, obs_request_config.req_chain_previous, obs_request_config.req_chain_next, obs_request_config.right_ascension, obs_request_config.declination, obs_request_config.ra_pm, obs_request_config.dec_pm, obs_request_config.epoch, obs_request_config.magnitude, obs_request_config.object_name, obs_request_config.imagetype, obs_request_config.observer, obs_request_config.project_name, obs_request_config.project_id, obs_request_config.exp_time, obs_request_config.x_bin, obs_request_config.y_bin, obs_request_config.x_begin, obs_request_config.y_begin, obs_request_config.x_end, obs_request_config.y_end, obs_request_config.no_exp, obs_request_config.no_target_exp, obs_request_config.no_thar_exp, obs_request_config.amp_gain, obs_request_config.readoutmode, obs_request_config.ang_rot_offset, obs_request_config.adc_mode, obs_request_config.iodine_cell, obs_request_config.obs_mode, obs_request_config.slit, obs_request_config.start_window, obs_request_config.stop_window, obs_request_config.constraint_1, obs_request_config.constraint_2, obs_request_config.constraint_3, obs_request_config.constraint_4, obs_request_config.constraint_5, obs_request_config.site, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) )

		conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_c_host, m_conf.or_db, m_conf.db_user, m_conf.db_password))
		curr = conn.cursor()

		params = '(req_prio, req_chain_previous, req_chain_next, right_ascension, declination, ra_pm, dec_pm, epoch, magnitude, object_name, imagetype, observer, project_name, project_id, exp_time, x_bin, y_bin, x_begin, y_begin, x_end, y_end, no_exp, no_target_exp, no_thar_exp, amp_gain, readoutmode, ang_rot_offset, adc_mode, iodine_cell, obs_mode, slit, start_window, stop_window, constraint_1, constraint_2, constraint_3, constraint_4, constraint_5, site, ins_at)'

		try:
			stmt = "INSERT INTO obs_request_1 %s VALUES %s" % (params, or_values)
			curr.execute(stmt)
		except Exception as e:
			conn.rollback()
			print("Could not insert OR in the database. Changes to database has been rolled back.")
			return_value = e
		else:
			conn.commit()
			curr.close()
		     	conn.close()  

			# This returns the request number of the request just inserted. 
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_c_host, m_conf.or_db, m_conf.db_user, m_conf.db_password))
			curr = conn.cursor()

			try:
				or_req_tmp = get_db_values.db_connection().get_fields(curr, db_table, fields=['req_no'])
				return_value = or_req_tmp['req_no']
			except Exception as e:
				conn.rollback()
				print("Could not get OR from the database. Call has been rolled back.")
				return_value = e

			curr.close()
		     	conn.close() 

		# This should add an entry in the status database for the inserted OR:
		self.update_db()

if __name__=='__main__':
	strat = defStrat()
	strat.handle_next()
