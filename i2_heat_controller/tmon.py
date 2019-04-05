import socket
import time
import song_timeclass

clock = song_timeclass.TimeClass()

IP = "10.8.0.33"	# SONG IP
PORT= 4001

def get_tmon_temps():

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(5)

	try:
		sock.connect((IP,PORT))
	except Exception, e:
		print clock.timename(), "Problem connecting to temperature monitor box!"
		print clock.timename(), e


	callback = sock.recv(2048)
	flag = 0
	while flag != 1:
		if "$ADC" in callback and "*" in callback and len(callback.split("\r\n")) == 2:
			flag = 1
			break
		callback = callback + sock.recv(2048)
		time.sleep(0.1)

#	print callback
	arr = str(callback).split("*")[0].split(",")
	temps = []
	for i in range(1,17):
		temps.append(0.00006023*(int(arr[i],16) - 4535495.0))

	return temps


