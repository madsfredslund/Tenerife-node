import song_checker
import song_timeclass
import mon_actions
import time
import thread
import song_monitor_config
import song_checker_config
import song_star_checker
import comm2tcs_read
import comm2tcs_write
import send_song_mail
import numpy
import set_ao
import master_config as m_conf
import psycopg2
import datetime

sun_handle = song_star_checker.sun_pos(site=m_conf.song_site) # site=1: Tenerife
clock = song_timeclass.TimeClass()

class Check_Telescope(object):
	"""
		@brief: This class handles all checks on the telescope.
	"""
	def __init__(self):
		"""
			Initialization of the telescope checks.
		"""
		self.verbose = song_monitor_config.verbose

		self.check_handle = song_checker.Checker()
		self.perform_actions = mon_actions.Do_Actions()

		self.email_send = 0
		self.second_occurence = 0
		self.dome_second = 0
		self.pc_dome_delay = 0
		self.old_error_list = ""
		self.error_time = 0
		self.no_stars_images = 0
	#	self.dc_pc_time_delay = 0	# Dome controller power cycle time delay

	
	def error_state(self, side_port_group_1, side_port_group_2, side_port_group_3, side_port_group_4, telescope_state, slit_state, flap_state, mirror_cover_state, who_did_it_tel,  who_did_it_sp):
		"""
			This function checks the telescope for critical errors.
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
		self.mirror_cover_timeout = 0

		try:
			if song_monitor_config.mon_telescope_actions == 1:
		        	t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()					
			else:
				return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp

		except Exception, e:
		        print clock.timename(), " An error occured while reading telescope error state"
			return "error"

		error_list = ""
		if self.verbose == "yes" and song_monitor_config.mon_telescope_actions == 1 and str(t_error_state) not in ["0", "0.0"]:
			print clock.timename(), " The telscope global status was: ", t_error_state
			error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()	
			print ""
			print clock.timename(), error_list
			print ""

		##### Return values for Global status:
		# -2: no license data found
		# -1: no telescope hardware found (no connection to a telescope)
		#  0: operational (everything is fine) 
		#  1: PANIC - a severe condition, completely disabling the telscope.
		#  2: ERROR - a serious condition, disabling important parts of the telescope
		#  4: WARNING - a critical condition, which might disable the telescope.
		#  8: INFO - an informal situation, that will not effect the telescope. 

		try:
			self.telescope_state = float(comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor"))
		except Exception,e:
			print clock.timename(), e
			self.telescope_state = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor")	

		if type(self.telescope_state) == numpy.str and str(t_error_state) not in ["0", "0.0"]:
			print clock.timename(), "The state of the telescope did not make sense...: '%s'" % str(self.telescope_state)
			print clock.timename(), "The monitor will now write the state '-1' for the telescope_state to continue"
			self.telescope_state = -1
			

		### If the telescope is put into local mode (-3) the monitor should not try to do anything...:
		if str(t_error_state) in ["0", "0.0"] or float(self.telescope_state) == float(-3.0):
			self.email_send = 0
			self.second_occurence = 0

		elif str(t_error_state) == "-2" and self.email_send == 0 and error_list != self.old_error_list:
			send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="No TSI license!", message="The license to the TSI has run out and no new license data was found...!\n\nContact Astelco and Tau-Tec\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
			if song_monitor_config.send_sms == "yes":
				send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="No TSI license... Astelco and Tau-Tec action needed!")
			if song_monitor_config.send_to_support == "yes":
				send_song_mail.send_mail().sending_an_email(reciever=['support'], sender="SONG_MS" ,subject="No TSI license!", message="The license to the TSI has run out and no new license data was found...!\n\nContact Astelco and Tau-Tec\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))	

			self.email_send = 1		

		elif str(t_error_state) == "-1" and self.email_send == 0 and error_list != self.old_error_list:
			send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Connection to telescope hardware failure!", message="The connection to the telescope control hardware has failed!.\n\nYou might need to call someone on site (night operator) to make a manual power cycle of the main switch on the Astelco control cabinet.\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
			if song_monitor_config.send_sms == "yes":
				send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="Wake up! Connection to telescope control is lost!")
			if song_monitor_config.send_to_support == "yes":
				send_song_mail.send_mail().sending_an_email(reciever=['support'], sender="SONG_MS" ,subject="Connection to telescope hardware failure!", message="The connection to the telescope control hardware has failed!.\n\nYou might need to call someone on site (night operator) to make a manual power cycle of the main switch on the Astelco control cabinet.\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))	

			self.email_send = 1

		elif str(t_error_state) in ["2", "6"] and ('DOME[2]|2:ERR_DeviceError|timeout reading status' in str(error_list) or 'invalid data|2|DOME[2]' in str(error_list) or 'DOME[0];ERR_DeviceError|protocol' in error_list):
			print clock.timename(), " The telescope has reported an error about the dome (power cycle of the dome controller):\n%s\n" % error_list
			if song_monitor_config.send_notifications == "yes" and self.email_send == 0 and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Telescope Error!", message="An error about the dome was raise. This means the dome controller was power cycled!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
				self.email_send = 1

			print clock.timename(), " Now trying to clear the error!"
			try:
				comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear first error
				time.sleep(5)
				comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear second error
			except Exception, e:
				print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 		

			time.sleep(10)	# Sleep 10 seconds for additional errors to occur

			try:
				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
				if str(t_error_state) == "0":
					print clock.timename(), " The error was acknowledge and the warning is cleared!\n"
					self.email_send = 0
				else:
					print clock.timename(), " The error was not acknowledged"
					print clock.timename(), " Now trying to clear the error!"
					try:
						comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear first error
						time.sleep(5)
						comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear second error
					except Exception, e:
						print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 
			except Exception, e:
				print clock.timename(), " An error occured while reading telescope error state"

			try:
				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
				if str(t_error_state) == "0":
					print clock.timename(), " The error was acknowledge and the warning is cleared!\n"
					self.email_send = 0
				else:
					print clock.timename(), " The error was not acknowledged"
			except Exception, e:
				print clock.timename(), " An error occured while reading telescope error state"


			t_error_state = "0"

		elif str(t_error_state) == "2" and "DOME" in str(error_list) and "timeout" in str(error_list).lower() and ("max" in str(error_list).lower() or "min" in str(error_list).lower()):
			print clock.timename(), " The telescope has reported an error about the dome not reaching the end before timeout:\n%s\n" % error_list
			if song_monitor_config.send_notifications == "yes" and self.email_send == 0 and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Telescope Error!", message="An error about the dome was raise. This means the dome did not reach the end (closing/opening) before timeout!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
				self.email_send = 1

			print clock.timename(), " Now trying to clear the error!"
			try:
				comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear first error
				time.sleep(5)
				comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear second error
			except Exception, e:
				print clock.timename(), " Could not send command 'Clear errors' to the tsi" 		

			try:
				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
				if str(t_error_state) == "0":
					print clock.timename(), " The error was acknowledge and the warning is cleared!\n"
					self.email_send = 0
				else:
					print clock.timename(), " The error was not acknowledged"
			except Exception, e:
				print clock.timename(), " An error occured while reading telescope error state"

			t_error_state = "0"

		elif str(t_error_state) == "1" or str(t_error_state) == "2" or str(t_error_state) == "6"  or str(t_error_state) == "5"  or str(t_error_state) == "3"  or str(t_error_state) == "7" and self.who_did_it_tel != "telescope":
			
			if song_monitor_config.send_to_wake_up == "yes" and ("err_phase_watcher" in str(error_list).lower()) and ("undervoltage" in str(error_list).lower()):
				if self.mirror_cover_state == 1 or self.slit_state == 1:
					if self.email_send == 0 and error_list != self.old_error_list:
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Power failure!", message="Errors from the telescope indicates a power failure at the SONG site. The dome or mirror covers were still open and you might need to call the night operator to manually close down!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
						if song_monitor_config.send_sms == "yes":
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="Power failure has occured at the SONG site... Please check and take action!")
						if song_monitor_config.send_to_support == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=['support'], sender="SONG_MS" ,subject="Power failure!", message="Power failure at the SONG site!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))	

						self.email_send = 1
				else:
					if self.email_send == 0:					
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Power failure!", message="Errors from the telescope indicates a power failure at the SONG site. The dome and mirror covers were closed!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))

						self.email_send = 1

				print clock.timename(), " Now trying to clear the error!"
				try:
					comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")	
					time.sleep(5)
					comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")
				except Exception, e:
					print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 	

				try:
					t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
					if str(t_error_state) == "0":
						print clock.timename(), " The Power failure warning was acknowledge and the warning is cleared!\n"
						self.email_send = 0
					else:
						print clock.timename(), " The Power failure warning was not acknowledged"
				except Exception, e:
					print clock.timename(), " An error occured while reading telescope error state"

			elif song_monitor_config.send_to_wake_up == "yes" and self.email_send == 0 and (self.mirror_cover_state == 1 or self.slit_state == 1) and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Telescope Error!", message="A serious condition with the telescope has occured and manual actions are needed!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
				if song_monitor_config.send_sms == "yes":
					send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="A serious condition with the telescope has occured... Please check the log files")
				if song_monitor_config.send_to_support == "yes":
					send_song_mail.send_mail().sending_an_email(reciever=['support'], sender="SONG_MS" ,subject="Telescope Error!", message="A serious condition with the telescope has occured and manual actions are needed!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))	

				self.email_send = 1

			elif self.email_send == 0 and self.mirror_cover_state == 0 and self.slit_state == 0 and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Telescope Error!", message="A serious condition with the telescope has occured and manual actions are needed! Everything was closed down when this mail was send\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))				

				self.email_send = 1

		elif str(t_error_state) == "4" and self.who_did_it_tel != "telescope" and ("gps" in str(error_list).lower()):
			print clock.timename(), " The telescope has reported a warning about the GPS:\n%s\n" % error_list
			if song_monitor_config.send_notifications == "yes" and self.email_send == 0 and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Telescope Warning!", message="A warning about the GPS has occured. Maybe it will go away later... Let's see!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
				self.email_send = 1

			print clock.timename(), " Now trying to clear the GPS warning!"
			try:
				comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")	
				time.sleep(5)
				comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 		

			try:
				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
				if str(t_error_state) == "0":
					print clock.timename(), " The GPS warning was acknowledge and the warning is cleared!\n"
					self.email_send = 0
				else:
					print clock.timename(), " The GPS warning was not acknowledged"
			except Exception, e:
				print clock.timename(), " An error occured while reading telescope error state"

			t_error_state = "0"

		elif str(t_error_state) == "2" and self.who_did_it_tel != "telescope" and ("dome radio connection lost" in str(error_list).lower()):
			print clock.timename(), " The telescope has reported a warning about the connection to the dome:\n%s\n" % error_list
			if song_monitor_config.send_notifications == "yes" and self.email_send == 0 and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Telescope Warning!", message="An error about the connection to the dome... Let's see!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
				self.email_send = 1

			print clock.timename(), " Now trying to clear the error!"
			try:
				comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")	
				time.sleep(5)
				comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not send command 'Clear error' to the tsi" 		

			try:
				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
				if str(t_error_state) == "0":
					print clock.timename(), " The dome connection error was acknowledge and the warning is cleared!\n"
					self.email_send = 0
				else:
					print clock.timename(), " The dome connection error was not acknowledged"
			except Exception, e:
				print clock.timename(), " An error occured while reading telescope error state"

			t_error_state = "0"

		elif str(t_error_state) == "4" and self.who_did_it_tel != "telescope" and ("az" in str(error_list).lower()) and ("err_soft_limit_max" in str(error_list).lower() or "err_soft_limit_min" in str(error_list).lower()):
			print clock.timename(), " The telescope has reported a warning about the Azimuth soft limit:\n%s\n" % error_list
			if song_monitor_config.send_notifications == "yes" and self.email_send == 0 and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Telescope Warning!", message="A warning about reaching the soft limit in azimuth has occured. The telescope will now be stopped and start tracking again which should work... Let's see!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
				self.email_send = 1

			print clock.timename(), " Now trying to fix the warning!"
			print clock.timename(), " Stop tracking..."
			try:
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not send command 'Stop tracking' to the tsi"
			time.sleep(5)
			print clock.timename(), " Start tracking..."
			try:
				comm2tcs_write.SET_TSI().set_pointing_setup_dome_syncmode(param=song_monitor_config.dome_syncmode_value,sender="Mads")
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not send command 'Stop tracking' to the tsi"

			try:
				comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")	
				time.sleep(5)
				comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 		

			try:
				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
				if str(t_error_state) == "0":
					print clock.timename(), " The AZ limit warning was acknowledge and the warning is cleared!\n"
					self.email_send = 0
				else:
					print clock.timename(), " The AZ limit warning was not acknowledged"
			except Exception, e:
				print clock.timename(), " An error occured while reading telescope error state"


		elif str(t_error_state) == "4" and self.who_did_it_tel != "telescope" and "ao_bender" in str(error_list).lower() and "err_soft_limit" in str(error_list).lower():
			print clock.timename(), " The telescope has reported a warning about the AO benders:\n%s\n" % error_list
			if song_monitor_config.send_notifications == "yes" and self.email_send == 0 and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Telescope Warning!", message="A warning about the AO benders has occured and AO offsets will be set to zero. Maybe that helps!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
				self.email_send = 1

			print clock.timename(), " Now trying to set AO offsets to zero!"
			try:
				set_ao.main(value="zero")
			except Exception, e:
				print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 		

			try:
				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
				if str(t_error_state) == "0":
					print clock.timename(), " The AO bender warning was acknowledge and the warning is cleared!\n"
					self.email_send = 0
				else:
					print clock.timename(), " The AO bender warning was not acknowledged"
			except Exception, e:
				print clock.timename(), " An error occured while reading telescope error state"

			t_error_state = "0"


		elif str(t_error_state) == "4" and self.who_did_it_tel != "telescope" and "cover" in str(error_list).lower() and "timeout moving to" in str(error_list).lower():
			print clock.timename(), " The telescope has reported a warning about the mirror covers:\n%s\n" % error_list
			if song_monitor_config.send_notifications == "yes" and self.email_send == 0 and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Telescope Warning!", message="A warning about the mirror covers reaching timeout has occured!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
				self.email_send = 1

			if time.time() > self.mirror_cover_timeout:

				print clock.timename(), " Now trying to clear the warning once!"
				try:
					comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")	
					time.sleep(2)
				except Exception, e:
					print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 	

				try:
					t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
					if str(t_error_state) == "0":
						print clock.timename(), " The mirror cover timeout warning was acknowledge and the warning is cleared!\n"
						self.email_send = 0
					else:
						print clock.timename(), " The mirror cover timeout warning was not acknowledged"
				except Exception, e:
					print clock.timename(), " An error occured while reading telescope error state"

				t_error_state = "0"

			self.mirror_cover_timeout = time.time() + 600


#		elif str(t_error_state) == "4" and self.who_did_it_tel != "telescope" and "no reply to stop command" in str(error_list).lower() and "dome" in str(error_list).lower():
#			print clock.timename(), " The TSI has reported a warning about the dome not reacting to a stop command. The controller will now be power cycled:\n%s\n" % error_list
#			status_pc = self.perform_actions.power_cycle_dome_controller()
#			if status_pc == "done":		
#				print clock.timename(), " The dome controller was power cycled..."
#				if song_monitor_config.send_notifications == "yes" and self.email_send == 0:
#					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="TSI Warning!", message="A warning about the Dome not reacting to a stop command has occured and the dome controller was power cycled. Maybe that helped!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % (error_list, clock.obstimeUT()))
#					self.email_send = 1
#			else:
#				print clock.timename(), " Something did not go well with the power cycle of the dome controller"
#				if song_monitor_config.send_notifications == "yes":						
#					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Dome - telescope out of sync!", message="The telescope and the dome is not pointing to the same direction any more and a power cycle of the dome controller failed!\n\nSend at: %s\n\n" % clock.obstimeUT())
#
#			try:
#				comm2tcs_write.SET_TSI().set_telescope_clear(sender="Monitor")	
#				time.sleep(5)
#				comm2tcs_write.SET_TSI().set_telescope_clear(sender="Monitor")
#			except Exception, e:
#				print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 	
#
#			try:
#				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
#				if str(t_error_state) == "0":
#					print clock.timename(), " The dome warning was acknowledge and the warning is cleared!\n"
#				else:
#					print clock.timename(), " The dome warning was not acknowledged"
#			except Exception, e:
#				print clock.timename(), " An error occured while reading telescope error state"
#
#			t_error_state = "0"

		elif str(t_error_state) == "4" and self.who_did_it_tel != "telescope" and "port_select" in str(error_list).lower() and "both limit switches active" in str(error_list).lower():
			print clock.timename(), " The telescope has reported a warning about the M3 both limit switches active:\n%s\n" % error_list

			if song_monitor_config.send_sms == "yes" and self.email_send == 0 and error_list != self.old_error_list:	#### Quick fix... might need some more for sms handling
				send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="M3 - both limit switches are active... crap!")

			if song_monitor_config.send_notifications == "yes" and self.email_send == 0 and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="M3 - both limit switches active!", message="A warning about the limit switches for M3 was raised...\n\nCRAP!!!!\n\nYou need to call the night operator and follow the manual on what to do!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
				self.email_send = 1

			t_error_state = "0"

		elif str(t_error_state) == "4" and '"DRIVES|0::,SYSTEM|4:CABINET|4:ERR_DeviceWarn|UPS battery low or malfunction|4|CABINET,AUXILIARY|0::,UNKNOWN|0::"' == str(error_list):
			print clock.timename(), " The telescope has reported a warning about the UPS battery level."
			t_error_state = "0"	
		
		elif str(t_error_state) == "4" and self.who_did_it_tel != "telescope" and self.second_occurence == 0:
			print clock.timename(), " A warning had occured for the first time!"

			if song_monitor_config.send_notifications == "yes" and error_list != self.old_error_list:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_error_who, sender="SONG_MS", subject="Telescope (TSI) warning!", message="A warning from the telescope TSI appeared!...\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))

			print clock.timename(), " Now trying to clear the warning!"
			try:
				comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")	
				time.sleep(5)
				comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 		
			time.sleep(3)
			try:
				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
				print clock.timename(), " The error state after trying to clear the warning is: ", t_error_state
			except Exception, e:
				print clock.timename(), " An error occured while reading telescope error state"
				t_error_state = 1

			if str(t_error_state) == "4":
				self.second_occurence = 1
			else:
				self.second_occurence = 0 

			t_error_state = "0"


		elif str(t_error_state) == "4" and self.who_did_it_tel != "telescope" and self.second_occurence == 1:

			# Try to clear the warning!
			track_param = 0
			try:
				track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Monitor")
				motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not collect telescope data" 
				track_value = 5

			if float(track_value) != float(0.0):
				print clock.timename(), " Stop tracking..."
				track_param = 1
				try:
					track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")
				except Exception, e:
					print clock.timename(), " Could not send command 'Stop tracking' to the tsi"
					track_param = 0

			print clock.timename(), " Now trying to clear the error!"
			try:
				comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")	
				time.sleep(5)
				comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 		

			try:
				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
				print clock.timename(), " The error state after trying to clear the warning is: ", t_error_state
			except Exception, e:
				print clock.timename(), " An error occured while reading telescope error state"
				t_error_state = 1

			if str(t_error_state) not in ["0", "0.0"]:
				print clock.timename(), " The error/warning was not cleared!"
#				if song_monitor_config.send_notifications == "yes" and self.email_send == 0 and error_list != self.old_error_list:						
#					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Telescope Warning!", message="A warning would not be cleared and the telescope will be shut down!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % (error_list, clock.obstimeUT()))
#					if song_monitor_config.send_sms == "yes":
#						send_song_mail.send_mail().send_sms(receiver=song_monitor_config.send_sms_to_whom, message="A warning would not be cleared and the telescope will be shut down!")
#					if song_monitor_config.send_to_support == "yes":
#						send_song_mail.send_mail().sending_an_email(reciever=['support'], sender="SONG_MS", subject="Telescope Warning!", message="A warning would not be cleared and the telescope will be shut down!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % (error_list, clock.obstimeUT()))
#					self.email_send = 1
			else:
				if track_param == 1:
					try:
						comm2tcs_write.SET_TSI().set_pointing_setup_dome_syncmode(param=song_monitor_config.dome_syncmode_value,sender="Mads")
						track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=1,sender="Monitor")
					except Exception, e:
						print clock.timename(), " Could not collect telescope data" 
						track_param = 0
					if track_param == 1:
						track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
						while str(track_value) not in ['11', '11.0']:
							time.sleep(0.2)
							track_value = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Observer")
						print clock.timename(), " The telescope is now tracking again!"

				self.email_send = 0
				self.second_occurence = 0 

		elif str(t_error_state) == "4" and self.who_did_it_tel == "telescope":	
			print clock.timename(), " The telescope was shutdown earlier and a warning still appears... now trying to clear it!"
			try:
				comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")	
				time.sleep(5)
				comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 		

			try:
				t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
				print clock.timename(), " The error state after trying to clear the warning is: ", t_error_state
			except Exception, e:
				print clock.timename(), " An error occured while reading telescope error state"
				t_error_state = 1
	
			if str(t_error_state) not in ["0", "0.0"]:
				print clock.timename(), " The error/warning was not cleared!"
			else:
				print clock.timename(), " The error/warning was cleared!"
				self.second_occurence = 0 

		######## SHUT DOWN THE TELESCOPE #########
		if song_monitor_config.mon_telescope_actions == 1 and str(t_error_state) not in ["0", "0.0"] and float(self.telescope_state) != float(-3.0) and str(t_error_state) != "-1":

			if  self.slit_state == 0 or self.flap_state == 0 or self.mirror_cover_state == 0:
				print clock.timename(), " Dome and mirror covers were closed and the telescope will stay in the current power state."

			if self.slit_state != 0 or self.flap_state != 0 or self.mirror_cover_state != 0:
				if song_monitor_config.send_notifications == "yes":						
					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Telescope shutdown!", message="A warning would not be cleared and the telescope will be shut down!\n\nThe Error message was:\n%s\n\nSend at: %s\n\n" % ("[CONN-ID: " + str(comm2tcs_read.GET_TSI().get_connid()) + "] " + error_list, clock.obstimeUT()))
				status_tel = self.perform_actions.shutdown_telescope()
				if status_tel == "done":
					self.who_did_it_tel = "telescope"	
					print clock.timename(), " The telescope was shut down due to an error [%s]" % (t_error_state)

				dome_check = self.perform_actions.check_shutdown()
				if dome_check == 1:
					print clock.timename(), " The dome was closed correctly"
				else:
					if song_monitor_config.send_to_wake_up == "yes":						
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Telescope Closing Error!", message="The dome was not closed correctly after shutdown!\n\nSend at: %s\n\n" % clock.obstimeUT())
					if song_monitor_config.send_sms == "yes":
						send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome was not closed corretly...")
					if song_monitor_config.send_to_support == "yes":
						send_song_mail.send_mail().sending_an_email(reciever=['support'], sender="SONG_MS",subject="Telescope Closing Error!", message="The dome was not closed correctly after shutdown!\n\nSend at: %s\n\n" % clock.obstimeUT())
					

		elif song_monitor_config.mon_telescope_actions == 0 and str(t_error_state) not in ["0", "0.0"]:
			self.who_did_it_tel = "telescope"

		if error_list != "":
			self.old_error_list = error_list
			self.error_time = time.time()

		else:
			if self.old_error_list != "" and self.error_time + 600 < time.time():	## If the error is cleared and stays cleared for 10 minutes e-mails are allowed to be send again...
				print clock.timename(), " The error has been cleared for 10 minutes... and the e-mails are allowed to be send again on this matter!"
				self.old_error_list = ""			


		if self.who_did_it_tel == "telescope" and str(t_error_state) in ["0", "0.0"] and self.error_time + 600 < time.time():
			## If a warning or error has appeared and the telescope was shutdown... If the monitor is able to clear the problem after shutdown it will wait 10 minutes afterwards and allow to open up again.
			self.who_did_it_tel = "free"


		#elif str(t_error_state) in ["0", "0.0"]:
		#	print "The warning was cleared and observation can continue!"

		#else:
		#	self.who_did_it_tel = "telescope"

		return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp

		
		
	def tel_altitude(self, side_port_group_1, side_port_group_2, side_port_group_3, side_port_group_4, telescope_state, slit_state, flap_state, mirror_cover_state, who_did_it_tel,  who_did_it_sp):
		"""
			This function checks the altitude of the telescope.
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

		try:
			if song_monitor_config.mon_telescope_actions == 1:
		        	tel_alt = comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="Monitor")
				tel_slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")
				tel_flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
				tel_mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
				telescope_status = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor")
			else:	
				return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp

		except Exception, e:
		        print clock.timename(), " An error occured while reading telescope error state"
			return "error"


		#### This is where the values for slit, flap and mirror covers are set in every cycle of the monitor loop ####
		#### If they are just a little bit open the values are set to open....
		self.telescope_state = int(numpy.ceil(float(telescope_status)))
		self.slit_state = int(numpy.ceil(float(tel_slit_state)))
		self.flap_state = int(numpy.ceil(float(tel_flap_state)))
		self.mirror_cover_state = int(numpy.ceil(float(tel_mirror_cover_state)))
		##############################################################################################################

		try:
			track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Monitor")
			motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Monitor")
		except Exception, e:
			print clock.timename(), " Could not collect telescope data" 
			motion_state = "error"
			error = "error"
			return "error"

		if self.verbose == "yes" and str(motion_state) not in ['0', '0.0']:
			print clock.timename(), " Dome state (slit, flap, mirror cover) was: %s, %s, %s" % (str(self.slit_state), str(self.flap_state), str(self.mirror_cover_state)) 

		if self.verbose == "yes" and str(motion_state) in ['11', '11.0']:
			print clock.timename(), " The telscope altitude was: ", tel_alt
		elif float(tel_alt) <= float(m_conf.telescope_min_altitude):
			print clock.timename(), " The telscope altitude was: ", tel_alt


		open_flap_allowed = self.check_handle.wind_check_dome_flap()
		#### This will open the dome flap if wind is below 10 m/s.
		if float(tel_flap_state) == float(0) and self.who_did_it_tel == "free" and open_flap_allowed == 1 and self.telescope_state == 1 and self.slit_state == 1:
			### The dome flap will be opend! ###
			status_flap = self.perform_actions.oc_flap(action=1)
		if float(tel_flap_state) == float(1) and self.who_did_it_tel == "free" and open_flap_allowed == 0 and self.telescope_state == 1 and self.slit_state == 1:
			### The dome flap will be closed! ###
			status_flap = self.perform_actions.oc_flap(action=0)

#		#### This will open the dome flap if we observe something under 40 degrees.
#		if float(tel_alt) <= float(song_monitor_config.dome_flap_open_angle) and float(tel_flap_state) == float(0) and self.who_did_it_tel == "free" and open_flap_allowed == 1:
#			### The dome flap will be opend! ###
#			status_flap = self.perform_actions.oc_flap(action=1)
#		if float(tel_alt) > float(song_monitor_config.dome_flap_open_angle) and float(tel_flap_state) == float(1) and self.who_did_it_tel == "free":
#			### The dome flap will be closed! ###
#			status_flap = self.perform_actions.oc_flap(action=0)
		

		if float(tel_alt) <= float(m_conf.telescope_min_altitude):
			#### The telescope should stop tracking and move to park position####
			if song_monitor_config.mon_telescope_actions == 1:
				if (self.slit_state != 0 or self.flap_state != 0 or self.mirror_cover_state != 0) and str(motion_state) not in ['0', '0.0']:
					#### Changed to just stop tracking in stead of also to park telescope on 2015-01-26:
					status_tel = self.perform_actions.move_tel_up()
					if status_tel == "done":		
						print clock.timename(), " The telescope was stopped and moved due to low object"
					else:
						print clock.timename(), " Something did not go well with moving the telescope when low object"
						if song_monitor_config.send_to_wake_up == "yes":						
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Telescope Stop Tracking Error!", message="The telescope was not stopped correctly after low object!\n\nSend at: %s\n\n" % clock.obstimeUT())
						if song_monitor_config.send_sms == "yes":
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="Telescope stop tracking problem...")
						if song_monitor_config.send_to_support == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=['support'], sender="SONG_MS", subject="Telescope stop tracking Error!", message="The telescope was not stopped correctly after low object!\n\nSend at: %s\n\n" % clock.obstimeUT())
			else:
				if self.telescope_state != 0:
					print clock.timename(), " The telescope would have been stopped tracking if monitoring were active!"

				elif self.telescope_state == 0:
					if self.verbose == "yes":
						print clock.timename(), " The object is to low so the telescope will be kept parked"

				
		return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp

			

	def tel_dome_sync(self, side_port_group_1, side_port_group_2, side_port_group_3, side_port_group_4, telescope_state, slit_state, flap_state, mirror_cover_state, who_did_it_tel,  who_did_it_sp):
		"""
			This function checks if the dome is in sync with the telescope.
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

		try:
			if song_monitor_config.mon_telescope_actions == 1:
		        	tel_az = comm2tcs_read.GET_TSI().get_position_horizontal_az(sender="Monitor")
				tel_alt = comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="Monitor")
				dome_az = comm2tcs_read.GET_TSI().get_position_instrumental_dome_az_currpos(sender="Monitor")
				dome_az_offset = comm2tcs_read.GET_TSI().get_pointing_setup_dome_offset(sender="Monitor")
			else:	
				return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp

		except Exception, e:
		        print clock.timename(), " An error occured while reading telescope and dome azimuth"
			return "error"

		try:
			track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Monitor")
			motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Monitor")
		except Exception, e:
			print clock.timename(), " Could not collect telescope data" 
			motion_state = "error"
			error = "error"
			return "error"


		try:
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
			curr = conn.cursor()
			select_string = "SELECT bw_cloud_cond FROM weather_station WHERE ins_at > (current_timestamp - INTERVAL '20 minutes')"
			curr.execute(select_string)
			cloud_data = curr.fetchall()
		except Exception, e:
			print clock.timename(), " Error: ", e
		else:
			curr.close()
			conn.close()

		number_of_cloud_events = len(numpy.where(numpy.array(cloud_data) >= 2)[0])


		nstars = 0
		skycam_timestamp = datetime.datetime.utcnow() - datetime.timedelta(seconds=600)
		try:
			sun_alt = sun_handle.sun_alt(unit="f")
			#### Check skycam stars:
			skycam_data = self.check_handle.check_last_solved_skycam_im()
			if len(skycam_data) == 2:
				nstars, skycam_timestamp = skycam_data				
		except Exception,e:
			print e
		else:

			try:
				if float(sun_alt) <= -10. and int(self.slit_state) == 1 and float(tel_alt) > 40. and float(motion_state) == 11.0: 
					if int(nstars) > 50 and skycam_timestamp > (datetime.datetime.utcnow() - datetime.timedelta(seconds=300)):
						print clock.timename(), " Number of skycam-1 stars detected was %i at %s" % (int(nstars), str(skycam_timestamp))
						self.no_stars_images = 0
					elif int(nstars) < 50 and int(nstars) > 0 and skycam_timestamp > (datetime.datetime.utcnow() - datetime.timedelta(seconds=300)):
						print clock.timename(), " Too few stars detected on skycam-1: %i at %s" % (int(nstars), str(skycam_timestamp))
						self.no_stars_images = 0
					elif int(nstars) == 0 and self.no_stars_images <= 5 and time.time() > self.pc_dome_delay and number_of_cloud_events == 0 and skycam_timestamp > (datetime.datetime.utcnow() - datetime.timedelta(seconds=300)):
						# Count number of images with no stars in a row.
						self.no_stars_images +=1
						### REACT
					elif int(nstars) == 0 and self.no_stars_images > 5 and time.time() > self.pc_dome_delay and number_of_cloud_events == 0 and skycam_timestamp > (datetime.datetime.utcnow() - datetime.timedelta(seconds=300)):						
						print clock.timename(), " It has been too long since stars were detected on skycam-1 at %s" % (str(skycam_timestamp))
												
						try:
							image_filename = self.perform_actions.save_dome_image()
						except Exception,e:
							print e
						else:
							try:
								ret_val = send_song_mail.send_mail().send_attachment(receiver=["mads"], subject="Dome misaligned", text="Hi,\n\nSkyCam-1 did not detect stars for 5 minutes and the sky is clear according to the weather station!\nThe dome might be misaligned witht the telescope and the dome controller will now be power cycled. See attachment to check!", files=[image_filename])
							except Exception,e:
								print "Mail Error: ", e


						status_pc = self.perform_actions.power_cycle_dome_controller()
						#status_ref = self.perform_actions.reference_dome()
						if status_pc == "done":		
							print clock.timename(), " The dome controller was power cycled..."

							t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
							error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()
							time_out_tmp = time.time() + 60
							while 'DOME[1];ERR_DeviceError' not in error_list:
								time.sleep(1)
							
								error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()
								if time.time() > time_out_tmp:
									print clock.timename(), " The warnings about the power cycle of the dome controller did not occur in 1 minute."
									break
								elif 'DOME[1];ERR_DeviceError' in error_list:
									print clock.timename(), " The warnings have now occured and the script will continue..."
									break

							print clock.timename(), " Now trying to clear the warnings!"
							try:
								comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear first error
								time.sleep(5)
								comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear second error
							except Exception, e:
								print clock.timename(), " Could not send command 'Clear errors' to the tsi" 
							else:
								try:
									print clock.timename(), comm2tcs_read.GET_TSI().get_telescope_status_list()
								except Exception, e:
									print clock.timename(), e
	
						else:
							print clock.timename(), " Something did not go well with the power cycle of the dome controller"
							if song_monitor_config.send_notifications == "yes":						
								send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Dome misbehaving!", message="The dome was not behaving as it should and the power cycle of the dome controller failed!\n\nSend at: %s\n\n" % clock.obstimeUT())

	#							print clock.timename(), " Now trying to clear the warnings!"
	#							try:
	#								comm2tcs_write.SET_TSI().set_telescope_clear(sender="Monitor")	
	#								time.sleep(5)
	#								comm2tcs_write.SET_TSI().set_telescope_clear(sender="Monitor")
	#							except Exception, e:
	#								print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 	
	#						if song_monitor_config.send_sms == "yes":
	#							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="Telescope and dome is not in sync...")

						self.pc_dome_delay = time.time() + (30 * 60) # 30 minutes
						self.dome_second = 0
						print clock.timename(), " The dome should be aligned again now if all went well!"
						tel_az = comm2tcs_read.GET_TSI().get_position_horizontal_az(sender="Monitor")
						dome_az = comm2tcs_read.GET_TSI().get_position_instrumental_dome_az_currpos(sender="Monitor")
						print clock.timename(), " Dome az: %s, telescope az: %s" % (dome_az, tel_az)
						print clock.timename(), " The monitor will now sleep for one minute to allow the dome to get close to the reference before continuing"
						time.sleep(60)

						print clock.timename(), " Now checking if new errors about the dome has occurred!"
						t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
						error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()
						if int(t_error_state) == 2:
							print clock.timename(), " Additional errors appeared... now trying to clear those!"

							print clock.timename(), error_list
							try:
								comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear first error
								time.sleep(5)
								comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear second error
							except Exception, e:
								print clock.timename(), " Could not send command 'Clear errors' to the tsi" 
							else:
								try:
									print clock.timename(), comm2tcs_read.GET_TSI().get_telescope_status_list()
								except Exception, e:
									print clock.timename(), e

					elif float(self.slit_state) == float(1.0) and float(motion_state) > float(0.0) and self.dome_second == 1:
						print clock.timename(), " The dome was misaligned in two loops and will next time be referenced..."
						self.dome_second = 2
					elif skycam_timestamp < (datetime.datetime.utcnow() - datetime.timedelta(seconds=300)):
						print clock.timename(), " SkyCam image too old to use..."
					else:
						print clock.timename(), " None of the above contraints caught the problem....."

			except Exception,e:
				print e					


#		try:
#			print clock.timename(), " Dome azimuth position: %s and offset: %s" % (str(dome_az), str(dome_az_offset))
#		except Exception, e:
#			print clock.timename(), e

		real_dome_az = (float(dome_az) + float(dome_az_offset))

		if (real_dome_az > 350. and float(tel_az) < 10.):
			tmp_offset = numpy.abs((float(tel_az) - float(real_dome_az)) % 360.)
		elif  (float(tel_az) > 350. and real_dome_az < 10.):
			tmp_offset = numpy.abs((float(real_dome_az) - float(tel_az)) % 360.)
		else:
			tmp_offset = numpy.abs(float(tel_az) - float(real_dome_az))	

		print clock.timename(), " The dome - telescope offset: ", tmp_offset

		if tmp_offset > float(m_conf.dome_tel_off) and self.dome_second > 0:
			#### The monitor should power cycle the dome controller ####
			if song_monitor_config.mon_telescope_actions == 1:
				if float(self.slit_state) == float(1.0) and float(motion_state) == float(11.0):	# If dome open and telescope tracking it should point together with the dome.
					#status_pc = self.perform_actions.power_cycle_dome_controller()
					status_ref = self.perform_actions.reference_dome()
					
					if status_ref == "done":		
						print clock.timename(), " The dome controller was power cycled..."
						if song_monitor_config.send_notifications == "yes":						
							send_song_mail.send_mail().sending_an_email(reciever=["mads"], sender="SONG_MS", subject="Dome - telescope out of sync!", message="The telescope and the dome was not pointing to the same direction any more and the dome was send to reference!\n\nSend at: %s\n\n" % clock.obstimeUT())
					else:
						print clock.timename(), " Something did not go well with the dome reference sequence"
						if song_monitor_config.send_notifications == "yes":						
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Dome - telescope out of sync!", message="The telescope and the dome is not pointing to the same direction any more and a reference cycle of the dome failed!\n\nSend at: %s\n\n" % clock.obstimeUT())
#						if song_monitor_config.send_sms == "yes":
#							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="Telescope and dome is not in sync...")
					print clock.timename(), " The dome should now have referenced!"
					tel_az = comm2tcs_read.GET_TSI().get_position_horizontal_az(sender="Monitor")
					dome_az = comm2tcs_read.GET_TSI().get_position_instrumental_dome_az_currpos(sender="Monitor")
					print clock.timename(), " Dome az: %s, telescope az: %s" % (dome_az, tel_az)
					self.dome_second = 0

				elif float(self.slit_state) == float(1.0) and float(motion_state) > float(0.0) and self.dome_second == 2 and time.time() > self.pc_dome_delay:	# If telescope and dome out of sync for a long time...
					status_pc = self.perform_actions.power_cycle_dome_controller()
					#status_ref = self.perform_actions.reference_dome()
					if status_pc == "done":		
						print clock.timename(), " The dome controller was power cycled..."
						if song_monitor_config.send_notifications == "yes":						
							send_song_mail.send_mail().sending_an_email(reciever=["mads"], sender="SONG_MS", subject="Dome misbehaving!", message="The dome was not behaving correctly and the dome controller was power cycled!\n\nSend at: %s\n\n" % clock.obstimeUT())

						t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
						error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()
						time_out_tmp = time.time() + 60
						while 'DOME[1];ERR_DeviceError' not in error_list:
							time.sleep(1)
							
							error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()
							if time.time() > time_out_tmp:
								print clock.timename(), " The warnings about the power cycle of the dome controller did not occur in 1 minute."
								break
							elif 'DOME[1];ERR_DeviceError' in error_list:
								print clock.timename(), " The warnings have now occured and the script will continue..."
								break

						print clock.timename(), " Now trying to clear the warnings!"
						try:
							comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear first error
							time.sleep(5)
							comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear second error
						except Exception, e:
							print clock.timename(), " Could not send command 'Clear errors' to the tsi" 
						else:
							try:
								print clock.timename(), comm2tcs_read.GET_TSI().get_telescope_status_list()
							except Exception, e:
								print clock.timename(), e
	
					else:
						print clock.timename(), " Something did not go well with the power cycle of the dome controller"
						if song_monitor_config.send_notifications == "yes":						
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Dome misbehaving!", message="The dome was not behaving as it should and the power cycle of the dome controller failed!\n\nSend at: %s\n\n" % clock.obstimeUT())

#							print clock.timename(), " Now trying to clear the warnings!"
#							try:
#								comm2tcs_write.SET_TSI().set_telescope_clear(sender="Monitor")	
#								time.sleep(5)
#								comm2tcs_write.SET_TSI().set_telescope_clear(sender="Monitor")
#							except Exception, e:
#								print clock.timename(), " Could not send command 'Clear warnings' to the tsi" 	
#						if song_monitor_config.send_sms == "yes":
#							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="Telescope and dome is not in sync...")

					self.pc_dome_delay = time.time() + (10 * 60) # 10 minutes
					self.dome_second = 0
					print clock.timename(), " The dome should be aligned again now if all went well!"
					tel_az = comm2tcs_read.GET_TSI().get_position_horizontal_az(sender="Monitor")
					dome_az = comm2tcs_read.GET_TSI().get_position_instrumental_dome_az_currpos(sender="Monitor")
					print clock.timename(), " Dome az: %s, telescope az: %s" % (dome_az, tel_az)
					print clock.timename(), " The monitor will now sleep for one minute to allow the dome to get close to the reference before continuing"
					time.sleep(60)

					print clock.timename(), " Now checking if new errors about the dome has occurred!"
					t_error_state = comm2tcs_read.GET_TSI().get_telescope_status_global()
					error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()
					if int(t_error_state) == 2:
						print clock.timename(), " Additional errors appeared... now trying to clear those!"

						print clock.timename(), error_list
						try:
							comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear first error
							time.sleep(5)
							comm2tcs_write.SET_TSI().set_telescope_clear_error(sender="Monitor")		# Clear second error
						except Exception, e:
							print clock.timename(), " Could not send command 'Clear errors' to the tsi" 
						else:
							try:
								print clock.timename(), comm2tcs_read.GET_TSI().get_telescope_status_list()
							except Exception, e:
								print clock.timename(), e

				elif float(self.slit_state) == float(1.0) and float(motion_state) > float(0.0) and self.dome_second == 1:
					print clock.timename(), " The dome was misaligned in two loops and will next time be referenced..."
					self.dome_second = 2
				else:
					print clock.timename(), " None of the above contraints caught the problem....."

			else:
				if self.telescope_state != 0:
					print clock.timename(), " The dome would be referenced if monitored!"

				elif self.telescope_state == 0:
					if self.verbose == "yes":
						print clock.timename(), " The dome was not in sync with the telescope..."

		elif tmp_offset > float(m_conf.dome_tel_off) and self.dome_second == 0:
			print clock.timename(), " The dome was not placed correctly!"
			print clock.timename(), " Dome az: %s, telescope az: %s" % (dome_az, tel_az)
			self.dome_second = 1

		elif tmp_offset < float(m_conf.dome_tel_off) and self.dome_second > 0:
			print clock.timename(), " Dome az: %s, telescope az: %s" % (dome_az, tel_az)
			self.dome_second = 0		


				
		return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp



			






