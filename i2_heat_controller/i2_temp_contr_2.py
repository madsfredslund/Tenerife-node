import socket
import time
import song_timeclass

clock = song_timeclass.TimeClass()

class heat_controler(object):

	def __init__(self):		

		#IP = "10.12.14.96"	# IFA IP
		IP = "10.8.0.33"	# SONG IP
		PORT= 4003

		self.path = "/tmp/"

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.settimeout(5)

		try:
			self.sock.connect((IP,PORT))
		except Exception, e:
			print clock.timename(), e

		try:
			self.sock.send("\r")
		except Exception, e:
			print clock.timename(), e

		time.sleep(1)
		callback = self.sock.recv(1024)


	def get_status(self):
		try:
			self.sock.send("stat?\r")
		except Exception, e:
			print clock.timename(), e

		time.sleep(1.0)

		callback = self.sock.recv(4096)
		callback = callback.strip()

		try:
			self.sock.close()
		except Exception, e:
			print clock.timename(), e

		a = []
		for line in callback:
			linje = line.replace('\r\r',', ')
			linje = linje.replace('\r',', ')
			a.append(linje)

		if a[7] == '1':
			print clock.timename(), "Status: Enabled!"
			return_value = 1
		elif a[7] == '0':
			print clock.timename(), "Status: Disabled!"
			return_value = 0
		else:
			return_value = -1

		return return_value

	def get_tact(self):
		try:
			self.sock.send("tact?\r")
		except Exception, e:
			print e

		time.sleep(1.0)

		callback = self.sock.recv(4096)

		file_tmp = open(self.path + "output.txt", "w")
		file_tmp.write(callback.strip())
		file_tmp.close()

		try:
			self.sock.close()
		except Exception, e:
			print e

		a = []
		file_tmp = open(self.path + "output.txt", "r")
		for line in file_tmp:
			linje = line.replace('\r\r',', ')
			linje = linje.replace('\r',', ')
			a.append(linje)

		liste = a[0].split(',')[1].split(' ')

		return liste[2]

	def get_tset(self):
		try:
			self.sock.send("tset?\r")
		except Exception, e:
			print clock.timename(), e

		time.sleep(1.0)

		callback = self.sock.recv(4096)

		file_tmp = open(self.path + "output.txt", "w")
		file_tmp.write(callback.strip())
		file_tmp.close()

		try:
			self.sock.close()
		except Exception, e:
			print clock.timename(), e

		a = []
		file_tmp = open(self.path + "output.txt", "r")
		for line in file_tmp:
			linje = line.replace('\r\r',', ')
			linje = linje.replace('\r',', ')
			a.append(linje)

		liste = a[0].split(',')[1].split(' ')

		return liste[2]

	def get_config(self):
		try:
			self.sock.send("config?\r")
		except Exception, e:
			print clock.timename(), e

		time.sleep(1.0)

		callback = self.sock.recv(4096)

		file_tmp = open(self.path + "output.txt", "w")
		file_tmp.write(callback.strip())
		file_tmp.close()


		try:
			self.sock.close()
		except Exception, e:
			print clock.timename(), e

		a = []
		file_tmp = open(self.path + "output.txt", "r")
		for line in file_tmp:
			linje = line.replace('\r\r',', ')
			linje = linje.replace('\r',', ')
			a.append(linje)

		file_tmp.close()

		liste = a[0].split(',') 

		for j in liste:
			print clock.timename(), j

		return 1

	def set_tset(self,temp):
		try:
			self.sock.send("tset=%s\r" % str(temp))
		except Exception, e:
			print clock.timename(), e

		time.sleep(1.0)

		callback = self.sock.recv(4096)

		file_tmp = open(self.path + "output.txt", "w")
		file_tmp.write(callback.strip())
		file_tmp.close()

		try:
			self.sock.close()
		except Exception, e:
			print clock.timename(), e

		a = []
		file_tmp = open(self.path + "output.txt", "r")
		for line in file_tmp:
			linje = line.replace('\r\r',', ')
			linje = linje.replace('\r',', ')
			a.append(linje)

		liste = a[0].split(',')

		print clock.timename(), liste[0]

		return 1

	def set_ens(self,state):
		
		status = self.get_status()
		if int(status) == 1 and int(state) == 1:
			print clock.timename(), "The heater is enabled"
		elif int(status) == 0 and int(state) == 0:
			print clock.timename(), "The heater is Disabled"

		else:
			self.__init__()
			try:
				self.sock.send("ens\r")
			except Exception, e:
				print clock.timename(), e

			time.sleep(1.0)

			callback = self.sock.recv(4096)

			file_tmp = open(self.path + "output.txt", "w")
			file_tmp.write(callback.strip())
			file_tmp.close()

			try:
				self.sock.close()
			except Exception, e:
				print clock.timename(), e

			a = []
			file_tmp = open(self.path + "output.txt", "r")
			for line in file_tmp:
				linje = line.replace('\r\r',', ')
				linje = linje.replace('\r',', ')
				a.append(linje)

			liste = a[0].split(',')

			print clock.timename(), liste[0]

		self.__init__()
		self.get_status()

		return 1
