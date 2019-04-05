import song_timeclass
import song_monitor_config
import song_checker
import pdu_module
import song_checker_config
import time
import bf_2300_controller
import update_song_database
import song_database_tables
import comm2tcs_read
import comm2tcs_write
import thread
import send_song_mail
import numpy
import slit_module
import pupil_module
import os
import master_config as m_conf
import get_db_values
import urllib2
import song_star_checker
import datetime
import song_star_checker

clock = song_timeclass.TimeClass()
sigu = slit_module.SIGU()
pugu = pupil_module.PUGU()

sun_handle = song_star_checker.sun_pos(m_conf.song_site)

class Do_Actions(object):
	"""
		@brief: This class handles all checks on the weather situation.
	"""

	def __init__(self):
		"""
			@brief: Initializes some parameters.
		"""	
		self.write_to_db = song_monitor_config.write_to_db # 0 = no, 1 = yes
		self.verbose = song_monitor_config.verbose
		self.pdu_handle = pdu_module.APC()

		self.sms_time = 0

		self.counter = 0


	def open_side_port(self,group):
		"""
			@brief: Opens a specified side port.
			group: 1 = South, 2 = West, 3 = North, 4 = East
		"""	
		error = 0
		try:
			value = self.pdu_handle.SetPower("side_ports",(int(group) + 4),2) # Switch off the outlet which keeps the group closed
			value = self.pdu_handle.SetPower("side_ports",int(group),1) # Switch on the outlet which opens the group
		except Exception, error:
			print clock.timename(), " An error occured while trying to open some side ports!: ", error

		try:
			thread.start_new_thread(self.power_outlet,("side_ports",int(group),2,1)) # This tread will turn the power of the outlet after a while.
		except Exception, error:
			print clock.timename(), " An error occured while trying to open some side ports!: ", error

		if error == 0:
			#print "The side port group number: ", group, " was opened at: ", clock.whattime()
			return "done"
		elif error != 0:
			return "error"
		else:
			return "what"

	def close_side_port(self,group):
		"""
			@brief: Closes a specified side port.
			group: 1 = South, 2 = West, 3 = North, 4 = East
		"""
		error = 0
		try:	
			self.pdu_handle.SetPower("side_ports",int(group),2)      # Switch off the outlet which keeps the group open     
			self.pdu_handle.SetPower("side_ports",(int(group) + 4),1)# Switch on the outlet which closes the group
		except Exception, error:
			print clock.timename(), " An error occured while trying to close some side ports!: ", error

		try:
			thread.start_new_thread(self.power_outlet,("side_ports",(int(group) + 4),2,0))	
		except Exception, error:
			print clock.timename(), " An error occured while trying to close some side ports!: ", error

		if error == 0:
			#print "The side port group number: ", group, " was closed at: ", clock.whattime() 
			return "done"
		elif error != 0:
			return "error"
		else:
			return "what"


	def startup_telescope(self):
		"""
			@brief: Starts up the telescope.
		"""
		error = 0

		# Test if the telescope is powered on:
		try:
			telescope_state = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor")
		except Exception, e:
			print clock.timename(), " Could not collect telescope data" 
			telescope_state = -1
			error = "error"
			return "error"	

		#Setting status flag in database about telescope startup. VALUE is 1.0
		try:
			update_song_database.update("tel_dome", ["extra_param_2"], [1.0], "tel_dome_id")
		except Exception,e:
			print clock.timename(), " Problem setting the status value of startup in database: ", e
		else:
			print clock.timename(), " Status flag was set in database to 1.0"

		if float(telescope_state) != float(1.0): 

			print clock.timename(), " The telescope was not powered on and will now be switched on!"
			val = comm2tcs_write.SET_TSI().set_telescope_ready(param=1, sender="Monitor")
			if val.lower() == "done":
				power_on = 1
			else:
				power_on = 0
		else:
			power_on = 1

		if power_on == 0:
			print clock.timename(), " The power on of the telescope did not succeed!"			
			return "error"
		else:

			try:
				focus_offset = comm2tcs_read.GET_TSI().get_position_instrumental_focus_offset(sender="Observer") # Asks what the focus offset is.
			except Exception, e:
				print clock.timename(), " Could not collect telescope info!"
				error = "error"
				return "error"

			if self.verbose == "yes":
				print clock.timename(), " The telescope focus offset is: ", str(focus_offset)

	#		focus_cmd_status = comm2tcs_write.SET_TSI().set_position_instrumental_focus_offset(param=0.0,sender="Observer") # Sets the focus offset to -2.3
	#		if self.verbose == "yes":
	#			print "The telescope focus offset is now 0.0"

			if self.verbose == "yes":
				print clock.timename(), " Now setting the AZ offset to 0.0"
			az_status = comm2tcs_write.SET_TSI().set_position_instrumental_az_offset(param=0.0,sender="Observer")	# Sets telescope azimuth offset to 0.0

	#		if self.verbose == "yes":
	#			print "Now setting the ZD offset to 0.0"
	#		az_status = comm2tcs_write.SET_TSI().set_position_instrumental_zd_offset(param=0.0,sender="Observer")	# Sets telescope zenith distance offset to 0.0


			######################### Initial part ##############################
			tel_state = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor") # This tells the current state of the telescope ( 0 = powered off, 1 = powered on, -3 = local mode)
			if self.verbose == "yes":
				print clock.timename(), " The status of the telescope is: ", tel_state
			if str(tel_state) == "0.0":
				if self.verbose == "yes":
					print clock.timename(), " The telescope will now power on. This takes a few minutes"
				tel_ready_state = comm2tcs_write.SET_TSI().set_telescope_ready(param=1,sender="Monitor") # This will power on the telescope.
			elif float(tel_state) == -3.0:
				print clock.timename(), " The telescope is in local mode and actions will not be performed..."
				return "local_mode"

			err_value = comm2tcs_read.GET_TSI().get_telescope_status_global(sender="Monitor") # This checks if there is any errors.

			if str(err_value) != "0":
				if self.verbose == "yes":
					print clock.timename(), " Some errors had occured. These will now be fixed (hopefully)"
					error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()	
					print ""
					print clock.timename(), error_list
					print ""
				tel_error_state = comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor") # This will fix the errors/warnings on the telescope if there is any.

	#		focus_offset = comm2tcs_read.GET_TSI().get_position_instrumental_focus_offset(sender="Observer") # Asks what the focus offset is.
	#		if float(focus_offset) == float(0.0):
	#			focus_cmd_status = comm2tcs_write.SET_TSI().set_position_instrumental_focus_offset(param=song_monitor_config.tel_focus, sender="Observer") # Sets the focus offset to -2.3
	#			if self.verbose == "yes":
	#				print "The focus offest was now set to -2.3"
	#		else:
	#			focus_cmd_status = comm2tcs_write.SET_TSI().set_position_instrumental_focus_offset(param=0.0,sender="Observer") # Sets the focus offset to 0.0
	#			if focus_cmd_status == "done":
	#				if self.verbose == "yes":
	#					print "The focus offest was now set to 0.0"
	#				focus_cmd_status = comm2tcs_write.SET_TSI().set_position_instrumental_focus_offset(param=song_monitor_config.tel_focus,sender="Observer") # Sets the focus offset to -2.3
	#				if self.verbose == "yes":
	#					print "And now set to: ", song_monitor_config.tel_focus
	
			#####################################################################
			
			# If the sun has set and the wind into the dome is too high the telescope will be moved away from the wind before the dome opens. 
			sun_alt = song_star_checker.sun_pos().sun_alt(unit="f")
			if int(song_checker.Checker().weather_check()[0]) == 8 and sun_alt < 0.0:

				print clock.timename(), " Moving the telescope away from the wind before opening up..."
				self.move_tel_away_from_wind()
			else:
				try:
					comm2tcs_write.SET_TSI().set_object_horizontal_alt(param=75, sender="Monitor")
					comm2tcs_write.SET_TSI().set_object_horizontal_az(param=90, sender="Monitor")
					comm2tcs_write.SET_TSI().set_pointing_setup_dome_syncmode(param=song_monitor_config.dome_syncmode_value,sender="Mads")
				except Exception, e:
					print clock.timename(), e
					print clock.timename(), " Could not set telescope coordinates" 
					motion_state = "error"
					error = "error"
					return "error"
		
				print clock.timename(), " The telescope will now move to AZ=%s and ALT=%s" % (str(90), str(75))
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=2,sender="Monitor")

				d_az = comm2tcs_read.GET_TSI().get_position_horizontal_dome(sender="monitor")
	
				while numpy.abs(float(d_az) - 90.0) > 5.0:
					time.sleep(5)
					d_az = comm2tcs_read.GET_TSI().get_position_horizontal_dome(sender="monitor")			 

			############ Open dome and mirror covers ###############

			if song_monitor_config.open_slit == "yes":

				if self.verbose == "yes":
					print clock.timename(), " The Dome slit will now open"
					print clock.timename(), " This will take a few minutes..."

				slit_value = comm2tcs_write.SET_TSI().set_position_instrumental_dome_slit_targetpos(param=1,sender="Monitor") # This will open the dome slit
				slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")
				time_out = time.time() + 180.0
				while float(slit_state) != float(1.0):

					err_value = comm2tcs_read.GET_TSI().get_telescope_status_global(sender="Observer")
					error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()	
					if int(err_value) == "2" and "timeout" in errorlist.lower():						
						print clock.timename(), " The dome did not finish the movement before timeout"
						print clock.timename(), error_list
						print clock.timename(), " The error will now be acknowledged"							
						tel_error_state = comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")	

					slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")
					time.sleep(5)
					if time.time() > time_out:
						print clock.timename(), " The while loop has timed out and the dome slit are most likely open!"
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Slit opening timeout!",message="The telescope was started and the dome should be open. The while loop timed out but dome might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						break

			if song_monitor_config.open_flap == "yes":
				if self.verbose == "yes":
					print clock.timename(), " The Dome flap will now open"

				flap_value = comm2tcs_write.SET_TSI().set_position_instrumental_dome_flap_targetpos(param=1,sender="Monitor") # This will open the dome flap
				flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
				time_out = time.time() + 180.0
				while float(flap_state) != float(1.0):
					err_value = comm2tcs_read.GET_TSI().get_telescope_status_global(sender="Monitor")
					error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()	
					if int(err_value) == "2" and "timeout" in errorlist.lower():						
						print clock.timename(), " The dome did not finish the movement before timeout"
						print clock.timename(), error_list
						print clock.timename(), " The error will now be acknowledged"							
						tel_error_state = comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor")	

					flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
					time.sleep(5)
					if time.time() > time_out:
						print clock.timename(), " The while loop has timed out and the flap are most likely open!"
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Flap opening timeout!",message="The telescope was started and the dome flap should be open. The while loop timed out but dome flap might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						break

			if song_monitor_config.open_mirror_covers == "yes":
				if self.verbose == "yes":
					print clock.timename(), " The mirror covers will now open"

				comm2tcs_write.SET_TSI().set_auxiliary_cover_targetpos(param=1,sender="Monitor") # This will open the mirror covers.
				mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
				time_out = time.time() + 120.0
				while float(mirror_cover_state) != float(1.0):
					mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
					time.sleep(5)
					if time.time() > time_out:
						print clock.timename(), " The while loop has timed out and the mirror covers are most likely open!"
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Mirror covers opening timeout!",message="The telescope was started and the mirror covers should be open. The while loop timed out but mirror covers might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						break
		
			if self.verbose == "yes":
				print ""
				print clock.timename(), " The telescope is now initialized and ready to observe..."

			if song_monitor_config.send_notifications == "yes" and error == 0:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Telescope Startup!",message="The telescope was started and is now ready to start observations!\n\nEnjoy!\n\nSend at: %s\n\n" % clock.obstimeUT())

			#Setting status flag in database about telescope startup. VALUE back to 0.0
			try:
				update_song_database.update("tel_dome", ["extra_param_2"], [0.0], "tel_dome_id")
			except Exception,e:
				print clock.timename(), " Problem setting the status value of startup done in database: ", e
			else:
				print clock.timename(), " Status flag was set back to 0.0 in database"


			if error == 0:
				return "done"
			elif error != 0:
				return "error"
			else:
				return "what"

	def shutdown_telescope(self):
		"""
			@brief: Shuts down the telescope.
		"""	
		error = 0

		print clock.timename(), " The monitor will now shut down the telescope..."

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

			if self.verbose == "yes":
				print clock.timename(), " The motion state of the telescope is currently: ", motion_state

			if float(track_value) != float(0.0) and error == 0:
				print clock.timename(), " Stop tracking..."
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")

			##### SET OFFSETS TO ZERO #######
			if self.verbose == "yes":
				print "Now setting the Telescope Focus offset to 0.0"
			focus_offset = comm2tcs_read.GET_TSI().get_position_instrumental_focus_offset(sender="Observer") # Asks what the focus offset is.
			if float(focus_offset) != float(0.0) and error == 0:
				focus_cmd_status = comm2tcs_write.SET_TSI().set_position_instrumental_focus_offset(param=0.0,sender="Observer") # Sets the focus offset to 0.0

			if self.verbose == "yes":
				print "Now setting the AZ offset to 0.0"
			az_offset = comm2tcs_read.GET_TSI().get_position_instrumental_az_offset(sender="Observer")
			if float(az_offset) != float(0.0):
				az_status = comm2tcs_write.SET_TSI().set_position_instrumental_az_offset(param=0.0,sender="Observer")	# Sets telescope azimuth offset to 0.0

			if self.verbose == "yes":
				print "Now setting the ZD offset to 0.0"
			zd_offset = comm2tcs_read.GET_TSI().get_position_instrumental_zd_offset(sender="Observer")
			if float(zd_offset) != float(0.0):
				zd_status = comm2tcs_write.SET_TSI().set_position_instrumental_zd_offset(param=0.0,sender="Observer")	# Sets telescope azimuth offset to 0.0



	##### ALL open parts will be closed in the right order:

			mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
			if float(mirror_cover_state) != float(0.0):
				if self.verbose == "yes":
					print clock.timename(), " The mirror covers will now be closed"
				comm2tcs_write.SET_TSI().set_auxiliary_cover_targetpos(param=0,sender="Monitor") # This will open the mirror covers.
				time_out = time.time() + 120.0
				while float(mirror_cover_state) != float(0.0):
					mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
					time.sleep(5)
					if time.time() > time_out:
						print clock.timename(), " The while loop has timed out and the mirror covers are most likely closed!"
						if song_monitor_config.send_notifications == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Mirror cover closing timeout!",message="The telescope was shut down and the mirror covers should be closed. The while loop timed out and the mirror covers might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						break
				if self.verbose == "yes":
					print clock.timename(), " The mirror covers are now closed"

			flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
			if float(flap_state) != float(0.0):
				if self.verbose == "yes":
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
						if song_monitor_config.send_notifications == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Flap closing timeout!",message="The telescope was shut down and the dome flap should be closed. The while loop timed out and the dome flap might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						if song_monitor_config.send_notify_sms == "yes" and self.sms_time < time.time():
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome flap was not closed corretly... Please check")
						if song_monitor_config.send_to_support == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Flap closing timeout!",message="The telescope was shut down and the dome flap should be closed. The while loop timed out and the dome flap might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						self.sms_time = time.time() + song_monitor_config.sms_wait_time
						break
				if self.verbose == "yes":
					print clock.timename(), " The flap is now closed"


			slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")
			if float(slit_state) != float(0.0):
				if self.verbose == "yes":
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
						if song_monitor_config.send_notifications == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Slit closing timeout!",message="The telescope was shut down and the dome slit should be closed. The while loop timed out and the dome slit might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						if song_monitor_config.send_notify_sms == "yes" and self.sms_time < time.time():
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome slit was not closed corretly... Please check")
						if song_monitor_config.send_to_support == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Slit closing timeout!",message="The telescope was shut down and the dome slit should be closed. The while loop timed out and the dome slit might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						self.sms_time = time.time() + song_monitor_config.sms_wait_time
						break
				if self.verbose == "yes":
					print clock.timename(), " The slit is now closed"


			print clock.timename(), " The telescope will now be parked!"
			self.stop_tracking_and_park()

			err_value = comm2tcs_read.GET_TSI().get_telescope_status_global(sender="Monitor") # This checks if there is any errors.
			if str(err_value) != "0":
				if self.verbose == "yes":
					print clock.timename(), " Some errors had occured. These will now be fixed (hopefully)"
					error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()	
					print ""
					print clock.timename(), error_list
					print ""
				tel_error_state = comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Monitor") # This will fix the errors/warnings on the telescope if there is any.

			tel_state = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor") # This tells the current state of the telescope ( 0 = powered off, 1 = powered on)
			if self.verbose == "yes":	
				print clock.timename(), " The status of the telescope is: ", tel_state

			if str(tel_state) != "0.0" and song_monitor_config.power_off_at_shutdown == "yes" and float(slit_state) == float(0.0) and float(flap_state) == float(0.0):
				if self.verbose == "yes":
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
						if song_monitor_config.send_notifications == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS",subject="Telescope shutdown failure!",message="The telescope was asked to shut down but did not!\n\nSend at: %s\n\n" % clock.obstimeUT())	
						if song_monitor_config.send_notify_sms == "yes":
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The telescope was not shut down correctly! Send at: %s" % clock.obstimeUT())
						break

				if self.verbose == "yes" and str(tel_ready_state) == "done":
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

	def abort_acquisition(self):
		"""
			@brief: Stops an ongoing acquisition of the spectrographic CCD camera.
		"""
		error = 0


		if error == 0:
			return "done"
		elif error != 0:
			return "error"
		else:
			return "what"


	def stop_tracking_and_park(self):
		"""
			@brief: This function will stop the telescope from tracking and park it.
		"""
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

			if self.verbose == "yes":
				print clock.timename(), " The motion state of the telescope is currently: ", motion_state

			if float(track_value) != float(0.0) and error == 0:
				print clock.timename(), " Stop tracking..."
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")

			print clock.timename(), " The telescope should have stopped tracking"
			print clock.timename(), " Now the telescope will be parked"
		
			try:
				comm2tcs_write.SET_TSI().set_object_horizontal_alt(param=m_conf.tel_park_alt, sender="Monitor")
				comm2tcs_write.SET_TSI().set_object_horizontal_az(param=m_conf.tel_park_az, sender="Monitor")
				comm2tcs_write.SET_TSI().set_pointing_setup_dome_syncmode(param=song_monitor_config.dome_syncmode_value,sender="Mads")
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

				if time.time() > warn_time + 120 and self.sms_time < time.time():	# If the telescope has not reached its parking position after 2 minutes....
					if song_monitor_config.send_notifications == "yes":
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS",subject="Telescope park fail!",message="The telescope was asked to park but did not!\n\nSend at: %s\n\n" % clock.obstimeUT())	
					if song_monitor_config.send_notify_sms == "yes":
						send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The telescope was not parked correctly! Send at: %s" % clock.obstimeUT())
						self.sms_time = time.time() + song_monitor_config.sms_wait_time
					if song_monitor_config.send_to_support == "yes":
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

	def stop_tracking(self):
		"""
			@brief: This function will stop the telescope from tracking.
		"""
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
			return "shutdown"

		else:
			try:
				track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Monitor")
				motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="Monitor")
			except Exception, e:
				print clock.timename(), " Could not collect telescope data" 
				motion_state = "error"
				error = "error"
				return "error"

			if self.verbose == "yes":
				print clock.timename(), " The motion state of the telescope is currently: ", motion_state

			if float(track_value) != float(0.0) and error == 0:
				print clock.timename(), " Stop tracking..."
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")
				time.sleep(2)
				track_value = comm2tcs_read.GET_TSI().get_pointing_track(sender="Monitor")
				if track_state != "done":
					print clock.timename(), " The telescope did not stop correctly!!!"
					error = 1
			elif float(track_value) == 0.0:
				print clock.timename(), " The telescope have stopped tracking"

			if error == 0:
				return "done"
			elif error != 0:
				return "error"
			else:
				return "what"

	def move_tel_up(self):
		"""
			@brief: This function will stop the telescope from tracking and park it.
		"""
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

			if self.verbose == "yes":
				print clock.timename(), " The motion state of the telescope is currently: ", motion_state

			if float(track_value) != float(0.0) and error == 0:
				print clock.timename(), " Stop tracking..."
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")

			print clock.timename(), " The telescope should have stopped tracking"
			print clock.timename(), " Now the telescope will be moved"
		
			try:
				comm2tcs_write.SET_TSI().set_object_horizontal_alt(param=30., sender="Monitor")
				comm2tcs_write.SET_TSI().set_pointing_setup_dome_syncmode(param=song_monitor_config.dome_syncmode_value,sender="Mads")
			except Exception, e:
				print clock.timename(), " Could not collect telescope data" 
				motion_state = "error"
				error = "error"
				return "error"

			tel_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="Monitor"))
		
			track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=2,sender="Monitor")
			warn_time = time.time()
			stop_param = 0
			while tel_alt < float(m_conf.telescope_min_altitude):
				time.sleep(1.0)				
				tel_alt = float(comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="Monitor"))
				print clock.timename(), " The telescope altitude is: ", tel_alt
		
			track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")

			if track_state != "done":
				print clock.timename(), " The telescope did move up correctly!!!"
				error = 1
			else:
				print clock.timename(), " The telescope has now moved up!"

			if error == 0:
				return "done"
			elif error != 0:
				return "error"
			else:
				return "what"

	def oc_flap(self, action=1):
		"""
			@brief: This function will open or close the dome flap.
		"""
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

			if (float(track_value) != float(0.0) or float(motion_state) != float(0.0)) and action == 1:
					flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
					if float(flap_state) == float(0.0):
						print clock.timename(), " Now opening the dome flap"
						comm2tcs_write.SET_TSI().set_position_instrumental_dome_flap_targetpos(param=1,sender="Monitor") # This will open the mirror covers.
					elif float(flap_state) == float(1):
						print clock.timename(), " The dome flap is already open!"
			elif (float(track_value) != float(0.0) or float(motion_state) != float(0.0)) and action == 0:			
					flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
					if float(flap_state) != float(0.0):
						print clock.timename(), " Now closing the dome flap"
						comm2tcs_write.SET_TSI().set_position_instrumental_dome_flap_targetpos(param=0,sender="Monitor") # This will open the mirror covers.
					elif float(flap_state) == float(0):
						print clock.timename(), " The dome flap is already closed!"

			if error == 0:
				return "done"
			elif error != 0:
				return "error"
			else:
				return "what"


	def stop_sigu_and_pugu(self):
		"""
			@brief: This function sets sigu and pugu to pause
		"""
		print clock.timename(), " Now stopping sigu and pugu"
		
		val = pugu.exec_action("pause")	
		if val != "done":
			print clock.timename(), " Return value of pugu pause was: ", val
			#return "no_go"
		else:
			print clock.timename(), " Pugu pause performed correctly..."

		val = pugu.exec_action("stop")	
		if val != "done":
			print clock.timename(), " Return value of pugu stop was: ", val
			#return "no_go"
		else:
			print clock.timename(), " Pugu stop performed correctly..."

		val = sigu.exec_action("pause")	
		if val != "done":
			print clock.timename(), " Return value of sigu pause was: ", val
			return "no_go"
		else:
			print clock.timename(), " Sigu pause performed correctly..."

		val = sigu.exec_action("stop")	
		if val != "done":
			print clock.timename(), " Return value of sigu stop was: ", val
			#return "no_go"
		else:
			print clock.timename(), " Sigu stop performed correctly..."

		val = sigu.exec_action("moveto", ["idle"])	
		if val != "done":
			print clock.timename(), " Return value of sigu moveto idle was: ", val
			#return "no_go"
		else:
			print clock.timename(), " Sigu movto idle performed correctly..."

		val = pugu.exec_action("moveto", ["idle"])	
		if val != "done":
			print clock.timename(), " Return value of pugu moveto idle was: ", val
			#return "no_go"
		else:
			print clock.timename(), " Pugu movto idle performed correctly..."

		try:
			os.system("python /home/obs/programs/guiders/pupil/pupil_guider.py -t")
			#os.system("python /home/obs/programs/guiders/slit/slit_guider.py -t")
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), " slit guider and pupil guider was not terminated correctly"	


		return 1


	def start_guiders(self):
		#try:
		#	os.popen("python /home/obs/programs/guiders/slit/slit_guider.py -t", "w")
		#except Exception, e:
		#	print clock.timename(), "Something went wrong when trying to stop slit guider!"
		#	print clock.timename(), e

		#time.sleep(2)

		#try:
		#	os.popen("python /home/obs/programs/guiders/slit/slit_guider.py -s", "w")
		#except Exception, e:
		#	print clock.timename(), "Something went wrong when trying to start slit guider!"
		#	print clock.timename(), e

		#time.sleep(10)

		#val = sigu.exec_action("pause")	
		#if val != "done":
		#	print clock.timename(), " Return value of sigu pause was: ", val
		#	#return "no_go"
		#else:
		#	print clock.timename(), " Sigu pause performed correctly..."

		#time.sleep(3)

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

		time.sleep(10)

		val = pugu.exec_action("pause")	
		if val != "done":
			print clock.timename(), " Return value of pugu pause was: ", val
			#return "no_go"
		else:
			print clock.timename(), " Pugu pause performed correctly..."

		return 1


	def start_cooler(self, temp):
		"""
			@brief: This will set the temperature of the cooling unit and set it to run
		"""
		try:
			cooler_state = os.popen("coolerd -s").readlines()[0].split("\n")[0][-2:].strip()
		except Exception, e:
			print clock.timename(), " The state of the cooler was not read correctly"	
			print clock.timename(), e

		if float(cooler_state) == 0.0:
			try:
				os.system("coolerd -T %f" % float(temp))
				os.system("coolerd -r")
				print clock.timename(), os.popen("coolerd -s").readlines()[0].strip()
			except Exception, e:	
				print clock.timename(), " The cooler was not set to cool correctly"
				print clock.timename(), e
				return "error"

		return "done"

	def stop_cooler(self):
		"""
			@brief: This will set the temperature of the cooling unit to a high value and set it to idle
		"""
		# This will read the actual temperature from the sensor of the cooling unit. 
		try:
			cooler_state = os.popen("coolerd -s").readlines()[0].split("\n")[0][-2:].strip()
		except Exception, e:
			print clock.timename(), " The state of the cooler was not read correctly"
			print clock.timename(), e

		if float(cooler_state) == 1.0:
			print clock.timename(), " Now trying to stop the cooler"
			try:
				act_temp = float(os.popen("coolerd -s").readlines()[0].split(" ")[1].split(":")[0])
			except Exception, e:
				print clock.timename(), " The temperature from the cooler was not read correctly"
				print clock.timename(), e
				act_temp = 20.0
			try:
				os.system("coolerd -T %f" % (float(act_temp) + 10.0))
				os.system("coolerd -i")
				print clock.timename(), os.popen("coolerd -s").readlines()[0].strip()
			except Exception, e:	
				print clock.timename(), " The cooler was not set to stop correctly"
				print clock.timename(), e
				return "error"

		return "done"


	def close_mc_and_dome(self):
		"""
			@brief: Shuts down the telescope.
		"""	
		error = 0

		print clock.timename(), " The monitor will now close the mirror covers and the dome..."

		# Test if the telescope is powered on:
		try:
			telescope_state = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor")
		except Exception, e:
			print clock.timename(), " Could not collect telescope data" 
			telescope_state = -1
			error = "error"
			return "error"	

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

			if self.verbose == "yes":
				print clock.timename(), " The motion state of the telescope is currently: ", motion_state

			if float(track_value) != float(0.0) and error == 0:
				print clock.timename(), " Stop tracking..."
				track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")

	##### ALL open parts will be closed in the right order:

			mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
			if float(mirror_cover_state) != float(0.0):
				if self.verbose == "yes":
					print clock.timename(), " The mirror covers will now be closed"
				comm2tcs_write.SET_TSI().set_auxiliary_cover_targetpos(param=0,sender="Monitor") # This will open the mirror covers.
				time_out = time.time() + 120.0
				while float(mirror_cover_state) != float(0.0):
					mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
					time.sleep(5)
					if time.time() > time_out:
						print clock.timename(), " The while loop has timed out and the mirror covers are most likely closed!"
						if song_monitor_config.send_notifications == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Mirror cover closing timeout!",message="The telescope was shut down and the mirror covers should be closed. The while loop timed out and the mirror covers might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						break

			flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
			if float(flap_state) != float(0.0):
				if self.verbose == "yes":
					print clock.timename(), " The flap will now be closed"
				comm2tcs_write.SET_TSI().set_position_instrumental_dome_flap_targetpos(param=0,sender="Monitor") # This will open the mirror covers.
				time_out = time.time() + 180.0
				while float(flap_state) != float(0.0):
					err_value = comm2tcs_read.GET_TSI().get_telescope_status_global(sender="Observer")
					error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()	
					if int(err_value) == "2" and "timeout" in errorlist.lower():						
						print clock.timename(), " The dome did not finish the movement before timeout"
						print clock.timename(), error_list
						print clock.timename(), " The error will now be acknowledged"							
						tel_error_state = comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Observer")						
						
					flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
					time.sleep(5)
					if time.time() > time_out and self.sms_time < time.time():
						print clock.timename(), " The while loop has timed out and the flap are most likely closed!"
						if song_monitor_config.send_notifications == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Flap closing timeout!",message="The telescope was shut down and the dome flap should be closed. The while loop timed out and the dome flap might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						if song_monitor_config.send_notify_sms == "yes":
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome flap was not closed corretly... Please check")
						if song_monitor_config.send_to_support == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Flap closing timeout!",message="The telescope was shut down and the dome flap should be closed. The while loop timed out and the dome flap might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						self.sms_time = time.time() + song_monitor_config.sms_wait_time
						break

			slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")
			if float(slit_state) != float(0.0):
				if self.verbose == "yes":
					print clock.timename(), " The slit will now be closed"
				comm2tcs_write.SET_TSI().set_position_instrumental_dome_slit_targetpos(param=0,sender="Monitor") # This will open the mirror covers.
				time_out = time.time() + 180.0
				while float(slit_state) != float(0.0):
					slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")

					err_value = comm2tcs_read.GET_TSI().get_telescope_status_global(sender="Observer")
					error_list = comm2tcs_read.GET_TSI().get_telescope_status_list()	
					if int(err_value) == "2" and "timeout" in errorlist.lower():						
						print clock.timename(), " The dome did not finish the movement before timeout"
						print clock.timename(), error_list
						print clock.timename(), " The error will now be acknowledged"							
						tel_error_state = comm2tcs_write.SET_TSI().set_telescope_clear_warning(sender="Observer")	

					time.sleep(5)
					if time.time() > time_out and self.sms_time < time.time():
						print clock.timename(), " The while loop has timed out and the dome slit are most likely closed!"
						if song_monitor_config.send_notifications == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Slit closing timeout!",message="The telescope was shut down and the dome slit should be closed. The while loop timed out and the dome slit might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						if song_monitor_config.send_notify_sms == "yes":
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome slit was not closed corretly... Please check")
						if song_monitor_config.send_to_support == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Slit closing timeout!",message="The telescope was shut down and the dome slit should be closed. The while loop timed out and the dome slit might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
						self.sms_time = time.time() + song_monitor_config.sms_wait_time
						break

			if error == 0:
				return "done"
			elif error != 0:
				return "error"
			else:
				return "what"
		

	def cooler_status(self):

		try:
			cooler_state = os.popen("coolerd -s").readlines()[0].split("\n")[0][-2:].strip()
		except Exception, e:
			print clock.timename(), " The state of the cooler was not read correctly"	
			print clock.timename(), e
			cooler_state = "error"

		return cooler_state


	def move_tel_away_from_wind(self):
		"""
		 @brief: This functions will move the telescope away from the wind direction.
		"""
		error = 0
		ret_val = self.stop_tracking()
		if ret_val == "done":
			wind_data = get_db_values.db_connection().get_fields_site01("weather_station", ["wxt520_wind_avgdir"])
			now_az = float(comm2tcs_read.GET_TSI().get_position_horizontal_az(sender="Monitor"))
			try:
				move_to_az = (float(wind_data["wxt520_wind_avgdir"]) + song_monitor_config.tel_away_angle) % 360.	# determine the az to move to.			
			except Exception, e:
				print clock.timename(), " Could not collect determine move to az using wind direction..." 
				move_to_az = (now_az + song_monitor_config.tel_away_angle) % 360.	# determine the az to move to.

			try:
				comm2tcs_write.SET_TSI().set_object_horizontal_alt(param=song_monitor_config.tel_away_alt, sender="Monitor")
				comm2tcs_write.SET_TSI().set_object_horizontal_az(param=move_to_az, sender="Monitor")
				comm2tcs_write.SET_TSI().set_pointing_setup_dome_syncmode(param=song_monitor_config.dome_syncmode_value,sender="Mads")
			except Exception, e:
				print clock.timename(), " Could not collect telescope data" 
				motion_state = "error"
				error = "error"
				return "error"

			print clock.timename(), " The telescope was pointing towards AZ=%s" % (str(now_az))
			print clock.timename(), " The telescope will now move to AZ=%s and ALT=%s" % (str(move_to_az), str(song_monitor_config.tel_away_alt))
			track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=2,sender="Monitor")
			tel_az = comm2tcs_read.GET_TSI().get_position_horizontal_az(sender="Monitor")
			timeout = time.time() + 60
			while float(tel_az) - move_to_az > 5.0:
				time.sleep(2.0)
				tel_az = comm2tcs_read.GET_TSI().get_position_horizontal_az(sender="Monitor")
				print clock.timename(), "The telescope was at %f and should go to %f" % (tel_az, move_to_az)
				if time.time() > timeout:
					print clock.timename(), "The telescope did not move away in time..."
					if song_monitor_config.send_notifications == "yes":
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Telescope movement timeout!",message="The telescope did not move away from the wind in less than one minute. Something is wrong!\n\nSend at: %s\n\n" % clock.obstimeUT())
					if song_monitor_config.send_notify_sms == "yes":
						send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The telescope is pointing into high wind... Please check")	
			
			track_state = comm2tcs_write.SET_TSI().set_pointing_track(param=0,sender="Monitor")

			if track_state != "done":
				print clock.timename(), " The telescope did not move away correctly!!!"
				error = 1
			else:
				print clock.timename(), " The telescope is now pointed away from the wind!"

			if error == 0:
				return "done"
			elif error != 0:
				return "error"
			else:
				return "what"

		elif ret_val == "shutdown":
			return "shutdown"
		
		else:
			return "error"


	def power_cycle_dome_controller(self):
		"""
		 @brief: This functions will move the telescope away from the wind direction.
		"""		
		error = 0

		try:	
			print clock.timename(), "Power off the dome controller..."
			self.pdu_handle.SetPower("container",24,2)      # Switch off the outlet for the dome controller 
		except Exception, error:
			print clock.timename(), " An error occured while trying to close some side ports!: ", error

		time.sleep(5)

		try:	
			print clock.timename(), "Power on the dome controller..."
			self.pdu_handle.SetPower("container",24,1)      # Switch on the outlet for the dome controller 
		except Exception, error:
			print clock.timename(), " An error occured while trying to close some side ports!: ", error

		if error == 0:
			#print "The side port group number: ", group, " was closed at: ", clock.whattime() 
			return "done"
		elif error != 0:
			return "error"
		else:
			return "what"

	def reference_dome(self):
		
		try:
			dome_position = comm2tcs_read.GET_TSI().get_position_instrumental_dome_az_currpos(sender="Monitor")
			print clock.timename(), "The current reported position of the dome was: ", dome_position		
			dome_az_offset = comm2tcs_read.GET_TSI().get_position_instrumental_dome_az_offset(sender="Monitor")
			print clock.timename(), "The current offsets of the dome was: ", dome_az_offset
			print clock.timename(), "Now setting offset to 180 degrees in one direction"
			comm2tcs_write.SET_TSI().set_position_instrumental_dome_az_offset(param=-180,sender="Monitor")

			timeout = time.time() + 40 # it has 40 seconds to reach the offset
			while numpy.abs(float(dome_az_offset) + 180.) > 5:
				time.sleep(30)
				dome_az_offset = comm2tcs_read.GET_TSI().get_position_instrumental_dome_az_offset(sender="Monitor")
				print clock.timename(), "The current offsets of the dome was: ", dome_az_offset
				if time.time() > timeout:
					print clock.timename(), "Timeout was reach for setting the offset"
					break
		
			print clock.timename(), "Now setting offset to 360 degrees which will move it back"
			comm2tcs_write.SET_TSI().set_position_instrumental_dome_az_offset(param=360,sender="Monitor")		
			
			timeout = time.time() + 40 # it has 40 seconds to reach the offset
			while numpy.abs(float(dome_az_offset) - 360.) > 5:
				time.sleep(30)
				dome_az_offset = comm2tcs_read.GET_TSI().get_position_instrumental_dome_az_offset(sender="Monitor")
				print clock.timename(), "The current offsets of the dome was: ", dome_az_offset
				if time.time() > timeout:
					print clock.timename(), "Timeout was reach for setting the offset"
					break

			print clock.timename(), "Now setting the offset to 0 degrees where it already should be"
			comm2tcs_write.SET_TSI().set_position_instrumental_dome_az_offset(param=0,sender="Monitor")
		except Exception,e:
			print clock.timename(), e
			return "error"
		else:		
			return "done"		



###################################################################################################################
###################################################################################################################
###################################################################################################################
################      Functions to take stand alone actions
###################################################################################################################
###################################################################################################################
###################################################################################################################

	def power_outlet(self, pdu, outlet, status, end_state):
		"""
		 @brief: This functions will turn off an outlet after a while to make sure the side ports are fully opned or closed.
			 The end_state is the value which the bf_controller should reach when the power is turned of the outlet. 
		"""
		print clock.timename(), " Power on/off PDU: ", pdu, outlet, status
		if self.write_to_db == 1 and pdu == "side_ports":
			if outlet == 1 or outlet == 5:
				update_song_database.update("tel_dome", ["side_port_1"], [2], "tel_dome_id") 
			if outlet == 2 or outlet == 6:
				update_song_database.update("tel_dome", ["side_port_2","side_port_3"], [2,2], "tel_dome_id") 
			if outlet == 3 or outlet == 7:
				update_song_database.update("tel_dome", ["side_port_4","side_port_5"], [2,2], "tel_dome_id") 
			if outlet == 4 or outlet == 8:
				update_song_database.update("tel_dome", ["side_port_6","side_port_7"], [2,2], "tel_dome_id") 

		clock.TimeSleep2(song_monitor_config.power_off_sleep_time)
		value = self.pdu_handle.SetPower(pdu,outlet,status)
		clock.TimeSleep2(1)
		try:
			hall_state = bf_2300_controller.bf_reader().read_input(song_monitor_config.hall_input[int(outlet)-1])
		except Exception, e:
			self.counter = 0
			print clock.timename(), " Could not read the BF 2300"
		if self.counter != 0: # This is not checked on startup!
			if hall_state != end_state and end_state == 1:
				print clock.timename(), " hall_state was: %s and end_state was: %s" % (hall_state, end_state)
				print clock.timename(), " The side ports at pdu outlet number ", outlet, " was not opend"
			elif hall_state != end_state and end_state == 0:
				print clock.timename(), " hall_state was: %s and end_state was: %s" % (hall_state, end_state)
				print clock.timename(), " The side ports at pdu outlet number ", outlet, " was not closed"
				
				#if song_monitor_config.send_sms == "yes":
					#send_song_mail.send_mail().send_sms(receiver=song_monitor_config.send_sms_to_whom, message="The side ports were not closed correctly! Damit!")		
   
		if self.counter == 0:
			#clock.TimeSleep2(30)
			self.counter = 1
 		return 1



	def check_shutdown(self):
		"""
			@brief: This functions will check if the dome is properly closed after shutdown. 
			Returns 1 if everything is okay and 0 if something is wrong.
		"""
		try:
			mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
			slit_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")	
			flap_state = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
		except Exception, e:
			print clock.timename(), e
			return_value = 0

		if float(slit_state) != float(0.0) or float(flap_state) != float(0.0):
			return_value = 0

		elif float(mirror_cover_state) != float(0.0) and (float(slit_state) == float(0.0) or float(flap_state) == float(0.0)):
			return_value = 2

		else:
			return_value = 1

		return return_value


	def open_mirror_covers(self, msg):
		if self.verbose == "yes":
			print clock.timename(), " The mirror covers will now open"
		try:
			comm2tcs_write.SET_TSI().set_auxiliary_cover_targetpos(param=1,sender="Observer") # This will open the mirror covers.
			mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Observer")
			time_out = time.time() + 180.0
			while float(mirror_cover_state) != float(1.0):
				mirror_cover_state = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Observer")
				time.sleep(5)
				if time.time() > time_out:
					print clock.timename(), " The while loop has timed out and the mirror covers are most likely open!"
					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Mirror covers opening timeout!",message="The telescope was started and the mirror covers should be open. The while loop timed out but mirror covers might be open.\n\nSend at: %s\n\n" % clock.obstimeUT())
					break
		except Exception,e:
			print clock.timename(), " Failure in opening the mirror covers: ", e

	def open_mc_now(self):
		try:
			ret_val = thread.start_new_thread(self.open_mirror_covers, ("",))	
		except Exception,e:
			print clock.timename(), " Failure in opening the mirror cover thread: ", e

		return 1

	def save_dome_image(self):
		#print clock.timename(), " Turn on light in dome"
		#self.pdu_handle.SetPower("container",9,1)
		#time.sleep(2)

		sun_alt = sun_handle.sun_alt(unit="f")

		now_hour = time.strftime("%H", time.gmtime())
		now_date = time.strftime("%Y%m%d", time.gmtime())

		if float(sun_alt) < 0.0 and int(now_hour) >= int(0):
			yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
			folder_date = yesterday.strftime('%Y%m%d')
		else:
			folder_date = now_date

		print clock.timename(), " Saving a web cam image from web cam 1"
		try:
			webcam_1 = "http://161.72.135.25/cgi-bin/viewer/video.jpg?streamid=4"
			opener1 = urllib2.build_opener()
			page1 = opener1.open(webcam_1)
			my_picture = page1.read()
			filename1 = "/scratch/star_spec/" + folder_date + "/web_cam_1_" + str(clock.timename()) + ".jpg"
			fout = open(filename1, "wb")
			fout.write(my_picture)
			fout.close()
		except Exception,e:
			print e
			print "Could not get web cam 4 image"
		else:
			print clock.timename(), "Web cam image was saved"

		#print clock.timename(), " Turn off light in dome"
		#self.pdu_handle.SetPower("container",9,2)

		return filename1



