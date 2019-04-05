#!/usr/bin/python
"""
	@brief: This module runs as a daemon.

	Created on the 24 Oct, 2011

	@author: Mads Fredslund Andersen 
"""

import time
from song_daemonize import Daemon
import os
import getopt
import sys
import daily_config
import daily_calib
import song_timeclass
import daily_logging_handler
import song_star_checker
import datetime
import pdu_module
import focusing_spec
import focus_determination
import comm2tcs_read
import comm2tcs_write
import master_config as m_conf
import send_song_mail
import get_db_values
import beating_heart
import songwriter_xmlrpcclient
import songwriter_MFA_client
import glob

import xmlrpclib

#attempt connection to server
isong_server = xmlrpclib.ServerProxy('http://%s:%s' % ("iodinepipe.kvmtenerife.prv", 8050)) 


clock = song_timeclass.TimeClass()

sun_handle = song_star_checker.sun_pos(site=m_conf.song_site) 	# site=1: Tenerife

gettsi = comm2tcs_read.GET_TSI()
settsi = comm2tcs_write.SET_TSI()

pdu_handle = pdu_module.APC()

class daily_daemon(Daemon):
	"""
		@brief: This class inherits Daemon from song.py and daemonizes the code.
	"""
	def run(self):
		"""
			@brief: This function overwrites the run function in song.py.
		"""
		global RUNNING
		RUNNING = True

		val = beating_heart.start_heartbeat(job_id=m_conf.daily_calib_id)

		exec_calibs = daily_calib.ACQ_CALIBS()
		done_log_param = 0
		done_param = 0
		done_isong_param = 0
		focusing_done = 0
		obs_sun_done = 0
		calib_done_param = 0
		m3_exercise_performed = 0

		self.songwriter_email_send = 0

		print "Starting loop at: ", clock.whattime()
		while RUNNING:

			# check if time of day is correct:
			sun_alt = sun_handle.sun_alt()

			if str(sun_alt)[0] == "-":
				 sun_alt_d = float(str(sun_alt).split(":")[0]) - float(str(sun_alt).split(":")[1])/60.0 - float(str(sun_alt).split(":")[2])/3600.0
			elif str(sun_alt)[0] != "-":
				 sun_alt_d = float(str(sun_alt).split(":")[0]) + float(str(sun_alt).split(":")[1])/60.0 + float(str(sun_alt).split(":")[2])/3600.0

			#################################
			#### Get time to next sun set ###
			tmp_time_str2 = datetime.datetime.strptime(str(sun_handle.sun_set_next()), "%Y/%m/%d %H:%M:%S")
			time_diff = tmp_time_str2-datetime.datetime.utcnow()
			hours_to_next_sun_set = int(time_diff.days) * 24. + time_diff.seconds / (24.*3600.) * 24
			#### Get time from previous sun set ###
			tmp_time_str2 = datetime.datetime.strptime(str(sun_handle.sun_set_pre()), "%Y/%m/%d %H:%M:%S")
			time_diff2 = datetime.datetime.utcnow() - tmp_time_str2
			hours_from_pre_sun_set = int(time_diff2.days) * 24. + time_diff2.seconds / (24.*3600.) * 24
			#################################
			#### Get time to next sun set ###
			tmp_time_str2 = datetime.datetime.strptime(str(sun_handle.sun_rise_next()), "%Y/%m/%d %H:%M:%S")
			time_diff = tmp_time_str2-datetime.datetime.utcnow()
			hours_to_next_sun_rise = int(time_diff.days) * 24. + time_diff.seconds / (24.*3600.) * 24
			#### Get time from previous sun set ###
			tmp_time_str2 = datetime.datetime.strptime(str(sun_handle.sun_rise_pre()), "%Y/%m/%d %H:%M:%S")
			time_diff2 = datetime.datetime.utcnow() - tmp_time_str2
			hours_from_pre_sun_rise = int(time_diff2.days) * 24. + time_diff2.seconds / (24.*3600.) * 24
			#################################

			if daily_config.observe_sun == "yes" and obs_sun_done == 0 and int(datetime.datetime.utcnow().hour) > 14:
				# Check if dome is open:
				slit_state = gettsi.get_position_instrumental_dome_slit_currpos(sender="observer")
				if str(slit_state) != '1.0':
					print "The Monitor had not opened the dome yet!"
				else:					
	
					if float(sun_alt_d) > float(1.0) and hours_to_next_sun_set < 2.0 and hours_to_next_sun_set > 1.0:
						print "The time is right and the Sun observations will now be performed at: ", clock.obstimeUT()	
			
						try:
							print os.system("python /home/madsfa/subversion/trunk/obs_scripts/sky_observations.py")
						except Exception,e:
							print e
							print "Could not perform the Sun observations..."
						else:
							print "The Sun observation script is now done at : ", clock.obstimeUT()	
							obs_sun_done = 1

      		
			######## Weekly focusing the spectrograph:
			if float(time.strftime("%H", time.gmtime())) == daily_config.focus_at and time.strftime("%a",time.gmtime()) == daily_config.which_day_to_focus and focusing_done == 0 and daily_config.run_weekly_focus == "yes":
				print "Starting to run the focus sequence for the spectrograph at: ", clock.obstimeUT()	
				
				ret_val = ""
				ret_val_focus = ""
				try:
					ret_val = focusing_spec.focus_the_spectrograph()
				except Exception,e:
					print e
					print "Could not acquire the spectres for focusing"
					ret_val = "fail"

				if ret_val == "done":
					try:
						ret_val_focus = focus_determination.main()
					except Exception,e:
						print e
						print "Could not calcullate the best focus value"
					
					if ret_val_focus != "":
						print "Focusing the spectrograph was completed at: ", clock.obstimeUT()	
						print "The focus will be set to: ", str(int(round(ret_val_focus)))
						print os.system( "/home/obs/programs/DMC/pst.py move -m5 -p%s" % (str(int(round(ret_val_focus)))))

						tmp_file = open(m_conf.focus_val_file, "w")
						tmp_file.write(str(int(round(ret_val_focus))))
						tmp_file.close()
				
				focusing_done = 1 


			######## MORNING CHECK SCRIPT ########	
			if float(sun_alt_d) > float(0.0) and hours_from_pre_sun_rise < 1.0 and float(sun_alt_d) < float(5.0) and done_param == 0:

			##########################################################################################
			################################## START THE PIPELINE ####################################
			##########################################################################################
				if m_conf.start_pipeline_morning == "yes":
					obs_night_date = datetime.date.today() - datetime.timedelta(days=1) #a date string. Format should be YYYMMDD and it should be the date the observations started!!!
					ret_val = ""
					try:
						print clock.timename(), "Calling SONGwriter to start the extraction of the spectre of the night: ", obs_night_date.strftime("%Y%m%d")
						ret_val = songwriter_xmlrpcclient.all_science(obs_night_date.strftime("%Y%m%d"))
#						ret_val = songwriter_MFA_client.all_science(obs_night_date.strftime("%Y%m%d"))
					except Exception,e:
						print clock.timename(),e
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="SONGwriter problem!",message="The request to start reducing the data from last night failed...\n\nSend at: %s\n\n" % clock.obstimeUT())
	
					if ret_val != 1:
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="SONGwriter problem!",message="The request to start reducing the data from last night failed...\n\nSend at: %s\n\n" % clock.obstimeUT())	


			##########################################################################################
			##########################################################################################
			##########################################################################################



				### Here the skycam can be stop and powered off...
				if daily_config.start_skycam_1_daemon == 1:
					e = ''
					try:
						print clock.timename(), "Trying to stop the skycam deamon"
						os.popen("python /home/madsfa/subversion/trunk/skycam/skycam_code/skycam_server.py -t", "w")
					except Exception,e: 
						print e
						print "Skycam server was not stopped correctly"

					### Here powering off the skycam is done:
					if e == '' and daily_config.power_skycam_1 == 1:
						try:				
							print clock.timename(), "Power off the skycam"			
							pdu_handle.SetPower('nasmyth',7,2)
						except Exception,e:
							print clock.timename(), e
							print clock.timename(), "Powering off the skycam was not performed correctly"
						if e == '':
							print clock.timename(), "The Skycam was powered off"

				### Here powering off the skycam is done:
				if e == '' and daily_config.power_skycam_2 == 1:
					try:				
						print clock.timename(), "Power off the skycam-2"			
						pdu_handle.SetPower('nasmyth',8,2)
					except Exception,e:
						print clock.timename(), e
						print clock.timename(), "Powering off the skycam was not performed correctly"
					if e == '':
						print clock.timename(), "The Skycam was powered off"					

				if m_conf.do_morning_calib == 1:
					# do calibration:
					#try:
					#	exec_calibs.restart_sigu()
					#except Exception,e:
					#	print clock.timename(), e
					#	print clock.timename(), "Failed to restart sigu"	
					#try:
					#	exec_calibs.calibration_spectres()
					#except Exception,e:
					#	print clock.timename(), e
					#	print clock.timename(), "Failed acquiring the calibration spectre"	
					try:
						exec_calibs.use_evening_spectre()
					except Exception,e:
						print clock.timename(), e
						print clock.timename(), "Failed to use standard spectre"	
					try:
						exec_calibs.check_offset()
					except Exception,e:
						print clock.timename(), e
						print clock.timename(), "Failed in the check of offsets"	
					try:
						exec_calibs.calc_line_width()
					except Exception,e:
						print clock.timename(), e
						print clock.timename(), "Failed calculating the line widths"	
					try:
						print clock.timename(), "Checking number of ThAr lines in ThAr spectra..."
						exec_calibs.thar_number_of_lines()
					except Exception,e:
						print clock.timename(), e
						print clock.timename(), "Failed checking ThAr lines"
					try:
						exec_calibs.create_plots()
					except Exception,e:
						print clock.timename(), e
						print clock.timename(), "Failed creating the plots"	


				done_param = 1



			if hours_from_pre_sun_rise < 6.0 and hours_from_pre_sun_rise > 1.0 and done_isong_param == 0:
				###### STARTING the iodine reduction....
				# find newest log file in folder:
				print clock.timename(), "Looking for the SONGWriter log file of the night..."
				try:
					obs_night_date = datetime.date.today() - datetime.timedelta(days=1)
					ext_folder = "/scratch/extr_spec/%s/%s/night/extracted_spec/" % (obs_night_date.strftime("%Y"), obs_night_date.strftime("%Y%m%d"))
					newest = max(glob.iglob(ext_folder+'*.log'), key=os.path.getctime)
					ctime = os.path.getctime(newest)

					update_time = time.time() - ctime

					print clock.timename(), "Checking for old SONGwriter log file for last night data reduction."
					print clock.timename(), "The log file was %s seconds old." % (update_time)

					if update_time > 600:
						# the newest log file is getting old.... start the isong pipeline
						print clock.timename(), "Calling IDL script to start creating the log files..."
						try:
							value = isong_server.make_log(obs_night_date.strftime("%Y%m%d"))
						except Exception, e:
							print clock.obstimeUT() ,'Could not connect to the server'
							print clock.obstimeUT() ,e	

						print clock.timename(), "Calling IDL script to start running isong..."
						try:
							value = isong_server.run_isong(obs_night_date.strftime("%Y%m%d"))
						except Exception, e:
							print clock.obstimeUT() ,'Could not connect to the server'
							print clock.obstimeUT() ,e
				
						done_isong_param = 1
				except Exception,e:

					if self.songwriter_email_send == 0:
						print clock.obstimeUT() ,"No SONGwriter file was created at this time... sending an e-mail..."
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="SONGWriter problem?",message="The daily calib daemon could not find any SONGWriter log file on scratch!\n\nPlease check if SONGWriter is running!\n\nSend at: %s" % (clock.timename()))
						self.songwriter_email_send = 1


			if done_param == 1 and float(time.strftime("%H", time.gmtime())) > daily_config.time_of_day:
				done_param = 0
				obs_sun_done = 0

			if focusing_done == 1 and float(time.strftime("%H", time.gmtime())) > daily_config.focus_at:
				focusing_done = 0

			######################################
			######## Afternoon - early evening calibrations #####

			sun_alt = sun_handle.sun_alt()
			if str(sun_alt)[0] == "-":
				 sun_alt_d = float(str(sun_alt).split(":")[0]) - float(str(sun_alt).split(":")[1])/60.0 - float(str(sun_alt).split(":")[2])/3600.0
			elif str(sun_alt)[0] != "-":
				 sun_alt_d = float(str(sun_alt).split(":")[0]) + float(str(sun_alt).split(":")[1])/60.0 + float(str(sun_alt).split(":")[2])/3600.0

			#################################
			#### Get time to next sun set ###
			tmp_time_str2 = datetime.datetime.strptime(str(sun_handle.sun_set_next()), "%Y/%m/%d %H:%M:%S")
			time_diff = tmp_time_str2-datetime.datetime.utcnow()
			hours_to_next_sun_set = int(time_diff.days) * 24. + time_diff.seconds / (3600.)
			#### Get time from previous sun set ###
			tmp_time_str2 = datetime.datetime.strptime(str(sun_handle.sun_set_pre()), "%Y/%m/%d %H:%M:%S")
			time_diff2 = datetime.datetime.utcnow() - tmp_time_str2
			hours_from_pre_sun_set = int(time_diff2.days) * 24. + time_diff2.seconds / (3600.)
			#################################

			if float(sun_alt_d) < float(daily_config.calib_sun_alt) and hours_from_pre_sun_set > 23.00 and calib_done_param == 0:

				### Here powering on the skycam is done:
				if daily_config.power_skycam_1 == 1:
					try:			
						print "Power on the SkyCam: ", clock.obstimeUT() 	
						pdu_handle.SetPower('nasmyth',7,1)
					except Exception,e:
						print e
						print "Powering off the skycam was not performed correctly"
				
					time.sleep(20)

					if daily_config.start_skycam_1_daemon == 1:
						e = ''
						try:
							print "Now trying to start the skycam daemon: ", clock.obstimeUT()
							print os.popen("python /home/madsfa/subversion/trunk/skycam/skycam_code/skycam_server.py -s", "w")
						except Exception,e: 
							print e
							print "Skycam server was not started correctly"

				if daily_config.power_skycam_2 == 1:
					try:			
						print "Power on the SkyCam-2: ", clock.obstimeUT() 	
						pdu_handle.SetPower('nasmyth',8,1)
					except Exception,e:
						print e
						print "Powering off the skycam was not performed correctly"

				
				if daily_config.shutter_handle == 1:
					print clock.timename(), "Switching to STELLAR shutter..."
					try:
						pdu_handle.SetPower("container", 13, 2)
					except Exception,e:
						print clock.timename(), "Could not activate Stellar shutter"
					else:
						print clock.timename(), "STELLAR shutter is now activated!"			



				print "\nDaily scientific calibration execution started at: %s\n" % clock.obstimeUT()

				if m_conf.do_evening_calib == 1:

					for slit_nr in daily_config.slits_to_use:					
						script_name = daily_config.script_path + "spec_calib_slit" + str(slit_nr) + ".py"
						print "Now executing: ", script_name
						try:
							os.system("python %s" % script_name)
						except Exception,e:
							print e
							print "%s was not executed correctly" % script_name

					
					try:
						print clock.timename(), "Performing the localization of the slits..."
						exec_calibs.locate_slit()
					except Exception,e:
						print clock.timename(), e
						print clock.timename(), "Failed calculating the line widths"	


					if m_conf.start_pipeline_morning == "yes":
						########################
						#### Create master calibration files				
						try:
							obs_night_date = datetime.date.today() #a date string. Format should be YYYMMDD and it should be the date the observations started!!!
							print clock.timename(), songwriter_xmlrpcclient.master_calib(obs_night_date.strftime("%Y%m%d"))
#							print clock.timename(), songwriter_MFA_client.master_calib(obs_night_date.strftime("%Y%m%d"))				
						except Exception,e:
							print clock.timename(),e
							send_song_mail.send_mail().sending_an_email(reciever=["mads"],sender="SONG_MS",subject="SONGwriter problem!",message="The request to start creating the master calibration files has failed.\n\nSend at: %s\n\n" % clock.obstimeUT())

				calib_done_param = 1
				print "Daily evening calibration scripts done at: ", clock.obstimeUT()



			tel_state_db_values = get_db_values.db_connection().get_fields_site01("tel_dome", ["tel_ready_state", "extra_param_1", "extra_param_2", "tel_motion_state"] )
			if daily_config.exercise_m3 == "yes" and calib_done_param == 1 and m3_exercise_performed == 0 and float(tel_state_db_values["tel_ready_state"]) == float(1.0) and float(tel_state_db_values["extra_param_2"]) == float(0.0) and (hours_from_pre_sun_set < 0.25 or hours_from_pre_sun_set > 23.0) and float(tel_state_db_values["tel_motion_state"]) != float(11):
				print clock.obstimeUT(), "Exercising M3 %i times" % (daily_config.m3_movements)
				m3_pos = [3,12]
				tel_az_now = int(round(float(gettsi.get_position_horizontal_az())))
				tel_alt_now = int(round(float(gettsi.get_position_horizontal_alt())))
				settsi.set_object_horizontal_alt(param=tel_alt_now, sender="Observer")
				settsi.set_object_horizontal_az(param=tel_az_now, sender="Observer")
				m3_pos_now = int(gettsi.get_pointing_setup_use_port())

				if m3_pos_now == 12:
					move_m3_to = 0
				else:
					move_m3_to = 1

				for movements in range(daily_config.m3_movements * 2):
					settsi.set_pointing_setup_use_port(param=m3_pos[move_m3_to], sender="Observer")
					settsi.set_pointing_track(param=2,sender="Observer")					
					track_value = gettsi.get_telescope_motion_state(sender="Observer")
					timeout = time.time() + 60
					while str(track_value) not in ['0', '0.0']:
						time.sleep(1.0)
						track_value = gettsi.get_telescope_motion_state(sender="Observer")
						if time.time() > timeout:
							print clock.obstimeUT(), "The M3 movement has timed out..."
							break
					print clock.obstimeUT(), "Moved M3 to port: ", m3_pos[move_m3_to]
					move_m3_to = (move_m3_to + 1) % 2
			
					time.sleep(5)

				if int(gettsi.get_pointing_setup_use_port()) != 12:
					settsi.set_pointing_setup_use_port(param=12, sender="Observer")
					settsi.set_pointing_track(param=2,sender="Observer")
					while str(track_value) not in ['0', '0.0']:
						time.sleep(1.0)
						track_value = gettsi.get_telescope_motion_state(sender="Observer")
						if time.time() > timeout:
							print clock.obstimeUT(), "The M3 movement has timed out in the final movement..."
							break

				else:
					print clock.obstimeUT(), "M3 is pointing at the coude side"

				if int(gettsi.get_pointing_setup_use_port()) == 12:
					print clock.obstimeUT(), "M3 is pointing at the coude side after the exercise..."

				m3_exercise_performed = 1

				print clock.obstimeUT(), "Daily exercising of M3 is done"

			if done_isong_param == 1 and float(sun_alt_d) < float(0.0):
				done_isong_param = 0

			if calib_done_param == 1 and float(sun_alt_d) > float(daily_config.calib_sun_alt):
				calib_done_param = 0
				m3_exercise_performed = 0

			##### LOG is cleared
			if int(float(time.strftime("%H", time.gmtime()))) == 12 and done_log_param == 0:
				daily_logging_handler.handle_log_files(daily_config.outstream, daily_config.outstream_old)
				done_log_param = 1

			if done_log_param == 1 and int(float(time.strftime("%H", time.gmtime()))) > 12:
				done_log_param = 0

			if self.songwriter_email_send == 1 and int(float(time.strftime("%H", time.gmtime()))) > 17:
				self.songwriter_email_send = 0	

			time.sleep(60) # 

			
def main():
	"""
		@brief: This is the main part of the code that starts up everything else. 
	"""

	daemon = daily_daemon(daily_config.pidfile, stdout=daily_config.outstream, stderr=daily_config.outstream)
	try:
		opts, list = getopt.getopt(sys.argv[1:], 'st')
	except getopt.GetoptError, e:
		print("Bad options provided!")
		sys.exit()
	
	for opt, a in opts:
		if opt == "-s":
			try:
				pid_number = open(daily_config.pidfile,'r').readline()
				if pid_number:
					sys.exit('Daemon is already running!')
			except Exception, e:
				pass
		
			daemon.start()

		elif opt == "-t":
			global RUNNING
			RUNNING = False
			daemon.stop()
			print "The daemon is stoped!"
		elif opt == "-l":
			print("Logging is turned off")
		else:
			print("Option %s not supported!" % (opt))

if __name__ == "__main__":
	try:
		main()
	except Exception, e:
		print clock.timename(), e
		print clock.timename(), " The daily calib daemon has crashed"
		send_song_mail.send_mail().sending_an_email(reciever=["mads", "frank"],sender="SONG_MS",subject="Daily Calib daemon Crash!",message="The daily calib daemon has crashed!\n\nCheck the log file to see why!\n\nMaybe a simple restart helps!!\nSend at: %s" % (clock.timename()))


#	send_song_mail.send_mail().send_sms(receiver=["Mads"], message="The daily calib daemon was stopped for some reason!")

