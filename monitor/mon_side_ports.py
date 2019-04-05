import song_checker
import song_timeclass
import mon_actions
import time
import thread
import song_monitor_config
import song_checker_config
import song_star_checker
import datetime
import bf_2300_controller
import send_song_mail
import psycopg2
import master_config as m_conf

clock = song_timeclass.TimeClass()

class Check_Time(object):
	"""
		@brief: This class handles all checks on the time of day.
	"""
	def __init__(self):
		"""
			Initialization of the time checks.
		"""
		self.mon_time_value = song_monitor_config.mon_side_ports # 1 = do things, 0 = do nothing.
		self.sun_handle = song_star_checker.sun_pos(site=m_conf.song_site) # site=1: Tenerife
		self.verbose = song_monitor_config.verbose
		self.perform_actions = mon_actions.Do_Actions()


	def check_time_and_sun(self, side_port_group_1, side_port_group_2, side_port_group_3, side_port_group_4, telescope_state, slit_state, flap_state, mirror_cover_state, who_did_it_tel,  who_did_it_sp):
		"""
			Checks the Suns position and returns a value corresponding to this.
		"""
		self.side_port_group_1 = side_port_group_1
		self.side_port_group_2 = side_port_group_2
		self.side_port_group_3 = side_port_group_3
		self.side_port_group_4 = side_port_group_4
		self.telescope_state = telescope_state
		self.slit_state = slit_state
		self.flap_state = flap_state
		self.mirror_cover_state = mirror_cover_state
		self.who_did_it_tel = who_did_it_tel
		self.who_did_it_sp = who_did_it_sp 


		############### Ask the bf2300 if the side ports are opened or closed ########################
		try:
			if song_monitor_config.mon_side_ports_actions == 1:
				side_port_1_status = bf_2300_controller.bf_reader().read_input(input_number=1)
				time.sleep(0.5)
				side_port_2_status = bf_2300_controller.bf_reader().read_input(input_number=2)
				time.sleep(0.5)
				side_port_3_status = bf_2300_controller.bf_reader().read_input(input_number=3)
				time.sleep(0.5)
				side_port_4_status = bf_2300_controller.bf_reader().read_input(input_number=4)
				time.sleep(0.5)
				side_port_5_status = bf_2300_controller.bf_reader().read_input(input_number=5)
				time.sleep(0.5)
				side_port_6_status = bf_2300_controller.bf_reader().read_input(input_number=6)
				time.sleep(0.5)
				side_port_7_status = bf_2300_controller.bf_reader().read_input(input_number=7)
			else:
				side_port_1_status = 0
				side_port_2_status = 0
				side_port_4_status = 0
				side_port_6_status = 0

		except Exception, e:
			print clock.timename(), e
			side_port_1_status = e

		if str(side_port_1_status) in ["0","1"]:
			self.side_port_group_1 = int(float(side_port_1_status))
			self.side_port_group_2 = int(float(side_port_2_status))
			self.side_port_group_3 = int(float(side_port_4_status))
			self.side_port_group_4 = int(float(side_port_6_status))
		###############################################################################################

		sun_alt = self.sun_handle.sun_alt()
		if str(sun_alt)[0] == "-":
			 sun_alt_d = float(str(sun_alt).split(":")[0]) - float(str(sun_alt).split(":")[1])/60.0 - float(str(sun_alt).split(":")[2])/3600.0
		elif str(sun_alt)[0] != "-":
			 sun_alt_d = float(str(sun_alt).split(":")[0]) + float(str(sun_alt).split(":")[1])/60.0 + float(str(sun_alt).split(":")[2])/3600.0

		#################################
		#### Get time to next sun set ###
		tmp_time_str2 = datetime.datetime.strptime(str(self.sun_handle.sun_set_next()), "%Y/%m/%d %H:%M:%S")
		time_diff = tmp_time_str2-datetime.datetime.utcnow()
		hours_to_next_sun_set = int(time_diff.days) * 24. + time_diff.seconds / (24.*3600.) * 24
		#### Get time from previous sun set ###
		tmp_time_str2 = datetime.datetime.strptime(str(self.sun_handle.sun_set_pre()), "%Y/%m/%d %H:%M:%S")
		time_diff2 = datetime.datetime.utcnow() - tmp_time_str2
		hours_from_pre_sun_set = int(time_diff2.days) * 24. + time_diff2.seconds / (24.*3600.) * 24
		#################################


		if (hours_to_next_sun_set <= m_conf.open_time_side_port or float(sun_alt_d) <= float(m_conf.close_sun_alt_side_port)) and time.strftime("%m-%d", time.gmtime()) != "12-24":			
			if self.who_did_it_sp == "time":
				print clock.timename(), " The side ports are now allowed to be opened"
				self.who_did_it_sp = "free"	

		elif hours_to_next_sun_set > m_conf.open_time_side_port and float(sun_alt_d) > float(m_conf.close_sun_alt_side_port):
			#############################
			####   Close Side ports  ####			
			#############################

			if song_monitor_config.mon_side_ports_actions == 1:
				if self.side_port_group_1 != 0:
					status_side_port_1 = self.perform_actions.close_side_port(group=1)
					time.sleep(1)

				if self.side_port_group_2 != 0:
					status_side_port_2 = self.perform_actions.close_side_port(group=2)
					time.sleep(1)

				if self.side_port_group_3 != 0:
					status_side_port_3 = self.perform_actions.close_side_port(group=3)
					time.sleep(1)

				if self.side_port_group_4 != 0:
					status_side_port_4 = self.perform_actions.close_side_port(group=4)
					time.sleep(1)

				if (self.side_port_group_1 != 0 or self.side_port_group_2 != 0 or self.side_port_group_3 != 0 or self.side_port_group_4 != 0) and self.who_did_it_sp == "free":
					print clock.timename(), " The side ports will now be closed due to the time of day"
				self.who_did_it_sp = "time"

			else:
				if self.side_port_group_1 != 0:
					print clock.timename(), " The side ports would have been closed due to daylight"
					self.who_did_it_sp = "time"

				if self.side_port_group_1 == 0 and self.verbose == "yes":
					print clock.timename(), " The Sun is above the horizon so the side ports will be kept closed"	
					self.who_did_it_sp = "time"

		return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp


		












			
