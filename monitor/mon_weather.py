import send_song_mail
import song_checker
import song_timeclass
import mon_actions
import time
import thread
import song_monitor_config
import song_checker_config
import send_song_mail
import comm2tcs_read
import master_config as m_conf
import song_star_checker
import datetime


clock = song_timeclass.TimeClass()

class Check_Weather(object):
	"""
		@brief: This class handles all checks on the weather situation.
	"""
	def __init__(self):
		"""
			Initialization of the weather checks.
		"""

		self.test = song_monitor_config.weather_test
	
		self.check_handle = song_checker.Checker()
		self.perform_actions = mon_actions.Do_Actions()
		self.sun_handle = song_star_checker.sun_pos(site=m_conf.song_site) # site=1: Tenerife

		self.verbose = song_monitor_config.verbose # yes or no


		try:
			value1 = self.check_weather(deduced_value=song_monitor_config.weather_deduced)
	        except Exception, e:
			value1 = 1

		self.time_active_delay_1 = 0
		self.time_active_delay_2 = 0
		self.time_active_delay_3 = 0
		self.time_active_delay_4 = 0

		self.time_delay_telescope = 0

		
		self.spg1_ws = 0	# side port group 1 - wind speed
		self.spg2_ws = 0	# side port group 2 - wind speed
		self.spg3_ws = 0	# side port group 3 - wind speed
		self.spg4_ws = 0	# side port group 4 - wind speed



		#################
		#################
		## DO SOMETHING
		#################
		#################



	def check_weather(self,side_port_group_1, side_port_group_2, side_port_group_3, side_port_group_4, telescope_state, slit_state, flap_state, mirror_cover_state, who_did_it_tel,  who_did_it_sp):
		"""
			@brief: This function checks the weather through the song_checker class.
			This can open and close the dome if needed.
		"""	
		if song_monitor_config.mon_telescope_actions == 1 and song_monitor_config.mon_telescope == 0:
			telescope_state = int(float(comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor")))
			slit_state = int(float(comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")))
			flap_state = int(float(comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")))
			mirror_cover_state = int(float(comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")))

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
			if self.test == 1:
				output, timestamp = self.check_handle.weather_check_test()
			else:
				output, timestamp = self.check_handle.weather_check(deduced=song_monitor_config.weather_deduced)
				output2, timestamp2 = self.check_handle.weather_check(deduced=1) # Returns the bits of the weather check
		except Exception, e:
			print clock.timename(), " Error while collecting song_checker data, check_weather", e
			output = ""
			output2 = [""]
			timestamp2 = ""

		if self.verbose == "yes" and output2[0] != 0:
			print clock.timename(), " Weather check deduced output: ", output2

		if self.verbose == "yes" and self.time_delay_telescope > time.time():
			print clock.timename(), " The minimum time until the telescope will open up is %f minutes" % ((self.time_delay_telescope - time.time()) / 60.)


		### If daytime (dome closed) and wind speed are in side port vs. cooler range they will be opend.
		### If dome is open we do not care about this check.
		if float(self.slit_state) == 0.0 and float(self.flap_state) == 0.0:
			self.side_wind = self.check_handle.low_wind_speed()
		else:
			self.side_wind = 0


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

		if output == "":
			return "error"

		elif output > 0 and output != 8:
			###########################	
			### The weather is bad  ###	
			###########################		
			
			#### Shut down telescope ###
			if song_monitor_config.mon_telescope_actions == 1:
				if float(self.slit_state) != 0.0 or float(self.flap_state) != 0.0 or (float(self.mirror_cover_state) != 0.0 and song_monitor_config.allow_mc_open != "yes"):

					status_tel = self.perform_actions.shutdown_telescope()

					if song_monitor_config.send_notifications == "yes":
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS",subject="Telescope Shutdown!",message="The telescope is now being shut down!\n\nThe weather has turned bad and the telescope will be shut down!\n\nSend at: %s\n\n" % clock.obstimeUT())

					if status_tel == "done":
						self.who_did_it_tel = "weather"	
						self.time_delay_telescope = time.time() + (song_checker_config.telescope_delay_time * 60)	
						print clock.timename(), " Weather check deduced output: ", output2
						print clock.timename(), " The telescope was shut down due to bad weather"

					dome_check = self.perform_actions.check_shutdown()
					if dome_check == 1:
						print clock.timename(), " The dome was closed correctly"
					elif dome_check == 2:
						print clock.timename(), " The dome was closed but mirror cover open"
						if song_monitor_config.send_notifications == "yes":						
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Mirror covers were open!", message="The dome was closed but mirror covers open!\n\nSend at: %s\n\n" % clock.obstimeUT())
					else:
						if song_monitor_config.send_to_wake_up == "yes":						
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Telescope Closing Error!", message="The dome was not closed correctly after shutdown!\n\nSend at: %s\n\n" % clock.obstimeUT())
						if song_monitor_config.send_sms == "yes":
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome was not closed corretly...")
						if song_monitor_config.send_to_support == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Telescope Closing Error!", message="The dome was not closed correctly after shutdown!\n\nSend at: %s\n\n" % clock.obstimeUT())

				else:
					self.who_did_it_tel = "weather"
					self.time_delay_telescope = time.time() + (song_checker_config.telescope_delay_time * 60)

			elif song_monitor_config.mon_telescope_actions == 0:
				if self.slit_state != 0 or self.flap_state != 0 or self.mirror_cover_state != 0:
					self.who_did_it_tel = "weather"	
					self.time_delay_telescope = time.time() + (song_checker_config.telescope_delay_time * 60)
					print clock.timename(), " Weather check deduced output: ", output2
					print clock.timename(), " The telescope would have been shut down due to bad weather"
				else:
					self.who_did_it_tel = "weather"
					self.time_delay_telescope = time.time() + (song_checker_config.telescope_delay_time * 60)
				


			if song_monitor_config.mon_side_ports_actions == 1 and output != 8:		
			### Close side ports ####	
				if self.side_port_group_1 != 0 and self.who_did_it_sp != "time" and self.who_did_it_sp != "network":
					status_side_port_1 = self.perform_actions.close_side_port(group=1)
				        time.sleep(0.5)
					if status_side_port_1 == "done":
						if self.time_active_delay_1 < time.time():
							print clock.timename(), " Weather check deduced output: ", output2
							print clock.timename(), " The side ports were closed caused by bad weather"
						self.who_did_it_sp = "weather"
						self.time_active_delay_1 = time.time() + (song_checker_config.delay_time * 60)

				else:
					self.who_did_it_sp = "weather"
					self.time_active_delay_1 = time.time() + (song_checker_config.delay_time * 60)

				if self.side_port_group_2 != 0 and self.who_did_it_sp != "time" and self.who_did_it_sp != "network":
					status_side_port_2 = self.perform_actions.close_side_port(group=2)
				        time.sleep(0.5)
					if status_side_port_2 == "done":
						self.who_did_it_sp = "weather"
						self.time_active_delay_2 = time.time() + (song_checker_config.delay_time * 60)
				else:
					self.who_did_it_sp = "weather"
					self.time_active_delay_2 = time.time() + (song_checker_config.delay_time * 60)

				if self.side_port_group_3 != 0 and self.who_did_it_sp != "time" and self.who_did_it_sp != "network":
					status_side_port_3 = self.perform_actions.close_side_port(group=3)
				        time.sleep(0.5)
					if status_side_port_3 == "done":
						self.who_did_it_sp = "weather"
						self.time_active_delay_3 = time.time() + (song_checker_config.delay_time * 60)
				else:
					self.time_active_delay_3 = time.time() + (song_checker_config.delay_time * 60)
					self.who_did_it_sp = "weather"

				if self.side_port_group_4 != 0 and self.who_did_it_sp != "time" and self.who_did_it_sp != "network":
					status_side_port_4 = self.perform_actions.close_side_port(group=4)
				        time.sleep(0.5)
					if status_side_port_4 == "done":
						self.who_did_it_sp = "weather"
						self.time_active_delay_4 = time.time() + (song_checker_config.delay_time * 60)
				else:
					self.time_active_delay_4 = time.time() + (song_checker_config.delay_time * 60)
					self.who_did_it_sp = "weather"

			elif song_monitor_config.mon_side_ports_actions == 0 and output != 8:
				if self.side_port_group_1 != 0 and self.who_did_it_sp != "time" and self.who_did_it_sp != "network":
					self.time_active_delay_1 = time.time() + (song_checker_config.delay_time * 60)
					self.time_active_delay_2 = time.time() + (song_checker_config.delay_time * 60)
					self.time_active_delay_3 = time.time() + (song_checker_config.delay_time * 60)
					self.time_active_delay_4 = time.time() + (song_checker_config.delay_time * 60)
					self.who_did_it_sp = "weather"
					print clock.timename(), " Weather check deduced output: ", output2
					print clock.timename(), " The side ports would have been closed caused by bad weather"

		elif output == 8:			
			if song_monitor_config.mon_move_away_actions == 1 and (float(self.slit_state) == 1.0 or float(self.flap_state) == 1.0) and float(self.telescope_state) == 1.0 and self.sun_handle.sun_alt(unit='f') < 0.0:
				print clock.timename(), " The wind speed into the dome is too high. The telescope will now be moved away from the wind"
				returned_value = self.perform_actions.move_tel_away_from_wind()
				if returned_value == "done":
					if song_monitor_config.send_notifications == "yes":
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS",subject="Moved telescope away from wind!",message="The telescope was moved away from the wind direction because of high wind speeds!\n\nSend at: %s\n\n" % clock.obstimeUT())
				elif returned_value == "shutdown":
					print clock.timename(), " No worries... telescope was shut down"
				else:
					if song_monitor_config.send_to_wake_up == "yes":
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Moved telescope away from wind!",message="The telescope should be moved away from the wind direction because of high wind speeds!\nBut something happend and the action was not performed correctly.\n\nSend at: %s\n\n" % clock.obstimeUT())		
						if song_monitor_config.send_sms == "yes":
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The telescope did not move away from the high wind speed as it should")		
						if song_monitor_config.send_to_support == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Moved telescope away from wind!",message="The telescope should be moved away from the wind direction because of high wind speeds!\nBut something happend and the action was not performed correctly.\n\nSend at: %s\n\n" % clock.obstimeUT())
			elif song_monitor_config.mon_move_away_actions == 1 and (float(self.slit_state) != 0.0 or float(self.flap_state) != 0.0) and float(self.telescope_state) == 1.0 and self.sun_handle.sun_alt(unit='f') >= 0.0:
				print clock.timename(), " The wind speed into the dome is too high. The telescope will now be closed"

#				returned_value = self.perform_actions.close_mc_and_dome()
#				self.who_did_it_tel = "weather"	
#				self.time_delay_telescope = time.time() + (song_checker_config.delay_time * 60)
#				if returned_value == "done":
#					if song_monitor_config.send_notifications == "yes":
#						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS",subject="Dome and mirror covers were closed!",message="The dome and mirror covers were closed because of high wind before sunset!\n\nSend at: %s\n\n" % clock.obstimeUT())
#				else:
#					if song_monitor_config.send_to_wake_up == "yes":
#						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Dome and mirror covers were closed!",message="Problems when closing the dome and mirror covers before sunset because of high wind!\n\nSend at: %s\n\n" % clock.obstimeUT())		
#						if song_monitor_config.send_sms == "yes":
#							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome and or mirror covers were not closed correctly")		
#						if song_monitor_config.send_to_support == "yes":
#							send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Dome and mirror covers were closed!",message="Problems when closing the dome and mirror covers before sunset because of high wind!\n\nSend at: %s\n\n" % clock.obstimeUT())

	# Changed to power off from 2018-04-11:

				status_tel = self.perform_actions.shutdown_telescope()

				if song_monitor_config.send_notifications == "yes":
					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS",subject="Telescope Shutdown!",message="The telescope is now being shut down!\n\nThe wind speed into the dome is too high and the telescope will be shut down!\n\nSend at: %s\n\n" % clock.obstimeUT())

				if status_tel == "done":
					if self.time_delay_telescope < time.time():
						self.who_did_it_tel = "wind"	
						self.time_delay_telescope = time.time() + (20 * 60)	# delay of five minutes
					print clock.timename(), " Weather check deduced output: ", output2
					print clock.timename(), " The telescope was shut down due to high wind"

				dome_check = self.perform_actions.check_shutdown()
				if dome_check == 1:
					print clock.timename(), " The dome was closed correctly"
				elif dome_check == 2:
					print clock.timename(), " The dome was closed but mirror cover open"
					if song_monitor_config.send_notifications == "yes":						
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Mirror covers were open!", message="The dome was closed but mirror covers open!\n\nSend at: %s\n\n" % clock.obstimeUT())
				else:
					if song_monitor_config.send_to_wake_up == "yes":						
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Telescope Closing Error!", message="The dome was not closed correctly after shutdown!\n\nSend at: %s\n\n" % clock.obstimeUT())
					if song_monitor_config.send_sms == "yes":
						send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome was not closed corretly...")
					if song_monitor_config.send_to_support == "yes":
						send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Telescope Closing Error!", message="The dome was not closed correctly after shutdown!\n\nSend at: %s\n\n" % clock.obstimeUT())	

			elif song_monitor_config.mon_move_away_actions == 1 and float(self.slit_state) == 0.0 and float(self.flap_state) == 0.0 and float(self.telescope_state) == 0.0 and self.sun_handle.sun_alt(unit='f') > 0.0:
				if self.who_did_it_tel == "wind":	
					self.time_delay_telescope = time.time() + (20 * 60) # delay of five minutes			
	
			elif song_monitor_config.mon_move_away_actions == 1 and float(self.slit_state) == 0.0 and float(self.flap_state) == 0.0 and float(self.telescope_state) == 0.0 and self.sun_handle.sun_alt(unit='f') < -2.0:				
#				if song_monitor_config.send_notifications == "yes":
#					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS",subject="The telescope will be allowe!",message="The telescope was moved away from the wind direction because of high wind speeds!\n\nSend at: %s\n\n" % clock.obstimeUT())
				if self.who_did_it_tel == "wind" or (self.who_did_it_tel == "weather" and self.time_delay_telescope < time.time()):
					print clock.timename(), " The wind speed into the dome is too high. The telescope will be allowed to open but will move away."
					self.who_did_it_tel = "free"
					self.time_delay_telescope = time.time()


		elif output == 0:
			###########################	
			### The weather is good ###	
			###########################

###################################	
			### Close side ports if wind speed is too low and dome is closed:
			if song_monitor_config.mon_side_ports_actions == 1 and self.who_did_it_sp == "free" and self.side_wind == 2:
				if self.side_port_group_1 != 0 or self.side_port_group_2 != 0 or self.side_port_group_3 != 0 or self.side_port_group_4 != 0:
					status_side_port_1 = self.perform_actions.close_side_port(group=1)
					status_side_port_2 = self.perform_actions.close_side_port(group=2)
					status_side_port_3 = self.perform_actions.close_side_port(group=3)
					status_side_port_4 = self.perform_actions.close_side_port(group=4)
					print clock.timename(), " Side ports were closed because the wind speed was very low"
###################################	

			if song_monitor_config.mon_side_ports_actions == 1 and self.who_did_it_sp != "time" and self.who_did_it_sp != "network" and self.side_wind == 0:
				### Open side ports ####	
				if self.side_port_group_1 == 0 and self.time_active_delay_1 <= time.time() and self.spg1_ws == 0:
					status_side_port_1 = self.perform_actions.open_side_port(group=1)
				        time.sleep(0.5)
					if status_side_port_1 == "done":
						self.who_did_it_sp = "free"

				if self.side_port_group_2 == 0 and self.time_active_delay_2 <= time.time() and self.spg2_ws == 0:
					status_side_port_2 = self.perform_actions.open_side_port(group=2)
				        time.sleep(0.5)
					if status_side_port_2 == "done":
						self.who_did_it_sp = "free"

				if self.side_port_group_3 == 0 and self.time_active_delay_3 <= time.time() and self.spg3_ws == 0:
					status_side_port_3 = self.perform_actions.open_side_port(group=3)
				        time.sleep(0.5)
					if status_side_port_3 == "done":
						self.who_did_it_sp = "free"

				if self.side_port_group_4 == 0 and self.time_active_delay_4 <= time.time() and self.spg4_ws == 0:
					status_side_port_4 = self.perform_actions.open_side_port(group=4)
				        time.sleep(0.5)
					if status_side_port_4 == "done":
						self.who_did_it_sp = "free"

			elif song_monitor_config.mon_side_ports_actions != 1:
				if self.side_port_group_1 == 0 and self.time_active_delay_1 <= time.time():
					self.who_did_it_sp = "free"
					#print "The side ports would have been opend if they were monitored!", clock.obstimeUT()


			if song_monitor_config.mon_telescope_actions == 1:
				if self.time_delay_telescope <= time.time() and (self.who_did_it_tel == "weather" or self.who_did_it_tel == "wind"): #self.who_did_it_tel != "telescope" and self.who_did_it_tel != "time" and self.who_did_it_tel != "network" and self.who_did_it_tel != "free":
					if float(sun_alt_d) < (float(m_conf.obs_sun_alt) + 1.0) or hours_to_next_sun_set < m_conf.open_time_tel or hours_from_pre_sun_set < m_conf.open_time_tel:
						if song_monitor_config.send_notifications == "yes":
							print clock.timename(), " The weather has improved and an e-mail will be sent out to notify now."
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Weather cleared up!",message="The weather is now good again!\n\nThe telescope is allowed to be opened!\n\nSend at: %s\n\n" % clock.obstimeUT())	
						print clock.timename(), " The telescope control string will now be set to -free-"				
						self.who_did_it_tel = "free"
					else:			
						if song_monitor_config.send_notifications == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Weather cleared up!",message="The weather in Tenerife is now good again!\n\nThe telescope will be allowed to open when the time is right!\n\nSend at: %s\n\n" % clock.obstimeUT())					
						self.who_did_it_tel = "time"	
				elif self.who_did_it_tel == "wind" and float(sun_alt_d) < -2.0:
					if float(sun_alt_d) < (float(m_conf.obs_sun_alt) + 1.0) or hours_to_next_sun_set < m_conf.open_time_tel or hours_from_pre_sun_set < m_conf.open_time_tel:
						if song_monitor_config.send_notifications == "yes":
							print clock.timename(), " The wind has improved and an e-mail will be sent out to notify now."
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Weather cleared up!",message="The weather is now okay!\n\nThe telescope is allowed to be opened!\n\nSend at: %s\n\n" % clock.obstimeUT())	
						print clock.timename(), " The telescope control string will now be set to -free-"				
						self.who_did_it_tel = "free"
					else:			
						self.who_did_it_tel = "time"

		#### This function returns the current state of the 4 side port groups and the state of the telescope
		return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp

	def check_wind(self, side_port_group_1, side_port_group_2, side_port_group_3, side_port_group_4, telescope_state, slit_state, flap_state, mirror_cover_state, who_did_it_tel,  who_did_it_sp):
		"""
			@brief: This function checks the windspeed and direction through the song_checker class.
			This can open and close the side ports if needed.
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

		wind_array = []
		try:
			if self.test == 1:
				wind_array = self.check_handle.wind_check_test()
			else:
				wind_array = self.check_handle.wind_check()
				weather_output, timestamp2 = self.check_handle.weather_check(deduced=0) # Returns the bits of the weather check
		except Exception, e:
			print clock.timename(), " Error: ", e

		if self.verbose == "yes":
			if weather_output != 0:
				print clock.timename(), " Weather output in wind function was: %s" % (weather_output)
			if len(wind_array) > 0:
				print clock.timename(), " Wind array in wind function was: %s" % (wind_array)
			

		if len(wind_array) > 0 and weather_output == 0:
			print clock.timename(), " Some side ports should be closed due to high wind speeds"
			for i in wind_array:
				if i == 1 and self.side_port_group_1 != 0 and song_monitor_config.mon_side_ports_actions == 1: 
					status_side_port_1 = self.perform_actions.close_side_port(group=1)
				        time.sleep(0.5)
					if status_side_port_1 == "done":
						if self.spg1_ws == 0:
							print clock.timename(), " Side port South will now close"
						self.spg1_ws = 1
						self.time_active_delay_1 = time.time() + (song_checker_config.delay_time * 60)


				elif i == 1 and self.side_port_group_1 == 0:
					self.time_active_delay_1 = time.time() + (song_checker_config.delay_time * 60) # Sets a delay time for reopening 

				elif song_monitor_config.mon_side_ports_actions == 0 and i == 1 and self.side_port_group_1 != 0:
					#print "The side port South would have been closed caused by high wind speed at: ", clock.obstimeUT()
					self.time_active_delay_1 = time.time() + (song_checker_config.delay_time * 60) # Sets a delay time for reopening 

				if i == 2 and self.side_port_group_2 != 0 and song_monitor_config.mon_side_ports_actions == 1: 
					status_side_port_2 = self.perform_actions.close_side_port(group=2)
				        time.sleep(0.5)
					if status_side_port_2 == "done":
						if self.spg2_ws == 0:
							print clock.timename(), " Side port West will now close"
						self.spg2_ws = 1
						self.time_active_delay_2 = time.time() + (song_checker_config.delay_time * 60)


				elif i == 2 and self.side_port_group_2 == 0:
					self.time_active_delay_2 = time.time() + (song_checker_config.delay_time * 60) # Sets a delay time for reopening 

				elif song_monitor_config.mon_side_ports_actions == 0 and i == 2 and self.side_port_group_2 != 0:
					#print "The side port West would have been closed caused by high wind speed at: ", clock.obstimeUT()
					self.time_active_delay_2 = time.time() + (song_checker_config.delay_time * 60) # Sets a delay time for reopening 

				if i == 3 and self.side_port_group_3 != 0 and song_monitor_config.mon_side_ports_actions == 1: 
					status_side_port_3 = self.perform_actions.close_side_port(group=3)
				        time.sleep(0.5)
					if status_side_port_3 == "done":
						if self.spg3_ws == 0:
							print clock.timename(), " Side port North will now close"
						self.spg3_ws = 1
						self.time_active_delay_3 = time.time() + (song_checker_config.delay_time * 60)


				elif i == 3 and self.side_port_group_3 == 0:
					self.time_active_delay_3 = time.time() + (song_checker_config.delay_time * 60) # Sets a delay time for reopening 

				elif song_monitor_config.mon_side_ports_actions == 0 and i == 3 and self.side_port_group_3 != 0:
					#print "The side port North would have been closed caused by high wind speed at: ", clock.obstimeUT()
					self.time_active_delay_3 = time.time() + (song_checker_config.delay_time * 60) # Sets a delay time for reopening 

				if i == 4 and self.side_port_group_4 != 0 and song_monitor_config.mon_side_ports_actions == 1: 
					status_side_port_4 = self.perform_actions.close_side_port(group=4)
				        time.sleep(0.5)
					if status_side_port_4 == "done":
						if self.spg3_ws == 0:
							print clock.timename(), " Side port East will now close"
						self.spg4_ws = 1
						self.time_active_delay_4 = time.time() + (song_checker_config.delay_time * 60)

				elif i == 4 and self.side_port_group_4 == 0:
					self.time_active_delay_4 = time.time() + (song_checker_config.delay_time * 60) # Sets a delay time for reopening 

				elif song_monitor_config.mon_side_ports_actions == 0 and i == 4 and self.side_port_group_4 != 0:
					#print "The side port East would have been closed caused by high wind speed at: ", clock.obstimeUT()
					self.time_active_delay_4 = time.time() + (song_checker_config.delay_time * 60) # Sets a delay time for reopening 


################################# This should open the side ports again after good weather has returned #############################

		if self.side_port_group_1 == 0 and self.time_active_delay_1 <= time.time() and song_monitor_config.mon_side_ports_actions == 1 and self.who_did_it_sp == "free" and weather_output == 0 and self.side_wind == 0:  
			status_side_port_1 = self.perform_actions.open_side_port(group=1)
	                time.sleep(0.5)
			if status_side_port_1 == "done":
				if self.spg1_ws == 1:
					print clock.timename(), " Side port South will now open"
					self.side_port_group_1 = 1
				self.spg1_ws = 0				

		elif self.side_port_group_1 == 0 and self.time_active_delay_1 <= time.time() and song_monitor_config.mon_side_ports_actions == 0 and self.who_did_it_sp == "free" and weather_output == 0:
			self.spg1_ws = 0
			#print "The side port South would have been opend at: ", clock.obstimeUT()

		if self.side_port_group_2 == 0 and self.time_active_delay_2 <= time.time() and song_monitor_config.mon_side_ports_actions == 1 and self.who_did_it_sp == "free" and weather_output == 0 and self.side_wind == 0:  
			status_side_port_2 = self.perform_actions.open_side_port(group=2)
	                time.sleep(0.5)
			if status_side_port_2 == "done":
				if self.spg2_ws == 1:
					print clock.timename(), " Side port West will now open"
					self.side_port_group_2 = 1
				self.spg2_ws = 0

		elif self.side_port_group_2 == 0 and self.time_active_delay_2 <= time.time() and song_monitor_config.mon_side_ports_actions == 0 and self.who_did_it_sp == "free" and weather_output == 0:
			self.spg2_ws = 0
			#print "The side port West would have been opend at: ", clock.obstimeUT()

		if self.side_port_group_3 == 0 and self.time_active_delay_3 <= time.time() and song_monitor_config.mon_side_ports_actions == 1 and self.who_did_it_sp == "free" and weather_output == 0 and self.side_wind == 0:  
			status_side_port_3 = self.perform_actions.open_side_port(group=3)
	                time.sleep(0.5)
			if status_side_port_3 == "done":
				if self.spg3_ws == 1:
					print clock.timename(), " Side port North will now open"
					self.side_port_group_3 = 1
				self.spg3_ws = 0


		elif self.side_port_group_3 == 0 and self.time_active_delay_3 <= time.time() and song_monitor_config.mon_side_ports_actions == 0 and self.who_did_it_sp == "free" and weather_output == 0:
			self.spg3_ws = 0
			#print "The side port North would have been opend at: ", clock.obstimeUT()

		if self.side_port_group_4 == 0 and self.time_active_delay_4 <= time.time() and song_monitor_config.mon_side_ports_actions == 1 and self.who_did_it_sp == "free" and weather_output == 0 and self.side_wind == 0:  
			status_side_port_4 = self.perform_actions.open_side_port(group=4)
	                time.sleep(0.5)
			if status_side_port_4 == "done":
				if self.spg4_ws == 1:
					print clock.timename(), " Side port East will now open"
					self.side_port_group_4 = 1
				self.spg4_ws = 0

		elif self.side_port_group_4 == 0 and self.time_active_delay_4 <= time.time() and song_monitor_config.mon_side_ports_actions == 0 and self.who_did_it_sp == "free" and weather_output == 0:
			self.spg4_ws = 0
			#print "The side port East would have been opend at: ", clock.obstimeUT()

		#### This function returns the current state of the 4 side port groups
		return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp

























