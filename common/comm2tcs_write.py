#!/usr/bin/python
'''
Created on 03-09-2010

@author: madsfa
 
'''
import xmlrpclib
import sys
import song_star_checker
import comm2tcs_read
import master_config as m_conf

gettsi = comm2tcs_read.GET_TSI()

########################################## TSI COMMANDS ##############################################
class SET_TSI(object):

	def __init__(self):
		try:
			self.server = xmlrpclib.ServerProxy('http://hw.ss3n1.prv:8130')
		except Exception, e:
			print e

	def shutdown_comm_daemon(self, sender=""):
		value = ''
		try:
			value = self.server.shutdown_connection(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not shutdown the connection!'
			return_value = e

		return return_value

	def set_telescope_ready(self, param=1,sender=""):
		value = ''
		try:
			value = self.server.set_telescope_ready(sender, param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set the telescope to ready!'
			return_value = e

		return return_value

	def set_telescope_stop(self,sender=""):
		value = ''
		try:
			value = self.server.set_telescope_stop(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not stop the telescope!'
			return_value = e

		return return_value

	def set_telescope_clear_panic(self,sender=""):
		value = ''
		try:
			value = self.server.set_telescope_clear_panic(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not clear the errors of the telescope!'
			return_value = e

		return return_value

	def set_telescope_clear_error(self,sender=""):
		value = ''
		try:
			value = self.server.set_telescope_clear_error(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not clear the errors of the telescope!'
			return_value = e

		return return_value

	def set_telescope_clear_warning(self,sender=""):
		value = ''
		try:
			value = self.server.set_telescope_clear_warning(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not clear the errors of the telescope!'
			return_value = e

		return return_value

	def set_telescope_clear_info(self,sender=""):
		value = ''
		try:
			value = self.server.set_telescope_clear_info(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not clear the errors of the telescope!'
			return_value = e

		return return_value

	def set_telescope_config_load(self,sender=""):
		value = ''
		try:
			value = self.server.set_telescope_config_load(sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not load tsi.conf for the telescope!'
			return_value = e

		return return_value

	def set_telescope_config_environment_temperature(self,sender="", param=""):
		value = ''
		try:
			value = self.server.set_telescope_config_environment_temperature(sender, param)
			if value != '':
				return_value = value
		except Exception, e:
			print e
			print 'Could not set environment temperature!'
			return_value = e

		return return_value

	def set_telescope_config_environment_pressure(self,sender="", param=""):
		value = ''
		try:
			value = self.server.set_telescope_config_environment_pressure(sender, param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set environment pressure!'
			return_value = e

		return return_value

	def set_object_equatorial_epoch(self, param=2000,sender=""):
		value = ''
		try:
			value = self.server.set_object_equatorial_epoch(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set equatorial epoch!'
			return_value = e

		return return_value

	def set_object_equatorial_equinox(self, param=2000,sender=""):
		value = ''
		try:
			value = self.server.set_object_equatorial_equinox(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set equatorial equinox!'
			return_value = e

		return return_value

	def set_object_solarsystem_object(self, param=6, sender=""):
		value = ''
		try:
			value = self.server.set_object_solarsystem_object(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set solar system object!'
			return_value = e

		return return_value

	def set_object_solarsystem_moon(self, param=1,sender=""):
		value = ''
		try:
			value = self.server.set_object_solarsystem_moon(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set solar system moon!'
			return_value = e

		return return_value

	def set_object_tle_line1(self, param="",sender=""):
		value = ''
		try:
			value = self.server.set_object_tle_line1(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set TLE line1 string!'
			return_value = e

		return return_value

	def set_object_tle_line2(self, param="",sender=""):
		value = ''
		try:
			value = self.server.set_object_tle_line2(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set TLE line2 string!'
			return_value = e

		return return_value


	def set_object_equatorial_ra(self, param=0.0,sender=""):
		value = ''
		try:
			value = self.server.set_object_equatorial_ra(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set equatorial ra!'
			return_value = e

		return return_value

	def set_object_equatorial_dec(self, param=0.0,sender=""):
		value = ''
		try:
			value = self.server.set_object_equatorial_dec(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set equatorial dec!'
			return_value = e

		return return_value


	def set_object_equatorial_ra_pm(self, param=0.0,sender=""):
		value = ''
		try:
			value = self.server.set_object_equatorial_ra_pm(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print e
			print 'Could not set equatorial ra pm!'
			return_value = e

		return return_value

	def set_object_equatorial_dec_pm(self, param=0.0,sender=""):
		value = ''
		try:
			value = self.server.set_object_equatorial_dec_pm(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set equatorial dec pm!'
			return_value = e

		return return_value

	def set_object_horizontal_alt(self, param=85.0,sender=""):
		value = ''
		try:
			value = self.server.set_object_horizontal_alt(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set horizontal altitude of object!'
			return_value = e

		return return_value

	def set_object_horizontal_az(self, param=90.0,sender=""):
		value = ''
		try:
			value = self.server.set_object_horizontal_az(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set horizontal azimuth of object!'
			return_value = e

		return return_value

	def set_pointing_track(self, param=0,sender=""):
		### Checks if object is above x degrees over the horizon. If not telescope will not move.
		if int(param) > 0:
			star_handle = song_star_checker.star_pos(site=1)
			sun_handle = song_star_checker.sun_pos(site=1)
			ra_object = gettsi.get_object_equatorial_ra(sender="Mads")
			dec_object = gettsi.get_object_equatorial_dec(sender="Mads")

			sun_dist = float(str(sun_handle.sun_dist(ra_object, dec_object)).split(":")[0])
			sun_alt = float(str(sun_handle.sun_alt()).split(":")[0])

#			if sun_alt >= 0.0 and sun_dist < 45.0:
#				print "The Sun is too close to the pointing position... the telescope will not go there...!!!"
#				return "Sun too close"

			object_alt = int(str(star_handle.star_alt(ra_object, dec_object)).split(":")[0])	
			if object_alt < m_conf.telescope_min_altitude:	# Hardcoded limit... because of the cooling unit.
				return "Object too low"

		value = ''
		try:
			value = self.server.set_pointing_track(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set pointing track!'
			return_value = e

		return return_value

	def set_pointing_setup(self, param=0,sender=""):
		value = ''
		try:
			value = self.server.set_pointing_setup(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set pointing track!'
			return_value = e

		return return_value

	def set_pointing_setup_use_port(self, param=2,sender=""):
		value = ''
		try:
			value = self.server.set_pointing_setup_use_port(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set pointing port!'
			return_value = e

		return return_value

	def set_pointing_model_calculate(self, param=2,sender=""):
		value = ''
		try:
			value = self.server.set_pointing_model_calculate(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not calculate pointing model!'
			return_value = e

		return return_value

	def set_pointing_model_type(self, param=2,sender=""):
		value = ''
		try:
			value = self.server.set_pointing_model_type(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set pointing model type!'
			return_value = e

		return return_value

	def set_pointing_model_add(self, param="",sender=""):
		value = ''
		try:
			value = self.server.set_pointing_model_add(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not add pointing model measurement!'
			return_value = e

		return return_value

	def set_pointing_model_file(self, param="",sender=""):
		value = ''
		try:
			value = self.server.set_pointing_model_file(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set pointing model measurement file!'
			return_value = e

		return return_value

	def set_pointing_model_load(self, param=1,sender=""):
		value = ''
		try:
			value = self.server.set_pointing_model_load(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not load pointing model measurement file!'
			return_value = e

		return return_value

	def set_pointing_model_save(self, param="",sender=""):
		value = ''
		try:
			value = self.server.set_pointing_model_save(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not save pointing model measurement file!'
			return_value = e

		return return_value

	def set_pointing_setup_dome_syncmode(self, param="",sender=""):
		value = ''
		try:
			value = self.server.set_pointing_setup_dome_syncmode(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set pointing setup dome syncmode!'
			return_value = e

		return return_value

	def set_pointing_setup_focus_syncmode(self, param="",sender=""):
		value = ''
		try:
			value = self.server.set_pointing_setup_focus_syncmode(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set pointing setup focus syncmode!'
			return_value = e

		return return_value

	def set_pointing_setup_dome_max_deviation(self, param="",sender=""):
		value = ''
		try:
			value = self.server.set_pointing_setup_dome_max_deviation(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set pointing setup dome max deviation!'
			return_value = e

		return return_value

	def set_pointing_setup_dome_offset(self, param="",sender=""):
		value = ''
		try:
			value = self.server.set_pointing_setup_dome_offset(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set pointing setup dome offset!'
			return_value = e

		return return_value

	def set_position_instrumental_dome_az_offset(self, param=0,sender=""):
		value = ''
		try:
			value = self.server.set_position_instrumental_dome_az_offset(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set position instrumental dome az offset!'
			return_value = e

		return return_value

	def set_position_instrumental_dome_flap_targetpos(self, param=0,sender=""):
		value = ''
		try:
			value = self.server.set_position_instrumental_dome_flap_targetpos(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set position instrumental dome flap targetpos!'
			return_value = e

		return return_value

	def set_position_instrumental_dome_slit_targetpos(self, param=0,sender=""):
		value = ''
		try:
			value = self.server.set_position_instrumental_dome_slit_targetpos(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set position instrumental dome slit targetpos!'
			return_value = e

		return return_value

#############################################

        def set_position_instrumental_derotator_targetpos(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_derotator_targetpos(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental derotator target position!'
                        return_value = e

                return return_value

        def set_position_instrumental_derotator_offset(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_derotator_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental derotator offset!'
                        return_value = e

                return return_value

        def set_position_mechanical_derotator_targetpos(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_mechanical_derotator_targetpos(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set mechanical derotator target position!'
                        return_value = e

                return return_value

        def set_position_mechanical_derotator_offset(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_mechanical_derotator_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set mechanical derotator offset!'
                        return_value = e

                return return_value

	def set_pointing_setup_derotator_syncmode(self, param=0,sender=""):
		value = ''
		try:
			value = self.server.set_pointing_setup_derotator_syncmode(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing setup derotator syncmode!'
			return_value = e

		return return_value

	def set_pointing_setup_mechanical_derotator_syncmode(self, param=0,sender=""):
		value = ''
		try:
			value = self.server.set_pointing_setup_mechanical_derotator_syncmode(param,sender)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not get pointing setup mechanical derotator syncmode!'
			return_value = e

		return return_value

        def set_position_instrumental_hexapod_x_targetpos(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_x_targetpos(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod x target position!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_y_targetpos(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_y_targetpos(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod y target position!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_z_targetpos(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_z_targetpos(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod z target position!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_u_targetpos(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_u_targetpos(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod u target position!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_v_targetpos(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_v_targetpos(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod v target position!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_w_targetpos(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_w_targetpos(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod w target position!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_x_offset(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_x_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod x offset!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_y_offset(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_y_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod y offset!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_z_offset(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_z_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod z offset!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_u_offset(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_u_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod u offset!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_v_offset(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_v_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod v offset!'
                        return_value = e

                return return_value

        def set_position_instrumental_hexapod_w_offset(self, param=0,sender=""):
                value = ''
                try:
                        value = self.server.set_position_instrumental_hexapod_w_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set instrumental hexapod w offset!'
                        return_value = e

                return return_value

        def set_position_instrumental_focus_targetpos(self, param=0,sender=""):
		value = ''
                try:
                        value = self.server.set_position_instrumental_focus_targetpos(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set position instrumental focus targetpos!'
                        return_value = e

                return return_value

        def set_position_instrumental_focus_offset(self, param=0,sender=""):
		value = ''
                try:
                        value = self.server.set_position_instrumental_focus_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set position instrumental focus offset!'
                        return_value = e

                return return_value

        def set_position_instrumental_az_offset(self, param=0,sender=""):
		value = ''
                try:
                        value = self.server.set_position_instrumental_az_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set position instrumental az offset!'
                        return_value = e

                return return_value

        def set_position_instrumental_alt_offset(self, param=0,sender=""):
		value = ''
                try:
                        value = self.server.set_position_instrumental_alt_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set position instrumental alt offset!'
                        return_value = e

                return return_value

        def set_position_instrumental_zd_offset(self, param=0,sender=""):
		value = ''
                try:
                        value = self.server.set_position_instrumental_zd_offset(sender,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set position instrumental zd offset!'
                        return_value = e

                return return_value

# AO
        def set_position_instrumental_ao_offset(self, param=0, sender="", bender_number=0):
		t_power = gettsi.get_telescope_state()
		if t_power != "1.0":
			return "Need power on telescope"

		value = ''
                try:
                        value = self.server.set_position_instrumental_ao_offset(sender,bender_number,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set position instrumental ao offset!'
                        return_value = e

                return return_value

        def set_position_instrumental_ao_targetpos(self, param=0,sender="", bender_number=0):
		t_power = gettsi.get_telescope_state()
		if t_power != "1.0":
			return "Need power on telescope"
		value = ''
                try:
                        value = self.server.set_position_instrumental_ao_targetpos(sender,bender_number,param)
                        if value != '':
                                return_value = value
                except Exception, e:
                        print 'Could not set position instrumental ao targetpos!'
                        return_value = e

                return return_value


	def set_auxiliary_cover_targetpos(self, param=0,sender=""):
		value = ''
		try:
			value = self.server.set_auxiliary_cover_targetpos(sender,param)
			if value != '':
				return_value = value
		except Exception, e:
			print 'Could not set mirror cover position!'
			return_value = e

		return return_value
	
	def switch_light(self, sender="", pdu='container', outlet=23, status=1):	
		try:
			value = self.server.set_pdu_light(sender, pdu, outlet, status)
			if value == 1:				
				return_value = "done"
			else:
				return_value = value
		except Exception, e:
			print e
			print 'Could not switch light!'
			return_value = e


class SET_OTHER(object):

	def __init__(self):
		try:
			self.server = xmlrpclib.ServerProxy('http://hw.ss3n1.prv:8030')
		except Exception, e:
			print e

	def shut_down_telescope(self,sender=""):
		try:
			value = self.server.shut_down_telescope(sender)
			if value == 1:				
				return_value = "done"
			else:
				return_value = value
		except Exception, e:
			print 'Could not shut down the telescope!'
			return_value = e

		return return_value

	def startup_telescope(self,sender=""):
		try:
			value = self.server.startup_telescope(sender)
			if value == 1:				
				return_value = "done"
			else:
				return_value = value
		except Exception, e:
			print 'Could not start up the telescope!'
			return_value = e

		return return_value




		return return_value



