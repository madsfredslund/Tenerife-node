import song_checker
import song_timeclass
import mon_actions
import time
import thread
import song_monitor_config
import song_checker_config
import song_star_checker
import datetime
import get_db_values
import xmlrpclib
import send_song_mail
import psycopg2
import master_config as m_conf
import os
import sys
import subprocess

skycam = xmlrpclib.ServerProxy('http://hw.prv:8035')

clock = song_timeclass.TimeClass()

class Check_Time(object):
	"""
		@brief: This class handles all checks on the time of day.
	"""
	def __init__(self):
		"""
			Initialization of the time checks.
		"""
		self.mon_time_value = song_monitor_config.mon_time # 1 = do things, 0 = do nothing.
		self.sun_handle = song_star_checker.sun_pos(site=m_conf.song_site) # site=1: Tenerife
		self.verbose = song_monitor_config.verbose
		self.perform_actions = mon_actions.Do_Actions()
		self.skycam_start = m_conf.start_skycam_movie
		self.local_mode = 0
		self.sms_send = 0
		self.check_ors = 0
		self.open_mirror_covers = 0
		self.bad_weather_sms = 0
		self.scheduler_val = 0
		self.local_mode_sms = 0
		self.x_mas_notify = 0


	def check_sun(self, side_port_group_1, side_port_group_2, side_port_group_3, side_port_group_4, telescope_state, slit_state, flap_state, mirror_cover_state, who_did_it_tel,  who_did_it_sp):
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


		### GET DUST VALUE: ##############################
		try:
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
			curr = conn.cursor()
			stmt = 'SELECT dust_level FROM weather_station WHERE ins_at = (SELECT max(ins_at) FROM weather_station)'
			curr.execute(stmt)
			results = curr.fetchone()
			dust_value = results[0]
		except Exception,e:
			print clock.timename(), " Could not get dust value from database!"
			dust_value = 0.011


		if song_monitor_config.mon_telescope_actions == 1:
			#### Get telescope poitning direktion ####
			tel_value = get_db_values.db_connection().get_fields_site01("tel_dome", ["tel_az"])
			tel_az = tel_value["tel_az"]

#		if float(self.telescope_state) == float(-3.0) and self.local_mode == 0:
#			print clock.timename(), " The telescope was put in local mode"
#			if song_monitor_config.send_notifications == "yes":						
#				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Telescope in local mode!", message="The telescope was put in local mode!\n\nSend at: %s\n\n" % clock.obstimeUT())	
#			if song_monitor_config.send_notify_sms == "yes":
#				send_song_mail.send_mail().send_sms(receiver=["Mads"], message="Someone has put the telescope into local mode")	
#			self.local_mode = 1
#		elif float(self.telescope_state) == float(0.0) and self.local_mode == 1:
#			print clock.timename(), " The telescope was put back in remote mode"
#			if song_monitor_config.send_notifications == "yes":						
#				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS", subject="Telescope back in remote mode!", message="The telescope was put back in remote mode!\n\nSend at: %s\n\n" % clock.obstimeUT())		
#			self.local_mode = 0

		if float(sun_alt_d) >= (float(m_conf.obs_sun_alt) + 2.0) and hours_to_next_sun_set >= m_conf.open_time_tel and hours_from_pre_sun_set >= m_conf.open_time_tel:
	
			#######################################
			#### Close dome and park telescope ####			
			#######################################
			if self.skycam_start == 0:
				print clock.timename(), " Resetting skycam starting parameter"
				self.skycam_start = 1
				try:
					self.sc2_handle.kill()
				except Exception,e:
					print e
					print clock.timename(), " Could not kill the skycam 2 process"

			if song_monitor_config.mon_telescope_actions == 1 and float(self.telescope_state) != float(0.0) and float(self.telescope_state) != float(-3.0):
#				if float(self.slit_state) != 0.0 or float(self.flap_state) != 0.0 or float(self.mirror_cover_state) != 0.0:
				if float(self.slit_state) != 0.0 or float(self.flap_state) != 0.0 or (float(self.mirror_cover_state) != 0.0 and song_monitor_config.allow_mc_open != "yes"):
					
					status_tel = self.perform_actions.shutdown_telescope()					

					if status_tel == "done":
						self.who_did_it_tel = "time"		
						print clock.timename(), " The dome was closed due to daylight"

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
						if song_monitor_config.send_sms == "yes" and self.sms_send == 0:
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The dome was not closed corretly...")							
						if song_monitor_config.send_to_support == "yes" and self.sms_send == 0:
							send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Telescope Closing Error!", message="The dome was not closed correctly after shutdown!\n\nSend at: %s\n\n" % clock.obstimeUT())
							self.sms_send = 1

					###### Stop sigu and pugu ########
					print clock.timename(), " Stopping the slit and pupil guiders"
					try:
						status_sigu_pugu = self.perform_actions.stop_sigu_and_pugu()
					except Exception, e:
						print clock.timename(), " Could not connect to Sigu and/or Pugu. They might be stopped already!"						

					if status_sigu_pugu != 1:
						print clock.timename(), " Something went wrong when trying to stop sigu and pugu"

				else:
					if self.who_did_it_tel == "free":
						self.who_did_it_tel = "time"
					self.time_delay_telescope = time.time() + (song_checker_config.telescope_delay_time * 60)
					### Maybe the sms send parameter should be placed elsewhere...
					self.sms_send = 0
		
			else:
				if float(self.telescope_state) != 0.0 and self.who_did_it_tel == "free":
					self.who_did_it_tel = "time"	
					print clock.timename(), " The dome would have been closed due to daylight"

				elif float(self.telescope_state) == 0.0 and self.who_did_it_tel != "weather":
					if self.verbose == "yes":
						print clock.timename(), " The Sun is above the horizon so the telescope will stay as it is"
					self.who_did_it_tel = "time"



		elif float(sun_alt_d) < (float(m_conf.obs_sun_alt) + 1.0) or hours_to_next_sun_set < m_conf.open_time_tel or hours_from_pre_sun_set < m_conf.open_time_tel:
			#######################################
			####      Start up telescope       ####			
			#######################################

			if self.verbose == 'yes':
				print clock.timename(), " The altitude of the Sun is: %s" % (sun_alt_d)

			allowed_to_observe = True
			for bad_date in m_conf.do_not_observe:
				year = time.strftime("%Y", time.gmtime())
				date_str = "%s/%s 23:59:59" % (year, bad_date)
				start_bad_time = datetime.datetime.strptime(str(date_str), "%Y/%d/%m %H:%M:%S") - datetime.timedelta(hours=12)
				stop_bad_time = datetime.datetime.strptime(str(date_str), "%Y/%d/%m %H:%M:%S") + datetime.timedelta(hours=12)
				if datetime.datetime.utcnow() > start_bad_time and datetime.datetime.utcnow() < stop_bad_time:
					allowed_to_observe = False

			if song_monitor_config.mon_telescope_actions == 1 and allowed_to_observe == True:	# around x-mas and new year 
			
				if self.who_did_it_tel == "time" or (float(self.telescope_state) == 0.0 and self.who_did_it_tel == "free"):	
			
					if self.verbose == "yes" and self.who_did_it_tel == "time":
						print clock.timename(), " The Sun is about to set so the dome is allowed to be opened"
					elif self.verbose == "yes" and float(self.telescope_state) == 0.0:
						print clock.timename(), " The Weather turned good and the telescope will now open"

					status_tel = self.perform_actions.startup_telescope()

					if status_tel == "done":
						print clock.timename(), " The telescope is now ready for observing"
						#if song_monitor_config.send_notifications == "yes":
							#send_song_mail.send_mail().sending_an_email(reciever=["mads"],sender="SONG_MS",subject="Observations startup!",message="The Sun has set and observation can be started!")

						if hours_to_next_sun_set < m_conf.open_time_tel and hours_to_next_sun_set > m_conf.open_time_tel - 1:
							try:
								if song_monitor_config.send_notify_sms == "yes" and self.who_did_it_tel == "time":
									print clock.timename(), " A SMS will be sent about telescope startup..."
									send_song_mail.send_mail().send_sms(receiver=m_conf.notify_sms_who, message="Weather is great at Tenerife and the telescope has opend up!")
							except Exception, e:
								print clock.timename(), e
								print clock.timename(), " Could not send startup SMS!"

					if status_tel == "local_mode" and self.local_mode_sms == 0:
						print clock.timename(), " A SMS will be sent about telescope in local mode..."
						send_song_mail.send_mail().send_sms(receiver=m_conf.notify_sms_who, message="The telescope is put into local mode and cannot start up!")
						self.local_mode_sms = 1
						

					self.who_did_it_tel = "free"

				elif self.who_did_it_tel == "weather" and self.bad_weather_sms == 0 and float(self.telescope_state) == 0.0:

					if hours_to_next_sun_set < m_conf.open_time_tel and hours_to_next_sun_set > m_conf.open_time_tel - 1:
						try:
							if song_monitor_config.send_notify_sms == "yes" and self.who_did_it_tel == "weather":
								print clock.timename(), " A SMS will be sent about telescope staying shut down because of bad weather..."
								send_song_mail.send_mail().send_sms(receiver=m_conf.notify_sms_who, message="Telescope remains closed due to bad weather at the moment!")
						except Exception, e:
							print clock.timename(), e
							print clock.timename(), " Could not send 2 hours before sunset SMS!"

						self.bad_weather_sms = 1

			elif time.strftime("%m-%d", time.gmtime()) in m_conf.do_not_observe and float(time.strftime("%H", time.gmtime())) > 10.:
				print clock.timename(), " The Teide Observatory is closed today and we will not observe...\n"	
				if self.x_mas_notify < time.time():			
					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Merry X-mas and happy new year!", message="The telescope will stay closed tonight because of no personal on site!\n\nSend at: %s\n\n" % clock.obstimeUT())
					self.x_mas_notify = time.time() + (3600*24)


			elif song_monitor_config.mon_telescope_actions == 1 and float(self.telescope_state) != float(1.0) and self.who_did_it_tel == "time":
				print clock.timename(), " The telescope was powered off and the dome was not opened"	
				if song_monitor_config.send_notifications == "yes":
					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Telescope powered off!", message="The telescope was powered off when the Sun was setting. If you want to open the slit now, then power it on!\n\nSend at: %s\n\n" % clock.obstimeUT())


				

			
		#### This will start the Skycam movie.... ###	
		if self.skycam_start == 1 and float(sun_alt_d) < m_conf.skycam_start_sun_alt and float(self.slit_state) != 0:
			try:			
				print clock.timename(), " Now starting the skycam movie"
				# exptime, movie_handle, time_between_im, binX, binY, starth, startv, endh, endv, gain
				skycam_val = skycam.movie_creator(m_conf.skycam_movie_exptime,"start",m_conf.skycam_movie_delay,1,1,1,1,1600,1200,1)
			except Exception, e:
				print clock.timename(), " Did not start the skycam movie"
				print clock.timename(), e

			if song_monitor_config.start_skycam2_loop == "yes":
				try:				
					sc2_output = open("/home/obs/logs/skycam2.log","a")
					#print clock.timename(), " Now starting to cool the skycam 2 to %s degrees" % str(song_monitor_config.skycam2_cool_temp)
					#sc2_set_temp = subprocess.Popen(["python","/home/madsfa/subversion/trunk/skycam/skycam-2/sc2_set_client.py", "-t%s" % str(song_monitor_config.skycam2_cool_temp)], stdout=sc2_output, stderr=sc2_output)
					print clock.timename(), " Now starting the skycam 2 automatic image collection"
					self.sc2_handle = subprocess.Popen(["python","/home/madsfa/subversion/trunk/skycam/skycam-2/sc2_looping.py"], stdout=sc2_output, stderr=sc2_output)
				except Exception, e:
					print clock.timename(), " Did not start the skycam 2 automatic image collection"
					print clock.timename(), e


			self.skycam_start = 0

		if song_monitor_config.mon_OR_scheduler == 1:
			if (float(sun_alt_d) < (float(m_conf.obs_sun_alt) + 1.0) or hours_to_next_sun_set < m_conf.open_time_tel or hours_from_pre_sun_set < m_conf.open_time_tel) and self.scheduler_val == 0:
				try:
	       				print clock.timename(), 'Now restarting the scheduler!'
					os.popen("python /home/madsfa/subversion/trunk/scheduler/scheduler.py -t","w")
					time.sleep(2)
					print clock.timename(), "Starting the Scheduler..."
					os.popen("python /home/madsfa/subversion/trunk/scheduler/scheduler.py -s","w")	
		 		except Exception, e:
		    			print clock.timename(), 'The scheduler restart failed... now trying again!'
					os.popen("python /home/madsfa/subversion/trunk/scheduler/scheduler.py -t","w")
					time.sleep(2)
				print clock.timename(), "Starting the Scheduler..."
				os.popen("python /home/madsfa/subversion/trunk/scheduler/scheduler.py -s","w")

				self.scheduler_val = 1	


		#### This will check for ORs just before sunset.... ###	
		if self.check_ors == 0 and float(sun_alt_d) < 1.0 and float(sun_alt_d) > 0.0 and float(clock.timename().split("T")[1][0:2]) > 12.0:
			if song_monitor_config.mon_OR_insertion == 1:
				print clock.timename(), " Checking for ORs before sunset!"
				ors_val = 0
				try:
					ors_val = song_checker.Checker().check_for_ors()
				except Exception, e:
					print clock.timename(), " Could not check for ORs"
					print clock.timename(), e


				#### Checking for calibration files:
				try:
					folder = "/scratch/star_spec/%s/night/raw/" % (time.strftime("%Y%m%d", time.localtime()))
					numb_of_files = len(os.listdir(folder))
				except Exception,e:
					print clock.timename(), e
					print clock.timename(), " Could not get the number of files!"	
				 
				else:
					try:
						if numb_of_files < 100:
							if song_monitor_config.send_notifications == "yes":
								send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Missing calibration files!", message="There was only %i files in the folder: %s which indicates that the calibrations were not done!!!\n\nSend at: %s\n\n" % (numb_of_files, folder, clock.obstimeUT()))
					except Exception,e:
						print clock.timename(), e

				if ors_val == 0:
					# No ORs were in ready for observations and a notification will be send out.
					#try:
					#	if song_monitor_config.send_notify_sms == "yes":
					#		print clock.timename(), " A SMS will be sent about no ORs ready for observations..."
					#		send_song_mail.send_mail().send_sms(receiver=["Mads", "Frank"], message="No ORs were inserted today. Please do so nows!")
					#except Exception, e:
					#	print clock.timename(), e
					#	print clock.timename(), " Could not send OR ready SMS!"	
					#try:
					#	if song_monitor_config.send_notifications == "yes":
					#		send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_2, sender="SONG_MS", subject="No ORs for observations!", message="There were no ORs inserted for observations tonight. The Conductor will decide what to observe!!!\n\nSend at: %s\n\n" % clock.obstimeUT())
					#except Exception, e:
					#	print clock.timename(), e
					#	print clock.timename(), " Could not send OR ready e-mail!"	
					print clock.timename(), " No ORs inserted at beginning of night! Conductor will decide"

				else:
					print clock.timename(), " ORs were inserted today and observations will be carried out if conditions permit!!"	

				self.check_ors = 1


		elif self.check_ors == 1 and float(sun_alt_d) > 10.0:	
			# Resetting the daily value back.
			self.check_ors = 0

		if self.bad_weather_sms == 1 and float(clock.timename().split("T")[1][0:2]) == 10.0:
			self.bad_weather_sms = 0	

		if self.scheduler_val == 1 and float(clock.timename().split("T")[1][0:2]) == 12.0:			
			self.scheduler_val = 0

		#### This will open the mirror covers before observations start.... ###	
		if self.open_mirror_covers == 0 and float(sun_alt_d) < (float(m_conf.obs_sun_alt) + 2) and song_monitor_config.open_mirror_covers == "no" and float(self.telescope_state) == 1.0 and float(self.slit_state) != 0.0:
			print clock.timename(), " Mirror covers will now open to be ready for observations in a few minutes..."	
			ret_val = self.perform_actions.open_mc_now()

			#### At the same time start the slit and pupil guider daemons:
			try:
				thread_val1 = thread.start_new_thread(self.perform_actions.start_guiders, ())
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), " Could not start the guider deamons!"			

			self.open_mirror_covers = 1

		elif self.open_mirror_covers == 1 and float(sun_alt_d) > 10.0:	
			# Resetting the value back.
			self.open_mirror_covers = 0	

		if self.local_mode_sms == 1 and float(self.telescope_state) != float(-3.0):
			self.local_mode_sms = 0

		return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp


		












			
