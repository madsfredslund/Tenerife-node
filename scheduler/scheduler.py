"""
Fetch ORs from db and execute them by running script

"""

import time
import ORstrategy as or_strategy
from song_daemonize import Daemon
import scheduler_config
import getopt
import daily_logging_handler
import sys
import datetime
import send_song_mail
import song_timeclass
import master_config as m_conf
import beating_heart
import sys

clock = song_timeclass.TimeClass()

def SigINTHandler(signum, frame):
	global RUNNING
	RUNNING = False
	return

class ORsched(Daemon):
	"""
	Class inheriting the daemon-abilities from Daemon. Only run()-methods is overridden.
	"""
	
	def run(self):
		"""
		
		"""
		done_param = 0
		global RUNNING
		RUNNING = True

		val = beating_heart.start_heartbeat(job_id=m_conf.scheduler_id)

		strat = or_strategy.defStrat()
		i = 0
		while RUNNING:
			strat.handle_next()

#			if int(float(time.strftime("%H", time.gmtime()))) >= 9 and int(float(time.strftime("%H", time.gmtime()))) <= 16:
#				time.sleep(scheduler_config.check_time_sleeping)
#			else:
#				time.sleep(scheduler_config.check_time)

			### This should copy the content of the log file to old log file and clear it at 7 UTC.
			## Moves nightly output til obs log. 

			yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
      			folder_date = yesterday.strftime('%Y%m%d')
			output_log = "/home/obs/logs/scheduler_logs/" + str(folder_date)+"_obs.log"
			if int(float(time.strftime("%H", time.gmtime()))) == 9 and done_param == 0:
				daily_logging_handler.handle_log_files(scheduler_config.outstream, output_log)
				done_param = 1
				#sys.exit("%s The scheduler was automatically stopped..." % clock.timename())
			if done_param == 1 and int(float(time.strftime("%H", time.gmtime()))) > 9:
				done_param = 0

			if i % 1000 == 0:
				print clock.timename(), "The scheduler was alive"
				sys.stdout.flush()
			i += 1

			time.sleep(scheduler_config.check_time)


def main():
	"""
	Parse command-line parameters, and start daemon
	"""



	daemon = ORsched(scheduler_config.pidfile, stdout=scheduler_config.outstream, stderr=scheduler_config.outstream)
	try:
		opts, list = getopt.getopt(sys.argv[1:], 'st')
	except getopt.GetoptError, e:
		print("Bad options provided!")
		sys.exit()

	for opt, a in opts:
		if opt == "-s":
			try:
				pid_number = open(scheduler_config.pidfile,'r').readline()
				if pid_number:
               				sys.exit('Daemon is already running!')
         		except Exception, e:
            			pass

			print("Starting daemon...!")
			daemon.start()
		elif opt == "-t":
			daemon.stop()
			print "The daemon is stoped!"
		else:
			print("Option %s not supported!" % (opt))



if __name__=='__main__':
	try:
		main()
	except Exception, e:
		print e
		print "The scheduler has crashed at: ", clock.obstimeUT()
		send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Scheduler Crash!",message="The scheduler daemon has crashed!\n\nCheck the log file to see why!\n\nMaybe a simple restart helps!!\nLog onto hw as the user obs and type\nor_scheduler -s\nThis should start the scheduler. Check the log file /home/obs/logs/or_scheduler.log if it starts correctly.")

		send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The scheduler daemon was stopped for some reason. You got mail!")

