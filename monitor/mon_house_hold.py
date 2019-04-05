import song_checker
import song_timeclass
import time
import thread
import song_monitor_config
import song_checker_config
import read_value_db
import numpy
import send_song_mail
#from  songerror import client
#import songerror
import subprocess
import os
import master_config as m_conf
import datetime
import sys
import subprocess, datetime, signal

sys.path.append("/home/madsfa/subversion/trunk/i2_heat_controller/") 
import i2_temp_contr

#error_notifier = songerror.client()
# Send message to error daemon
#ticket =  error_notifier.serror(20,"Text to send with the error")	# The number "20" indicatas that it is a warning 
#ticket =  error_notifier.serror(21,"Text to send with the error")	# The number "21" indicatas that it is a critical problem. 


clock = song_timeclass.TimeClass()

class Check_House_Hold(object):
	"""
		@brief: This class handles all checks on the time of day.
	"""
	def __init__(self):
		"""
			Initialization of the time checks.
		"""
		self.mon_house_hold_value = song_monitor_config.mon_house_hold_actions # 1 = do things, 0 = do nothing.
		self.verbose = song_monitor_config.verbose
		self.checker = song_checker.Checker()
		self.delay_time = time.time()
		self.specbox_delay_time = time.time()
		self.email_slony = 0
		self.email_ds = 0
		self.email_ds_alarm = 0
		self.email_ds_scratch = 0
		self.email_ds_scratch_alarm = 0
		self.slony_delay = time.time()
		self.notify_swap_delay = 0
		self.notify_mem_delay = 0
		self.notify_test_i2_heater_delay = 0
		self.notify_i2_heater_delay = 0

	def check_container(self):
		"""
			Checks the temperature inside the container.
		"""
		try:
			temp_values = read_value_db.get_fields_with_id("house_hold", ["temperature_9","temperature_10","temperature_13","temperature_14"], "box_id", "2")
			time_stamp = read_value_db.get_fields_with_id("house_hold", ["ins_at"], "box_id", "2")
		except Exception, e:
			print clock.timename(), " Could not connect to the database to read container temperatures"
			return 0	

		temp_arr = []	
		for temp in temp_values.values():
			if float(temp) != float(1.0):
				temp_arr.append(float(temp))

		### Calculate the mean temperature of the four messured inside the container:
		mean_value = numpy.mean(temp_arr)
		if self.verbose == 'yes' and float(mean_value) >= float(song_checker_config.container_temp):
			print clock.timename(), " The temperature inside the container was:", mean_value

		if float(mean_value) >= float(song_checker_config.container_temp) and time.time() > self.delay_time:
			if self.verbose == 'yes':
				print clock.timename(), " The temperature inside the container was %s and an email was sendt out" % (str(mean_value))
			# If the temperature is higher than the allowed limit an email will be sendt out. 
			if self.mon_house_hold_value == 1:
				if song_monitor_config.send_sms == "yes":
					value = send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The temperature inside the container is higher than %s. Please do something!!!" % str(song_checker_config.container_temp))
				if song_monitor_config.send_to_support == "yes":
					send_song_mail.send_mail().sending_an_email(reciever=['support'], sender="SONG_MS", subject="Container temp too high!", message="The temperature inside the container is higheder than %s.\nPlease contact the IAC night operator to tell him to go to the container. Maybe the air condition is failing.!!!\n\nSend at: %s\n\n"  % (str(song_checker_config.dome_temp), clock.obstimeUT()))
				if song_monitor_config.send_notifications == "yes":
					value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Container temp too high!", message="The temperature inside the container is higheder than %s.\nPlease contact the IAC night operator to tell him to go to the container. Maybe the air condition is failing.!!!\n\nSend at: %s\n\n"  % (str(song_checker_config.dome_temp), clock.obstimeUT()))
				
				# Send message to error daemon
				#ticket_container =  error_notifier.serror(20,"Monitor: Container temperature is %s" % str(mean_value))

				######################
				# The monitor should stop the telescope, park it and close the dome and close the side ports.
				######################


			self.delay_time = time.time() + 7200	# this is so that the function will not sendt out an email every 10 second. 
			

		return 1

	def check_spec_box(self):
		"""
			Checks the temperature inside the spectrograph box.
		"""
		try:
			temp_values = read_value_db.get_fields_with_id("house_hold", ["temperature_11","temperature_12","temperature_15","temperature_16"], "box_id", "2")
			time_stamp = read_value_db.get_fields_with_id("house_hold", ["ins_at"], "box_id", "2")
		except Exception, e:
			print clock.timename(), " Could not connect to the database to read spectrograph box temperatures"	
			return 0	

		temp_arr = []	
		for temp in temp_values.values():
			if float(temp) != float(1.0):
				temp_arr.append(float(temp))

		### Calculate the mean temperature of the four messured inside the spectrograph box:
		mean_value = numpy.mean(temp_arr)
		if self.verbose == 'yes':
			#print mean_value, temp_values["temperature_11"], temp_values["temperature_12"], temp_values["temperature_15"], temp_values["temperature_16"]
			print clock.timename(), " The mean temperature inside the spectrograph box was %s and air temp was %s" % (mean_value, temp_values["temperature_11"])

		# using the spectrograph air temperature which reacts quickly to changes.
		if time.time() > self.specbox_delay_time and (temp_values["temperature_11"] > float(song_checker_config.spec_box_temp_max) or temp_values["temperature_11"] < float(song_checker_config.spec_box_temp_min) or time_stamp["ins_at"] + datetime.timedelta(seconds=300) < datetime.datetime.utcnow()):
#		if float(mean_value) >= float(song_checker_config.spec_box_temp_max) and time.time() > self.delay_time:
			if self.verbose == 'yes':
				print clock.timename(), " The temperature inside the spectrograph box was %s and an email was sendt out" % (str(mean_value))
			if self.mon_house_hold_value == 1:
				# If the temperature is higher than the allowed limit an email will be sendt out. 
				if song_monitor_config.send_notifications == "yes":
					if time_stamp["ins_at"] + datetime.timedelta(seconds=300) < datetime.datetime.utcnow():
						value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Temperatures too old!", message="The temperatures (from our tmon sensor) in the database are no longer up to date.\nLast datapoint was inserted at %s.\nPlease do something!!!\n\nSend at: %s\n\n" % (str(time_stamp), clock.obstimeUT()))
					elif temp_values["temperature_11"] > float(song_checker_config.spec_box_temp_max):
						value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Spec box temp too high!", message="The temperature inside the spectrograph box was %s.\nPlease do something!!!\n\nSend at: %s\n\n" % (str(temp_values["temperature_11"]), clock.obstimeUT()))

					elif temp_values["temperature_11"] < float(song_checker_config.spec_box_temp_min):
						value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Spec box temp too low!", message="The temperature inside the spectrograph box was %s.\nPlease do something!!!\n\nSend at: %s\n\n" % (str(temp_values["temperature_11"]), clock.obstimeUT()))

				# Send message to error daemon
				#ticket_spec_box =  error_notifier.serror(20,"Monitor: Spectrograph box temperature is %s" % str(mean_value))

			self.specbox_delay_time = time.time() + 24*60*60	# this is so that the function will not sendt out an email every 10 second. 

		return 1

	def check_dome(self):
		"""
			Checks the temperature inside the dome.
		"""
		try:
			temp_values = read_value_db.get_fields_with_id("house_hold", ["temperature_3","temperature_4","temperature_7","temperature_8"], "box_id", "2")
			time_stamp = read_value_db.get_fields_with_id("house_hold", ["ins_at"], "box_id", "2")
		except Exception, e:
			print clock.timename(), " Could not connect to the database to read dome temperatures"
			return 0	

		temp_arr = []	
		for temp in temp_values.values():
			if float(temp) != float(1.0):
				temp_arr.append(float(temp))

		### Calculate the mean temperature of the four messured inside the dome:
		mean_value = numpy.mean(temp_arr)
		if self.verbose == 'yes' and float(mean_value) >= float(song_checker_config.dome_temp):
			print clock.timename(), " The temperature inside the dome was:", mean_value

		if float(mean_value) >= float(song_checker_config.dome_temp) and time.time() > self.delay_time:
			if self.verbose == 'yes':
				print clock.timename(), " The temperature inside the dome was %s and an email was sendt out" % (str(mean_value))
			if self.mon_house_hold_value == 1:
				if song_monitor_config.send_notifications == "yes":
					# If the temperature is higher than the allowed limit an email will be sendt out. 
					value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Dome temp too high!", message="The temperature inside the dome is higheder than %s.\nPlease do something!!!\n\nSend at: %s\n\n" % (str(song_checker_config.dome_temp), clock.obstimeUT()))

				# Send message to error daemon
				#ticket_dome =  error_notifier.serror(20,"Monitor: Dome temperature is %s" % str(mean_value))


				######################
				# The monitor should stop the telescope, park it and close the dome and close the side ports.
				######################

			self.delay_time = time.time() + 7200	# this is so that the function will not sendt out an email every 10 second. 

		return 1


	def check_slony(self):
		"""
			@brief: This function will check if data are copied to the central database.
		"""
		if song_monitor_config.mon_slony == 1:

			slony_val = ""
			time_stamp = 0
			try:
				slony_val, time_stamp = self.checker.check_slony()
			except Exception, e:
				print clock.timename(), " Could not check slony"
				print clock.timename(), e

			if slony_val == 0:
				print clock.timename(), " Slony is working fine"

			if self.email_slony == 0 and slony_val !=0 :				
				if slony_val == 1:
					value = send_song_mail.send_mail().sending_an_email(reciever=["mads", "frank", "eric"], sender="SONG_MS", subject="Slony is down!", message="Slony is not replicating the ORs from central to tenerife!!!Last weather data was inserted at: %s\n\nSend at: %s\n\n" % (time_stamp,clock.obstimeUT()))
					print clock.timename(), " Slony was not replicating the ORs from central to tenerife"
				elif slony_val == 2:
					value = send_song_mail.send_mail().sending_an_email(reciever=["mads", "frank", "eric"], sender="SONG_MS", subject="Slony is down!", message="Slony is not replicating data from tenerife to central!!!\nLast weather data was inserted at: %s\n\nSend at: %s\n\n" % (time_stamp,clock.obstimeUT()))
					print clock.timename(), " Slony was not replicating data from tenerife to central"
				elif slony_val == 3:
					value = send_song_mail.send_mail().sending_an_email(reciever=["mads", "frank", "eric"], sender="SONG_MS", subject="Slony is down!", message="Slony is not replicating at all!!!\n\nSend at: %s\n\n" % clock.obstimeUT())
					print clock.timename(), " Slony was not replicating at all"
				elif slony_val == 5:
					value = send_song_mail.send_mail().sending_an_email(reciever=["mads", "frank", "eric"], sender="SONG_MS", subject="Database is down!", message="Connection to the central database could not be achieved!!!\n\nSend at: %s\n\n" % clock.obstimeUT())
					print clock.timename(), " Connection to the central database was not achieved"
				elif slony_val == 4:
					value = send_song_mail.send_mail().sending_an_email(reciever=["mads", "frank", "eric"], sender="SONG_MS", subject="Database is down!", message="Connection to the tenerife database could not be achieved!!!\n\nSend at: %s\n\n" % clock.obstimeUT())
					print clock.timename(), " Connection to the tenerife database was not achieved"
				self.email_slony = 1
				self.slony_delay = time.time()

			elif self.email_slony == 1 and time.time() >= self.slony_delay + 86400:	# Only allow one email per day.
				self.email_slony = 0
				self.slony_delay = 0

			if slony_val == 5:
				print clock.timename(), " Connection to the central database was not achieved"
			elif slony_val == 4:
				print clock.timename(), " Connection to the tenerife database was not achieved"
	
			return 1	

		else:
			return 1



	def check_disk_space_hw(self):
		if song_monitor_config.mon_disk_space == 1:
			df = subprocess.Popen(["df", song_monitor_config.outstream], stdout=subprocess.PIPE)
			output = df.communicate()[0]
			hw_device, hw_size, hw_used, hw_available, hw_percent, hw_mountpoint = output.split("\n")[1].split()
		
			hw_free_ds_percent = (float(hw_available) / float(hw_size)) * 100.
			hw_used_ds_percent = (float(hw_used) / float(hw_size)) * 100.

			if float(hw_available) < song_monitor_config.hw_ds_limit and self.email_ds_alarm == 0:
				print clock.timename(), " There is not much space left on hw: %f GB" % (float(hw_available) / 1000000.)
				print clock.timename(), " Free disk space in percent: %f\n" % hw_free_ds_percent
				value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="hw out of disk space!", message="hw has less than 15 percent disk space left. Please check soon!\n\nSend at: %s\n\n" % clock.obstimeUT())
				self.email_ds_alarm = 1
			elif hw_free_ds_percent < song_monitor_config.hw_ds_soft_limit_percent and self.email_ds == 0:
				print clock.timename(), " There is not much space left on hw: %f GB" % (float(hw_available) / 1000000.)
				print clock.timename(), " There is less than 15 percent disk space left on hw!"
				print clock.timename(), " Free disk space in percent: %f\n" % hw_free_ds_percent
				value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="hw out of disk space!", message="hw has less than 15 percent disk space left. Please check soon!\n\nSend at: %s\n\n" % clock.obstimeUT())
				self.email_ds = 1			
			elif hw_free_ds_percent > song_monitor_config.hw_ds_soft_limit_percent:
				print clock.timename(), " hw has sufficient disk space left: %f GB" % (float(hw_available) / 1000000.)
				self.email_ds = 0
			
			return 1
		else:
			return 1


	def check_disk_space_scratch(self):
		if song_monitor_config.mon_disk_space == 1:

#			output = os.popen("df").readlines()[-4]
			for line in os.popen("df").readlines():
				if "scratch" in line.split()[-1]:
					scratch_device, scratch_size, scratch_used, scratch_available, scratch_percent, scratch_mountpoint = line.split()
		
					scratch_free_ds_percent = (float(scratch_available) / float(scratch_size)) * 100.
					scratch_used_ds_percent = (float(scratch_used) / float(scratch_size)) * 100.

					if float(scratch_available) < song_monitor_config.scratch_ds_limit and self.email_ds_scratch_alarm == 0:
						print clock.timename(), " There is not much space left on scratch: %f GB\n" % (float(scratch_available) / 1000000.)
						value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="scratch out of disk space!", message="scratch has %sGB disk space left. Please clean now!\n\nSend at: %s\n\n" % ((float(scratch_available) / 1000000.), clock.obstimeUT()))
						self.email_ds_scratch_alarm = 1
					elif float(scratch_available) < song_monitor_config.scratch_ds_soft_limit and self.email_ds_scratch == 0:
						print clock.timename(), " There is not much space left on scratch: %f GB\n" % (float(scratch_available) / 1000000.)
						value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="scratch out of disk space!", message="scratch has %sGB disk space left. Please clean soon!\n\nSend at: %s\n\n" % ((float(scratch_available) / 1000000.), clock.obstimeUT()))
						self.email_ds_scratch = 1
					elif float(scratch_available) < song_monitor_config.scratch_ds_soft_limit and self.email_ds_scratch == 1:
						print clock.timename(), " There is not much space left on scratch: %f GB" % (float(scratch_available) / 1000000.)
					elif float(scratch_available) > song_monitor_config.scratch_ds_soft_limit:
						print clock.timename(), " scratch has sufficient disk space left: %f GB" % (float(scratch_available) / 1000000.)
						self.email_ds_scratch = 0
			
			return 1
		else:
			return 1

	def check_memory_hw(self):
		if song_monitor_config.mon_memory_hw == 1:	
			try:
				import psutil
			except Exception,e:
				print e
				print "psutil was not installed..."
				return 0

			else:
				# psutil.virtual_memory():
				# vmem(total=8392966144L, available=7489146880L, percent=10.8, used=7220899840L, free=1172066304L, active=2213416960, inactive=4481515520, buffers=375693312L, cached=5941387264)
				mem = psutil.virtual_memory()
				swap = psutil.swap_memory()

				print clock.timename(), " HW memory usage: Tot: %iMB, Av: %iMB, Us: %iMB, Free: %iMB, Act: %iMB, InAct: %iMB, Buf: %iMB, Cach: %iMB" % (int(mem.total/1.0e6), int(mem.available/1.0e6),int(mem.used/1.0e6), int(mem.free/1.0e6), int(mem.active/1.0e6), int(mem.inactive/1.0e6), int(mem.buffers/1.0e6), int(mem.cached/1.0e6))
				
				print clock.timename(), " HW SWAP memory usage: Tot: %iMB, Us: %iMB, Free: %iMB" % (int(swap.total/1.0e6),int(swap.used/1.0e6), int(swap.free/1.0e6))

				if (swap.free/1.0e6) < song_monitor_config.hw_swap_limit and self.notify_swap_delay < time.time():
					print clock.timename(), " Swap memory is in use. Swap memory left on hw: %f MB\n" % (swap.free/1.0e6)
					value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="hw out of swap memory!", message="hw is using swap meory and only %fMB swap memory is left.\n\n Maybe restart some of the python modules to free memory!!\n\n Please be aware!\n\nSend at: %s\n\n" % ((swap.free/1.0e6), clock.obstimeUT()))
					#value = send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="hw is using up the swap memory. Please be aware!!!")
					self.notify_swap_delay = time.time() + (24. * 60. * 60.)	# Add a delay of 1 day

				elif (mem.free/1.0e6) < song_monitor_config.hw_mem_limit and self.notify_mem_delay < time.time():
					print clock.timename(), " There is not much memory left on hw: %f MB\n" % (mem.free/1.0e6)
					value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="hw out of memory!", message="hw has %fMB memory left.\n\n Maybe restart some of the python modules to free memory!!\n\n Please be aware!\n\nSend at: %s\n\n" % ((mem.free/1.0e6), clock.obstimeUT()))
					self.notify_mem_delay = time.time() + (24. * 60. * 60.)		# Add a delay of 1 day


			return 1
		else:
			return 1
	
	def timeout_command(self, command, timeout):
		"""call shell-command and either return its output or kill it
		if it doesn't normally exit within timeout seconds and return None"""
		start = datetime.datetime.now()
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		while process.poll() is None:
			time.sleep(0.1)
			now = datetime.datetime.now()
			if (now - start).seconds > timeout:
				os.kill(process.pid, signal.SIGKILL)
				os.waitpid(-1, os.WNOHANG)
				return None

		return repr(process.stdout.readlines())				
	
	def check_iodine_heaters(self):
		if song_monitor_config.mon_iodine_heaters == 1:			

			#### Check test iodine cell heater
			try:
				output = self.timeout_command(["ssh", "10.8.0.111", "python /home/obs/mads/i2_usb.py tact?"], 10)
			except Exception,e:
				print clock.timename(), " Could not get test iodine heater data"
				if self.notify_test_i2_heater_delay < time.time():
					value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Could not check iodine test cell heater!", message="The monitor caught an exception when trying to check the test iodine cell heater.\n\n Please check the machine: IP: 10.8.0.111 as obs to see if it is running. Use the script > python /home/obs/mads/i2_usb.py' to check and enable the heater!\n\nSend at: %s\n\n" % (clock.obstimeUT()))
					self.notify_test_i2_heater_delay = time.time() + (24. * 60. * 60.)		# Add a delay of 1 day
			else:
				if output == None:
					print clock.timename(), " Did not get data... now sending an e-mail..."
					if self.notify_test_i2_heater_delay < time.time():
						value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Iodine test cell not heated!", message="The monitor did not get a reply from the small hp machine to which the iodine test cells heater is connected.\n\n Please check the machine: IP: 10.8.0.111 as obs to see if it is running. Use the script > python /home/obs/mads/i2_usb.py' to check and enable the heater!\n\nSend at: %s\n\n" % (clock.obstimeUT()))
						self.notify_test_i2_heater_delay = time.time() + (24. * 60. * 60.)		# Add a delay of 1 day
				else:	
					#print float(output[0].strip(">\r\n C"))
					try:
						temp = float(output.split()[1])
					except Exception,e:
						print clock.timename(), " Did not get meaningful data from test iodine heater... now sending an e-mail..."
						if self.notify_test_i2_heater_delay < time.time():
							value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Iodine test cell not heated!", message="The monitor did not get a meaningful reply from the heater.\n\n Please log onto the machine: IP: 10.8.0.111 as obs and use the script > python /home/obs/mads/i2_usb.py' to check and enable the heater!\n\nSend at: %s\n\n" % (clock.obstimeUT()))
							self.notify_test_i2_heater_delay = time.time() + (24. * 60. * 60.)		# Add a delay of 1 day
					else:
						if numpy.abs(song_monitor_config.tset_temp_test - temp) > song_monitor_config.temp_diff_limit:
							print clock.timename(), " The temperature of test iodine cell is not within the limit: ", temp
							if self.notify_test_i2_heater_delay < time.time():
								value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Iodine test cell not heated!", message="The heater is not heating the test iodine cell at the moment.\n\n Please log onto the machine: IP: 10.8.0.111 as obs and use the script > python /home/obs/mads/i2_usb.py' to check and enable the heater!\n\nSend at: %s\n\n" % (clock.obstimeUT()))
								self.notify_test_i2_heater_delay = time.time() + (24. * 60. * 60.)		# Add a delay of 1 day
						else:
							print clock.timename(), " The temperature of test iodine cell is: ", temp

			##### Test regular iodine cell heater
			
			try:
				output = i2_temp_contr.heat_controler().get_tact()
			except Exception,e:
				print e
				print clock.timename(), " Could not get iodine heater data"
				if self.notify_i2_heater_delay < time.time():
					value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Regular iodine cell problem!", message="The monitor caught an exceptione when trying to check the regular iodine cell heater.\n\n Please check the web cam.\n\nSend at: %s\n\n" % (clock.obstimeUT()))
					self.notify_i2_heater_delay = time.time() + (24. * 60. * 60.)		# Add a delay of 1 day
			else:
				if output == None:
					print clock.timename(), " Did not get iodine heater data... now sending an e-mail..."
					if self.notify_i2_heater_delay < time.time():
						value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Regular iodine cell not heated!", message="The monitor did not get a reply from the regular iodine cell heater.\n\n Please check the web cam.\n\nSend at: %s\n\n" % (clock.obstimeUT()))
						self.notify_i2_heater_delay = time.time() + (24. * 60. * 60.)		# Add a delay of 1 day
				else:	
					try:
						temp = float(output)
					except Exception,e:
						print e
						print clock.timename(), " Did not get meaningful iodine heater data... now sending an e-mail..."
						if self.notify_i2_heater_delay < time.time():
							value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Iodine cell possibly not heated!", message="The monitor did not get a meaningful reply from the heater of the regular iodine cell.\n\n Please check the web cam!\n\nSend at: %s\n\n" % (clock.obstimeUT()))
							self.notify_i2_heater_delay = time.time() + (24. * 60. * 60.)		# Add a delay of 1 day
					else:
						if numpy.abs(song_monitor_config.tset_temp - temp) > song_monitor_config.temp_diff_limit:
							print clock.timename(), " The temperature of test iodine cell is not within the limit: ", temp
							if self.notify_i2_heater_delay < time.time():
								value = send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Iodine cell not heated correctly!", message="The heater is not heating the regular iodine cell at the moment.\n\n Please do something!\n\nSend at: %s\n\n" % (clock.obstimeUT()))
								self.notify_i2_heater_delay = time.time() + (24. * 60. * 60.)		# Add a delay of 1 day

						else:
							print clock.timename(), " The temperature of regular iodine cell is: ", temp

			return 1


	def check_machines(self):

		for m in song_monitor_config.machines:
			output = self.timeout_command(["ssh", m, "date"], 15)

			print clock.timename(), "Output from %s was: %s" % (m, str(output).strip())

			if output == None:
				print clock.timename(), "The check on %s had a timeout..." % (m)
				print clock.timename(), "Now sending an e-mail..."
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="%s is not responding" % (m), message="%s is not responding on the ssh connection from hw.sstenerife.prv. It might be hanging...\n\nPlease check!!" % (m))

				if song_monitor_config.send_sms == "yes":
					value = send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="%s is not responding. Please check!" % (m))				

		return 1














