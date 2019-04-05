import song_checker
import song_timeclass
import mon_actions
import time
import thread
import song_monitor_config
import song_checker_config
import song_star_checker
import urllib2
import send_song_mail

clock = song_timeclass.TimeClass()

class Check_Network(object):
	"""
		@brief: This class handles all checks on the network connection.
	"""
	def __init__(self):
		"""
			Initialization of the time checks.
		"""
		self.verbose = song_monitor_config.verbose
		self.the_world_responded = "nothing_yet"
		self.thread_counter = 0
		self.RUNNING = True

	def hello_world(self, side_port_group_1, side_port_group_2, side_port_group_3, side_port_group_4, telescope_state, slit_state, flap_state, mirror_cover_state, who_did_it_tel,  who_did_it_sp):
		"""
			Checks the network connection to the outside world.
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

		if self.thread_counter == 0:			
			thread_handle = thread.start_new_thread(self.ping_the_world, ())	
			print clock.timename(), " The first network test is skiped since no ping is made yet!"
		
		if self.the_world_responded != "hi" and song_monitor_config.mon_telescope_actions == 1 and self.thread_counter != 0 and self.who_did_it_tel == "free":
			#### SOME ACTIONS TO THE TELESCOPE WILL BE CARRIED OUT ####
			print clock.timename(), " The Telescope and side ports would be closed due to lost network connection"

		elif self.the_world_responded != "hi" and self.thread_counter != 0 and self.who_did_it_tel == "free":
			print clock.timename(), " The Telescope and side ports would be closed due to lost network connection"
			self.who_did_it_tel = "network"

		if self.the_world_responded != "hi":
			if self.verbose == "yes":
				print clock.timename(), " The world did NOT say hi"

		return self.side_port_group_1, self.side_port_group_2, self.side_port_group_3, self.side_port_group_4, self.telescope_state, self.slit_state, self.flap_state, self.mirror_cover_state, self.who_did_it_tel, self.who_did_it_sp



	def ping_the_world(self):

		while self.RUNNING == True:
		
			try:
				response=urllib2.urlopen('http://'+song_monitor_config.check_conn_ip_1,timeout=2.0) # Ping the IAC network.
				self.the_world_responded = "hi"
			except urllib2.URLError as err:
				print clock.timename(), " First ping test timed out"
				self.the_world_responded = "nothing"
			except Exception, e:
				print clock.timename(), " Another exception was thrown"
				print clock.timename(), e
				self.the_world_responded = "nothing"

			if self.the_world_responded == "nothing" or self.the_world_responded == "nothing_yet":
				try:
					response=urllib2.urlopen('http://'+song_monitor_config.check_conn_ip_1,timeout=5.0) # Ping google.com.
					print clock.timename(), " Second ping test worked"
					self.the_world_responded = "hi"
				except urllib2.URLError as err:
					#print err
					print clock.timename(), " Second ping test timed out"
					self.the_world_responded = "nothing"
				except Exception, e:
					print clock.timename(), " Another exception was thrown"
					print clock.timename(), e
					self.the_world_responded = "nothing"

			self.thread_counter = 1

			time.sleep(10)

		#return 1


