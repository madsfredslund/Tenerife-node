#!/usr/bin/python
"""
   @brief: This module runs as a monitor daemon.

   Created on the 23 August, 2012

   @author: Mads Fredslund Andersen
"""
import song_timeclass
import thread
from song_daemonize import Daemon
import os
import getopt
import song_monitor_config
import sys
import time
import update_song_database
import song_database_tables
import comm2tcs_read
import comm2tcs_write
import song_timeclass
import bf_2300_controller
import mon_weather
import mon_time
import mon_side_ports
import mon_network
import mon_telescope
import mon_house_hold
import mon_cooler
import song_checker
import daily_logging_handler
import send_song_mail
import numpy
import psycopg2
import master_config as m_conf
import beating_heart

check_handle = song_checker.Checker()
clock = song_timeclass.TimeClass()

weather_handle = mon_weather.Check_Weather()
time_handle = mon_time.Check_Time()
side_port_handle = mon_side_ports.Check_Time()
network_handle = mon_network.Check_Network()
telescope_handle = mon_telescope.Check_Telescope()
house_hold_handle = mon_house_hold.Check_House_Hold()
cooler_handle = mon_cooler.Check_Cooler()

def get_fields(table_name, fields):
	field_str = ''
	for field in fields:
 		field_str += field
 		field_str += ','
	field_str = field_str[0:-1]

	conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
	curr = conn.cursor()
	stmt = 'SELECT %s FROM %s WHERE ins_at = (SELECT max(ins_at) FROM %s)' % (field_str, table_name, table_name)
	curr.execute(stmt)
	results = curr.fetchone()
	curr.close()
	res_dict = {}
	if results != None:
 		for i in range(len(results)):
    			res_dict[fields[i]] = results[i]
 		return res_dict
	else:
 		return None

class Check_something(object):
	def __init__(self):

		print ""
		print clock.timename(), " Monitor daemon started"
 
		self.verbose = song_monitor_config.verbose # yes / no

		self.who_did_it_tel = "time"    # Who did it for the telescope
		self.who_did_it_sp = "time"     # Who did it for the side ports
	
		self.monitor_hangs_send_mail = 0
		self.telescope_hangs_sms = 0
		self.i2_counter = 0

		output, timestamp = song_checker.Checker().weather_check(deduced=song_monitor_config.weather_deduced)
		print clock.timename(), " Weather output at daemon start was: ", output
		if output > 0:
			self.who_did_it_tel = "weather"    # Who did it for the telescope
			self.who_did_it_sp = "weather"     # Who did it for the side ports

		self.old_output = ''

		global RUNNING

		# Ask the bf2300 if the side ports are opened or closed:
		try:
			if song_monitor_config.mon_side_ports == 1:
				side_port_1_status = bf_2300_controller.bf_reader().read_input(input_number=1)
				time.sleep(1)
				side_port_2_status = bf_2300_controller.bf_reader().read_input(input_number=2)
				time.sleep(1)
				side_port_3_status = bf_2300_controller.bf_reader().read_input(input_number=3)
				time.sleep(1)
				side_port_4_status = bf_2300_controller.bf_reader().read_input(input_number=4)
				time.sleep(1)
				side_port_5_status = bf_2300_controller.bf_reader().read_input(input_number=5)
				time.sleep(1)
				side_port_6_status = bf_2300_controller.bf_reader().read_input(input_number=6)
				time.sleep(1)
				side_port_7_status = bf_2300_controller.bf_reader().read_input(input_number=7)
				time.sleep(1)
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
			print clock.timename(), " Side ports working fine"
		else:
			print clock.timename(), " Could not get the side port status"
			global RUNNING
			RUNNING = False	

		# Ask the tcs daemon if the telescope is powered on or off
		try:
			if song_monitor_config.mon_telescope == 1 or song_monitor_config.mon_telescope_info == 1:
				print clock.timename(), " Now connecting to telescope"
				telescope_status = comm2tcs_read.GET_TSI().get_telescope_state(sender="Monitor")
				slit_status = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="Monitor")
				flap_status = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="Monitor")
				mirror_cover_status = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="Monitor")
			else:
				telescope_status = 0
				slit_status = 0
				flap_status = 0
				mirror_cover_status = 0
		except Exception, e:
			print clock.timename(), " An exception was thrown: ", e
			telescope_status = 0
			slit_status = 0
			flap_status = 0
			mirror_cover_status = 0

		print clock.timename(), " The telescope status was: ", telescope_status
		print clock.timename(), " The dome status was: ", slit_status

		if str(telescope_status) in ["0.0", "1.0", "0", "1", "-3"]:
			self.telescope_state = int(float(telescope_status))
		elif float(telescope_status) > 0.0 and float(telescope_status) < 1.0:
			print clock.timename(), " The telescope was in a changing state...!!!"
		elif float(telescope_status) ==  -3.0:
			print clock.timename(), " The telescope was in local mode...!!!"
		else:
			print clock.timename(), " Could not get the Telescope status"
			RUNNING = False		

		try:
			update_song_database.update("tel_dome", ["extra_param_2"], [0.0], "tel_dome_id")
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), " Could not set the over all observing state startup/shutdown parameter to zero!"

		if str(slit_status) in ["0.0", "1.0", "0", "1", "0.5"]:
			self.slit_state = int(float(slit_status))
		else:
			print clock.timename(), " Could not get the Dome slit status"
			RUNNING = False	

		if str(flap_status) in ["0.0", "1.0", "0", "1", "0.5"]:
			self.flap_state = int(float(flap_status))
		else:
			print clock.timename(), " Could not get the Dome flap status"
			RUNNING = False		

		if str(mirror_cover_status) in ["0.0", "1.0", "0", "1"]:
			self.mirror_cover_state = int(float(mirror_cover_status))
		else:
			self.mirror_cover_state = 2
			print clock.timename(), " Mirror cover state was: ", mirror_cover_status
	#		RUNNING = False		

		# Set the startup/shutdown value to 0 to make sure it will not be hanging on this...
		try:
			update_song_database.update("tel_dome", ["extra_param_2"], [0], "tel_dome_id")
		except Exception,e:
			print clock.timename(), " The over all obs value were not updated in the database: ", e
      
	def check_weather(self):
     
		output = weather_handle.check_weather(self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp)	

		self.side_port_group_1 = output[0]
		self.side_port_group_2 = output[1]
		self.side_port_group_3 = output[2]
		self.side_port_group_4 = output[3]
		self.telescope_state = output[4]
		self.slit_state = output[5]
		self.flap_state = output[6]
		self.mirror_cover_state = output[7]
		self.who_did_it_tel= output[8]
		self.who_did_it_sp= output[9]	

		if self.verbose == "yes" and self.old_output != output:
			print clock.timename(), " The status of the side ports and telescope was: ", output

		self.old_output = output


		return 1


	def check_telescope(self):

		output1 = telescope_handle.error_state(self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp)

		self.side_port_group_1 = output1[0]
		self.side_port_group_2 = output1[1]
		self.side_port_group_3 = output1[2]
		self.side_port_group_4 = output1[3]
		self.telescope_state = output1[4]
		self.slit_state = output1[5]
		self.flap_state = output1[6]
		self.mirror_cover_state = output1[7]
		self.who_did_it_tel= output1[8]
		self.who_did_it_sp= output1[9]

		output2 = telescope_handle.tel_altitude(self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp)

		self.side_port_group_1 = output2[0]
		self.side_port_group_2 = output2[1]
		self.side_port_group_3 = output2[2]
		self.side_port_group_4 = output2[3]
		self.telescope_state = output2[4]
		self.slit_state = output2[5]
		self.flap_state = output2[6]
		self.mirror_cover_state = output2[7]
		self.who_did_it_tel= output2[8]
		self.who_did_it_sp= output2[9]

		output3 = telescope_handle.tel_dome_sync(self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp)

		return 1


	def check_network(self):

		output = network_handle.hello_world(self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp)

		self.side_port_group_1 = output[0]
		self.side_port_group_2 = output[1]
		self.side_port_group_3 = output[2]
		self.side_port_group_4 = output[3]
		self.telescope_state = output[4]
		self.slit_state = output[5]
		self.flap_state = output[6]
		self.mirror_cover_state = output[7]
		self.who_did_it_tel= output[8]
		self.who_did_it_sp= output[9]

		return 1

	def check_time(self):

		output = time_handle.check_sun(self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp)

		self.side_port_group_1 = output[0]
		self.side_port_group_2 = output[1]
		self.side_port_group_3 = output[2]
		self.side_port_group_4 = output[3]
		self.telescope_state = output[4]
		self.slit_state = output[5]
		self.flap_state = output[6]
		self.mirror_cover_state = output[7]
		self.who_did_it_tel= output[8]
		self.who_did_it_sp= output[9]

		return 1

	def check_side_ports(self):

		output = side_port_handle.check_time_and_sun(self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp)

		self.side_port_group_1 = output[0]
		self.side_port_group_2 = output[1]
		self.side_port_group_3 = output[2]
		self.side_port_group_4 = output[3]
		self.telescope_state = output[4]
		self.slit_state = output[5]
		self.flap_state = output[6]
		self.mirror_cover_state = output[7]
		self.who_did_it_tel= output[8]
		self.who_did_it_sp= output[9]

		return 1

	def check_cooler(self):

		output = cooler_handle.handle_cooler(self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp)

		return 1

	def check_wind(self):
		"""
			@brief: This function checks the windspeed and direction through the song_checker class.
			This can open and close the side ports if needed.
		"""

		output = weather_handle.check_wind(self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp)

		self.side_port_group_1 = output[0]
		self.side_port_group_2 = output[1]
		self.side_port_group_3 = output[2]
		self.side_port_group_4 = output[3]
		self.telescope_state = output[4]
		self.slit_state = output[5]
		self.flap_state = output[6]
		self.mirror_cover_state = output[7]
		self.who_did_it_tel= output[8]
		self.who_did_it_sp= output[9]
     
		return 1

	def check_house_hold(self):
		"""
			@brief: This function checks the temperature inside the container, spec box and dome.
    		"""
		output1 = house_hold_handle.check_container()
		output2 = house_hold_handle.check_spec_box()
		output3 = house_hold_handle.check_dome()
		output4 = house_hold_handle.check_slony()
		output5 = house_hold_handle.check_disk_space_hw()
		output6 = house_hold_handle.check_disk_space_scratch()
		output7 = house_hold_handle.check_memory_hw()

		if self.i2_counter % 30 == 0:		# Check approx every hour
			output8 = house_hold_handle.check_iodine_heaters()	
			output9 = house_hold_handle.check_machines()		# Checking the most critical machines with a ssh date command.
			self.i2_counter +=1


	
     		return 1

	def collect_tel_info(self):
		"""
			@brief: This function checks the state of the telescope and writes the state to the databasa:

		"""		

		global RUNNING
		while RUNNING:
			try:
				try:
					t_ready_state = float(comm2tcs_read.GET_TSI().get_telescope_state(sender="monitor"))
				except Exception,e:
					print clock.timename(), e
					t_ready_state = comm2tcs_read.GET_TSI().get_telescope_state(sender="monitor")		
					print clock.timename(), " The telescope replied : '%s' for the ready state in main monitor code" % str(t_ready_state)

				if type(self.telescope_state) == numpy.str:
					t_ready_state = -1	# Error state					
				elif float(t_ready_state) == float(-3.0):
					t_ready_state = 10	# Local mode
				elif float(t_ready_state) == float(-2.0):
					t_ready_state = 9	# Emergency stop
				t_motion_state = comm2tcs_read.GET_TSI().get_telescope_motion_state(sender="monitor")
				t_ra = comm2tcs_read.GET_TSI().get_position_equatorial_ra_j2000(sender="monitor")
				t_dec = comm2tcs_read.GET_TSI().get_position_equatorial_dec_j2000(sender="monitor")
				t_az = comm2tcs_read.GET_TSI().get_position_horizontal_az(sender="monitor")
				t_zd = comm2tcs_read.GET_TSI().get_position_horizontal_zd(sender="monitor")
				t_alt = comm2tcs_read.GET_TSI().get_position_horizontal_alt(sender="monitor")
				t_error = comm2tcs_read.GET_TSI().get_telescope_status_global(sender="monitor")	
				t_focus = comm2tcs_read.GET_TSI().get_position_instrumental_focus_currpos(sender="monitor")
				t_focus_offset = comm2tcs_read.GET_TSI().get_position_instrumental_hexapod_z_offset(sender="monitor")
				o_ra = comm2tcs_read.GET_TSI().get_object_equatorial_ra(sender="monitor")
				o_dec = comm2tcs_read.GET_TSI().get_object_equatorial_dec(sender="monitor")
				d_az = comm2tcs_read.GET_TSI().get_position_horizontal_dome(sender="monitor")
				d_slit = comm2tcs_read.GET_TSI().get_position_instrumental_dome_slit_currpos(sender="monitor")
				if float(d_slit) != 0.0 and float(d_slit) != 1.0 and float(d_slit) != -1.0:
					d_slit = 2
				else:
					d_slit = int(float(d_slit))
				d_flap = comm2tcs_read.GET_TSI().get_position_instrumental_dome_flap_currpos(sender="monitor")
				if float(d_flap) != 0.0 and float(d_flap) != 1.0 and float(d_flap) != -1.0:
					d_flap = 2
				else:
					d_flap = int(float(d_flap))
				if d_slit > 0 or d_flap > 0:
					d_state = 1
				elif d_slit == 0 and d_flap == 0:
					d_state = 0	
				else:
					d_state = -1
				m_cover = comm2tcs_read.GET_TSI().get_auxiliary_cover_realpos(sender="monitor")
				if float(m_cover) != 0.0 and float(m_cover) != 1.0 and float(m_cover) != -1.0:
					m_cover = 2
				else:
					m_cover = int(float(m_cover))				
				thr_mirror = comm2tcs_read.GET_TSI().get_pointing_setup(sender="monitor")
				temp_cab = comm2tcs_read.GET_TSI().get_auxiliary_temp_cabinet(sender="monitor")
				temp_m1 = comm2tcs_read.GET_TSI().get_auxiliary_temp_m1(sender="monitor")
				temp_m2 = comm2tcs_read.GET_TSI().get_auxiliary_temp_m2(sender="monitor")	
				temp_m3 = comm2tcs_read.GET_TSI().get_auxiliary_temp_m3(sender="monitor")	
				temp_tt = comm2tcs_read.GET_TSI().get_auxiliary_ttelescope(sender="monitor")
#				derot_position = comm2tcs_read.GET_TSI().get_position_mechanical_derotator_currpos()	
				derot_position = float(comm2tcs_read.GET_TSI().get_position_mechanical_derotator_currpos(sender="monitor")) % 360.0
				derot_offset = comm2tcs_read.GET_TSI().get_position_mechanical_derotator_offset(sender="monitor")
	
			except Exception, e:
				print clock.timename(), " Could not get telescope status values: ", e


			try:
				update_song_database.update("tel_dome", ["tel_ready_state", "tel_motion_state", "tel_ra", "tel_dec", "tel_az", "tel_zd", "tel_alt", "tel_error", "tel_focus","obj_ra", "obj_dec", "dome_az", "dome_slit_state", "dome_flap_state", "dome_state", "mirror_cover_state", "third_mirror", "cabinet_state", "temp_cabinet", "temp_m1", "temp_m2", "temp_m3", "temp_n1","rot2_angle", "rot2_field_direct"], [int(float(t_ready_state)),int(float(t_motion_state)),float(t_ra),float(t_dec),float(t_az), float(t_zd), float(t_alt), int(float(t_error)), float(t_focus) + float(t_focus_offset), float(o_ra), float(o_dec), float(d_az), d_slit, d_flap, int(float(d_state)), m_cover, int(float(thr_mirror)), int(float(1)), float(temp_cab), float(temp_m1), float(temp_m2), float(temp_m3), float(temp_tt), float(derot_position), float(derot_offset)], "tel_dome_id")
			except Exception,e:
				print clock.timename(), " The telescope status values were not updated in the database: ", e

			try:
				tenerife_tel_temps_values = get_fields("tenerife_tel_temps", ["tenerife_tel_temps_id"])	
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), " Could not connect to the central server... "
	
			try:
				if not tenerife_tel_temps_values["tenerife_tel_temps_id"]:
					tenerife_tel_temps_id = 0
				else:
					tenerife_tel_temps_id = int(tenerife_tel_temps_values["tenerife_tel_temps_id"])	
			except Exception,e:
				tenerife_tel_temps_id = 0

			params = "(tenerife_tel_temps_id, select_id, m1_temp, m2_temp, m3_temp, tel_temp, cabinet_temp, extra_param_1, extra_param_2, extra_param_3, extra_param_4, extra_param_5, extra_param_6, extra_param_7, extra_param_8, extra_param_9, extra_param_10, extra_value_1, extra_value_2, extra_value_3, extra_value_4, extra_value_5, extra_value_6, extra_value_7, extra_value_8, extra_value_9, extra_value_10, ins_at)"

			values = "(%i, %i, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, '%s')" % (tenerife_tel_temps_id+1, 1, float(temp_m1), float(temp_m2), float(temp_m3), float(temp_tt), float(temp_cab), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
	
			try:
				conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
				curr = conn.cursor()
				stmt = 'INSERT INTO %s %s VALUES %s' % ("tenerife_tel_temps", params, values)               
				curr.execute(stmt)		
				conn.commit()
				curr.close()
			except Exception, e:
				print clock.timename(), " An error occurred: ", e

			#print "Telescope data inserted into the database!"
			time.sleep(song_monitor_config.tel_data_insertion_delay)

		return 1



	def over_all_obs_state(self):

		global RUNNING
		while RUNNING:
			try:
				tenerife_tel_state = get_fields("tel_dome", ["extra_param_2"])	
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), " Could not connect to the server... "

			if float(tenerife_tel_state["extra_param_2"]) == 0.0:
				try:
					obs_state = check_handle.check_obs_state()
					over_all_obs_state_strings = ['Okay for observing','Bad weather', 'Day time', 'DB error', 'Not tracking', 'Dome not open', 'Mirror cover not open', 'Telescope pointing too low', "Old DB data"]
					print clock.timename(), " The over all observing state was:  [ %s ]" % (over_all_obs_state_strings[int(obs_state)])
				except Exception, e:
					print clock.timename(), " Could not get over all obs state from checker: ", e

				try:
					update_song_database.update("tel_dome", ["extra_param_1"], [int(float(obs_state))], "tel_dome_id")
				except Exception,e:
					print clock.timename(), " The over all obs value were not updated in the database: ", e
			else:

				try:
					over_all_obs_state_strings = ['Starting up','Shutting down']
					print clock.timename(), " The over all observing state was:  [ %s ]" % (over_all_obs_state_strings[int(float(tenerife_tel_state["extra_param_2"]))-1])
				except Exception, e:
					print clock.timename(), " Could not convert obs state: ", e

				try:
					update_song_database.update("tel_dome", ["extra_param_1"], [int(float(tenerife_tel_state["extra_param_2"]))+8], "tel_dome_id")
				except Exception,e:
					print clock.timename(), " The over all obs value were not updated in the database: ", e

			time.sleep(song_monitor_config.over_all_obs_state_delay)

		return 1


	def check_if_monitor_runs(self):

		delay_time = 0

		while RUNNING:
			if past_time + 600 < time.time() and self.monitor_hangs_send_mail == 0:
				print clock.timename(), " It has been 10 minutes since the monitor went through a loop!"
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Monitor hangs!",message="The monitor daemon is hanging somewhere and a restart is most likely needed. Please check if things looks fine!\n\nThis is what will be send out if the connection to the telescope is lost from the Astelco side\n\nSend at: %s" % clock.obstimeUT())
				send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The monitor daemon hangs for some reason!")	
				if song_monitor_config.send_to_support == "yes":
					send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Monitor hangs!",message="The monitor daemon is hanging somewhere and a restart is most likely needed. Please check if things looks fine!\n\nThis is what will be send out if the connection to the telescope is lost from the Astelco side\n\nSend at: %s" % clock.obstimeUT())
				self.monitor_hangs_send_mail = 1	
				delay_time = time.time() + 3600		# Wait an hour to send another SMS and emails. 		

			elif past_time + 600 > time.time() and self.monitor_hangs_send_mail == 0:
				loop_time = time.time() - past_time
				print clock.timename(), " Monitor runs as it should... loop past %s seconds ago" % loop_time

			else:			
				if delay_time < time.time() and self.monitor_hangs_send_mail == 1:
					self.monitor_hangs_send_mail = 0

			time.sleep(30)
				
				
	

#	def check_daemons(self):
#		"""
#			@brief: This function checks the state of some specified daemons.
#			This can restart the daemons if needed.
#		"""
#		#ping the daemons
#		return 1

#	def pause_daemons(self):
#		"""
#			@brief: This function will close some specified daemons when they are inactive and restart them when needed.
#		"""
#		return 1

class monitor_daemon(Daemon):
	"""
		@brief: This class inherits Daemon from song.py and daemonizes the monitor_daemon.py code.
	"""
	def run(self):
		"""
			@brief: This function overwrites the run function in song.py.
		"""
		global RUNNING
		RUNNING = True

		val = beating_heart.start_heartbeat(job_id=m_conf.monitor_id)

		song_checker_handle = Check_something()

		if song_monitor_config.mon_telescope_info == 1:
			col_tel_info_thread_handle = thread.start_new_thread(song_checker_handle.collect_tel_info, ())
		
		over_all_obs_state_thread_handle = thread.start_new_thread(song_checker_handle.over_all_obs_state, ())
		monitor_runs_thread_handle = thread.start_new_thread(song_checker_handle.check_if_monitor_runs, ())

		done_param = 0
		self.telescope_hangs_sms = 0

		global past_time
		past_time = time.time()

		print clock.timename(), " Starting handle_request loop..."
		while RUNNING:

			#### This checks if the loop is running. If it hangs somewhere a wakeup message will be sent out. 
			past_time = time.time()		
	
			if song_monitor_config.mon_time == 1:		# If the config file specifies it time checks will be carried out.
				try:
					song_checker_handle.check_time()
				except Exception,e:
					print clock.timename(), " Problem in check_time()"
					print clock.timename(), e

			if song_monitor_config.mon_weather == 1:	# If the config file specifies it weather checks will be carried out.
				try:
					song_checker_handle.check_weather()
				except Exception,e:
					print clock.timename(), " Problem in check_weather()"
					print clock.timename(), e

			if song_monitor_config.mon_side_ports == 1:	# If the config file specifies it side port checks will be carried out.
				try:
					song_checker_handle.check_side_ports()
				except Exception,e:
					print clock.timename(), " Problem in check_side_ports()"
					print clock.timename(), e

			if song_monitor_config.mon_telescope == 1:	# If the config file specifies it telescope checks will be carried out.
				try:
					song_checker_handle.check_telescope()
				except Exception,e:
					print clock.timename(), e
					print clock.timename(), " Problem in check_telescope()"
					if song_monitor_config.send_notifications == "yes" and self.telescope_hangs_sms == 0:
						send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Telescope Error!",message="The monitor could not connect to the telescope!\n\nPlease check if something is wrong. Check if the TSI is running on the astelco pc. Check if the tcs_daemon is running on hw. \n\nSend at: %s\n\n" % (clock.obstimeUT()))
						if song_monitor_config.send_sms == "yes":	
							print clock.timename(), " Sending an sms to: %s " % (m_conf.wakeup_sms_who)
							send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The monitor could not connect to the telescope!")
						if song_monitor_config.send_to_support == "yes":
							send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Telescope Error!",message="The monitor could not connect to the telescope!\n\nPlease check if something is wrong. Check if the TSI is running on the astelco pc. Check if the tcs_daemon is running on hw. \n\nSend at: %s\n\n" % (clock.obstimeUT()))

						self.telescope_hangs_sms = 1

			if song_monitor_config.mon_network == 1:	# If the config file specifies it netowrk checks will be carried out.
				try:
					song_checker_handle.check_network()
				except Exception,e:
					print clock.timename(), " Problem in check_network()"
					print clock.timename(), e

			if song_monitor_config.mon_house_hold == 1:	# If the config file specifies it house hold checks will be carried out.
				try:
					song_checker_handle.check_house_hold()
				except Exception,e:
					print clock.timename(), " Problem in check_house_hold()"
					print clock.timename(), e

			if song_monitor_config.mon_wind_speed == 1:	# If the config file specifies it wind speed checks will be carried out.
				try:
					song_checker_handle.check_wind()
				except Exception,e:
					print clock.timename(), " Problem in check_wind()"
					print clock.timename(), e

			if song_monitor_config.mon_cooling_unit == 1:	# If the config file specifies it cooling unit checks will be carried out.
				try:
					song_checker_handle.check_cooler()
				except Exception,e:
					print clock.timename(), " Problem in check_cooler()"
					print clock.timename(), e


			### This should copy the content of the log file to old log file and clear it at 12 UTC.
			if int(float(time.strftime("%H", time.gmtime()))) == 12 and done_param == 0:
				daily_logging_handler.handle_log_files(song_monitor_config.outstream, song_monitor_config.outstream_old)
				done_param = 1
			if done_param == 1 and int(float(time.strftime("%H", time.gmtime()))) > 12:
				done_param = 0


			clock.TimeSleep2(song_monitor_config.monitor_sleep_time) 

		print clock.timename(), " The monitor daemon was stopped"
		print clock.timename(), " The while loop got a False signal... "
			
def main():
	"""
		@brief: This is the main part of the code that starts up everything else. 
	"""

	daemon = monitor_daemon(song_monitor_config.pidfile, stdout=song_monitor_config.outstream, stderr=song_monitor_config.outstream)
	try:
		opts, list = getopt.getopt(sys.argv[1:], 'st')
	except getopt.GetoptError, e:
		print clock.timename(), " Bad options provided!"
		sys.exit()

	for opt, a in opts:
		if opt == "-s":
			try:
				pid_number = open(song_monitor_config.pidfile,'r').readline()
				if pid_number:
               				sys.exit('Daemon is already running!')
         		except Exception, e:
            			pass

			#try:
			#	os.rename(song_monitor_config.outstream, "/tmp/monitor_old.log")
			#except OSError, e:
			#	pass

			print clock.timename(), " Starting daemon...!"
			daemon.start()
		elif opt == "-t":
			daemon.stop()
			print clock.timename(), " The daemon is stoped!"
		else:
			print clock.timename(), " Option %s not supported!" % (opt)

if __name__ == "__main__":
	try:
		main()
	except Exception, e:
		print clock.timename(), e
		print clock.timename(), " The monitor has crashed"
#		send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Monitor Crash!",message="The monitor daemon has crashed!\n\nCheck the log file to see why!\n\nMaybe a simple restart helps!!\nLog onto hw as the user obs and type\nsong_monitor -s\nThis should start the monitor. Check the log file /home/obs/logs/monitor.log if it starts correctly.")

#		send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The monitor daemon was stopped for some reason!")

		if song_monitor_config.send_to_support == "yes":
			send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="Monitor Crash!",message="The monitor daemon has crashed!\n\nCheck the log file to see why!\n\nMaybe a simple restart helps!!\nLog onto hw as the user obs and type\nsong_monitor -s\nThis should start the monitor. Check the log file /home/obs/logs/monitor.log if it starts correctly.")

	#send_song_mail.send_mail().send_sms(receiver=["Mads"], message="The monitor daemon was stopped for some reason!")

