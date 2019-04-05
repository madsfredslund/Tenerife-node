#!/usr/bin/python
'''
Created on 03-09-2010

@author: madsfa
 
'''
import xmlrpclib
import sys
import socket

########################################## TSI COMMANDS ##############################################
########################################## TSI COMMANDS ##############################################
########################################## TSI COMMANDS ##############################################

class GET_TSI(object):

	def __init__(self):
		try:
			self.server = xmlrpclib.ServerProxy('http://hw.ss3n1.prv:8130')
		except Exception, e:
			print e

	def get_connid(self,sender=""):
		value = ''
		try:
			value = self.server.get_connid(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get telescope connection if!'
			return_value = e

		return return_value

	def get_telescope_state(self,sender=""):
		value = ''
		try:
			value = self.server.get_telescope_state(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get telescope state!'
			return_value = e

		return return_value

	def get_telescope_motion_state(self,sender=""):
		value = ''
		try:
			value = self.server.get_telescope_motion_state(sender)
			if value != '':
				return_value = value

		except Exception, e:
			print 'Could not get telescope motion state!'
			print 'The TCS daemon was properly not running!'
			return_value = e

		return return_value

	def get_telescope_status_global(self,sender=""):
		value = ''
		try:
			value = self.server.get_telescope_status_global(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get telescope global status!'
			return_value = e

		return return_value

	def get_telescope_status_list(self,sender=""):
		value = ''
		try:
			value = self.server.get_telescope_status_list(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get telescope status list!'
			return_value = e

		return return_value

	def get_object_equatorial_epoch(self,sender=""):
		value = ''
		try:
			value = self.server.get_object_equatorial_epoch(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial epoch of object!'
			return_value = e

		return return_value

	def get_object_equatorial_equinox(self,sender=""):
		value = ''
		try:
			value = self.server.get_object_equatorial_equinox(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial equinox of object !'
			return_value = e

		return return_value

	def get_object_equatorial_ra(self,sender=""):
		value = ''
		try:
			value = self.server.get_object_equatorial_ra(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial ra of object!'
			return_value = e

		return return_value

	def get_object_solarsystem_object(self,sender=""):
		value = ''
		try:
			value = self.server.get_object_solarsystem_object(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial ra of object!'
			return_value = e

		return return_value

	def get_object_solarsystem_moon(self,sender=""):
		value = ''
		try:
			value = self.server.get_object_solarsystem_moon(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial ra of object!'
			return_value = e

		return return_value

	def get_object_tle_name(self,sender=""):
		value = ''
		try:
			value = self.server.get_object_tle_name(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get TLE name!'
			return_value = e

		return return_value

	def get_object_equatorial_dec(self,sender=""):
		value = ''
		try:
			value = self.server.get_object_equatorial_dec(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial dec of object!'
			return_value = e

		return return_value

	def get_pointing_track(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_track(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing track!'
			return_value = e

		return return_value

	def get_pointing_setup(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_setup(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing setup!'
			return_value = e

		return return_value

	def get_pointing_setup_use_port(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_setup_use_port(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing setup use port!'
			return_value = e

		return return_value

	def get_pointing_setup_derotator_syncmode(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_setup_derotator_syncmode(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing setup derotator syncmode!'
			return_value = e

		return return_value

	def get_pointing_setup_mechanical_derotator_syncmode(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_setup_mechanical_derotator_syncmode(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing setup mechanical derotator syncmode!'
			return_value = e

		return return_value

	def get_pointing_model_calculate(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_model_calculate(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing model RMS!'
			return_value = e

		return return_value

	def get_pointing_model_type(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_model_type(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing model type!'
			return_value = e

		return return_value

	def get_pointing_model_list(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_model_list(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing model list!'
			return_value = e

		return return_value

	def get_pointing_model_file(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_model_file(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing model measurement file!'
			return_value = e

		return return_value

	def get_pointing_model_file_list(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_model_file_list(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing model measurement file list!'
			return_value = e

		return return_value

	def get_pointing_setup_dome_syncmode(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_setup_dome_syncmode(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing setup dome syncmode!'
			return_value = e

		return return_value

	def get_pointing_setup_focus_syncmode(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_setup_focus_syncmode(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing setup focus syncmode!'
			return_value = e

		return return_value

	def get_pointing_setup_dome_max_deviation(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_setup_dome_max_deviation(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing setup dome max deviation!'
			return_value = e

		return return_value

	def get_pointing_setup_dome_offset(self,sender=""):
		value = ''
		try:
			value = self.server.get_pointing_setup_dome_offset(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing setup dome offset!'
			return_value = e

		return return_value


	def get_position_horizontal_az(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_horizontal_az(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get horizontal az of telescope!'
			return_value = e

		return return_value

	def get_position_horizontal_alt(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_horizontal_alt(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get horizontal alt of telescope!'
			return_value = e

		return return_value

	def get_position_horizontal_zd(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_horizontal_zd(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get horizontal zd of telescope!'
			return_value = e

		return return_value

	def get_position_horizontal_derotator(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_horizontal_derotator(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get the position of the horizontal derotator!'
			return_value = e

		return return_value

	def get_position_horizontal_dome(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_horizontal_dome(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get the position of the dome in horizontal coordinates!'
			return_value = e

		return return_value

	def get_position_equatorial_ra_j2000(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_equatorial_ra_j2000(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial ra_j2000 position!'
			return_value = e

		return return_value

	def get_position_equatorial_dec_j2000(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_equatorial_dec_j2000(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial dec_j2000 position!'
			return_value = e

		return return_value

	def get_position_equatorial_ra_current(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_equatorial_ra_current(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial ra_current position!'
			return_value = e

		return return_value

	def get_position_equatorial_dec_current(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_equatorial_dec_current(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial dec_current position!'
			return_value = e

		return return_value

	def get_object_equatorial_ra_pm(self,sender=""):
		value = ''
		try:
			value = self.server.get_object_equatorial_ra_pm(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get object equatorial pm in ra!'
			return_value = e

		return return_value

	def get_object_equatorial_dec_pm(self,sender=""):
		value = ''
		try:
			value = self.server.get_object_equatorial_dec_pm(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get object equatorial pm in dec!'
			return_value = e

		return return_value


	def get_position_equatorial_parallactic_angle(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_equatorial_parallactic_angle(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get equatorial parallactic angle position!'
			return_value = e

		return return_value

	def get_position_instrumental_zd_targetpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_instrumental_zd_targetpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get instrumental zd target position!'
			return_value = e

		return return_value

	def get_position_instrumental_zd_currpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_instrumental_zd_currpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get instrumental zd current position!'
			return_value = e

		return return_value

#### This function is deprecated ####
#	def get_position_instrumental_alt_currpos(self,sender=""):
#		value = ''
#		try:
#			value = self.server.get_position_instrumental_alt_currpos(sender)
#			if value != '':
#				return_value = value
#		except Exception, e:
#			print 'Could not get instrumental alt current position!'
#			return_value = e
#
#		return return_value

	def get_position_instrumental_az_currpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_instrumental_az_currpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get instrumental az current position!'
			return_value = e

		return return_value

	def get_position_instrumental_derotator_currpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_instrumental_derotator_currpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get instrumental derotator current position!'
			return_value = e

		return return_value

        def get_position_instrumental_derotator_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_derotator_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental derotator offset!'
                        return_value = e

                return return_value

	def get_position_mechanical_derotator_currpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_mechanical_derotator_currpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get mechanical derotator current position!'
			return_value = e

		return return_value

        def get_position_mechanical_derotator_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_mechanical_derotator_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get mechanical derotator offset!'
                        return_value = e

                return return_value

	def get_position_instrumental_focus_currpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_instrumental_focus_currpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get instrumental focus current position!'
			return_value = e

		return return_value

        def get_position_instrumental_focus_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_focus_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental focus offset!'
                        return_value = e

                return return_value


	def get_position_instrumental_port_select_currpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_instrumental_port_select_currpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get instrumental port_select current position!'
			return_value = e

		return return_value



        def get_position_instrumental_hexapod_x_currpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_x_currpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod x position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_x_realpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_x_realpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod real x position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_y_currpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_y_currpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod y position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_y_realpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_y_realpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod real y position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_z_currpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_z_currpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod z position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_z_realpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_z_realpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod real z position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_u_currpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_u_currpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod u position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_u_realpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_u_realpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod real u position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_v_currpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_v_currpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod v position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_v_realpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_v_realpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod real v position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_w_currpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_w_currpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod w position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_w_realpos(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_w_realpos(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod real w position!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_x_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_x_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod x offset!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_y_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_y_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod y offset!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_z_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_z_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod z offset!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_u_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_u_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod u offset!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_v_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_v_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod v offset!'
                        return_value = e

                return return_value

        def get_position_instrumental_hexapod_w_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_hexapod_w_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental hexapod w offset!'
                        return_value = e

                return return_value



        def get_position_instrumental_zd_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_zd_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental zd offset!'
                        return_value = e

                return return_value

        def get_position_instrumental_alt_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_alt_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental alt offset!'
                        return_value = e

                return return_value


        def get_position_instrumental_az_offset(self,sender=""):
                value = ''
                try:
                        value = self.server.get_position_instrumental_az_offset(sender)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental az offset!'
                        return_value = e

                return return_value

# AO
        def get_position_instrumental_ao_offset(self,sender="", bender_number=0):
                value = ''
                try:
                        value = self.server.get_position_instrumental_ao_offset(sender,bender_number)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental ao offset!'
                        return_value = e

                return return_value

        def get_position_instrumental_ao_currpos(self,sender="", bender_number=0):
                value = ''
                try:
                        value = self.server.get_position_instrumental_ao_currpos(sender, bender_number)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not get instrumental ao currpos!'
                        return_value = e

                return return_value

	def get_position_instrumental_dome_az_offset(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_instrumental_dome_az_offset(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get instrumental dome az offset!'
			return_value = e

		return return_value

	def get_position_instrumental_dome_az_currpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_instrumental_dome_az_currpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get instrumental dome az current position!'
			return_value = e

		return return_value

	def get_position_instrumental_dome_flap_currpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_instrumental_dome_flap_currpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get instrumental dome flap current position!'
			return_value = e

		return return_value

	def get_position_instrumental_dome_slit_currpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_position_instrumental_dome_slit_currpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get instrumental dome slit current position!'
			return_value = e

		return return_value

	def get_auxiliary_cover_realpos(self,sender=""):
		value = ''
		try:
			value = self.server.get_auxiliary_cover_realpos(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get mirror cover position!'
			return_value = e

		return return_value

	def get_auxiliary_temp_cabinet(self,sender=""):
		value = ''
		try:
			value = self.server.get_auxiliary_temp_cabinet(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get cabinet temperature!'
			return_value = e

		return return_value

	def get_auxiliary_temp_m1(self,sender=""):
		value = ''
		try:
			value = self.server.get_auxiliary_temp_m1(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get mirror 1 temperature!'
			return_value = e

		return return_value

	def get_auxiliary_temp_m2(self,sender=""):
		value = ''
		try:
			value = self.server.get_auxiliary_temp_m2(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get mirror 2 temperature!'
			return_value = e

		return return_value

	def get_auxiliary_temp_m3(self,sender=""):
		value = ''
		try:
			value = self.server.get_auxiliary_temp_m3(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get mirror 3 temperature!'
			return_value = e

		return return_value

	def get_auxiliary_ttelescope(self,sender=""):
		value = ''
		try:
			value = self.server.get_auxiliary_ttelescope(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get telescope temperature!'
			return_value = e

		return return_value

	def get_auxiliary_mancontrolspeed(self,sender=""):
		value = ''
		try:
			value = self.server.get_auxiliary_mancontrolspeed(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get the manual control speed!'
			return_value = e

		return return_value

	def get_sidereal_time(self,sender=""):
		value = ''
		try:
			value = self.server.get_sidereal_time(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get sidereal time!'
			return_value = e

		return return_value

	def get_UTC_time(self,sender=""):
		value = ''
		try:
			value = self.server.get_UTC_time(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get gps utc time!'
			return_value = e

		return return_value

	def get_pdu_light(self, sender="", pdu="container", outlet=23):
		value = ''
		try:
			value = self.server.get_pdu_light(sender, pdu, outlet)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pdu state!'
			return_value = e

		return return_value


