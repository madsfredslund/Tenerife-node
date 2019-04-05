import song_timeclass
import mon_actions
import time
import thread
import song_monitor_config
import send_song_mail
import master_config as m_conf

clock = song_timeclass.TimeClass()

class Check_Cooler(object):
	"""
		@brief: This class handles the cooling unit.
	"""
	def __init__(self):
		"""
			Initialization of the time checks.
		"""
		self.verbose = song_monitor_config.verbose
		self.perform_actions = mon_actions.Do_Actions()
		self.cooler_state = self.perform_actions.cooler_status()

	def handle_cooler(self, side_port_group_1, side_port_group_2, side_port_group_3, side_port_group_4, telescope_state, slit_state, flap_state, mirror_cover_state, who_did_it_tel,  who_did_it_sp):
		"""
			Checks the dome and side port state and will turn the cooler on or off depending on the state of these.
		"""
		### If any of the dome openings are open the cooler will be stoped:
		if float(side_port_group_1) != 0.0 or float(side_port_group_2) != 0.0 or float(side_port_group_3) != 0.0 or float(side_port_group_4) != 0.0 or float(slit_state) != 0.0 or float(flap_state) != 0.0:			
			if song_monitor_config.mon_cooler_actions == 1 and float(self.cooler_state) == 1.0:

				status_cooler = self.perform_actions.stop_cooler()	
		
				if status_cooler != "done" and song_monitor_config.send_notifications == "yes":
					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Cooler not off!", message="The dome or side ports were opened and the cooling unit was not switched off!\n\nSend at: %s\n\n" % clock.obstimeUT())

				self.cooler_state = self.perform_actions.cooler_status()

			elif song_monitor_config.mon_cooler_actions == 0 and float(self.cooler_state) == 1.0:
				print clock.timename(), " The cooler whould have been stopped now"
				self.cooler_state = 0
			

		### If all dome openings are closed the cooler are allowed to start:
		elif float(side_port_group_1) == 0.0 and float(side_port_group_2) == 0.0 and float(side_port_group_3) == 0.0 and float(side_port_group_4) == 0.0 and float(slit_state) == 0.0 and float(flap_state) == 0.0:

			if song_monitor_config.mon_cooler_actions == 1 and float(self.cooler_state) == 0.0:
				status_cooler = self.perform_actions.start_cooler(m_conf.cooling_temp)			
				if status_cooler != "done" and song_monitor_config.send_notifications == "yes":
					send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who, sender="SONG_MS", subject="Cooler not on!", message="The cooling unit was not switched on!\n\nSend at: %s\n\n" % clock.obstimeUT())
				self.cooler_state = self.perform_actions.cooler_status()

			elif song_monitor_config.mon_cooler_actions == 0 and float(self.cooler_state) == 0.0:
				print clock.timename(), " The cooler whould have been started now"
				self.cooler_state = 1	


		return 1



