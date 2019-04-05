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
import update_song_database
import song_database_tables
import i2_temp_contr
import i2_write2db_config
import daily_logging_handler
import master_config as m_conf
import tmon
import psycopg2
import beating_heart
import song_timeclass

clock = song_timeclass.TimeClass()

class i2_write2db_daemon(Daemon):
   """
      @brief: This class inherits Daemon from song.py and daemonizes the code.
   """
   def run(self):
      """
         @brief: This function overwrites the run function in song.py.
      """
      global RUNNING
      RUNNING = True

      val = beating_heart.start_heartbeat(job_id=m_conf.i2_write_to_db_id)

      print "Starting loop..."
      done_param = 0
      ins_tid = time.time() - 60.5
      temperatures = ""
      while RUNNING:

	tid = time.time()
	if tid - ins_tid >= 60.:
		 ins_tid = time.time()
		 try:
		 	tmp_temp_set = i2_temp_contr.heat_controler().get_tset()
		 except Exception,e:
			tmp_temp_set = 0
			print clock.timename(), e
		 try:	 
		 	tmp_temp_act = i2_temp_contr.heat_controler().get_tact()
		 except Exception,e:
			tmp_temp_act = 0
			print clock.timename(), e
		 try:
		 	tmp_status = i2_temp_contr.heat_controler().get_status()
		 except Exception,e:
			tmp_status = 0
			print clock.timename(), e
	
		 if tmp_status != 1:
			 try:
			 	i2_temp_contr.heat_controler().set_tset(m_conf.i2_set_temp)
				i2_temp_contr.heat_controler().set_ens(1)
				time.sleep(5)
			 except Exception,e:
				tmp_status = 0
				print clock.timename(), e	
			 try:
			 	tmp_status = i2_temp_contr.heat_controler().get_status()
			 except Exception,e:
				tmp_status = 0
				print clock.timename(), e

		 try:
		 	update_song_database.update("coude_unit", ["iodine_temp_set","iodine_temp_read", "iodine_heater_on"], [tmp_temp_set, tmp_temp_act, tmp_status], "coude_unit_id")
		 except Exception, e:
			print clock.timename(), "Could not insert or update the database: ", e


		 if int(float(time.strftime("%H", time.gmtime()))) == 12 and done_param == 0:
			daily_logging_handler.handle_log_files(i2_write2db_config.outstream, i2_write2db_config.outstream_old)
			done_param = 1
		 if done_param == 1 and int(float(time.strftime("%H", time.gmtime()))) > 12:
			done_param = 0

		 ### Printing out the tmon temperatures once every minute.
		 print clock.timename(), temperatures
		
	try:
		temperatures = tmon.get_tmon_temps()
	except Exception,e:
		print clock.timename(), e
		print clock.timename(), "Could not get tmon temperatures..."
		
	try:
		conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
		curr = conn.cursor()
		i = 0
		for temp in temperatures:
			if float(temp) > 100. or float(temp) < -100.:
				temp = -99
			if i > 0:
				temps = temps + ", " + str(temp)
			else:
				temps = str(temp)
			i += 1

		parameters = "box_id, temperature_1, temperature_2, temperature_3, temperature_4, temperature_5, temperature_6, temperature_7, temperature_8, temperature_9, temperature_10, temperature_11, temperature_12, temperature_13, temperature_14, temperature_15, temperature_16, power_1, power_2, power_3, power_4, power_5, power_6, power_7, power_8, humidity_1, humidity_2, sensor_1, sensor_2, sensor_3, aircon_set_temp, aircon_actual_temp, ins_at"

		ins_values = "2, " + temps + ", 0,0,0,0,0,0,0,0,0,0,'off','off','off',0,0, '%s' " % time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
		stmt = "INSERT INTO house_hold (%s) VALUES (%s)" % (parameters, ins_values)
		curr.execute(stmt)		
		conn.commit()
		curr.close()		
	except Exception,e:
		print clock.timename(), e
		print clock.timename(), "Could not insert temperatures into database..."

	time.sleep(5) 
	
			
def main():
   """
      @brief: This is the main part of the code that starts up everything else. 
   """

   daemon = i2_write2db_daemon(i2_write2db_config.pidfile, stdout=i2_write2db_config.outstream, stderr=i2_write2db_config.outstream)
   try:
      opts, list = getopt.getopt(sys.argv[1:], 'st')
   except getopt.GetoptError, e:
      print clock.timename(), "Bad options provided!"
      sys.exit()

   for opt, a in opts:
      if opt == "-s":
         try:
            pid_number = open(i2_write2db_config.pidfile,'r').readline()
            if pid_number:
               sys.exit('Daemon is already running!')
         except Exception, e:
            pass
         print("Starting daemon...")
	 time.sleep(1)
         daemon.start()
      elif opt == "-t":
	 global RUNNING
         RUNNING = False
         daemon.stop()
         #print("Use python2.5 stop_camera_server.py to stop the daemon!")
         print "The daemon is stoped!"
      elif opt == "-l":
         print("Logging is turned off")
      else:
         print("Option %s not supported!" % (opt))

if __name__ == "__main__":
   main()

