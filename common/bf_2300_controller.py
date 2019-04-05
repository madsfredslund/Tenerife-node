import socket
import sys
import time
import numpy
import update_song_database
import song_database_tables

class bf_reader(object):
	"""
		@brief: This class will handle reading of states on the BF 2300 I/O controller.
	"""   
	def __init__(self):
		"""
			@brief: This function will will make the connection to the BF 2300 controller.
		"""	
		self.IP = "10.8.0.18" # IFA IP adress of bf2300
		self.PORT= 50000

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		try:
			self.sock.connect((self.IP,self.PORT))
		except Exception, e:
			print "Connection error to the BF-2300 controller"
			print e	

	def read_input(self, input_number):
		"""
			@brief: This function will check the state of an input and return 1 or 0 corresponding to the state.
		"""
		##### Message to parse to the bf-2300 to read digital I/O state:
		empty_arr = "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
		msg = "\xf0\xf0\x00\x01" + empty_arr + empty_arr +"\xf0\xf0"
		#########################

		#crc_sum = "\x3f" # THIS IS THE ONE THAT WORKS WITH only \x00 for the empty arrays!!!!!

		crc_value = 0
		for i in msg:
			crc_value = crc_value + ord(i)

		crc_sum = chr(256 - (crc_value % 256))

		#print "CRC value: ", crc_sum, ",", hex(256 - (crc_value % 256)), ",", (256 - (crc_value % 256)) 

		try:
			self.sock.send(msg+crc_sum)
		except Exception, e:
			print e

		callback = self.sock.recv(1400)

		if ord(callback[2]) == 0 and ord(callback[3]) == 2:

			#inputs = ["IN-1: ","IN-2: ","IN-3: ","IN-4: ","IN-5: ","IN-6: ","IN-7: ","IN-8: ","IN-9: ","IN-10: ","IN-11: ","IN-12: "]

			if input_number:

				if ord(callback[3 + input_number]) == 0:
					return_value = 0 # High
					if str(input_number) == '1':
						try:
							update_song_database.update("tel_dome", ["side_port_1"], [0], "tel_dome_id") 
						except Exception, e:
							print "Could not update database with side_port_1 status ", e
					elif str(input_number) == '2':
						try:
							update_song_database.update("tel_dome", ["side_port_2"], [0], "tel_dome_id")  
						except Exception, e:
							print "Could not update database with side_port_2 status ", e
					elif str(input_number) == '3':
						try:
					  		update_song_database.update("tel_dome", ["side_port_3"], [0], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_3 status ", e
					elif str(input_number) == '4':
						try:
					  		update_song_database.update("tel_dome", ["side_port_4"], [0], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_4 and side_port_7 status ", e
					elif str(input_number) == '5':
						try:
					  		update_song_database.update("tel_dome", ["side_port_5"], [0], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_5 and status ", e
					elif str(input_number) == '6':
						try:
					  		update_song_database.update("tel_dome", ["side_port_6"], [0], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_6 status ", e
					elif str(input_number) == '7':
						try:
					  		update_song_database.update("tel_dome", ["side_port_7"], [0], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_7 status ", e
					else:
						print "Something was wrong: input_number was not 1-7", e
					
				elif ord(callback[3 + input_number]) == 1:
					return_value = 1 # Low
					if str(input_number) == '1':
						try:
							update_song_database.update("tel_dome", ["side_port_1"], [1], "tel_dome_id") 
						except Exception, e:
							print "Could not update database with side_port_1 status ", e
					elif str(input_number) == '2':
						try:
							update_song_database.update("tel_dome", ["side_port_2"], [1], "tel_dome_id")  
						except Exception, e:
							print "Could not update database with side_port_2 status ", e
					elif str(input_number) == '3':
						try:
					  		update_song_database.update("tel_dome", ["side_port_3"], [1], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_3 status ", e
					elif str(input_number) == '4':
						try:
					  		update_song_database.update("tel_dome", ["side_port_4"], [1], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_4 and status ", e
					elif str(input_number) == '5':
						try:
					  		update_song_database.update("tel_dome", ["side_port_5"], [1], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_5 and status ", e
					elif str(input_number) == '6':
						try:
					  		update_song_database.update("tel_dome", ["side_port_6"], [1], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_6 status ", e
					elif str(input_number) == '7':
						try:
					  		update_song_database.update("tel_dome", ["side_port_7"], [1], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_7 status ", e
					else:
						print "Something was wrong: input_number was not 1-7", e
				else:
					return_value = 2


		else:
			print "Error msg: ", repr(callback[2]), repr(callback[3])

		try:
			#print "Closing socket!"
			self.sock.close()
		except Exception, e:
			print e

		return return_value

	def read_all_side_ports(self):
		"""
			@brief: This function will check the state of all input and return 1 or 0 corresponding to the state.
		"""
		##### Message to parse to the bf-2300 to read digital I/O state:
		empty_arr = "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
		msg = "\xf0\xf0\x00\x01" + empty_arr + empty_arr +"\xf0\xf0"
		#########################

		#crc_sum = "\x3f" # THIS IS THE ONE THAT WORKS WITH only \x00 for the empty arrays!!!!!

		crc_value = 0
		for i in msg:
			crc_value = crc_value + ord(i)

		crc_sum = chr(256 - (crc_value % 256))

		#print "CRC value: ", crc_sum, ",", hex(256 - (crc_value % 256)), ",", (256 - (crc_value % 256)) 

		try:
			self.sock.send(msg+crc_sum)
		except Exception, e:
			print e

		callback = self.sock.recv(1400)

		if ord(callback[2]) == 0 and ord(callback[3]) == 2:

			#inputs = ["IN-1: ","IN-2: ","IN-3: ","IN-4: ","IN-5: ","IN-6: ","IN-7: ","IN-8: ","IN-9: ","IN-10: ","IN-11: ","IN-12: "]

			for input_number in (numpy.arange(7)+1):

				if ord(callback[3 + input_number]) == 0:
					print "Side port ", input_number, " is: Closed" # High
					if str(input_number) == '1':
						try:
							update_song_database.update("tel_dome", ["side_port_1"], [0], "tel_dome_id") 
						except Exception, e:
							print "Could not update database with side_port_1 status ", e
					elif str(input_number) == '2':
						try:
							update_song_database.update("tel_dome", ["side_port_2"], [0], "tel_dome_id")  
						except Exception, e:
							print "Could not update database with side_port_2 status ", e
					elif str(input_number) == '3':
						try:
							update_song_database.update("tel_dome", ["side_port_3"], [0], "tel_dome_id")  
						except Exception, e:
							print "Could not update database with side_port_3 status ", e
					elif str(input_number) == '4':
						try:
					  		update_song_database.update("tel_dome", ["side_port_4"], [0], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_4 status ", e
					elif str(input_number) == '5':
						try:
					  		update_song_database.update("tel_dome", ["side_port_5"], [0], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_5 status ", e
					elif str(input_number) == '6':
						try:
					  		update_song_database.update("tel_dome", ["side_port_6"], [0], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_6 status ", e
					elif str(input_number) == '7':
						try:
					  		update_song_database.update("tel_dome", ["side_port_7"], [0], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_7 status ", e
					else:
						print "Something was wrong: input_number was not 1-7", e

				elif ord(callback[3 + input_number]) == 1:
					print "Side port ", input_number, " is: Open" # Low
					if str(input_number) == '1':
						try:
							update_song_database.update("tel_dome", ["side_port_1"], [1], "tel_dome_id") 
						except Exception, e:
							print "Could not update database with side_port_1 status ", e
					elif str(input_number) == '2':
						try:
							update_song_database.update("tel_dome", ["side_port_2"], [1], "tel_dome_id")  
						except Exception, e:
							print "Could not update database with side_port_2 status ", e
					elif str(input_number) == '3':
						try:
							update_song_database.update("tel_dome", ["side_port_3"], [1], "tel_dome_id")  
						except Exception, e:
							print "Could not update database with side_port_3 status ", e
					elif str(input_number) == '4':
						try:
					  		update_song_database.update("tel_dome", ["side_port_4"], [1], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_4 status ", e
					elif str(input_number) == '5':
						try:
					  		update_song_database.update("tel_dome", ["side_port_5"], [1], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_5 status ", e
					elif str(input_number) == '6':
						try:
					  		update_song_database.update("tel_dome", ["side_port_6"], [1], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_6 status ", e
					elif str(input_number) == '7':
						try:
					  		update_song_database.update("tel_dome", ["side_port_7"], [1], "tel_dome_id") 
					  	except Exception, e:
					        	print "Could not update database with side_port_7 status ", e
					else:
						print "Something was wrong: input_number was not 1-7", e
				else:
					print "Side port ", input_number, " is: Error" # Low

		else:
			print "Error msg: ", repr(callback[2]), repr(callback[3])

		try:
			#print "Closing socket!"
			self.sock.close()
		except Exception, e:
			print e

		return 1




		
