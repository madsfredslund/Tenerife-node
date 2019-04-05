#!/usr/bin/python

'''
Created on 12/04/2010

	This module is the "server" end of the communication with the telescope. When this daemon is running it can be called through the client module. 
	Functions from the astelco.py module needs to be called from this daemon and needs to be defined here. 
	

@author: Mads Fredslund Andersen
'''
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib
import os
import syslog
import socket
import sys
import time
from song_daemonize import Daemon
import astelco_TSI
import getopt
import song_telescope_config
import thread
import update_song_database
from easygui import *
import song_timeclass
import smtplib
import string
import daily_logging_handler
import pdu_module
import master_config as m_conf
import beating_heart
import psycopg2
import send_song_mail
import numpy
import comm2tcs_read
import comm2tcs_write


clock = song_timeclass.TimeClass()
pdu_handle = pdu_module.APC()
gettsi = comm2tcs_read.GET_TSI()
settsi = comm2tcs_write.SET_TSI()

#################
#################
# This falg indicates if something is currently changing or being executed
global performing_falg
performing_falg = 0
#################
#################

class RequestHandler(SimpleXMLRPCRequestHandler):
    """Some XMLPRC-magic here. This is needed, and cannot be left out. Check the documentation?"""
    rpc_paths = ('/RPC2')
    
def is_alive():
    """This function will return 1 if the daemon is running."""
    return 1

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



###################################################################
###################################################################
##################     TSI     ####################################
###################################################################
###################################################################

def get_connid(sender):
	return conn.connid

def shutdown_connection(sender):
	try:	
		value = conn.close_connection()
	except Exception, e:
		print e

	if value == 1:
		return "Connection was closed!"
	else:
		return "An error occurred!"

def set_telescope_ready(sender, param):
	telescope_ready_state = ''
	try:
		telescope_ready_state = conn.get_telescope_state()
	except Exception, e:
		print e
	if float(telescope_ready_state) != float(param) and int(float(param)) in [0,1]:

		if float(telescope_ready_state) == float(0.0) and float(param) == float(1.0):
			try:
				update_song_database.update("tel_dome", ["tel_ready_state"], [int(2)], "tel_dome_id")
			except Exception,e:
				print "The telescope ready state was not updated in the database: ", e
		elif float(telescope_ready_state) == float(1.0) and float(param) == float(0.0):
			try:
				update_song_database.update("tel_dome", ["tel_ready_state"], [int(3)], "tel_dome_id")
			except Exception,e:
				print "The telescope ready state was not updated in the database: ", e

		try:	
			return_data = conn.set_telescope_ready(param)
		except Exception, e:
			print e
		
		if 'COMPLETE' in return_data:
			try:
				update_song_database.update("tel_dome", ["tel_ready_state"], [int(float(param))], "tel_dome_id")
			except Exception,e:
				print "The telescope ready state was not updated in the database: ", e
		return "done"

	elif float(telescope_ready_state) == float(param) and int(float(param)) in [0,1]:
		return "done"	
	else:
		return "Something went wrong with setting the telescope ready state"

def get_telescope_state(sender):
	e = ''
	try:
		telescope_state = conn.get_telescope_state()
	except Exception, e:
		print e
	if e == '':
		try:
			update_song_database.update("tel_dome", ["tel_ready_state"], [int(float(telescope_state))], "tel_dome_id")
		except Exception,e:
			print "The telescope ready state was not updated in the database: ", e
	return telescope_state

def get_telescope_motion_state(sender):
	e = ''
	try:
		telescope_motion_state = conn.get_telescope_motion_state()
	except Exception, e:
		print e
	if e == '':
		try:
			update_song_database.update("tel_dome", ["tel_motion_state"], [int(float(telescope_motion_state))], "tel_dome_id")
		except Exception,e:
			print "The telescope motion state was not updated in the database: ", e
	return telescope_motion_state

def set_telescope_stop(sender):
	telescope_motion_state = ''
	try:
		telescope_motion_state = conn.get_telescope_motion_state()
	except Exception, e:
		print e
	if float(telescope_motion_state) != float(0):
		try:	
			return_data = conn.set_telescope_stop()
		except Exception, e:
			print e

		print return_data
		if 'COMPLETE' in return_data:
			try:
				update_song_database.update("tel_dome", ["tel_motion_state"], [0], "tel_dome_id")
			except Exception,e:
				print "The telescope motion state was not updated in the database: ", e

		return "done"

	elif float(telescope_motion_state) == float(0):
		return "done"		
	else:
		return "Something went wrong with stopping the telescope"

def get_telescope_status_global(sender):
	try:
		telescope_status_global = conn.get_telescope_status_global()
	except Exception, e:
		print e
	return telescope_status_global

def get_telescope_status_list(sender):
	try:
		telescope_status_list = conn.get_telescope_status_list()
	except Exception, e:
		print e
	return telescope_status_list

def set_telescope_clear_panic(sender):
	e = ""
	try:
		error_value = conn.get_telescope_status_global()
	except Exception, e:
		print e
	if e =="":
		try:	
			telescope_clear = conn.set_telescope_status_clear_panic(error_value)
		except Exception, e:
			print e

	return telescope_clear	

def set_telescope_clear_error(sender):
	e = ""
	try:
		error_value = conn.get_telescope_status_global()
	except Exception, e:
		print e
	if e =="":
		try:	
			telescope_clear = conn.set_telescope_status_clear_error(error_value)
		except Exception, e:
			print e

	return telescope_clear	

def set_telescope_clear_warning(sender):
	e = ""
	try:
		error_value = conn.get_telescope_status_global()
	except Exception, e:
		print e
	if e =="":
		try:	
			telescope_clear = conn.set_telescope_status_clear_warning(error_value)
		except Exception, e:
			print e

	return telescope_clear	

def set_telescope_clear_info(sender):
	e = ""
	try:
		error_value = conn.get_telescope_status_global()
	except Exception, e:
		print e
	if e =="":
		try:	
			telescope_clear = conn.set_telescope_status_clear_info(error_value)
		except Exception, e:
			print e

	return telescope_clear		

def set_telescope_config_load(sender):
	e = ""
	try:
		return_value = conn.set_telescope_config_load()
	except Exception, e:
		print e

	return return_value	

def set_telescope_config_environment_temperature(sender,param):
	e = ""
	try:
		return_value = conn.set_telescope_config_environment_temperature(param)
	except Exception, e:
		print e

	return return_value	

def set_telescope_config_environment_pressure(sender,param):
	e = ""
	try:
		return_value = conn.set_telescope_config_environment_pressure(param)
	except Exception, e:
		print e

	return return_value



def set_object_equatorial_epoch(sender,param):
	if int(float(param)) in range(1950, 2101):	
		try:	
			object_equatorial_epoch = conn.set_object_equatorial_epoch(param)
		except Exception, e:
			print e
		return "done"
	else:
		return "The specified epoch was invalid. Must be between 1950 and 2050"

def get_object_equatorial_epoch(sender):
	try:
		object_equatorial_epoch = conn.get_object_equatorial_epoch()
	except Exception, e:
		print e
	return object_equatorial_epoch

def set_object_equatorial_equinox(sender,param):
	if int(float(param)) in range(1950, 2101):	
		try:	
			object_equatorial_equinox = conn.set_object_equatorial_equinox(param)
		except Exception, e:
			print e
		return "done"
	else:
		return "The specified equinox was invalid. Must be between 1950 and 2050"

def get_object_equatorial_equinox(sender):
	try:
		object_equatorial_equinox = conn.get_object_equatorial_equinox()
	except Exception, e:
		print e
	return object_equatorial_equinox

def set_object_solarsystem_object(sender,param):
	try:
		object_solarsystem_object= conn.set_object_solarsystem_object(param)
	except Exception, e:
		print e
	else:
		return object_solarsystem_object

def get_object_solarsystem_object(sender):
	try:
		object_solarsystem_object = conn.get_object_solarsystem_object()
	except Exception, e:
		print e
	else:
		return object_solarsystem_object

def set_object_solarsystem_moon(sender,param):
	try:
		object_solarsystem_moon = conn.set_object_solarsystem_moon(param)
	except Exception, e:
		print e
	else:
		return object_solarsystem_moon

def get_object_solarsystem_moon(sender):
	try:
		object_solarsystem_moon = conn.get_object_solarsystem_moon()
	except Exception, e:
		print e
	else:
		return object_solarsystem_moon

def set_object_tle_line1(sender,param):
	try:
		object_tle_line1 = conn.set_object_tle_line1(param)
	except Exception, e:
		print e
	else:
		return object_tle_line1

def set_object_tle_line2(sender,param):
	try:
		object_tle_line2 = conn.set_object_tle_line2(param)
	except Exception, e:
		print e
	else:
		return object_tle_line2

def get_object_tle_name(sender):
	try:
		object_tle_name = conn.get_object_tle_name()
	except Exception, e:
		print e
	else:
		return object_tle_name

def set_object_equatorial_ra(sender,param):
	if float(param) >= 0.0 or float(param) <= 24.0:	
		try:	
			return_data = conn.set_object_equatorial_ra(param)
		except Exception, e:
			print e

		print return_data
	#### THIS SHOULD UPDATE THE OBJ_RA ENTRY IN THE DATABASE
		if 'COMPLETE' in return_data:
			try:
				update_song_database.update("tel_dome", ["obj_ra"], [float(param)], "tel_dome_id")
			except Exception,e:
				print "The object ra was not updated in the database: ", e

		return "done"
	else:
		return "The specified ra was invalid. Must be between 0 and 24"

def get_object_equatorial_ra(sender):
	e = ''
	try:
		object_equatorial_ra = conn.get_object_equatorial_ra()
	except Exception, e:
		print e
	if e == '':
		try:
			update_song_database.update("tel_dome", ["obj_ra"], [float(object_equatorial_ra)], "tel_dome_id")
		except Exception,e:
			print "The object ra was not updated in the database: ", e
	return object_equatorial_ra

def set_object_equatorial_dec(sender,param):
	if float(param) >= -90.0 or float(param) <= 90.0:		
		try:	
			return_data = conn.set_object_equatorial_dec(param)
		except Exception, e:
			print e

		print return_data
	#### THIS SHOULD UPDATE THE OBJ_DEC ENTRY IN THE DATABASE
		if 'COMPLETE' in return_data:
			try:
				update_song_database.update("tel_dome", ["obj_dec"], [float(param)], "tel_dome_id")
			except Exception,e:
				print "The object dec was not updated in the database: ", e

		return "done"
	else:
		return "The specified dec was invalid. Must be between -90 and 90"

def get_object_equatorial_dec(sender):
	e = ''
	try:
		object_equatorial_dec = conn.get_object_equatorial_dec()
	except Exception, e:
		print e
	if e == '':
		try:
			update_song_database.update("tel_dome", ["obj_dec"], [float(object_equatorial_dec)], "tel_dome_id")
		except Exception,e:
			print "The object dec was not updated in the database: ", e
	return object_equatorial_dec



def set_object_equatorial_ra_pm(sender,param):
	if float(param) >= 0.0:	
		try:	
			return_data = conn.set_object_equatorial_ra_pm(param)
		except Exception, e:
			print e
		print return_data
	
	return "done"

def get_object_equatorial_ra_pm(sender):
	e = ''
	try:
		object_equatorial_ra_pm = conn.get_object_equatorial_ra_pm()
	except Exception, e:
		print e
	
	return object_equatorial_ra_pm

def set_object_equatorial_dec_pm(sender,param):
	if float(param) >= 0.0:
		try:	
			return_data = conn.set_object_equatorial_dec_pm(param)
		except Exception, e:
			print e
		print return_data
	return "done"

def get_object_equatorial_dec_pm(sender):
	e = ''
	try:
		object_equatorial_dec_pm = conn.get_object_equatorial_dec_pm()
	except Exception, e:
		print e
	return object_equatorial_dec_pm

def set_object_horizontal_alt(sender,param):
	if float(param) >= 15.0 and float(param) <= 90.0:
		try:	
			return_data = conn.set_object_horizontal_alt(param)
		except Exception, e:
			print e
		print return_data
	return "done"

def set_object_horizontal_az(sender,param):
	if float(param) >= 0.0 and float(param) <= 360.0:
		try:	
			return_data = conn.set_object_horizontal_az(param)
		except Exception, e:
			print e
		print return_data
	return "done"

#################################################################

def set_pointing_track(sender,param):
	pointing_track_state = ''
	try:
		pointing_track_state = conn.get_pointing_track()
	except Exception, e:
		print e

	if str(pointing_track_state) != '' and float(pointing_track_state) != float(param):
		if int(float(param)) in range(0,9):
#			if int(float(param)) != 8:
#				### Write to db that telescope is moving ###
#				try:
#					update_song_database.update("tel_dome", ["tel_motion_state"], [int(5)], "tel_dome_id")
#				except Exception,e:
#					print "The telescope motion state was not updated in the database: ", e

			try:	
				return_data = conn.set_pointing_track(param)
			except Exception, e:
				print e

#			if int(float(param)) != 8:
#				if return_data == "stopped":
#					try:
#						update_song_database.update("tel_dome", ["tel_motion_state"], [int(0)], "tel_dome_id")
#					except Exception,e:
#						print "The telescope motion state was not updated in the database: ", e
#
#				elif return_data == "started":
#					try:
#						update_song_database.update("tel_dome", ["tel_motion_state"], [int(1)], "tel_dome_id")
#					except Exception,e:
#						print "The telescope motion state was not updated in the database: ", e
#
#				elif return_data == "done":
#					try:
#						update_song_database.update("tel_dome", ["tel_motion_state"], [int(0)], "tel_dome_id")
#					except Exception,e:
#						print "The telescope motion state was not updated in the database: ", e

			return "done"
		else:
			return "The specified track parameter was invalid. Must be between 0 and 8"
	elif float(pointing_track_state) == float(param):
		return "done"
	else:
		return "Something went wrong with setting the tracking"

def get_pointing_track(sender):
	try:
		pointing_track = conn.get_pointing_track()
	except Exception, e:
		print e
	if float(pointing_track) == float(0.0):
		try:
			update_song_database.update("tel_dome", ["tel_motion_state"], [int(0)], "tel_dome_id")
		except Exception,e:
			print "The telescope motion state was not updated in the database: ", e
	elif float(pointing_track) == float(1.0):
		try:
			update_song_database.update("tel_dome", ["tel_motion_state"], [int(1)], "tel_dome_id")
		except Exception,e:
			print "The telescope motion state was not updated in the database: ", e
	elif float(pointing_track) == float(2.0):
		try:
			update_song_database.update("tel_dome", ["tel_motion_state"], [int(2)], "tel_dome_id")
		except Exception,e:
			print "The telescope motion state was not updated in the database: ", e
	return pointing_track

def get_pointing_setup(sender):
	e = ''
	try:
		pointing_setup = conn.get_pointing_setup_use_port()
	except Exception, e:
		print e

	return pointing_setup

def set_pointing_setup(param,sender):
	try:
		return_data = conn.set_pointing_setup_use_port(param)
	except Exception, e:
		print e

	if "COMMAND COMPLETE" in return_data:
		try:
			update_song_database.update("tel_dome", ["third_mirror"], [int(float(param))], "tel_dome_id")
		except Exception,e:
			print "The telescope M3 position was not updated in the database: ", e

	return pointing_setup

def get_pointing_setup_use_port(sender):
	e = ''
	try:
		pointing_setup = conn.get_pointing_setup_use_port()
	except Exception, e:
		print e
	if e == '':
		try:
			update_song_database.update("tel_dome", ["third_mirror"], [int(float(pointing_setup))], "tel_dome_id")
		except Exception,e:
			print "The telescope M3 position was not updated in the database: ", e

	return pointing_setup

def set_pointing_setup_use_port(param,sender):
	try:
		return_data = conn.set_pointing_setup_use_port(param)
	except Exception, e:
		print e

	if "COMMAND COMPLETE" in return_data:
		try:
			update_song_database.update("tel_dome", ["third_mirror"], [int(float(param))], "tel_dome_id")
		except Exception,e:
			print "The telescope M3 position was not updated in the database: ", e

	return pointing_setup


def get_pointing_model_calculate(sender):
	try:
		pointing_model_calculate = float(conn.get_pointing_model_calculate()) * 60. * 60.	# Converts to " in stead of degrees
	except Exception, e:
		print e
	return pointing_model_calculate

def set_pointing_model_calculate(param,sender):
	if int(param) in [1,2]:
		try:
			pointing_model_calculate = conn.set_pointing_model_calculate(param)
		except Exception, e:
			print e
		return pointing_model_calculate
	else:
		return "Parameter not 1 or 2"

def get_pointing_model_type(sender):
	try:
		pointing_model_type = conn.get_pointing_model_type()
	except Exception, e:
		print e
	return pointing_model_type

def get_pointing_model_file(sender):
	try:
		pointing_model_file = conn.get_pointing_model_file()
	except Exception, e:
		print e
	return pointing_model_file

def get_pointing_model_file_list(sender):
	try:
		pointing_model_file_list= conn.get_pointing_model_file_list()
	except Exception, e:
		print e
	return pointing_model_file_list

def set_pointing_model_file(param,sender):
	try:
		pointing_model_file = conn.set_pointing_model_file(param)
	except Exception, e:
		print e
	return pointing_model_file

def get_pointing_setup_use_port(sender):
	try:
		pointing_setup_use_port = conn.get_pointing_setup_use_port()
	except Exception, e:
		print e
	return pointing_setup_use_port

def set_pointing_setup_use_port(param,sender):
	try:
		pointing_setup_use_port = conn.set_pointing_setup_use_port(param)
	except Exception, e:
		print e
	return pointing_setup_use_port

def get_pointing_model_list(sender):
	try:
		pointing_model_list = conn.get_pointing_model_list()
	except Exception, e:
		print e
	return pointing_model_list

def set_pointing_model_type(param,sender):
	if int(param) in [0,1,2]:
		try:
			pointing_model_type = conn.set_pointing_model_type(param)
		except Exception, e:
			print e
		return pointing_model_type
	else:
		return "Parameter not 0, 1 or 2"

def set_pointing_model_add(param,sender):
	try:
		pointing_model_add = conn.set_pointing_model_add(param)
	except Exception, e:
		print e
	return pointing_model_add

def set_pointing_model_load(param,sender):
	if int(param) in [1,2]:
		try:
			pointing_model_load = conn.set_pointing_model_load(param)
		except Exception, e:
			print e
		return pointing_model_load
	else:
		return "Parameter not 1 or 2"

def set_pointing_model_save(param,sender):
	if int(param) in [1,2]:
		try:
			pointing_model_save = conn.set_pointing_model_save(param)
		except Exception, e:
			print e
		return pointing_model_save
	else:
		return "Parameter not 1 or 2"




def get_pointing_setup_dome_syncmode(sender):
	try:
		pointing_setup_dome_syncmode = conn.get_pointing_setup_dome_syncmode()
	except Exception, e:
		print e
	return pointing_setup_dome_syncmode

def set_pointing_setup_dome_syncmode(param,sender):
	if int(param) in [0,1,2,3,4,5]:
		try:
			pointing_setup_dome_syncmode = conn.set_pointing_setup_dome_syncmode(param)
		except Exception, e:
			print e
		return pointing_setup_dome_syncmode
	else:
		return "Parameter not 0, 1, 2, 3, 4, 5"

def get_pointing_setup_dome_max_deviation(sender):
	try:
		pointing_setup_dome_max_deviation = conn.get_pointing_setup_dome_max_deviation()
	except Exception, e:
		print e
	return pointing_setup_dome_max_deviation

def set_pointing_setup_dome_max_deviation(param,sender):
	if float(param) >= 0.0 and float(param) <= 360.0:
		try:
			pointing_setup_dome_max_deviation = conn.set_pointing_setup_dome_max_deviation(param)
		except Exception, e:
			print e
		return pointing_setup_dome_max_deviation
	else:
		return "Parameter not in range from 0 to 360!"

def get_pointing_setup_dome_offset(sender):
	try:
		pointing_setup_dome_offset = conn.get_pointing_setup_dome_offset()
	except Exception, e:
		print e
	return pointing_setup_dome_offset

def set_pointing_setup_dome_offset(param,sender):
	if float(param) >= 0.0 and float(param) <= 360.0:
		try:
			pointing_setup_dome_offset = conn.set_pointing_setup_dome_offset(param)
		except Exception, e:
			print e
		return pointing_setup_dome_offset
	else:
		return "Parameter not in range from 0 to 360!"



def get_pointing_setup_focus_syncmode(sender):
	try:
		pointing_setup_focus_syncmode = conn.get_pointing_setup_focus_syncmode()
	except Exception, e:
		print e
	return pointing_setup_focus_syncmode

def set_pointing_setup_focus_syncmode(param,sender):
	if int(param) in range(127):
		try:
			pointing_setup_focus_syncmode = conn.set_pointing_setup_focus_syncmode(param)
		except Exception, e:
			print e
		return pointing_setup_focus_syncmode
	else:
		return "Parameter not 0, 1, 2,..., 64, 65"


def get_pointing_setup_derotator_syncmode(sender):
	try:
		pointing_setup_derotator_syncmode = conn.get_pointing_setup_derotator_syncmode()
	except Exception, e:
		print e
	return pointing_setup_derotator_syncmode

def set_pointing_setup_derotator_syncmode(param,sender):
	if int(param) in range(7):
		try:
			pointing_setup_derotator_syncmode = conn.set_pointing_setup_derotator_syncmode(param)
		except Exception, e:
			print e
		return pointing_setup_derotator_syncmode
	else:
		return "Parameter not 0, 1, 2,..., 6"

def get_pointing_setup_mechanical_derotator_syncmode(sender):
	try:
		pointing_setup_mechanical_derotator_syncmode = conn.get_pointing_setup_mechanical_derotator_syncmode()
	except Exception, e:
		print e
	return pointing_setup_mechanical_derotator_syncmode

def set_pointing_setup_mechanical_derotator_syncmode(param,sender):
	if int(param) in range(7):
		try:
			pointing_setup_mechanical_derotator_syncmode = conn.set_pointing_setup_mechanical_derotator_syncmode(param)
		except Exception, e:
			print e
		return pointing_setup_mechanical_derotator_syncmode
	else:
		return "Parameter not 0, 1, 2,..., 6"



#############################################################

def get_position_horizontal_az(sender):
	e = ''
	try:
		position_horizontal_az = conn.get_position_horizontal_az()
	except Exception, e:
		print e
	if e == '':
		try:
			update_song_database.update("tel_dome", ["tel_az"], [float(position_horizontal_az)], "tel_dome_id")
		except Exception,e:
			print "The telescope azimuth position was not updated in the database: ", e

	return position_horizontal_az

def get_position_horizontal_alt(sender):
	e = ''
	try:
		position_horizontal_alt = conn.get_position_horizontal_alt()
	except Exception, e:
		print e
	if e == '':
		try:
			update_song_database.update("tel_dome", ["tel_alt"], [float(position_horizontal_alt)], "tel_dome_id")
		except Exception,e:
			print "The telescope altitude position was not updated in the database: ", e

	return position_horizontal_alt

def get_position_horizontal_zd(sender):
	try:
		position_horizontal_zd = conn.get_position_horizontal_zd()
	except Exception, e:
		print e
	return position_horizontal_zd

def get_position_horizontal_derotator(sender):
	try:
		position_horizontal_derotator = conn.get_position_horizontal_derotator()
	except Exception, e:
		print e
	return position_horizontal_derotator

def get_position_horizontal_dome(sender):
	try:
		position_horizontal_dome = conn.get_position_horizontal_dome()
	except Exception, e:
		print e
	return position_horizontal_dome

def get_position_equatorial_ra_j2000(sender):
	try:
		position_equatorial_ra_j2000 = conn.get_position_equatorial_ra_j2000()
	except Exception, e:
		print e
	return position_equatorial_ra_j2000

def get_position_equatorial_dec_j2000(sender):
	try:
		position_equatorial_dec_j2000 = conn.get_position_equatorial_dec_j2000()
	except Exception, e:
		print e
	return position_equatorial_dec_j2000

def get_position_equatorial_ra_current(sender):
	try:
		position_equatorial_ra_current = conn.get_position_equatorial_ra_current()
	except Exception, e:
		print e
	return position_equatorial_ra_current

def get_position_equatorial_dec_current(sender):
	try:
		position_equatorial_dec_current = conn.get_position_equatorial_dec_current()
	except Exception, e:
		print e
	return position_equatorial_dec_current

def get_position_equatorial_parallactic_angle(sender):
	try:
		position_equatorial_parallactic_angle = conn.get_position_equatorial_parallactic_angle()
	except Exception, e:
		print e
	return position_equatorial_parallactic_angle

def get_position_instrumental_zd_targetpos(sender):
	try:
		position_instrumental_zd_targetpos = conn.get_position_instrumental_zd_targetpos()
	except Exception, e:
		print e
	return position_instrumental_zd_targetpos

def get_position_instrumental_zd_currpos(sender):
	e = ''
	try:
		position_instrumental_zd_currpos = conn.get_position_instrumental_zd_currpos()
	except Exception, e:
		print e
	if e == '':
		try:
			update_song_database.update("tel_dome", ["tel_zd"], [float(position_instrumental_zd_currpos)], "tel_dome_id")
		except Exception,e:
			print "The telescope zenit distance position was not updated in the database: ", e

	return position_instrumental_zd_currpos

#### This function is deprecated ####
#def get_position_instrumental_alt_currpos(sender):
#	try:
#		position_instrumental_alt_currpos = conn.get_position_instrumental_alt_currpos()
#	except Exception, e:
#		print e
#
#	return position_instrumental_alt_currpos

def get_position_instrumental_az_currpos(sender):
	try:
		position_instrumental_az_currpos = conn.get_position_instrumental_az_currpos()
	except Exception, e:
		print e

	return position_instrumental_az_currpos

def get_position_instrumental_derotator_currpos(sender):
	try:
		position_instrumental_derotator_currpos = conn.get_position_instrumental_derotator_currpos()
	except Exception, e:
		print e
	return position_instrumental_derotator_currpos

def set_position_instrumental_derotator_targetpos(sender,param):
	try:
		return_data = conn.set_position_instrumental_derotator_targetpos(param)
	except Exception, e:
		print e
        return "done"

def get_position_instrumental_derotator_offset(sender):
        try:
                position_instrumental_derotator_offset = conn.get_position_instrumental_derotator_offset()
        except Exception, e:
                print e
        return position_instrumental_derotator_offset

def set_position_instrumental_derotator_offset(sender,param):
        try:
                return_data = conn.set_position_instrumental_derotator_offset(param)
        except Exception, e:
                print e
        return "done"

def get_position_instrumental_focus_currpos(sender):
	try:
		position_instrumental_focus_currpos = conn.get_position_instrumental_focus_currpos()
	except Exception, e:
		print e
	return position_instrumental_focus_currpos

def get_position_mechanical_derotator_currpos(sender):
	try:
		position_mechanical_derotator_currpos = conn.get_position_mechanical_derotator_currpos()
	except Exception, e:
		print e
	return position_mechanical_derotator_currpos

def get_position_mechanical_derotator_offset(sender):
        try:
                position_mechanical_derotator_offset = conn.get_position_mechanical_derotator_offset()
        except Exception, e:
                print e
        return position_mechanical_derotator_offset

def set_position_mechanical_derotator_targetpos(sender,param):
        try:
                return_data = conn.set_position_mechanical_derotator_targetpos(param)
        except Exception, e:
                print e
        return "done"

def set_position_mechanical_derotator_offset(sender,param):
        try:
                return_data = conn.set_position_mechanical_derotator_offset(param)
        except Exception, e:
                print e
        return "done"

def get_position_instrumental_port_select_currpos(sender):
	try:
		position_instrumental_port_select_currpos = conn.get_position_instrumental_port_select_currpos()
	except Exception, e:
		print e

	return position_instrumental_port_select_currpos

#### HEXAPOD ####

def get_position_instrumental_hexapod_x_currpos(sender):
	try:
		position_instrumental_hexapod_x_currpos = conn.get_position_instrumental_hexapod_x_currpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_x_currpos

def get_position_instrumental_hexapod_x_realpos(sender):
	try:
		position_instrumental_hexapod_x_realpos = conn.get_position_instrumental_hexapod_x_realpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_x_realpos

def set_position_instrumental_hexapod_x_targetpos(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_x_targetpos(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_y_currpos(sender):
	try:
		position_instrumental_hexapod_y_currpos = conn.get_position_instrumental_hexapod_y_currpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_y_currpos

def get_position_instrumental_hexapod_y_realpos(sender):
	try:
		position_instrumental_hexapod_y_realpos = conn.get_position_instrumental_hexapod_y_realpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_y_realpos

def set_position_instrumental_hexapod_y_targetpos(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_y_targetpos(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_z_currpos(sender):
	try:
		position_instrumental_hexapod_z_currpos = conn.get_position_instrumental_hexapod_z_currpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_z_currpos

def get_position_instrumental_hexapod_z_realpos(sender):
	try:
		position_instrumental_hexapod_z_realpos = conn.get_position_instrumental_hexapod_z_realpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_z_realpos

def set_position_instrumental_hexapod_z_targetpos(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_z_targetpos(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_u_currpos(sender):
	try:
		position_instrumental_hexapod_u_currpos = conn.get_position_instrumental_hexapod_u_currpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_u_currpos

def get_position_instrumental_hexapod_u_realpos(sender):
	try:
		position_instrumental_hexapod_u_realpos = conn.get_position_instrumental_hexapod_u_realpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_u_realpos

def set_position_instrumental_hexapod_u_targetpos(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_u_targetpos(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_v_currpos(sender):
	try:
		position_instrumental_hexapod_v_currpos = conn.get_position_instrumental_hexapod_v_currpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_v_currpos

def get_position_instrumental_hexapod_v_realpos(sender):
	try:
		position_instrumental_hexapod_v_realpos = conn.get_position_instrumental_hexapod_v_realpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_v_realpos

def set_position_instrumental_hexapod_v_targetpos(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_v_targetpos(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_w_currpos(sender):
	try:
		position_instrumental_hexapod_w_currpos = conn.get_position_instrumental_hexapod_w_currpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_w_currpos

def get_position_instrumental_hexapod_w_realpos(sender):
	try:
		position_instrumental_hexapod_w_realpos = conn.get_position_instrumental_hexapod_w_realpos()
	except Exception, e:
		print e
	return position_instrumental_hexapod_w_realpos

def set_position_instrumental_hexapod_w_targetpos(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_w_targetpos(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_x_offset(sender):
	try:
		position_instrumental_hexapod_x_offset = conn.get_position_instrumental_hexapod_x_offset()
	except Exception, e:
		print e
	return position_instrumental_hexapod_x_offset

def set_position_instrumental_hexapod_x_offset(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_x_offset(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_y_offset(sender):
	try:
		position_instrumental_hexapod_y_offset = conn.get_position_instrumental_hexapod_y_offset()
	except Exception, e:
		print e
	return position_instrumental_hexapod_y_offset

def set_position_instrumental_hexapod_y_offset(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_y_offset(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_z_offset(sender):
	try:
		position_instrumental_hexapod_z_offset = conn.get_position_instrumental_hexapod_z_offset()
	except Exception, e:
		print e
	return position_instrumental_hexapod_z_offset

def set_position_instrumental_hexapod_z_offset(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_z_offset(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_u_offset(sender):
	try:
		position_instrumental_hexapod_u_offset = conn.get_position_instrumental_hexapod_u_offset()
	except Exception, e:
		print e
	return position_instrumental_hexapod_u_offset

def set_position_instrumental_hexapod_u_offset(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_u_offset(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_v_offset(sender):
	try:
		position_instrumental_hexapod_v_offset = conn.get_position_instrumental_hexapod_v_offset()
	except Exception, e:
		print e
	return position_instrumental_hexapod_v_offset

def set_position_instrumental_hexapod_v_offset(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_v_offset(param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_hexapod_w_offset(sender):
	try:
		position_instrumental_hexapod_w_offset = conn.get_position_instrumental_hexapod_w_offset()
	except Exception, e:
		print e
	return position_instrumental_hexapod_w_offset

def set_position_instrumental_hexapod_w_offset(sender,param):
        try:
            return_data = conn.set_position_instrumental_hexapod_w_offset(param)
        except Exception, e:
            print e
        return "done"










###################################

def get_position_instrumental_focus_offset(sender):
        try:
                position_instrumental_focus_offset = conn.get_position_instrumental_focus_offset()
        except Exception, e:
                print e
        return position_instrumental_focus_offset

def get_position_instrumental_alt_offset(sender):
        try:
                position_instrumental_alt_offset = conn.get_position_instrumental_alt_offset()
        except Exception, e:
                print e
        return position_instrumental_alt_offset

def get_position_instrumental_zd_offset(sender):
        try:
                position_instrumental_zd_offset = conn.get_position_instrumental_zd_offset()
        except Exception, e:
                print e
        return position_instrumental_zd_offset


def get_position_instrumental_az_offset(sender):
        try:
                position_instrumental_az_offset = conn.get_position_instrumental_az_offset()
        except Exception, e:
                print e
        return position_instrumental_az_offset

#####################################

def get_position_instrumental_dome_az_currpos(sender):
	try:
		position_instrumental_dome_az_currpos = conn.get_position_instrumental_dome_az_currpos()
	except Exception, e:
		print e
	return position_instrumental_dome_az_currpos

def get_position_instrumental_dome_az_offset(sender):
	try:
		position_instrumental_dome_az_offset = conn.get_position_instrumental_dome_az_offset()
	except Exception, e:
		print e
	return position_instrumental_dome_az_offset

def set_position_instrumental_dome_az_offset(sender,param):

        try:
            return_data = conn.set_position_instrumental_dome_az_offset(param)
        except Exception, e:
            print e

        return "done"

def get_position_instrumental_dome_flap_currpos(sender):
	e = ''
	try:
		position_instrumental_dome_flap_currpos = conn.get_position_instrumental_dome_flap_currpos()
	except Exception, e:
		print e
	if e == '':
		if float(position_instrumental_dome_flap_currpos) == float(0.5):
			try:
				update_song_database.update("tel_dome", ["dome_flap_state"], [int(2)], "tel_dome_id")
			except Exception,e:
				print "The dome flap state was not updated in the database: ", e
		else:
			try:
				update_song_database.update("tel_dome", ["dome_flap_state"], [int(float(position_instrumental_dome_flap_currpos))], "tel_dome_id")
			except Exception,e:
				print "The dome flap state was not updated in the database: ", e
	return position_instrumental_dome_flap_currpos

def get_position_instrumental_dome_slit_currpos(sender):
	e = ''
	try:
		position_instrumental_dome_slit_currpos = conn.get_position_instrumental_dome_slit_currpos()
	except Exception, e:
		print e
	if e == '':
		if float(position_instrumental_dome_slit_currpos) == float(0.5):
			try:
				update_song_database.update("tel_dome", ["dome_slit_state"], [int(2)], "tel_dome_id")
			except Exception,e:
				print "The dome slit state was not updated in the database: ", e
		else:
			try:
				update_song_database.update("tel_dome", ["dome_slit_state"], [int(float(position_instrumental_dome_slit_currpos))], "tel_dome_id")
			except Exception,e:
				print "The dome slit state was not updated in the database: ", e
		
	return position_instrumental_dome_slit_currpos


def set_position_instrumental_dome_flap_targetpos(sender,param):
	flap_state = ''
	try:
		flap_state = conn.get_position_instrumental_dome_flap_currpos()
	except Exception, e:
		print e

	if str(flap_state) != '' and float(flap_state) != float(param) and int(float(param)) in [0,1]:
		### Write to db that dome flap is moving###
		try:
			update_song_database.update("tel_dome", ["dome_flap_state"], [int(2)], "tel_dome_id")
		except Exception,e:
			print "The dome flap state was not updated in the database: ", e

		try:
			return_data = conn.set_position_instrumental_dome_flap_targetpos(param)
		except Exception, e:
			print e

		print return_data
		if 'COMPLETE' in return_data:
			try:
				flap_state = get_position_instrumental_dome_flap_currpos(sender="Observer")
			except Exception,e:
				print "The dome flap state was not updated in the database: ", e

		return "done"
	elif float(flap_state) == float(param) and int(param) in [0,1]:
		return "done"
	else:
		return "Something went wrong with setting the dome flap position"

def set_position_instrumental_dome_slit_targetpos(sender,param):
	slit_state = ''
	try:
		slit_state = conn.get_position_instrumental_dome_slit_currpos()
	except Exception, e:
		print e

	if str(slit_state) != '' and float(slit_state) != float(param) and int(float(param)) in [0,1]:
		### Write to db that dome flap is moving###
		try:
			update_song_database.update("tel_dome", ["dome_slit_state"], [int(2)], "tel_dome_id")
		except Exception,e:
			print "The dome slit state was not updated in the database: ", e

		try:
			return_data = conn.set_position_instrumental_dome_slit_targetpos(param)
		except Exception, e:
			print e

		if 'COMPLETE' in return_data:	
			try:
				slit_state = get_position_instrumental_dome_slit_currpos(sender="Observer")
			except Exception,e:
				print "The dome slit state was not updated in the database: ", e

		return "done"
	elif float(slit_state) == float(param) and int(param) in [0,1]:
		return "done"
	else:
		return "Something went wrong with setting the dome slit position"

####################################################################################

def set_position_instrumental_focus_targetpos(sender,param):

        try:
            return_data = conn.set_position_instrumental_focus_targetpos(param)
        except Exception, e:
            print e

        return "done"

def set_position_instrumental_focus_offset(sender,param):

        try:
            return_data = conn.set_position_instrumental_focus_offset(param)
        except Exception, e:
            print e

        return "done"

def set_position_instrumental_alt_offset(sender,param):

        try:
            return_data = conn.set_position_instrumental_alt_offset(param)
        except Exception, e:
            print e

        return "done"

def set_position_instrumental_zd_offset(sender,param):

        try:
            return_data = conn.set_position_instrumental_zd_offset(param)
        except Exception, e:
            print e

        return "done"

def set_position_instrumental_az_offset(sender,param):

        try:
            return_data = conn.set_position_instrumental_az_offset(param)
        except Exception, e:
            print e

        return "done"


###################################################################################
# AO

def get_position_instrumental_ao_offset(sender,bender_number):
        try:
                position_instrumental_ao_offset = conn.get_position_instrumental_ao_offset(bender_number)
        except Exception, e:
                print e
        return position_instrumental_ao_offset

def set_position_instrumental_ao_offset(sender,bender_number,param):
        try:
            return_data = conn.set_position_instrumental_ao_offset(bender_number,param)
        except Exception, e:
            print e
        return "done"

def get_position_instrumental_ao_currpos(sender,bender_number):
        try:
                position_instrumental_ao_currpos = conn.get_position_instrumental_ao_currpos(bender_number)
        except Exception, e:
                print e
        return position_instrumental_ao_currpos

def set_position_instrumental_ao_targetpos(sender,bender_number,param):
        try:
            return_data = conn.set_position_instrumental_ao_targetpos(bender_number,param)
        except Exception, e:
            print e
        return "done"

def get_pointing_setup_instrument_name(sender):
        try:
                pointing_setup_instrument_name = conn.get_pointing_setup_instrument_name()
        except Exception, e:
                print e
        return pointing_setup_instrument_name

def get_pointing_setup_instrument_index(sender):
        try:
                pointing_setup_instrument_index = conn.get_pointing_setup_instrument_index()
        except Exception, e:
                print e
        return pointing_setup_instrument_index

def set_pointing_setup_instrument_index(sender,param):
        try:
            return_data = conn.set_pointing_setup_instrument_index(param)
        except Exception, e:
            print e

        return "done"

###################################################################################

def get_auxiliary_cover_realpos(sender):
	e = ''
	try:
		auxiliary_cover_realpos = conn.get_auxiliary_cover_realpos()
	except Exception, e:
		print e

	return auxiliary_cover_realpos

def set_auxiliary_cover_targetpos(sender,param):
	mirror_cover_state = ''
	try:
		mirror_cover_state = conn.get_auxiliary_cover_realpos()
	except Exception, e:
		print e

	if str(mirror_cover_state) != '' and float(mirror_cover_state) != float(param) and int(float(param)) in [0,1]:
		### Write to db that dome flap is moving###
		try:
			update_song_database.update("tel_dome", ["mirror_cover_state"], [int(2)], "tel_dome_id")
		except Exception,e:
			print "The dome slit state was not updated in the database: ", e

		try:
			return_data = conn.set_auxiliary_cover_targetpos(param)
		except Exception, e:
			print e

		if 'COMPLETE' in return_data:
			try:
				mirror_cover_state = get_auxiliary_cover_realpos(sender="Observer")
			except Exception,e:
				print "The mirror_cover state was not updated in the database: ", e

		return "done"
	elif float(mirror_cover_state) == float(param) and int(param) in [0,1]:
		return "done"
	else:
		return "Something went wrong with setting the mirror cover position"

def get_auxiliary_cover_targetpos(sender):
	try:
		auxiliary_cover_targetpos = conn.get_auxiliary_cover_targetpos()
	except Exception, e:
		print e
	return auxiliary_cover_targetpos

def get_auxiliary_temp_cabinet(sender):
	try:
		auxiliary_temp_cabinet = conn.get_auxiliary_temp_cabinet()
	except Exception, e:
		print e
	return auxiliary_temp_cabinet

def get_auxiliary_temp_m1(sender):
	try:
		auxiliary_temp_m1 = conn.get_auxiliary_temp_m1()
	except Exception, e:
		print e
	return auxiliary_temp_m1

def get_auxiliary_temp_m2(sender):
	try:
		auxiliary_temp_m2 = conn.get_auxiliary_temp_m2()
	except Exception, e:
		print e
	return auxiliary_temp_m2

def get_auxiliary_temp_m3(sender):
	try:
		auxiliary_temp_m3 = conn.get_auxiliary_temp_m3()
	except Exception, e:
		print e
	return auxiliary_temp_m3

def get_auxiliary_ttelescope(sender):
	try:
		auxiliary_ttelescope = conn.get_auxiliary_ttelescope()
	except Exception, e:
		print e
	return auxiliary_ttelescope

def get_auxiliary_mancontrolspeed(sender):
	try:
		auxiliary_mancontrolspeed = conn.get_auxiliary_mancontrolspeed()
	except Exception, e:
		print e
	return auxiliary_mancontrolspeed

def get_sidereal_time(sender):
	try:
		sidereal_time = conn.get_sidereal_time()
	except Exception, e:
		print e
	return sidereal_time

def get_UTC_time(sender):
	try:
		UTC_time = conn.get_UTC_time()
	except Exception, e:
		print e
	return UTC_time


###################################################################
###################################################################
###################################################################
###################################################################
###################################################################

def shut_down_telescope(sender):
	"""
		@brief: This function handles a total shutdown of the telescope. 
			1) Close mirror_cover
			2) Close dome flap
			3) Close dome slit
	"""
	value = ''
	print "Stop tracking"
	value = set_pointing_track(sender,param=0)	
	if value == 'done':
		value = ''
		print "Closing mirror cover"
		value = set_auxiliary_cover_targetpos(sender,param=0)
	if value == 'done':
		value = ''
		print "Closing dome flap"
		value = set_position_instrumental_dome_flap_targetpos(sender,param=0)
	if value == 'done':
		value = ''
		print "Closing dome slit"
		value = set_position_instrumental_dome_slit_targetpos(sender,param=0)
	if value == 'done':
		value = ''
		print "Powering off the telescope"
		value = set_telescope_ready(sender,param=0)	

	return 1

def startup_telescope(sender):
	"""
		@brief: This function handles a start up of the telescope if power is on. 		
			1) Opening the dome slit
			2) Opening the dome flap
			3) Opening the mirror cover
	"""

	value = ''
        print "Powering on the telescope"
	value = set_telescope_ready(sender,param=1)
	if value == 'done':
		value = ''
		print "opening dome slit"
		value = set_position_instrumental_dome_slit_targetpos(sender,param=1)	
	if value == 'done':
		value = ''
		print "Opening dome flap"
		value = set_position_instrumental_dome_flap_targetpos(sender,param=1)
	if value == 'done':
		value = ''
		print "Opening mirror cover"
		value = set_auxiliary_cover_targetpos(sender,param=1)

	return 1



def controller(sender): 
	"""
		@breif: This should control the communication with the telescope.
	"""

	#if sender.lower() == "monitor":
	#	global in_use
	#	in_use = 1
	#elif sender.lower() == "error_daemon":
	#	global in_use
	#	in_use = 2
	#elif sender.lower() == "observer":
	#	global in_use
	#	in_use = 3
	#elif sender.lower() == "scheduler":
	#	global in_use
	#	in_use = 4	
	#elif sender == "":
	#	global in_use
	#	in_use = 5
	#else:
	#	global in_use
	#	in_use = -1
	
	#return	in_use
	return 1

def set_pdu_light(sender, pdu, outlet, status): 
	"""
		@breif: This should turn on/off light in container or dome
	"""
	print "hej"
	if pdu == 'container' and outlet in [9,23,24] and status in [1,2]:
		print pdu_handle.SetPower(pdu,outlet,status)

	return -1

def get_pdu_light(sender, pdu, outlet): 
	"""
		@breif: This should status of the pdu outlet
	"""
	if pdu == 'container' and outlet in [9,23,24]:
		pdu_outlet_state = pdu_handle.GetPower(pdu,outlet)
		return pdu_outlet_state

	return -1


def collect_tel_info():
	"""
		@brief: This function checks the state of the telescope and writes the state to the databasa:

	"""		

	local_mode = 0
	emergency_state = 0

	global RUNNING
	while RUNNING:
		try:
			try:
				t_ready_state = float(gettsi.get_telescope_state(sender="monitor"))
			except Exception,e:
				print clock.timename(), e
				t_ready_state = gettsi.get_telescope_state(sender="monitor")		
				print clock.timename(), " The telescope replied : '%s' in the collect tel info function" % str(t_ready_state)

			if float(t_ready_state) == float(-3.0) and local_mode == 0:
				print clock.timename(), " The telescope was put in local mode"
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Telescope in local mode!", message="The telescope was put in local mode!\n\nSend at: %s\n\n" % clock.obstimeUT())	
				send_song_mail.send_mail().send_sms(receiver=["Mads"], message="Someone has put the telescope into local mode")	
				local_mode = 1
			elif float(t_ready_state) == float(0.0) and local_mode == 1:
				print clock.timename(), " The telescope was put back in remote mode"
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS", subject="Telescope back in remote mode!", message="The telescope was put back in remote mode!\n\nSend at: %s\n\n" % clock.obstimeUT())		
				local_mode = 0
			elif float(t_ready_state) == float(-2.0) and emergency_state == 0:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Telescope in emergency state!", message="Someone has pushed an emergency botton at SONG!\n\nSend at: %s\n\n" % clock.obstimeUT())	
				send_song_mail.send_mail().send_sms(receiver=["Mads"], message="Someone has pushed an emergency botton at SONG")	
				emergency_state = 1
			elif float(t_ready_state) == float(0.0) and emergency_state == 1:
				send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="Telescope back in remote mode!", message="Someone has released the emergency botton at SONG and the telescope is back in remote mode!\n\nSend at: %s\n\n" % clock.obstimeUT())	
				emergency_state = 0

			try:
				t_error_list = gettsi.get_telescope_status_list(sender="monitor")
			except Exception,e:
				print clock.timename(), e

			if type(t_ready_state) == numpy.str:
				t_ready_state = -1	# Error state					
			elif float(t_ready_state) == float(-3.0):
				t_ready_state = 10	# Local mode
			elif float(t_ready_state) == float(-2.0):
				t_ready_state = 9	# Emergency stop

			t_motion_state = gettsi.get_telescope_motion_state(sender="monitor")
			t_ra = gettsi.get_position_equatorial_ra_j2000(sender="monitor")
			t_dec = gettsi.get_position_equatorial_dec_j2000(sender="monitor")

			t_az = gettsi.get_position_horizontal_az(sender="monitor")
			if float(t_az) < 0.0 or float(t_az) > 360.:
				print clock.timename(), " Azimuth angle were not calibrated"
				t_az = 0

			t_zd = gettsi.get_position_horizontal_zd(sender="monitor")
			if float(t_zd) < 0.0 or float(t_zd) > 90.:
				print clock.timename(), " Zenith distance were not calibrated"
				t_zd = 0

			t_alt = gettsi.get_position_horizontal_alt(sender="monitor")
			if float(t_alt) < 0.0 or float(t_alt) > 90.:
				print clock.timename(), " Altitude were not calibrated"
				t_alt = 0

			t_error = gettsi.get_telescope_status_global(sender="monitor")
			t_focus = gettsi.get_position_instrumental_focus_currpos(sender="monitor")
			t_focus_offset = gettsi.get_position_instrumental_hexapod_z_offset(sender="monitor")
			o_ra = gettsi.get_object_equatorial_ra(sender="monitor")
			o_dec = gettsi.get_object_equatorial_dec(sender="monitor")
			d_az = gettsi.get_position_horizontal_dome(sender="monitor")
			if float(d_az) < 0.0 or float(d_az) > 360.:
				print clock.timename(), " Dome azimuth angle were not calibrated"
				d_az = 0

			d_slit = gettsi.get_position_instrumental_dome_slit_currpos(sender="monitor")
			if float(d_slit) != 0.0 and float(d_slit) != 1.0 and float(d_slit) != -1.0:
				d_slit = 2
			else:
				d_slit = int(float(d_slit))
			d_flap = gettsi.get_position_instrumental_dome_flap_currpos(sender="monitor")
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
			m_cover = gettsi.get_auxiliary_cover_realpos(sender="monitor")
			if float(m_cover) != 0.0 and float(m_cover) != 1.0 and float(m_cover) != -1.0:
				m_cover = 2
			else:
				m_cover = int(float(m_cover))				
			thr_mirror = gettsi.get_position_instrumental_port_select_currpos(sender="monitor")
			temp_cab = gettsi.get_auxiliary_temp_cabinet(sender="monitor")
			temp_m1 = gettsi.get_auxiliary_temp_m1(sender="monitor")
			temp_m2 = gettsi.get_auxiliary_temp_m2(sender="monitor")	
			temp_m3 = gettsi.get_auxiliary_temp_m3(sender="monitor")	
			temp_tt = gettsi.get_auxiliary_ttelescope(sender="monitor")
#				derot_position = get_position_mechanical_derotator_currpos()	
			derot_position = float(gettsi.get_position_mechanical_derotator_currpos(sender="monitor")) % 360.0
			derot_offset = gettsi.get_position_mechanical_derotator_offset(sender="monitor")

		except Exception, e:
			print clock.timename(), " Could not get telescope status values: ", e

		try:
			tel_az_off = float(gettsi.get_position_instrumental_az_offset(sender="monitor"))*3600.
			tel_zd_off = float(gettsi.get_position_instrumental_zd_offset(sender="monitor"))*3600.
		except Exception,e:
			print clock.timename(), " Could not get telescope pointing offsets: ", e

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

		try:
			params = "(tenerife_tel_temps_id, select_id, m1_temp, m2_temp, m3_temp, tel_temp, cabinet_temp, extra_param_1, extra_param_2, extra_param_3, extra_param_4, extra_param_5, extra_param_6, extra_param_7, extra_param_8, extra_param_9, extra_param_10, extra_value_1, extra_value_2, extra_value_3, extra_value_4, extra_value_5, extra_value_6, extra_value_7, extra_value_8, extra_value_9, extra_value_10, ins_at)"
		except Exception,e:
			print clock.timename(), e

		try:
			values = "(%i, %i, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, '%s')" % (tenerife_tel_temps_id+1, 1, float(temp_m1), float(temp_m2), float(temp_m3), float(temp_tt), float(temp_cab), 0.0, 0.0, 0.0, 0.0, tel_zd_off, tel_az_off, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
		except Exception,e:
			print clock.timename(), e

		try:
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (m_conf.db_host, m_conf.data_db, m_conf.db_user, m_conf.db_password))
			curr = conn.cursor()
			stmt = 'INSERT INTO %s %s VALUES %s' % ("tenerife_tel_temps", params, values)               
			curr.execute(stmt)		
			conn.commit()
			curr.close()
		except Exception, e:
			print clock.timename(), " An error occurred: ", e


#################################### UPDATE ENVIRONMENTAL VALUES FOR TEMPERATURE AND PRESSURE
		try:
			environment_conditions = get_fields("weather_station", ["wxt520_temp1", "wxt520_pressure"])	
		except Exception,e:
			print clock.timename(), e
			print clock.timename(), " Could not collect weather data from database... "

		if song_telescope_config.use_fixed_env_vals == "yes":
			try:
				settsi.set_telescope_config_environment_temperature(sender="tcs_comm", param=float(song_telescope_config.pm_temp))
				settsi.set_telescope_config_environment_pressure(sender="tcs_comm", param=song_telescope_config.pm_pres)
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), " Could not update the environment conditions in the TSI"
		else:
			try:
				settsi.set_telescope_config_environment_temperature(sender="tcs_comm", param=float(environment_conditions["wxt520_temp1"]))
				settsi.set_telescope_config_environment_pressure(sender="tcs_comm", param=environment_conditions["wxt520_pressure"])
			except Exception,e:
				print clock.timename(), e
				print clock.timename(), " Could not update the environment conditions in the TSI"


		#print "Telescope data inserted into the database!"
		time.sleep(song_telescope_config.tel_data_insertion_delay)

	return 1

	

class telescope(Daemon):
    """
	This class is the fundemental class for the daemon. This is what handles the incomming commands and operates as the server. All functions that needs to be defined has to be registered here aswell. 
    """
    
    def run(self):
        """This method will be called when the process has been daemonized."""
       
        global RUNNING
        RUNNING = True	

	val = beating_heart.start_heartbeat(job_id=m_conf.tcs_comm_id)

        server1 = SimpleXMLRPCServer((song_telescope_config.SERVER_HOST1, song_telescope_config.SERVER_PORT1), requestHandler=RequestHandler, logRequests=False)
        server2 = SimpleXMLRPCServer((song_telescope_config.SERVER_HOST2, song_telescope_config.SERVER_PORT2), requestHandler=RequestHandler, logRequests=False)       

        server1.register_function(is_alive)

############ REGISTER TSI FUNCTIONS ################

	server1.register_function(get_connid)
	server1.register_function(shutdown_connection)
	server1.register_function(set_telescope_ready)
	server1.register_function(get_telescope_state)
	server1.register_function(get_telescope_motion_state)
	server1.register_function(set_telescope_stop)
	server1.register_function(get_telescope_status_global)
	server1.register_function(get_telescope_status_list)
	server1.register_function(set_telescope_config_load)
	server1.register_function(set_telescope_config_environment_temperature)
	server1.register_function(set_telescope_config_environment_pressure)
	server1.register_function(set_object_equatorial_epoch)
	server1.register_function(get_object_equatorial_epoch)
	server1.register_function(set_object_equatorial_equinox)
	server1.register_function(get_object_equatorial_equinox)
	server1.register_function(get_object_solarsystem_object)
	server1.register_function(set_object_solarsystem_object)
	server1.register_function(get_object_solarsystem_moon)
	server1.register_function(set_object_solarsystem_moon)

	server1.register_function(set_object_tle_line1)
	server1.register_function(set_object_tle_line2)
	server1.register_function(get_object_tle_name)

	server1.register_function(set_object_equatorial_ra)
	server1.register_function(get_object_equatorial_ra)
	server1.register_function(set_object_equatorial_dec)
	server1.register_function(get_object_equatorial_dec)
	server1.register_function(set_object_equatorial_ra_pm)
	server1.register_function(get_object_equatorial_ra_pm)
	server1.register_function(set_object_equatorial_dec_pm)
	server1.register_function(get_object_equatorial_dec_pm)
	server1.register_function(set_object_horizontal_alt)
	server1.register_function(set_object_horizontal_az)
#	server1.register_function(set_object_equatorial_name)
#	server1.register_function(get_object_equatorial_name)

	server1.register_function(set_pointing_track)
	server1.register_function(get_pointing_track)
	server1.register_function(get_pointing_setup)
	server1.register_function(set_pointing_setup)
	server1.register_function(get_pointing_setup_use_port)
	server1.register_function(set_pointing_setup_use_port)
	server1.register_function(get_pointing_model_calculate)
	server1.register_function(set_pointing_model_calculate)
	server1.register_function(get_pointing_model_type)
	server1.register_function(set_pointing_model_type)
	server1.register_function(set_pointing_model_add)
	server1.register_function(get_pointing_model_list)
	server1.register_function(get_pointing_model_file)
	server1.register_function(get_pointing_model_file_list)
	server1.register_function(set_pointing_model_file)
	server1.register_function(set_pointing_model_load)
	server1.register_function(set_pointing_model_save)
	server1.register_function(get_pointing_setup_dome_syncmode)
	server1.register_function(set_pointing_setup_dome_syncmode)
	server1.register_function(get_pointing_setup_dome_max_deviation)
	server1.register_function(set_pointing_setup_dome_max_deviation)
	server1.register_function(get_pointing_setup_dome_offset)
	server1.register_function(set_pointing_setup_dome_offset)
	server1.register_function(get_pointing_setup_focus_syncmode)
	server1.register_function(set_pointing_setup_focus_syncmode)
	server1.register_function(get_pointing_setup_derotator_syncmode)
	server1.register_function(set_pointing_setup_derotator_syncmode)
	server1.register_function(get_pointing_setup_mechanical_derotator_syncmode)
	server1.register_function(set_pointing_setup_mechanical_derotator_syncmode)
	server1.register_function(get_pointing_setup_instrument_name)
	server1.register_function(get_pointing_setup_instrument_index)
	server1.register_function(set_pointing_setup_instrument_index)

	server1.register_function(get_position_horizontal_az)
	server1.register_function(get_position_horizontal_alt)
	server1.register_function(get_position_horizontal_zd)
	server1.register_function(get_position_horizontal_derotator)
	server1.register_function(get_position_horizontal_dome)
	server1.register_function(get_position_equatorial_ra_j2000)
	server1.register_function(get_position_equatorial_dec_j2000)
	server1.register_function(get_position_equatorial_ra_current)
	server1.register_function(get_position_equatorial_dec_current)
	server1.register_function(get_position_equatorial_parallactic_angle)
	server1.register_function(get_position_instrumental_zd_targetpos)
	server1.register_function(get_position_instrumental_zd_currpos)
	#server1.register_function(get_position_instrumental_alt_currpos)
	server1.register_function(get_position_instrumental_az_currpos)
	server1.register_function(get_position_instrumental_derotator_currpos)
	server1.register_function(set_position_instrumental_derotator_targetpos)
	server1.register_function(get_position_instrumental_derotator_offset)
	server1.register_function(set_position_instrumental_derotator_offset)
	server1.register_function(get_position_mechanical_derotator_currpos)
        server1.register_function(set_position_mechanical_derotator_targetpos)
        server1.register_function(get_position_mechanical_derotator_offset)
        server1.register_function(set_position_mechanical_derotator_offset)
        server1.register_function(get_position_instrumental_port_select_currpos)
	server1.register_function(get_position_instrumental_focus_currpos)
	server1.register_function(get_position_instrumental_dome_az_currpos)
	server1.register_function(get_position_instrumental_dome_az_offset)
	server1.register_function(set_position_instrumental_dome_az_offset)
	server1.register_function(get_position_instrumental_dome_flap_currpos)
	server1.register_function(get_position_instrumental_dome_slit_currpos)
	server1.register_function(set_position_instrumental_dome_flap_targetpos)
	server1.register_function(set_position_instrumental_dome_slit_targetpos)
##################

	server1.register_function(get_position_instrumental_hexapod_x_currpos)
	server1.register_function(get_position_instrumental_hexapod_x_realpos)
	server1.register_function(set_position_instrumental_hexapod_x_targetpos)
	server1.register_function(get_position_instrumental_hexapod_x_offset)
	server1.register_function(set_position_instrumental_hexapod_x_offset)

	server1.register_function(get_position_instrumental_hexapod_y_currpos)
	server1.register_function(get_position_instrumental_hexapod_y_realpos)
	server1.register_function(set_position_instrumental_hexapod_y_targetpos)
	server1.register_function(get_position_instrumental_hexapod_y_offset)
	server1.register_function(set_position_instrumental_hexapod_y_offset)

	server1.register_function(get_position_instrumental_hexapod_z_currpos)
	server1.register_function(get_position_instrumental_hexapod_z_realpos)
	server1.register_function(set_position_instrumental_hexapod_z_targetpos)
	server1.register_function(get_position_instrumental_hexapod_z_offset)
	server1.register_function(set_position_instrumental_hexapod_z_offset)

	server1.register_function(get_position_instrumental_hexapod_u_currpos)
	server1.register_function(get_position_instrumental_hexapod_u_realpos)
	server1.register_function(set_position_instrumental_hexapod_u_targetpos)
	server1.register_function(get_position_instrumental_hexapod_u_offset)
	server1.register_function(set_position_instrumental_hexapod_u_offset)

	server1.register_function(get_position_instrumental_hexapod_v_currpos)
	server1.register_function(get_position_instrumental_hexapod_v_realpos)
	server1.register_function(set_position_instrumental_hexapod_v_targetpos)
	server1.register_function(get_position_instrumental_hexapod_v_offset)
	server1.register_function(set_position_instrumental_hexapod_v_offset)

	server1.register_function(get_position_instrumental_hexapod_w_currpos)
	server1.register_function(get_position_instrumental_hexapod_w_realpos)
	server1.register_function(set_position_instrumental_hexapod_w_targetpos)
	server1.register_function(get_position_instrumental_hexapod_w_offset)
	server1.register_function(set_position_instrumental_hexapod_w_offset)

	server1.register_function(set_position_instrumental_focus_targetpos)
	server1.register_function(set_position_instrumental_focus_offset)
	server1.register_function(get_position_instrumental_focus_offset)
	server1.register_function(get_position_instrumental_alt_offset)
	server1.register_function(get_position_instrumental_zd_offset)
	server1.register_function(get_position_instrumental_az_offset)
	server1.register_function(set_position_instrumental_alt_offset)
	server1.register_function(set_position_instrumental_zd_offset)
	server1.register_function(set_position_instrumental_az_offset)

	server1.register_function(get_position_instrumental_ao_offset)
	server1.register_function(set_position_instrumental_ao_offset)
	server1.register_function(get_position_instrumental_ao_currpos)
	server1.register_function(set_position_instrumental_ao_targetpos)
##################
	server1.register_function(get_auxiliary_cover_realpos)
	server1.register_function(set_auxiliary_cover_targetpos)
	server1.register_function(get_auxiliary_cover_targetpos)
	server1.register_function(get_auxiliary_temp_cabinet)
	server1.register_function(get_auxiliary_temp_m1)
	server1.register_function(get_auxiliary_temp_m2)
	server1.register_function(get_auxiliary_temp_m3)
	server1.register_function(get_auxiliary_mancontrolspeed)
	server1.register_function(get_auxiliary_ttelescope)
	server1.register_function(get_sidereal_time)
	server1.register_function(get_UTC_time)

	server1.register_function(set_telescope_clear_panic)
	server1.register_function(set_telescope_clear_error)
	server1.register_function(set_telescope_clear_warning)
	server1.register_function(set_telescope_clear_info)
	#server1.register_function()
	#server1.register_function()
	#server1.register_function()
	#server1.register_function()
	#server1.register_function()
	#server1.register_function()


############ REGISTER OTHER FUNCTIONS ################
	server1.register_function(shut_down_telescope)
	server1.register_function(startup_telescope)
	server1.register_function(controller)
  	server1.register_function(set_pdu_light)          
     	server1.register_function(get_pdu_light) 
     
        print 'The daemon was started at: ', clock.whattime()
        

	def clear_log_function():
		done_param = 0
        	while RUNNING:
			### This should copy the content of the log file to old log file and clear it at 12 UTC.
			if int(float(time.strftime("%H", time.gmtime()))) == 12 and done_param == 0:
				daily_logging_handler.handle_log_files(song_telescope_config.SERVER_LOGFILE, song_telescope_config.SERVER_LOGFILE_OLD)
				done_param = 1
			if done_param == 1 and int(float(time.strftime("%H", time.gmtime()))) > 12:
				done_param = 0

			time.sleep(600)

	thread_value = thread.start_new_thread(clear_log_function, ())
###############################

	############### SET ALL RELEVANT VALUES IN DATABASE ##############
	try:
		t_ready_state = get_telescope_state(sender="Observer")
		time.sleep(1.1)
		t_motion_state = get_telescope_motion_state(sender="Observer")
		time.sleep(1.1)		
		t_ra = get_position_equatorial_ra_j2000(sender="Observer")
		time.sleep(1.1)
		t_dec = get_position_equatorial_dec_j2000(sender="Observer")
		time.sleep(1.1)
		obj_ra = get_object_equatorial_ra(sender="Observer")
		time.sleep(1.1)
		obj_dec = get_object_equatorial_dec(sender="Observer")	
		time.sleep(1.1)	
		t_az = get_position_horizontal_az(sender="Observer")
		time.sleep(1.1)
		t_alt = get_position_horizontal_alt(sender="Observer")
		time.sleep(1.1)
		t_focus = get_position_instrumental_focus_currpos(sender="Observer")
		time.sleep(1.1)
		d_slit = get_position_instrumental_dome_slit_currpos(sender="Observer")
		time.sleep(1.1)
		d_flap = get_position_instrumental_dome_flap_currpos(sender="Observer")
		time.sleep(1.1)
		m_cover = get_auxiliary_cover_realpos(sender="Observer")
		time.sleep(1.1)
		thr_mirror = get_pointing_setup(sender="Observer")
		time.sleep(1.1)
	except Exception, e:
		print "Could not get telescope status values: ", e

	try:
		update_song_database.update("tel_dome", ["tel_ready_state", "tel_motion_state", "tel_ra", "tel_dec", "tel_az", "tel_alt", "tel_focus", "dome_slit_state", "dome_flap_state", "mirror_cover_state", "third_mirror", "obj_ra", "obj_dec"], [int(float(t_ready_state)),int(float(t_motion_state)),float(t_ra),float(t_dec),float(t_az), float(t_alt), float(t_focus), int(float(d_slit)), int(float(d_flap)), int(float(m_cover)), int(float(thr_mirror)), float(obj_ra), float(obj_dec)], "tel_dome_id")
	except Exception,e:
		print "The telescope status values were not updated in the database: ", e

##########################################      THREAD TO RUN     ###########################################

	#def server2_thread():
	#	while RUNNING:
	#		server2.handle_request()
	#thread_value = thread.start_new_thread(server2_thread, ())

##############################################################################################################

	if song_telescope_config.set_m3.lower() == "yes":
		try:
			m3_pos = set_pointing_setup_use_port(param=song_telescope_config.m3_pos, sender="Observer") 
		except Exception, e:
			print "M3 position could not be set!"
			print e		


	if song_telescope_config.load_pm.lower() == "yes":
		#### INITIALIZE TSI:
		#### LOAD POINTING MODEL

		if get_pointing_model_file(sender="Observer") != song_telescope_config.PM_measurement_file:

			e = ''
			try:
				pm_file = set_pointing_model_file(param=song_telescope_config.PM_measurement_file, sender="Observer") 
			except Exception, e:
				print "Pointing model measurement file could not be set"
				print e

			if e == '':
				print "Pointing model measurement file '%s' is set" % str(song_telescope_config.PM_measurement_file)
	
				try:
					pm_file = set_pointing_model_load(param=1, sender="Observer")	# param = 1 : load and overwrite, param = 2: load and append
		 		except Exception, e:
					print "Pointing model measurement file could not be loaded"
					print e

			if e == '':
				print "Pointing model measurement file '%s' was loaded" % str(song_telescope_config.PM_measurement_file)

				try:
					pm_file = set_pointing_model_type(param=1, sender="Observer")	# param = -1: No PM, param = 0: Classic PM, param = 1: Extended PM
		 		except Exception, e:
					print "Pointing model type could not be set to: Extended"
					print e

			if e == '':
				print "Pointing model type was set to: Extended"

				try:
					pm_file = set_pointing_model_calculate(param=2, sender="Observer")	# param = 1: Calculate, param = 2: Calculate and reset all offsets to zero
		 		except Exception, e:
					print "Pointing model could not be calculated"
					print e

				if e == '':
					print "Pointing model was calculated and will now be used!"
				try:
					pm_file = get_pointing_model_calculate(sender="Observer")
		 		except Exception, e:
					print e
				if e == '':
					print 'The RMS of the calculated model was: %f"' % (float(pm_file))

	else:
		print "No pointing model was loaded!"

	if song_telescope_config.apply_focus_syncmode.lower() == "yes":
		e = ''
		try:
			syncmode = set_pointing_setup_focus_syncmode(param=song_telescope_config.focus_syncmode_value, sender="Observer") 
		except Exception, e:
			print "Focus syncmode could not be set"
			print e

	if song_telescope_config.set_mech_derotator_syncmode_startup.lower() == "yes":
		e = ''
		try:
			derot_syncmode = set_pointing_setup_mechanical_derotator_syncmode(param=song_telescope_config.mech_derot_syncmode, sender="Observer") 
		except Exception, e:
			print "Mechanical derotator syncmode not set"
			print e

	if song_telescope_config.set_instrument_at_startup.lower() == "yes":
		e = ''
		try:
			inst_index = set_pointing_setup_instrument_index(param=song_telescope_config.instrument_index, sender="Observer") 
		except Exception, e:
			print "Pointing setup instrument was not set"
			print e


	if song_telescope_config.apply_dome_syncmode.lower() == "yes":
		e = ''
		try:
			syncmode = set_pointing_setup_dome_syncmode(param=song_telescope_config.dome_syncmode_value, sender="Observer") 
		except Exception, e:
			print "Dome syncmode could not be set"
			print e
		e = ''
		try:
			syncmode = set_pointing_setup_dome_max_deviation(param=song_telescope_config.max_dome_devi, sender="Observer") 
		except Exception, e:
			print "Dome maximum deviation could not be set"
			print e

	if song_telescope_config.set_hexapod_at_startup.lower() == "yes":
		try:
			hexapod_x = set_position_instrumental_hexapod_x_targetpos(param=song_telescope_config.hexapod_x, sender="Observer")
			hexapod_y = set_position_instrumental_hexapod_y_targetpos(param=song_telescope_config.hexapod_y, sender="Observer")
			hexapod_u = set_position_instrumental_hexapod_u_targetpos(param=song_telescope_config.hexapod_u, sender="Observer")
			hexapod_v = set_position_instrumental_hexapod_v_targetpos(param=song_telescope_config.hexapod_v, sender="Observer")
			hexapod_w = set_position_instrumental_hexapod_w_targetpos(param=song_telescope_config.hexapod_w, sender="Observer")

			hexapod_x = set_position_instrumental_hexapod_x_offset(param=0.0, sender="Observer")
			hexapod_y = set_position_instrumental_hexapod_y_offset(param=0.0, sender="Observer")
			hexapod_u = set_position_instrumental_hexapod_u_offset(param=0.0, sender="Observer")
			hexapod_v = set_position_instrumental_hexapod_v_offset(param=0.0, sender="Observer")
			hexapod_w = set_position_instrumental_hexapod_w_offset(param=0.0, sender="Observer")
		except Exception,e:
			print e
			print "Could not get the hexapod values"
		else:
			print "Hexapod values are now set"

		
	print "######### Initialization of the telescope is now completed! #########"


###########################################
	# START thread to insert telescope things into database every 10 seconds....
	col_tel_info_thread_handle = thread.start_new_thread(collect_tel_info, ())

######### THE MAIN server handle ##########
		
        while RUNNING:
		server1.handle_request()

		global alive_time
		alive_time = time.time()

def main():
    """
	This function is called when the communicator_daemon.py module is called. 
	This will set some logging paths and starts the daemon class.
    """
    outstream = song_telescope_config.SERVER_LOGFILE
    pidfile = song_telescope_config.SERVER_PIDFILE

    daemon = telescope(pidfile, stdout=outstream, stderr=outstream)
    try:
        opts, list = getopt.getopt(sys.argv[1:], 'st')
    except getopt.GetoptError, e:
        print("Bad options provided!")
        usage()
        sys.exit()

    for opt, a in opts:
        if opt == "-s":
	    try:
                pid_number = open(pidfile,'r').readline()
                if pid_number:
                   sys.exit('Daemon is already running!')
            except Exception, e:
                pass
	   # try:
		#os.rename(outstream, "/tmp/telescope_old.log")
	    #except OSError, e:
		#pass

            print("Starting daemon!")
	    global conn
	    conn = astelco_TSI.astelco()
            daemon.start()

        elif opt == "--shutdown":

	    ####### THIS IS TO PREVENT WRONG SHUTDOWN ######

            if boolbox(msg='Do you want to shut down the Telescope?', title='Please Confirm', choices=('Yes', 'No')):     # show a Continue/Cancel dialog
	    	print "Confirm with password!"
	    else:
		sys.exit(0)           # user chose No		

	    if enterbox(msg='Please enter the password:', title='Please Confirm', default='') == "hej":

	        ################### call the shut down function ###################
                print("Preparing the telescope and dome for shut down!")
		print("1) Mirror covers will be closed!")
		print("2) Dome flap will be closed!")
		print("3) Dome slit will be closed!")
		print("4) The TCS daemon will be stopped!")
	        server1 = xmlrpclib.ServerProxy('http://'+str(song_telescope_config.SERVER_HOST1)+':'+str(song_telescope_config.SERVER_PORT1))
	        return_value = server1.shut_down_telescope("")
		if return_value == 1:
			print "The telescope was shut down" 
		else:
			print "Something went wrong when shutting down the telescope!"
		
	    else:
		print "Wrong password!"
		sys.exit(0)           # user chose Cancel

	    ################################################


	    ###################################################################
            print("Closing the connection!")
	    server1 = xmlrpclib.ServerProxy('http://'+str(song_telescope_config.SERVER_HOST1)+':'+str(song_telescope_config.SERVER_PORT1))
	    server1.shutdown_connection("")
            print("Stopping daemon!")
            daemon.stop()
	elif opt == "-t":
	    #if boolbox(msg='Do you want to shut down the Communicator Daemon?', title='Please Confirm', choices=('Yes', 'No')):     # show a Continue/Cancel dialog
	    #	print "The daemon will now be shut down regardsless of the telescope status!"
	    #else:
	    #	sys.exit(0)           # user chose No	

         #   if str(raw_input("Shutdown daemon [Y/N]: ")) != "Y":
         #      sys.exit("The Daemon was not shut down!")
         #   else:		
               print("Stopping daemon!")
               daemon.stop()
        elif opt == "-l":
            print("Logging is turned off")
        else:
            print("Option %s not supported!" % (opt))

if __name__ == "__main__":
	"""
		This is the first thing to be performed when and the module is started and this will call the main() function.
	"""
	try:
		main()
	except Exception, e:
		print e
		print "The TCS daemon has crashed at: ", clock.obstimeUT()
		send_song_mail.send_mail().sending_an_email(reciever=m_conf.notify_email_who,sender="SONG_MS",subject="TCS daemon Crash!",message="The TCS communication daemon has crashed!\n\nCheck the log file to see why!\n\nLog onto hw as the user obs and check the log file /home/obs/logs/telescope.log!")

		send_song_mail.send_mail().send_sms(receiver=m_conf.wakeup_sms_who, message="The TCS daemon has crashed for some reason!")

		time.sleep(5)

		send_song_mail.send_mail().sending_an_email(reciever=['support'],sender="SONG_MS",subject="TCS Crash!",message="The tcs communication daemon has crashed!\n\nCheck the log file /home/obs/logs/telescope.log.")


