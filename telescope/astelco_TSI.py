import song_timeclass
import socket
import string
import time
import sys
import song_telescope_config

clock = song_timeclass.TimeClass()

# In this module all the commands, which operates the telescope, are written. When this class gets called the __init__ function will connect to the telescope and the user gets registered. When connection is made the telescope can be operated. 		

class astelco(object):
	"""
		This class handles all the astelco commands which can opperate the telescope. 
	"""
	def __init__(self):
		#Server: sim.tt-data.eu 
		logon_message = 'AUTH PLAIN "%s" "%s"\n' % (song_telescope_config.ASTELCO_USER, song_telescope_config.ASTELCO_PASS)

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.connid = 0

		#print "Connecting to remote server..."

		try:
			self.sock.connect((song_telescope_config.ASTELCO_IP,song_telescope_config.ASTELCO_TSI_PORT))
		except Exception, e:
			print "SOCKET CONNECT ERROR: ", e
			print "CHECK IF TSI program runs on Astelco PC!"
			sys.exit("Socket connect error!")

		self.sock.settimeout(1.0)

		data = ''
		while len(data.split("\n")) != 2:
			try:
				data = data + self.sock.recv(1024)
			except socket.timeout, e:
				pass
			time.sleep(0.1)

		try:
			self.connid = int(data.split(" ")[3])
		except Exception, e:
			print e
		else:
			print "Connection id: ", self.connid		

		try:
			self.sock.send(logon_message)
		except Exception, e:
			print e
		
		data = ''
		while len(data.split("\n")) != 2:
			try:
				data = data + self.sock.recv(1024)
			except socket.timeout, e:
				pass
			time.sleep(0.1)

		print data


# These two functions are the message handling functions that talks with the telescope. #################################

	def perform_query_set(self, number, msg):
		"""
		This function sends the messages to the telescope. Only for the set functions.
		"""

		if song_telescope_config.DEBUG == "yes":
			print "[CONN-ID: %s] - [COMMAND: '%s'] - [TIMESTAMP: %s]" % (self.connid, msg.strip("\n"), clock.obstimeUT())

		try:
			self.sock.send(msg)
		except Exception, e:
			print e

		index = msg.split(" ")[0]
		conn_timeout = time.time() + 60 * 7	# 7 minutes to make sure it will not happen before dome open/close time.

		if index in ["1", "82", "83", "90"]: # Power on/off telescope, Open/close dome slit/flap, open/close mirror covers... The ones that take maybe more than 120 s to complete.
			return_time = time.time() + 10

			data = ''
			while index + ' COMMAND COMPLETE' not in data:
				try:
					data = data + self.sock.recv(1024)
				except socket.timeout, e:
					if 'COMMAND FAILED' in data:
						print data
						data = "Wrong parameter!!!"
						break
					elif data != '' and time.time() < conn_timeout:
						print data
						pass
					else:
						print "Socket timeout!", e
						self.sock.close()
						time.sleep(5)
						print "Trying to reconnect..."
						self.__init__()
						time.sleep(5)
						break

				time.sleep(0.1)
				if return_time < time.time():
					data = data + self.get_telescope_state_all()
					return_time = time.time() + 10
					
		else:
			data = ''
			while index + ' COMMAND COMPLETE' not in data:
				try:
					data = data + self.sock.recv(1024)
				except socket.timeout, e:
					if 'COMMAND FAILED' in data:
						print data
						data = "Wrong parameter!!!"
						break
					elif data != '' and time.time() < conn_timeout:
						print data
						pass
					else:
						print data
						self.sock.close()
						time.sleep(5)
						print "Trying to reconnect..."
						self.__init__()
						time.sleep(5)
						break
				time.sleep(0.1)

		if song_telescope_config.DEBUG == "yes":
			print data

		return data

	def perform_query_get(self, number, msg):
		"""
		This function sends the messages to the telescope and recieves the responds. Only for the get functions.
		"""

		if song_telescope_config.DEBUG == "yes":
			print "[CONN-ID: %s] - [COMMAND: '%s'] - [TIMESTAMP: %s]" % (self.connid, msg.strip("\n"), clock.obstimeUT())

		try:
			self.sock.send(msg)
		except Exception, e:
			print e

		data = ''
		reconnect = 0
		index = msg.split(" ")[0]

		while index + ' COMMAND COMPLETE' not in data:
			try:
				data = data + self.sock.recv(1024)
			except socket.timeout, e:
				if 'COMMAND FAILED' in data:
					print data
					data = "Wrong parameter!!!"
					break
				else:
					print data
					print "Will now try to close connection by sending DISCONNECT!"
					self.sock.close()
					time.sleep(5)
					print "Trying to reconnect..."
					self.__init__()
					time.sleep(5)
					reconnect = 1
					break
			time.sleep(0.1)

		if reconnect == 1:
			print "Trying to collect data again..."
			try:
				self.sock.send(msg)
			except Exception, e:
				print e

			data = ''
			index = msg.split(" ")[0]

			while index + ' COMMAND COMPLETE' not in data:
				try:
					data = data + self.sock.recv(1024)
				except socket.timeout, e:
					if 'COMMAND FAILED' in data:
						print data
						data = "Wrong parameter!!!"
						break
					else:
						print data
						print "Will now try to close connection by sending DISCONNECT!"
						self.sock.close()
						time.sleep(5)
						print "Trying to reconnect..."
						self.__init__()
						time.sleep(5)
						break
				time.sleep(0.1)		

			if "Tracking stopped" in data:
				print "Tracking was stopped due to the re-initialization."
				print "Now trying to start tracking again"
				self.set_pointing_track(param=1)	

		if song_telescope_config.DEBUG == "yes":
			print data

	        return data

###############################################################################################################################

	def close_connection(self):
		"""
		This function closes the connection to the telescope correctly and closes the socket connection.
		"""
		close_message = "DISCONNECT\n"
		try:
			self.sock.send(close_message)
		except Exception, e:
			print e
		
		data = ''
		while "DISCONNECT OK" not in data:
			try:
				data = data + self.sock.recv(1024)
			except socket.timeout, e:
				print data
				print "Socket timeout!", e
				break
			time.sleep(0.1)

		try:
			self.sock.close()
		except Exception, e:
			print e

		print data

		if "DISCONNECT OK" in data:
			return 1
		else:
			return 0

#############################################################################################
################################# TELESCOPE #################################################
#############################################################################################

	def set_telescope_ready(self, param):
		# This powers the telescope. param = 1 for turning the telescope on, open the dome and open the covers. param = 0 for the opposite.  
		number = "1"
		msg = number + " SET TELESCOPE.READY="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_telescope_state_all(self):
		number = "2"
		msg = number + " GET TELESCOPE.READY_STATE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data

	def get_telescope_state(self):
		number = "2"
		msg = number + " GET TELESCOPE.READY_STATE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_telescope_motion_state(self):
		number = "3"
		msg = number + " GET TELESCOPE.MOTION_STATE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()
	
	def set_telescope_stop(self):
		number = "4"
		msg = number + " SET TELESCOPE.STOP=1\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_telescope_status_global(self):
		number = "5"
		msg = number + " GET TELESCOPE.STATUS.GLOBAL\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_telescope_status_clear(self,param):
		number = "6"
		msg = number + " SET TELESCOPE.STATUS.CLEAR="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data


#############################################################################################
#################################    OBJECT #################################################
#############################################################################################

	def set_object_equatorial_epoch(self,param):
		number = "7"
		msg = number + " SET OBJECT.EQUATORIAL.EPOCH="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_object_equatorial_epoch(self):
		number = "8"
		msg = number + " GET OBJECT.EQUATORIAL.EPOCH\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_object_equatorial_equinox(self,param):
		number = "9"
		msg = number + " SET OBJECT.EQUATORIAL.EQUINOX="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_object_equatorial_equinox(self):
		number = "10"
		msg = number + " GET OBJECT.EQUATORIAL.EQUINOX\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_object_equatorial_ra(self,param):
		number = "11"
		msg = number + " SET OBJECT.EQUATORIAL.RA="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_object_equatorial_ra(self):
		number = "12"
		msg = number + " GET OBJECT.EQUATORIAL.RA\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_object_equatorial_dec(self,param):
		number = "13"
		msg = number + " SET OBJECT.EQUATORIAL.DEC="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_object_equatorial_dec(self):
		number = "14"
		msg = number + " GET OBJECT.EQUATORIAL.DEC\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_object_equatorial_ra_pm(self,param):
		number = "15"
		msg = number + " SET OBJECT.EQUATORIAL.RA_PM="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_object_equatorial_ra_pm(self):
		number = "16"
		msg = number + " GET OBJECT.EQUATORIAL.RA_PM\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_object_equatorial_dec_pm(self,param):
		number = "17"
		msg = number + " SET OBJECT.EQUATORIAL.DEC_PM="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_object_equatorial_dec_pm(self):
		number = "18"
		msg = number + " GET OBJECT.EQUATORIAL.DEC_PM\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()


#	def set_object_equatorial_name(self,param):
#		number = "14"
#		msg = number + " SET OBJECT.EQUATORIAL.NAME="+str(param)+"\n"
#		print msg
#		return_data = self.perform_query_set(number, msg)
#		return return_data

#	def get_object_equatorial_name(self):
#		number = "15"
#		msg = number + " GET OBJECT.EQUATORIAL.NAME\n"
#		return_data = self.perform_query_get(number, msg)
#		return return_data.split("=")[1].split("\n")[0].strip()

#############################################################################################
#################################  POINTING #################################################
#############################################################################################

	def set_pointing_track(self,param):
		number = "19"
		msg = number + " SET POINTING.TRACK="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

#		if float(param) == 2.0:
#			return_data = self.perform_query_set(number, msg)
#			return return_data
#		else:
#			try:
#				self.sock.send(msg)
#			except Exception, e:
#				print e
#		
#			data=''
#			if float(param) == float(0.0):
#				while "Tracking stopped" not in data:
#					try:
#						data = data + self.sock.recv(1024)
#					except socket.timeout, e:				
#						print "Socket timeout!", e
#						print data
#					time.sleep(0.1)
#				return_value = "stopped"
#
#			elif float(param) == float(1.0):
#				while "Tracking started" not in data:
#					try:
#						data = data + self.sock.recv(1024)
#					except socket.timeout, e:				
#						print "Socket timeout!", e
#						print data
#					time.sleep(0.1)
#				return_value = "started"
#
#			elif float(param) == float(2.0):
#				while "Tracking stopped" not in data:
#					try:
#						data = data + self.sock.recv(1024)
#					except socket.timeout, e:				
#						print "Socket timeout!", e
#						print data
#					time.sleep(0.1)
#				return_value = "done"
#
#			elif float(param) == float(4.0):
#				while "COMPLETE" not in data:
#					try:
#						data = data + self.sock.recv(1024)
#					except socket.timeout, e:				
#						print "Socket timeout!", e
#						print data
#					time.sleep(0.1)
#				return_value = "done"
#
#			elif float(param) == float(6.0):
#				while "COMPLETE" not in data:
#					try:
#						data = data + self.sock.recv(1024)
#					except socket.timeout, e:				
#						print "Socket timeout!", e
#						print data
#					time.sleep(0.1)
#				return_value = "done"
#
#			elif float(param) == float(8.0):
#				while "COMPLETE" not in data:
#					try:
#						data = data + self.sock.recv(1024)
#					except socket.timeout, e:				
#						print "Socket timeout!", e
#						print data
#					time.sleep(0.1)
#				return_value = "done"
#
#			if song_telescope_config.VERBOSE == "yes" and song_telescope_config.DEBUG != "yes":
#				print "Command: ", msg.strip("\n"), " performed at: ", clock.obstimeUT()
#			elif song_telescope_config.DEBUG == "yes":
#				print "Command: ", msg.strip("\n"), " performed at: ", clock.obstimeUT()
#				print data
#
#			return return_value

	def get_pointing_track(self):
		number = "20"
		msg = number + " GET POINTING.TRACK\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_pointing_setup_use_port(self):
		number = "21"
		msg = number + " GET POINTING.SETUP.USE_PORT\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_pointing_setup_use_port(self,param):
		number = "22"
		msg = number + " SET POINTING.SETUP.USE_PORT="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_pointing_model_calculate(self):
		number = "23"
		msg = number + " GET POINTING.MODEL.CALCULATE\n"
		return_data = self.perform_query_set(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_pointing_model_calculate(self,param):
		number = "24"
		msg = number + " SET POINTING.MODEL.CALCULATE="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_pointing_model_type(self):
		number = "25"
		msg = number + " GET POINTING.MODEL.TYPE\n"
		return_data = self.perform_query_set(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_pointing_model_type(self,param):
		number = "26"
		msg = number + " SET POINTING.MODEL.TYPE="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def set_pointing_model_add(self,param):
		number = "27"
		msg = number + " SET POINTING.MODEL.ADD="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_pointing_model_list(self):
		number = "28"
		msg = number + " GET POINTING.MODEL.LIST\n"
		return_data = self.perform_query_set(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_pointing_model_file(self):
		number = "29"
		msg = number + " GET POINTING.MODEL.FILE\n"
		return_data = self.perform_query_set(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_pointing_model_file(self,param):
		number = "30"
		msg = number + " SET POINTING.MODEL.FILE="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def set_pointing_model_load(self,param):
		number = "31"
		msg = number + " SET POINTING.MODEL.LOAD="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def set_pointing_model_save(self,param):
		number = "32"
		msg = number + " SET POINTING.MODEL.SAVE="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data


#############################################################################################
################################# POSITION  #################################################
#############################################################################################


	def get_position_horizontal_az(self):
		number = "33"
		msg = number + " GET POSITION.HORIZONTAL.AZ\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()
		
	def get_position_horizontal_alt(self):
		number = "34"
		msg = number + " GET POSITION.HORIZONTAL.ALT\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_horizontal_zd(self):
		number = "35"
		msg = number + " GET POSITION.HORIZONTAL.ZD\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_horizontal_derotator(self):
		number = "36"
		msg = number + " GET POSITION.HORIZONTAL.DEROTATOR\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_horizontal_dome(self):
		number = "37"
		msg = number + " GET POSITION.HORIZONTAL.DOME\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_equatorial_ra_j2000(self):
		number = "38"
		msg = number + " GET POSITION.EQUATORIAL.RA_J2000\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_equatorial_dec_j2000(self):
		number = "39"
		msg = number + " GET POSITION.EQUATORIAL.DEC_J2000\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_equatorial_ra_current(self):
		number = "40"
		msg = number + " GET POSITION.EQUATORIAL.RA_CURRENT\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_equatorial_dec_current(self):
		number = "41"
		msg = number + " GET POSITION.EQUATORIAL.DEC_CURRENT\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_equatorial_parallactic_angle(self):
		number = "42"
		msg = number + " GET POSITION.EQUATORIAL.PARALLACTIC_ANGLE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_zd_targetpos(self):
		number = "43"
		msg = number + " GET POSITION.INSTRUMENTAL.ZD.TARGETPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_zd_currpos(self):
		number = "44"
		msg = number + " GET POSITION.INSTRUMENTAL.ZD.CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

#### This function is deprecated ####
#	def get_position_instrumental_alt_currpos(self):
#		number = "30"
#		msg = number + " GET POSITION.INSTRUMENTAL.ALT.CURRPOS\n"
#		return_data = self.perform_query_get(number, msg)
#		print return_data
#		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_az_currpos(self):
		number = "45"
		msg = number + " GET POSITION.INSTRUMENTAL.AZ.CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_derotator_currpos(self):
		number = "46"
		msg = number + " GET POSITION.INSTRUMENTAL.DEROTATOR[2].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_derotator_targetpos(self, param):
		number = "47"
		msg = number + " SET POSITION.INSTRUMENTAL.DEROTATOR[2].TARGETPOS="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

        def get_position_instrumental_derotator_offset(self):
                number = "48"
                msg = number + " GET POSITION.INSTRUMENTAL.DEROTATOR[2].OFFSET\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_derotator_offset(self, param):
		number = "49"
		msg = number + " SET POSITION.INSTRUMENTAL.DEROTATOR[2].OFFSET="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_focus_currpos(self):
		number = "50"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[2].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

##########   HEXAPOD  ##########

	### Positions ###
	def get_position_instrumental_hexapod_x_currpos(self):
		number = "51"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[0].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_hexapod_x_realpos(self):
		number = "121"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[0].REALPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_x_targetpos(self, param):
		number = "52"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[0].TARGETPOS="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_hexapod_y_currpos(self):
		number = "53"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[1].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_hexapod_y_realpos(self):
		number = "122"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[1].REALPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_y_targetpos(self, param):
		number = "54"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[1].TARGETPOS="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_hexapod_z_currpos(self):
		number = "55"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[2].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_hexapod_z_realpos(self):
		number = "123"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[2].REALPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_z_targetpos(self, param):
		number = "56"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[2].TARGETPOS="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_hexapod_u_currpos(self):
		number = "57"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[3].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_hexapod_u_realpos(self):
		number = "124"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[3].REALPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_u_targetpos(self, param):
		number = "58"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[3].TARGETPOS="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_hexapod_v_currpos(self):
		number = "59"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[4].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_hexapod_v_realpos(self):
		number = "125"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[4].REALPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_v_targetpos(self, param):
		number = "60"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[4].TARGETPOS="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_hexapod_w_currpos(self):
		number = "61"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[5].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_hexapod_w_realpos(self):
		number = "126"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[5].REALPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_w_targetpos(self, param):
		number = "62"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[5].TARGETPOS="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	### Offsets ###
	def get_position_instrumental_hexapod_x_offset(self):
		number = "63"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[0].OFFSET\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_x_offset(self, param):
		number = "64"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[0].OFFSET="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_hexapod_y_offset(self):
		number = "65"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[1].OFFSET\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_y_offset(self, param):
		number = "66"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[1].OFFSET="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_hexapod_z_offset(self):
		number = "67"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[2].OFFSET\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_z_offset(self, param):
		number = "68"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[2].OFFSET="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_hexapod_u_offset(self):
		number = "69"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[3].OFFSET\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_u_offset(self, param):
		number = "70"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[3].OFFSET="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_hexapod_v_offset(self):
		number = "71"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[4].OFFSET\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_v_offset(self, param):
		number = "72"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[4].OFFSET="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_position_instrumental_hexapod_w_offset(self):
		number = "73"
		msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[5].OFFSET\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_hexapod_w_offset(self, param):
		number = "74"
		msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[5].OFFSET="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data




################################

        def get_position_instrumental_focus_offset(self):
                number = "75"
                msg = number + " GET POSITION.INSTRUMENTAL.FOCUS[2].OFFSET\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

        def get_position_instrumental_alt_offset(self):
                number = "76"
                msg = number + " GET POSITION.INSTRUMENTAL.ALT.OFFSET\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

        def get_position_instrumental_az_offset(self):
                number = "77"
                msg = number + " GET POSITION.INSTRUMENTAL.AZ.OFFSET\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

        def get_position_instrumental_zd_offset(self):
                number = "78"
                msg = number + " GET POSITION.INSTRUMENTAL.ZD.OFFSET\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

##############

	def get_position_instrumental_dome_az_currpos(self):
		number = "79"
		msg = number + " GET POSITION.INSTRUMENTAL.DOME[0].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_dome_flap_currpos(self):
		number = "80"
		msg = number + " GET POSITION.INSTRUMENTAL.DOME[2].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_position_instrumental_dome_slit_currpos(self):
		number = "81"
		msg = number + " GET POSITION.INSTRUMENTAL.DOME[1].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_dome_flap_targetpos(self,param):
		number = "82"
		msg = number + " SET POSITION.INSTRUMENTAL.DOME[2].TARGETPOS="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def set_position_instrumental_dome_slit_targetpos(self,param):
		number = "83"
		msg = number + " SET POSITION.INSTRUMENTAL.DOME[1].TARGETPOS="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

###########

        def set_position_instrumental_focus_targetpos(self,param):
                number = "84"
                msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[2].TARGETPOS="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

        def set_position_instrumental_focus_offset(self,param):
                number = "85"
                msg = number + " SET POSITION.INSTRUMENTAL.FOCUS[2].OFFSET="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

        def set_position_instrumental_alt_offset(self,param):
                number = "86"
                msg = number + " SET POSITION.INSTRUMENTAL.ALT.OFFSET="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

        def set_position_instrumental_az_offset(self,param):
                number = "87"
                msg = number + " SET POSITION.INSTRUMENTAL.AZ.OFFSET="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

        def set_position_instrumental_zd_offset(self,param):
                number = "88"
                msg = number + " SET POSITION.INSTRUMENTAL.ZD.OFFSET="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data


###########





#############################################################################################
################################# AUXILIARY #################################################
#############################################################################################

	def get_auxiliary_cover_realpos(self):
		number = "89"
		msg = number + " GET AUXILIARY.COVER.REALPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_auxiliary_cover_targetpos(self,param):
		number = "90"
		msg = number + " SET AUXILIARY.COVER.TARGETPOS="+str(float(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_auxiliary_cover_targetpos(self):
		number = "91"
		msg = number + " GET AUXILIARY.COVER.TARGETPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_auxiliary_temp_cabinet(self):
		number = "92"
		msg = number + " GET AUXILIARY.SENSOR[0].VALUE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_auxiliary_temp_m1(self):
		number = "93"
		msg = number + " GET AUXILIARY.SENSOR[3].VALUE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_auxiliary_temp_m2(self):
		number = "94"
		msg = number + " GET AUXILIARY.SENSOR[4].VALUE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_auxiliary_temp_m3(self):
		number = "95"
		msg = number + " GET AUXILIARY.SENSOR[5].VALUE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()


	def get_auxiliary_ttelescope(self):
		number = "96"
		msg = number + " GET AUXILIARY.SENSOR[6].VALUE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_auxiliary_mancontrolspeed(self):
		number = "97"
		msg = number + " GET AUXILIARY.SENSOR[1].VALUE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_sidereal_time(self):
		number = "98"
		msg = number + " GET POSITION.LOCAL.SIDEREAL_TIME\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_UTC_time(self):
		number = "99"
		msg = number + " GET POSITION.LOCAL.UTC\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_object_horizontal_alt(self, param):
                number = "100"
                msg = number + " SET OBJECT.HORIZONTAL.ALT="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

	def set_object_horizontal_az(self, param):
                number = "101"
                msg = number + " SET OBJECT.HORIZONTAL.AZ="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

	def get_telescope_status_list(self):
		number = "102"
		msg = number + " GET TELESCOPE.STATUS.LIST\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def get_pointing_setup_dome_syncmode(self):
		number = "103"
		msg = number + " GET POINTING.SETUP.DOME.SYNCMODE\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_pointing_setup_dome_syncmode(self, param):
                number = "104"
                msg = number + " SET POINTING.SETUP.DOME.SYNCMODE="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data
	
	def get_pointing_setup_dome_max_deviation(self):
		number = "105"
		msg = number + " GET POINTING.SETUP.DOME.MAX_DEVIATION\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_pointing_setup_dome_max_deviation(self, param):
                number = "106"
                msg = number + " SET POINTING.SETUP.DOME.MAX_DEVIATION="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

	def get_pointing_setup_dome_offset(self):
		number = "107"
		msg = number + " GET POINTING.SETUP.DOME.OFFSET\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_pointing_setup_dome_offset(self, param):
                number = "108"
                msg = number + " SET POINTING.SETUP.DOME.OFFSET="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

	def set_telescope_config_load(self):
                number = "109"
                msg = number + " SET TELESCOPE.CONFIG.LOAD=1\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

	def get_position_mechanical_derotator_currpos(self):
		number = "110"
		msg = number + " GET POSITION.INSTRUMENTAL.DEROTATOR[3].CURRPOS\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

        def set_position_mechanical_derotator_targetpos(self, param):
                number = "111"
                msg = number + " SET POSITION.INSTRUMENTAL.DEROTATOR[3].TARGETPOS="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

        def get_position_mechanical_derotator_offset(self):
                number = "112"
                msg = number + " GET POSITION.INSTRUMENTAL.DEROTATOR[3].OFFSET\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

        def set_position_mechanical_derotator_offset(self, param):
                number = "113"
                msg = number + " SET POSITION.INSTRUMENTAL.DEROTATOR[3].OFFSET="+str(float(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

########################## AO BENDERS

        def get_position_instrumental_ao_offset(self, bender_number):
                number = "114"
                msg = number + " GET POSITION.INSTRUMENTAL.AO_BENDER[%i].OFFSET\n" % (int(bender_number))
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

        def set_position_instrumental_ao_offset(self, bender_number, param):
                number = "115"
                msg = number + " SET POSITION.INSTRUMENTAL.AO_BENDER[%i].OFFSET=%f\n" % (int(bender_number),float(param))
                return_data = self.perform_query_set(number, msg)
                return return_data

        def get_position_instrumental_ao_currpos(self, bender_number):
                number = "116"
                msg = number + " GET POSITION.INSTRUMENTAL.AO_BENDER[%i].CURRPOS\n" % (int(bender_number))
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

        def set_position_instrumental_ao_targetpos(self, bender_number, param):
                number = "117"
                msg = number + " SET POSITION.INSTRUMENTAL.AO_BENDER[%i].TARGETPOS=%f\n" % (int(bender_number),float(param))
                return_data = self.perform_query_set(number, msg)
                return return_data

##################################

	def set_pointing_setup_focus_syncmode(self, param):
                number = "118"
                msg = number + " SET POINTING.SETUP.FOCUS.SYNCMODE="+str(int(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data
	
	def get_pointing_setup_focus_syncmode(self):
                number = "119"
                msg = number + " GET POINTING.SETUP.FOCUS.SYNCMODE\n"
                return_data = self.perform_query_set(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

	def get_pointing_model_file_list(self):
		number = "120"
		msg = number + " GET POINTING.MODEL.FILE_LIST\n"
		return_data = self.perform_query_set(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

        def get_pointing_setup_derotator_syncmode(self):
                number = "127"
                msg = number + " GET POINTING.SETUP.DEROTATOR.SYNCMODE\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

	def set_pointing_setup_derotator_syncmode(self, param):
		number = "128"
		msg = number + " SET POINTING.SETUP.DEROTATOR.SYNCMODE="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

        def get_pointing_setup_mechanical_derotator_syncmode(self):
                number = "129"
                msg = number + " GET POINTING.SETUP.DEROTATOR.SYNCMODE\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

	def set_pointing_setup_mechanical_derotator_syncmode(self, param):
		number = "130"
		msg = number + " SET POINTING.SETUP.DEROTATOR.SYNCMODE="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

        def get_position_instrumental_port_select_currpos(self):
                number = "131"
                msg = number + " GET POSITION.INSTRUMENTAL.PORT_SELECT.CURRPOS\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

        def get_pointing_setup_instrument_name(self):
                number = "132"
                msg = number + " GET POINTING.SETUP.INSTRUMENT.NAME\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

        def get_pointing_setup_instrument_index(self):
                number = "133"
                msg = number + " GET POINTING.SETUP.INSTRUMENT.INDEX\n"
                return_data = self.perform_query_get(number, msg)
                return return_data.split("=")[1].split("\n")[0].strip()

        def set_pointing_setup_instrument_index(self, param):
                number = "134"
                msg = number + " SET POINTING.SETUP.INSTRUMENT.INDEX="+str(int(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

	def get_position_instrumental_dome_az_offset(self):
		number = "135"
		msg = number + " GET POSITION.INSTRUMENTAL.DOME[0].OFFSET\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_position_instrumental_dome_az_offset(self,param):
		number = "136"
		msg = number + " SET POSITION.INSTRUMENTAL.DOME[0].OFFSET="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data
###----

	def set_telescope_status_clear_panic(self,param):
		number = "137"
		msg = number + " SET TELESCOPE.STATUS.CLEAR_PANIC="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def set_telescope_status_clear_error(self,param):
		number = "138"
		msg = number + " SET TELESCOPE.STATUS.CLEAR_ERROR="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def set_telescope_status_clear_warning(self,param):
		number = "139"
		msg = number + " SET TELESCOPE.STATUS.CLEAR_WARNING="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def set_telescope_status_clear_info(self,param):
		number = "140"
		msg = number + " SET TELESCOPE.STATUS.CLEAR_INFO="+str(int(param))+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def set_telescope_config_environment_temperature(self,param):
                number = "141"
                msg = number + " SET TELESCOPE.CONFIG.ENVIRONMENT.TEMPERATURE="+str(int(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

	def set_telescope_config_environment_pressure(self,param):
                number = "142"
                msg = number + " SET TELESCOPE.CONFIG.ENVIRONMENT.PRESSURE="+str(int(param))+"\n"
                return_data = self.perform_query_set(number, msg)
                return return_data

	def set_object_solarsystem_object(self,param):
		number = "143"
		msg = number + " SET OBJECT.SOLARSYSTEM.OBJECT="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_object_solarsystem_object(self):
		number = "144"
		msg = number + " GET OBJECT.SOLARSYSTEM.OBJECT\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_object_solarsystem_moon(self,param):
		number = "145"
		msg = number + " SET OBJECT.SOLARSYSTEM.MOON="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_object_solarsystem_moon(self):
		number = "146"
		msg = number + " GET OBJECT.SOLARSYSTEM.MOON\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

	def set_object_tle_line1(self,param):
		number = "147"
		msg = number + " SET OBJECT.TLE.LINE1="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def set_object_tle_line2(self,param):
		number = "148"
		msg = number + " SET OBJECT.TLE.LINE2="+str(param)+"\n"
		return_data = self.perform_query_set(number, msg)
		return return_data

	def get_object_tle_name(self):
		number = "149"
		msg = number + " GET OBJECT.TLE.NAME\n"
		return_data = self.perform_query_get(number, msg)
		return return_data.split("=")[1].split("\n")[0].strip()

