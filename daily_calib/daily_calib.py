#!/usr/bin/python

import sys
import os
import time
import xmlrpclib
import song_timeclass
import numpy
import string
import pyfits
import mfa
import daily_config
import update_song_database
import song_database_tables
import get_db_values
import psycopg2
from scipy.optimize import curve_fit
from scipy.interpolate import UnivariateSpline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import Set_M8
import subprocess
import slit_module
import send_song_mail
import master_config as m_conf
import gc
import datetime
import scipy.ndimage as ndimage
from scipy import signal
import lmfit
from scipy.optimize import leastsq
from numpy import sqrt, pi, exp, loadtxt

plt.ioff()

sigu = slit_module.SIGU()

#####################################

clock = song_timeclass.TimeClass()

#host = "192.168.66.65"	# Tenerife site
#user = "postgres"
#db = "db_tenerife"
#password = ""
host = m_conf.db_host	# Tenerife site
user = m_conf.db_user
db = m_conf.data_db
password = m_conf.db_password

########################################################################
DMC_PATH =  daily_config.DMC_PATH
ANDOR_PATH = daily_config.ANDOR_PATH
SLIT_PATH = daily_config.SLIT_PATH
ccd_server = xmlrpclib.ServerProxy('http://%s:%s' % (m_conf.ccd_server, m_conf.ccd_port))

sys.path.append(DMC_PATH) 
import pst		
import lamp
########################################################################


class ACQ_CALIBS(object):
	"""
		@brief: This class will acquire calibration spectres. 

	"""
	def __init__(self):
		self.bias_mean = 0
		self.bias_rms = 0
		self.bias_std = 0
		self.thar_xoff1 = 0
		self.thar_yoff1 = 0
		self.thar_xoff1 = 0
		self.thar_yoff2 = 0

	def get_fields(self, table_name, fields):
		field_str = ''
		for field in fields:
	 		field_str += field
	 		field_str += ','
		field_str = field_str[0:-1]

		conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (host, db, user, password))
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

	def restart_sigu(self):
		#### stop and start slit guider:
		try:
			os.popen("python /home/obs/programs/guiders/slit/slit_guider.py -t", "w")
		except Exception, e:
			print "Something went wrong when trying to stop slit guider!"
			print e

		time.sleep(20)

		try:
			os.popen("python /home/obs/programs/guiders/slit/slit_guider.py -s", "w")
		except Exception, e:
			print "Something went wrong when trying to start slit guider!"
			print e

		time.sleep(20)

		val = sigu.exec_action("pause")	
		if val != "done":
			print "Return value of sigu pause was: ", val
			return "no_go"
		else:
			print "Sigu pause performed correctly..."

		val = sigu.exec_action("moveto", ["idle"])	
		if val != "done":
			print "Return value of sigu moveto idle was: ", val
			return "no_go"
		else:
			print "Sigu movto idle performed correctly..."

		return 1

	def calibration_spectres(self):

		##########################

		number_of_bias = daily_config.number_of_bias
		number_of_flats = daily_config.number_of_flats
		number_of_flatsi2 = daily_config.number_of_flatsi2
		number_of_thar = daily_config.number_of_thar
		slit = daily_config.slit

		##########################


		def acq_spectres(exptime, imagetype, daynight, nofs, spec_name):
			_object = imagetype

			for i in range(nofs):
				e = None
				value = ""

				if spec_name == "":
					filename = "daily_%s_%i.fits" % (string.lower(imagetype),i+1)
				else:
					filename = spec_name

				try:
					#value = ccd_server.acquire_an_image(filename, req_no, exptime, hsspeed, pregain, highcap, hbin, vbin, acmode, hstart, hend, vstart, vend, imagetype, _object, obj_ra, obj_dec, daynight)
					value = ccd_server.acquire_an_image(filename, "", exptime, 1, 2, 0, 1, 1, 1, 1, 2088, 1, 2048, imagetype, _object, "00:00:00", "00:00:00", daynight, "")
				except Exception, e:
					print 'error'
					sys.exit()
				if e != None:
					print e
					print "String returned: ", value
					sys.exit()
				elif value == 2:
					print "Something was wrong!\nCheck if directory permissions are OKAY!"
					sys.exit()
				else:
					#print "%s number %i out of %i was acquired!" % (imagetype, i+1, nofs)
					i +=1


			### Move collected images to calib folder
			image_folder = "/scratch/star_spec/%s/day/raw/" % time.strftime("%Y%m%d", time.localtime())

			if os.path.exists(image_folder):
				if not os.path.exists(image_folder+"/calib"):
					try:
						os.mkdir(image_folder+"/calib")
					except Exception, e:
						print e

				try:
					string_check = "daily_%s" % string.lower(imagetype)
					for file_in_dir in os.listdir(image_folder):		
						if string_check in file_in_dir:
							os.rename(image_folder+file_in_dir, image_folder+"/calib/"+file_in_dir)
				except Exception, e:
					print e	
	


		#########################################################################
		#---------------------
		value = pst.PST().move(3,2) 	# Move iodine cell out ouf light path
		value = pst.PST().move(2,3) 	# Move Mirror slide to Beam Splitter cube position
		value = pst.PST().move(6,slit) 	# Move slit to right position
		value = pst.PST().move(1,4) 	# Move Filter wheel to position 4 (Free)

		#################################
		### ThAr exposures:
		#################################
		value = pst.PST().move(4,3) 
		value = lamp.Lamp(lamp='halo').set_off()
		value = lamp.Lamp(lamp='thar').set_on()

		exptime = daily_config.thar_exptime
		imagetype = "THAR"
		daynight = "day"


		#### Making sure M8 is correctly positioned!
		Set_M8.set_m8_pos()
		##### Collecting the spectres:
		acq_spectres(exptime, imagetype, daynight, number_of_thar, "")
		#####

		value = lamp.Lamp(lamp='thar').set_off()

		#######################
		####### bias:
		#######################

		exptime = 0.0
		imagetype = "BIAS"
		daynight = "day"

		##### Collecting the spectres:
		acq_spectres(exptime, imagetype, daynight, number_of_bias, "")
		#####


		##################################
		### 10 Flat fields without I2:
		##################################

		value = pst.PST().move(4,2) 	# Move calibration mirror into light path
		value = lamp.Lamp(lamp='halo').set_on()	# Turn on the Halogen lamp
		value = lamp.Lamp(lamp='thar').set_off() # Turn off the ThAr lamp if it was on

		exptime = daily_config.flat_exptime
		imagetype = "FLAT"
		daynight = "day"

		#### Making sure M8 is correctly positioned!
		Set_M8.set_m8_pos()
		##### Collecting the spectres:
		acq_spectres(exptime, imagetype, daynight, number_of_flats, "")
		#####


		##################################
		### 10 Flat fields with I2:
		##################################

		value = pst.PST().move(3,3) 	# Move iodine cell into light path

		exptime = daily_config.flati2_exptime
		imagetype = "FLATI2"
		daynight = "day"

		##### Collecting the spectres:
		acq_spectres(exptime, imagetype, daynight, number_of_flatsi2, "")
		#####

		value = lamp.Lamp(lamp='halo').set_off()


		try:
			os.popen("python /home/obs/programs/guiders/slit/slit_guider.py -t", "w")
		except Exception, e:
			print "Something went wrong when trying to stop slit guider!"
			print e

		#######################################
		#######################################
		#######################################
		##### combining to master images ######
		#######################################

		image_folder = "/scratch/star_spec/%s/day/raw/" % time.strftime("%Y%m%d", time.localtime())

		try:
			os.mkdir(image_folder+"calib/masters/")
		except Exception, e:
			print e

		calib_files = os.listdir(image_folder+"calib/")



		#### Master BIAS ######
		j = 1
		for calib_file in calib_files:
			if "bias_" in calib_file:
				tmp_im, tmp_hdr = pyfits.getdata(image_folder+"calib/"+calib_file, header=True)
				if j == 1:
					new_im = tmp_im
				else:
					new_im = tmp_im + new_im
	
				j += 1

		mean_im = new_im / j

		self.bias_std = mfa.std(mean_im)
		self.bias_rms = mfa.rms(mean_im)
		self.bias_mean = mfa.mean(mean_im)

		print "Master BIAS [mean, rms, std]: ", self.bias_mean, self.bias_rms, self.bias_std, "	", clock.whattime()

		tmp_hdr.update('--CALIB-', '-------CALIB------', comment='-------------------------------------')
		file_name = tmp_hdr["FILE"]
		tmp_hdr.update('FILE',file_name, comment='File used for the header')
		tmp_hdr.update('RMS', self.bias_rms, comment='RMS value of master')
		tmp_hdr.update('MEAN', self.bias_mean, comment='Mean value of master')
		tmp_hdr.update('STD', self.bias_std, comment='Standard deviation of master')


		### Create int image...
		stacked_im = mean_im.astype('int')
		hdu = pyfits.PrimaryHDU(stacked_im)
		hdu.header = tmp_hdr
		hdu.scale('uint16')


		try:
			hdu.writeto(image_folder+"calib/masters/daily_bias_master.fits")
			#print "Master bias was created at: ", clock.whattime()
		except Exception, e:
			print "Image already exists: %s" % (image_folder+"calib/masters/daily_bias_master.fits")

		### Clearing memory again
		mean_im = []
		new_im = []
		tmp_im = []	
		stacked_im = []	

		#### Master FLAT ######
		j = 1
		for calib_file in calib_files:
			if "flat_" in calib_file:
				tmp_im, tmp_hdr = pyfits.getdata(image_folder+"calib/"+calib_file, header=True)
				if j == 1:
					new_im = tmp_im
				else:
					new_im = tmp_im + new_im
	
				j += 1

		mean_im = new_im / j

		### Create int image...
		stacked_im = mean_im.astype('int')
		hdu = pyfits.PrimaryHDU(stacked_im)
		hdu.header = tmp_hdr
		hdu.scale('uint16')


		try:
			hdu.writeto(image_folder+"calib/masters/daily_flat_master.fits")
			#print "Master flat was created at: ", clock.whattime()
		except Exception, e:
			print e

		### Clearing memory again
		mean_im = []
		new_im = []
		tmp_im = []
		stacked_im = []

		#### Master FLATI2 ######
		j = 1
		for calib_file in calib_files:
			if "flati2_" in calib_file:
				tmp_im, tmp_hdr = pyfits.getdata(image_folder+"calib/"+calib_file, header=True)
				if j == 1:
					new_im = tmp_im
				else:
					new_im = tmp_im + new_im
	
				j += 1

		mean_im = new_im / j

		### Create int image...
		stacked_im = mean_im.astype('int')
		hdu = pyfits.PrimaryHDU(stacked_im)
		hdu.header = tmp_hdr
		hdu.scale('uint16')


		try:
			hdu.writeto(image_folder+"calib/masters/daily_flati2_master.fits")
			#print "Master flati2 was created at: ", clock.whattime()
		except Exception, e:
			print e

		try:

			#### TAKE DARK FRAMES ####
			exptime1 = 300	# 5 min
			exptime2 = 1800	# 30 min
			imagetype = "DARK"
			daynight = "day"
			number_of_darks = 1
			acq_spectres(exptime1, imagetype, daynight, number_of_darks, "daily_dark_1.fits")
			acq_spectres(exptime2, imagetype, daynight, number_of_darks, "daily_dark_2.fits")
			#####
		except Exception, e:
			print "Could not acquire dark frames..."
			print e

		### Clearing memory again
		mean_im = []
		new_im = []
		tmp_im = []
		stacked_im = []

		return 1

	def use_evening_spectre(self):

		### Folders with fits files datetime.datetime.strftime(datetime.datetime.utcnow(),"%Y-%m-%d")
		self.folder_date = datetime.datetime.strftime(datetime.datetime.utcnow() - datetime.timedelta(days=1), "%Y%m%d")
		self.folder_year = datetime.datetime.strftime(datetime.datetime.utcnow() - datetime.timedelta(days=1), "%Y")		
		self.raw_image_folder = "/scratch/star_spec/%s/night/raw/" % self.folder_date
		self.raw_thar_image_folder = "/scratch/star_spec/%s/day/raw/" % self.folder_date
		self.master_image_folder = "/scratch/extr_spec/%s/%s/night/calib_master/" % (self.folder_year, self.folder_date)

		# Master bias
		master_bias_filename = "masterbias_%s.fits" % (self.folder_date)
		tmp_im, tmp_hdr = pyfits.getdata(self.master_image_folder+master_bias_filename, header=True)

		self.bias_std = mfa.std(tmp_im)
		self.bias_rms = mfa.rms(tmp_im)
		self.bias_mean = mfa.mean(tmp_im)
		
		#print self.bias_mean, self.bias_std, self.bias_rms

		return 1


	def check_offset(self):
		"""
			@brief: This will make a crosscorelation of the ThAr spectres (between today and yesterday).
		"""
		im1_name = daily_config.im_ref_1 ## REFERENCE
		#im2_name = "/scratch/star_spec/%s/day/raw/calib/daily_thar_1.fits" % time.strftime("%Y%m%d", time.localtime())
		im2_name = self.raw_thar_image_folder + "daily_thar_1.fits"

		im1,hdr1 = pyfits.getdata(im1_name, header=True)
		im2,hdr2 = pyfits.getdata(im2_name, header=True)

	        self.xoff1 = 999
	        self.yoff1 = 999

		try:
		        self.xoff1, self.yoff1 = mfa.findshift(im2[daily_config.cc_start:daily_config.cc_end,daily_config.cc_start:daily_config.cc_end], im1[daily_config.cc_start:daily_config.cc_end,daily_config.cc_start:daily_config.cc_end])
		except Exception,e:
			print e
			try:
				self.xoff1, self.yoff1 = mfa.findshift(im1[daily_config.cc_start:daily_config.cc_end,daily_config.cc_start:daily_config.cc_end], im2[daily_config.cc_start:daily_config.cc_end,daily_config.cc_start:daily_config.cc_end])
				self.xoff1 = - self.xoff1
				self.yoff1 = - self.yoff1
			except Exception,e:
				print e


		print "ThAr shifts 1 [xoff, yoff]: ", "[",self.xoff1, ",", self.yoff1, "]	", clock.whattime()

		hdr2.update('--CALIB-', '-------CALIB------', comment='-------------------------------------')
		hdr2.update('XOFF', self.xoff1, comment='Shift in x from yesterday')
		hdr2.update('YOFF', self.yoff1, comment='Shift in y from yesterday')
		
		pyfits.update(im2_name, im2, hdr2)

		############# Second thar image ############

		im3_name = daily_config.im_ref_2 ## REFERENCE
		#im4_name = "/scratch/star_spec/%s/day/raw/calib/daily_thar_2.fits" % time.strftime("%Y%m%d", time.localtime())
		im4_name = self.raw_thar_image_folder + "daily_thar_2.fits"

		im3,hdr3 = pyfits.getdata(im3_name, header=True)
		im4,hdr4 = pyfits.getdata(im4_name, header=True)

	        self.xoff2 = 999
	        self.yoff2 = 999

		try:
			self.xoff2, self.yoff2 = mfa.findshift(im4[daily_config.cc_start:daily_config.cc_end,daily_config.cc_start:daily_config.cc_end], im3[daily_config.cc_start:daily_config.cc_end,daily_config.cc_start:daily_config.cc_end])
		except Exception, e:
		        self.xoff2, self.yoff2 = mfa.findshift(im3[daily_config.cc_start:daily_config.cc_end,daily_config.cc_start:daily_config.cc_end], im4[daily_config.cc_start:daily_config.cc_end,daily_config.cc_start:daily_config.cc_end])
			self.xoff2 = - self.xoff2
			self.yoff2 = - self.yoff2
			print e

		print "ThAr shifts 2 [xoff, yoff]: ", "[",self.xoff2, ",", self.yoff2, "]	", clock.whattime()

		hdr4.update('--CALIB-', '-------CALIB------', comment='-------------------------------------')
		hdr4.update('XOFF', self.xoff2, comment='Shift in x from yesterday')
		hdr4.update('YOFF', self.yoff2, comment='Shift in y from yesterday')	

		pyfits.update(im4_name, im4, hdr4)


		if numpy.abs(self.xoff1) > daily_config.max_xy_offset or numpy.abs(self.yoff1) > daily_config.max_xy_offset or numpy.abs(self.xoff2) > daily_config.max_xy_offset or numpy.abs(self.yoff2) > daily_config.max_xy_offset:
			send_song_mail.send_mail().sending_an_email(reciever=["mads"],sender="SONG_MS",subject="ThAr movement!",message="The daily calibration script detected a shift in the ThAr spectrum of %s in X and %s in Y.\n\nThis was too much. Please check!" % (self.xoff1, self.yoff1))

		else:
			#########################################################################################################
			#### Write to db ####
			#########################################################################################################
		
			maintenance_values = self.get_fields("maintenance", ["maintenance_id"])	
	
			try:
				if not maintenance_values["maintenance_id"]:
					maintenance_id = 0
				else:
					maintenance_id = int(maintenance_values["maintenance_id"])	
			except Exception,e:
				maintenance_id = 0


			tid = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

			params = "(maintenance_id, bias_mean, bias_rms, bias_std, thar_xoff1, thar_yoff1, thar_xoff2, thar_yoff2, thar_line_width_1, thar_line_width_2, spec_focus, spec_resolution , blaze_peak_level, extra_param_1, extra_param_2, extra_param_3, extra_param_4, extra_param_5, extra_param_6, extra_param_7, extra_param_8, extra_param_9, extra_param_10, extra_value_1, extra_value_2, extra_value_3, extra_value_4, extra_value_5, extra_value_6, extra_value_7, extra_value_8, extra_value_9, extra_value_10, ins_at)"

			values = "(%i, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, '%s')" % (maintenance_id+1, self.bias_mean, self.bias_rms, self.bias_std, self.xoff1, self.yoff1, self.xoff2, self.yoff2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 99.0, 99.0, 99.0, 99.0, 99.0, 99.0, 0.0, 0.0, 0.0, 0.0, tid)
	
			try:
				update_song_database.insert("maintenance", params, values)
			except Exception, e:
				print "An error occured at insertion of data to database: ", e


		im1 = []
		im2 = []
		im3 = []
		im4 = []

		return 1

	def calc_line_width(self):
		"""
			@brief: This function will determine the width of two specific spectral lines in the ThAr 1 exposure. 
		"""

		if numpy.abs(self.xoff1) > daily_config.max_xy_offset or numpy.abs(self.yoff1) > daily_config.max_xy_offset or numpy.abs(self.xoff2) > daily_config.max_xy_offset or numpy.abs(self.yoff2) > daily_config.max_xy_offset:
			#try:
			#	update_song_database.update("maintenance", ["thar_line_width_1", "thar_line_width_2", "extra_param_1", "extra_param_2"], [0, 0, 0, 0], "maintenance_id")
			#except Exception, e:
			#	print "An error occured at update of data to database: ", e
			print "Something did not go well with the cross corr!"

			return 1
		else:
			#im_name = "/scratch/star_spec/%s/day/raw/calib/daily_thar_1.fits" % time.strftime("%Y%m%d", time.localtime())
			im_name = self.raw_thar_image_folder + "daily_thar_1.fits"
			im = pyfits.getdata(im_name, header=False)

			#chunk_2 = im[1367+self.yoff1:1397+self.yoff1,204+self.xoff1]	# left-to side of CCD:		FWHM = 3.4615	- Worst : Res ~			
			#chunk_8 = im[285+self.yoff1:315+self.yoff1,1850+self.xoff1]	# right-bottom side of CCD:	FWHM = 1.9758	- Best : Res ~ 

			chunk_2 = im[(daily_config.thar1_y - daily_config.line_area) + self.yoff1 : (daily_config.thar1_y + daily_config.line_area) + self.yoff1 , daily_config.thar1_x + self.xoff1]	# left-to side of CCD:	FWHM = 3.4615	- Worst : Res~			
			chunk_8 = im[(daily_config.thar2_y - daily_config.line_area) + self.yoff1 : (daily_config.thar2_y + daily_config.line_area) + self.yoff1 , daily_config.thar2_x + self.xoff1]	# right-bottom side of CCD:	FWHM = 1.9758	- Best : Res ~ 



			background_1 = numpy.min(chunk_2)
			background_2 = numpy.min(chunk_8)
			coeff = [20000., 20.0, 3.0]

			try:
				new_x1, new_y1, bla, y_max1 = mfa.fit_with_gauss(range(len(chunk_2)),chunk_2-background_1, coeffi=coeff)	# LINE 1 ( Worst )

#				plt.plot(new_x1, new_y1, "-r")
#				plt.plot(range(len(chunk_2)),chunk_2-background_1, "b*")
#				plt.savefig(daily_config.web_images_dir+"test1.jpg")
#				plt.clf()
#				plt.close()
	
				new_x2, new_y2, bla, y_max2 = mfa.fit_with_gauss(range(len(chunk_8)),chunk_8-background_2, coeffi=coeff)	# LINE 2 ( Best )
#				plt.plot(new_x2, new_y2, "-r")
#				plt.plot(range(len(chunk_8)),chunk_8-background_2, "b*")
#				plt.savefig(daily_config.web_images_dir+"test2.jpg")

				line_width_1 = mfa.fwhm(new_x1, new_y1)		# Line width in pixels
				res_1 = (4000.0 / (float(line_width_1)*0.020))   # ~ resolution 
				print "Resolution in left side of CCD: ", res_1

				line_width_2 = mfa.fwhm(new_x2, new_y2)		# Line width in pixels
				res_2 = (6000.0 / (float(line_width_2)*0.024)) 	# ~ resolution
				print "Resolution in right side of CCD: ", res_2

			except Exception,e:
				print e
				print "Could not fit with a gaussian!"
				
			else:

				try:
					update_song_database.update("maintenance", ["thar_line_width_1", "thar_line_width_2", "extra_param_1", "extra_param_2", "extra_param_3", "extra_param_4"], [line_width_1, line_width_2, y_max1, y_max2, res_1, res_2 ], "maintenance_id")
				except Exception, e:
					print "An error occured at update of data to database: ", e

				#### Create plots of line profile:
				#### line 1				
				plt.figure(figsize=(5.0, 4.0),facecolor='w', edgecolor='k')
				plt.subplots_adjust(left=0.17, bottom=0.20, right=0.95, top=0.90, wspace=0.4, hspace=0.3)
				ax=plt.subplot(111)

				plt.plot(range(len(chunk_2)), chunk_2-background_1, 'b*-')
				plt.plot(new_x1, new_y1, 'r-')

				plt.ylabel("Pixel count", size=10)
				plt.xlabel("Pixel number", size=10)
				plt.title("Line 1 profile" + " - " + time.strftime("%Y-%m-%d", time.localtime()), size=10)
				
				plt.savefig(daily_config.web_images_dir+"line1_profile.jpg")

				#### line 2
				plt.figure(figsize=(5.0, 4.0),facecolor='w', edgecolor='k')
				plt.subplots_adjust(left=0.17, bottom=0.20, right=0.95, top=0.90, wspace=0.4, hspace=0.3)
				ax=plt.subplot(111)

				plt.plot(range(len(chunk_8)), chunk_8-background_2, 'b*-')
				plt.plot(new_x2, new_y2, 'r-')

				plt.ylabel("Pixel count", size=10)
				plt.xlabel("Pixel number", size=10)
				plt.title("Line 2 profile" + " - " + time.strftime("%Y-%m-%d", time.localtime()), size=10)
				
				plt.savefig(daily_config.web_images_dir+"line2_profile.jpg")


			im = []

			return 1


	def create_plots(self):
		"""
			@brief:
				This function will create plots to show on the web page.

		"""	
		values_to_plot = ["bias_mean", "bias_rms", "bias_std", "thar_line_width_1", "thar_line_width_2", "extra_param_1", "extra_param_2", "extra_param_3", "extra_param_4", "thar_xoff1", "thar_yoff1","extra_value_7"]
		titles_to_plot = ["Bias Mean Level", "Bias RMS", "Bias Standard Deviation", "ThAr Line Width 1", "ThAr Line Width 2", "ThAr Line Peak 1", "ThAr Line Peak 2", "Spectral resolution - ThAr Line 1", "Spectral resolution - ThAr Line 2", "ThAr displacement in X","ThAr displacement in Y", "Number ThAr lines"]
		yvalues_to_plot = ["Mean Value", "RMS Value", "STD Value", "Line Width [pixels]", "Line Width [pixels]", "Peak Value", "Peak Value", "Resolution", "Resolution", "Pixels", "Pixels", "Number of lines"]

		## What should be added and subtracted to the max and min values on the y-axis?
		ylims = [25.0, 25.0, 1.0, 1.0, 1.0, 1000.0, 1000.0, 1000.0, 1000.0, 1.0, 1.0, 50.]

		def get_data(field_name, timeint):
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (host, db, user, password))
			curr = conn.cursor()
			curr.execute("SELECT %s, ins_at, maintenance_id FROM maintenance WHERE maintenance_id > (SELECT max(maintenance_id) FROM maintenance) - %s order by ins_at ASC" % (field_name, str(timeint)))
			output = curr.fetchall()
			curr.close()
			conn.close()
			return output

		i = 0
		for param in values_to_plot:

			maintenance_values = get_data(param, 365)

			print values_to_plot[i]

			db_values = []
			timestamps = []
			idm = []
			for line in maintenance_values:
				if "off1" in values_to_plot[i] or float(line[0]) != 0.0:
					db_values.append(float(line[0]))
					timestamps.append(line[1])
					idm.append(line[2])
			try:

				fig = plt.figure(figsize=(5.0, 4.0),facecolor='w', edgecolor='k')
				plt.subplots_adjust(left=0.17, bottom=0.20, right=0.95, top=0.90, wspace=0.4, hspace=0.3)

				ax=fig.add_subplot(111)
				daysFmt=matplotlib.dates.DateFormatter("%Y-%m-%d") #x-axis major tick labels for plot
				ax.xaxis.set_major_formatter(daysFmt)  #x-axis major tick labels

				ax.tick_params(axis='both', which='major', labelsize=8)

				ax.plot_date(timestamps, db_values, 'b*-')

				ymin = min(db_values)
				print ymin
				ymax = max(db_values)

				plt.ylim([ymin-ylims[i], ymax+ylims[i]])

				plt.ylabel(yvalues_to_plot[i], size=10)
				plt.title(titles_to_plot[i] + " - " + self.folder_date, size=10)
				plt.xticks(rotation = 90) # Virker!!!!!
				#
				fig.savefig(daily_config.web_images_dir+values_to_plot[i]+".jpg")

				plt.close(fig)
				plt.clf()
				plt.close()
				del timestamps, db_values, idm, maintenance_values

			except Exception,e:
				print e

			i += 1

		## What should be added and subtracted to the max and min values on the y-axis?
		ylims2 = [25.0, 25.0, 1.0, 1.0, 1.0, 10000.0, 10000.0, 10000.0, 10000.0, 1.0, 1.0, 50.]

		j = 0
		for param in values_to_plot:

			maintenance_values = get_data(param, 14)

			db_values = []
			timestamps = []
			idm = []
			for line in maintenance_values:
				if "off1" in values_to_plot[j] or float(line[0]) != 0.0:
					db_values.append(float(line[0]))
					timestamps.append(line[1])
					idm.append(line[2])
			try:

				fig = plt.figure(figsize=(5.0, 4.0),facecolor='w', edgecolor='k')
				plt.subplots_adjust(left=0.17, bottom=0.20, right=0.95, top=0.90, wspace=0.4, hspace=0.3)

				ax=fig.add_subplot(111)
				daysFmt=matplotlib.dates.DateFormatter("%Y-%m-%d") #x-axis major tick labels for plot
				ax.xaxis.set_major_formatter(daysFmt)  #x-axis major tick labels

				ax.tick_params(axis='both', which='major', labelsize=8)

				ax.plot_date(timestamps, db_values, 'b*-')

				try:
					ymin = min(db_values)
					ymax = max(db_values)
				except Exception,e:
					print e
					ymin = 0
					ymax = 0

				plt.ylim([ymin-ylims2[j], ymax+ylims2[j]])

				plt.ylabel(yvalues_to_plot[j], size=10)
				plt.title(titles_to_plot[j] + " - " + self.folder_date, size=10)
				plt.xticks(rotation = 90) # Virker!!!!!
				#
				fig.savefig(daily_config.web_images_dir+values_to_plot[j]+"_2weeks.jpg")

				plt.close(fig)
				plt.clf()
				plt.close()
				del timestamps, db_values, idm, maintenance_values

			except Exception,e:
				print e

			j += 1

		#### Create cross-order plot of flat master and image of thar-spectrum:
		flat = 1
		#flat_name = "/scratch/star_spec/%s/day/raw/calib/daily_flat_5.fits" % time.strftime("%Y%m%d", time.localtime())
		try:
			flat_name = self.master_image_folder + "masterflat_%s_slit8.fits" % self.folder_date
			flat_im = pyfits.getdata(flat_name, header=False)
		except Exception,e:
			print flat_name, " did not exist..."
			try:
				flat_name = self.master_image_folder + "masterflat_%s_slit6.fits" % self.folder_date
				flat_im = pyfits.getdata(flat_name, header=False)
			except Exception,e:
				print flat_name, " did not exist..."			
				flat = 0

		if flat == 1:
			fig = plt.figure(figsize=(5.0, 4.0),facecolor='w', edgecolor='k')
			plt.subplots_adjust(left=0.15, bottom=0.05, right=0.95, top=0.90, wspace=0.4, hspace=0.3)

			ax=fig.add_subplot(111)

			ax.plot(range(len(flat_im[1000,1900:2000])), flat_im[1000,1900:2000], 'k-')

			plt.ylabel("Pixel count", size=10)
			plt.title("Flat field cross order", size=10)
			fig.savefig(daily_config.web_images_dir+"daily_flat.jpg")

			plt.close(fig)
			plt.clf()
			flat_im = ""
			del flat_im

		#thar_im_name = "/scratch/star_spec/%s/day/raw/calib/daily_thar_1.fits" % time.strftime("%Y%m%d", time.localtime())
		thar_im_name = self.raw_thar_image_folder + "daily_thar_1.fits"
		try:
			os.popen("convert %s -equalize -resize 400x400 %s" % (thar_im_name, daily_config.web_images_dir+"daily_thar.jpg"))
		except Exception, e:
			print e
			return 0


		### Copy images to srf:
		try:
			scp_string = "scp %s*.jpg madsfa@srf:/var/www/song_app/calib_plots/plots/" % (daily_config.web_images_dir)
			os.system(scp_string)
		except Exception,e:
			print "The plots were not copied over to srf!"
			print e


		gc.collect()

		return 1

	def thar_number_of_lines(self,folder_date=""):
		update_db = 1
		if folder_date == "":		
			folder_date = datetime.datetime.strftime(datetime.datetime.utcnow() - datetime.timedelta(days=1), "%Y%m%d")
			folder_year = datetime.datetime.strftime(datetime.datetime.utcnow() - datetime.timedelta(days=1), "%Y")
			update_db = 0
		else:
			folder_now = datetime.datetime.strftime(datetime.datetime.strptime(folder_date, '%Y%m%d') + datetime.timedelta(days=1), "%Y%m%d")
			folder_year = datetime.datetime.strftime(datetime.datetime.strptime(folder_date, '%Y%m%d') + datetime.timedelta(days=1), "%Y")


		folder_to_check = "/scratch/extr_spec/%s/%s/night/calib_master/" % (str(folder_year), str(folder_date))
		files = os.listdir(folder_to_check)

		n_lines_arr = []
		for filename in files:
			if "thar" in filename:
				try:
					data,hdr = pyfits.getdata(folder_to_check+filename, header=True)
					n_lines_arr.append(int(hdr["NLINES"]))
					#print filename, hdr["NLINES"]
				except Exception,e:
					print e

		mean_numb_lines = numpy.mean(n_lines_arr)
		error = numpy.std(n_lines_arr) / numpy.sqrt(len(n_lines_arr))

		try:
			update_song_database.update("maintenance", ["extra_value_7"], [mean_numb_lines], "maintenance_id")
		except Exception, e:
			print "An error occured at update of data to database: ", e

		print mean_numb_lines, "+-", error
		return 1


	def locate_slit(self,folder_date=""):

		update_db = 1
		if folder_date == "":		
			folder_date = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y%m%d")
			update_db = 0
		else:
			folder_now = datetime.datetime.strftime(datetime.datetime.strptime(folder_date, '%Y%m%d') + datetime.timedelta(days=1), "%Y-%m-%d")

		# Read latest determined values:
		# ["extra_value_1", "extra_value_2"], ["extra_value_3", "extra_value_4"], ["extra_value_5", "extra_value_6"]
		try:
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (host, db, user, password))
			curr = conn.cursor()
			curr.execute("SELECT extra_value_1, extra_value_2, extra_value_3, extra_value_4, extra_value_5, extra_value_6, ins_at, maintenance_id FROM maintenance WHERE maintenance_id = (SELECT max(maintenance_id) FROM maintenance WHERE extra_value_1 != 99.0 AND extra_value_2 != 99.0 AND extra_value_3 != 99.0 AND extra_value_4 != 99.0 AND extra_value_5 != 99.0 AND extra_value_6 != 99.0)")
			output = curr.fetchone()
			curr.close()
			conn.close()
		except Exception,e:
			print "An error occured at get old slit positions: ", e		
			self.x_off_slit5 = 99.0
			self.y_off_slit5 = 99.0
			self.x_off_slit6 = 99.0
			self.y_off_slit6 = 99.0
			self.x_off_slit8 = 99.0
			self.y_off_slit8 = 99.0
		else:
			self.x_off_slit5 = output[0]
			self.y_off_slit5 = output[1]
			self.x_off_slit6 = output[2]
			self.y_off_slit6 = output[3]
			self.x_off_slit8 = output[4]
			self.y_off_slit8 = output[5]

		for slit in [5,6,8]:
			try:
				slit_in = "/scratch/star_spec/%s/guide_images/slit%i_halo_slit_in.fits" % (folder_date, slit)
				slit_out = "/scratch/star_spec/%s/guide_images/slit%i_halo_slit_out.fits" % (folder_date, slit)
				slit_template = "/scratch/calibs_refs/slit_location/slit%i_template.fits" % (slit)

				data_slit_in = pyfits.getdata(slit_in)
				data_slit_out = pyfits.getdata(slit_out)
				data_template = pyfits.getdata(slit_template)


			#	n = 4
			#	data_slit_in = numpy.kron(data_slit_in, numpy.ones((n,n)))
			#	data_slit_out = numpy.kron(data_slit_out, numpy.ones((n,n)))
			#	data_template = numpy.kron(data_template, numpy.ones((n,n)))


				res = numpy.array(data_slit_out,dtype=numpy.float)-numpy.array(data_slit_in,dtype=numpy.float)
				ii = numpy.where(res < 0.0)

				res[ii] = 0

				image_product = numpy.fft.fft2(data_template) * numpy.fft.fft2(res).conj()
				cc_image = numpy.fft.fftshift(numpy.fft.ifft2(image_product))

				y,x = numpy.where(cc_image.real == numpy.max(cc_image.real))

			#	print x[0],y[0]

		
				#amp = numpy.max(cc_image.real)
				#cen = x[0]
				#wid = 13.
			#	def gaussian(x, amp, cen, wid):
			#		"1-d gaussian: gaussian(x, amp, cen, wid)"
			#		return (amp/(sqrt(2*pi)*wid)) * exp(-(x-cen)**2 /(2*wid**2))

			#	mod = lmfit.Model(gaussian)
			#	pars = mod.make_params(amp=amp, cen=cen, wid=wid)
			#	result = mod.fit(cc_image.real[y[0]-5:y[0]+5,x[0]], pars, x=range(len(cc_image.real[y[0]-5:y[0]+5,x[0]])), method= 'least_squares')
			#	result = mod.fit(cc_image.real[y[0],:], pars, x=range(len(cc_image.real[y[0],:])), method= 'least_squares')	

				#print "Amp: ", result.params['amp'].value
	#			print "Cen: ", y[0]-5+result.params['cen'].value #, result.params['cen'].stderr
			#	print "Cen: ", result.params['cen'].value / float(n) #, result.params['cen'].stderr
			#	print "Wid: ", result.params['wid'].value / float(n)



		#		fig = plt.figure(figsize=(8.0, 6.0),facecolor='w', edgecolor='k')
		#		plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.4, hspace=0.3)

		#		plt.plot(range(len(cc_image.real[y[0],:])), cc_image.real[y[0],:])
		#		plt.plot(range(len(cc_image.real[y[0],:])), ndimage.filters.gaussian_filter(cc_image.real[y[0],:],10,0), '-r', linewidth=1)
			
		#		fig.savefig(daily_config.web_images_dir+"slit%i_test.jpg" % slit)

		#		ii = numpy.where(ndimage.filters.gaussian_filter(cc_image.real[y[0],:],10,0) == numpy.max(ndimage.filters.gaussian_filter(cc_image.real[y[0],:],10,0)))
		#		jj = numpy.where(ndimage.filters.gaussian_filter(cc_image.real[:,x[0]],10,0) == numpy.max(ndimage.filters.gaussian_filter(cc_image.real[:,x[0]],10,0)))
		#		print ii[0][0], jj[0][0]

				slit_name = "slit%i" % slit
				x_off = ((x[0] - cc_image.real.shape[1]/2) - daily_config.x_offsets[slit_name]) 
				y_off = ((y[0] - cc_image.real.shape[0]/2) - daily_config.y_offsets[slit_name][0])
			#	x_off = ((ii[0][0] - res.shape[1]/2) - daily_config.x_offsets[slit_name]) 
			#	y_off = ((jj[0][0] - res.shape[0]/2) - daily_config.y_offsets[slit_name][0])



				print "x offset: %i, y offset: %i" % (x_off, y_off)

				fig = plt.figure(figsize=(8.0, 6.0),facecolor='w', edgecolor='k')
				plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.4, hspace=0.3)

				ax=fig.add_subplot(111)

				ax.imshow(cc_image.real, origin="lower") # [140:340,200:440]
			#	ax.plot([(cc_image.real.shape[1]/2)-1 + x_off, (cc_image.real.shape[1]/2)-1 + x_off], [0.0, (cc_image.real.shape[0])-1], "w-")
			#	ax.plot([0.0,(cc_image.real.shape[1])-1], [(cc_image.real.shape[0]/2)-1 + y_off - daily_config.y_offsets[slit_name][1], (cc_image.real.shape[0]/2)-1 + y_off - daily_config.y_offsets[slit_name][1]], "w-")

				ax.plot([(cc_image.real.shape[1]/2) + x_off, (cc_image.real.shape[1]/2) + x_off], [0.0, (cc_image.real.shape[0])], "w-")
				ax.plot([0.0,(cc_image.real.shape[1])], [(cc_image.real.shape[0]/2) + y_off - daily_config.y_offsets[slit_name][1], (cc_image.real.shape[0]/2) + y_off - daily_config.y_offsets[slit_name][1]], "w-")

				#ax.plot([0.0,res.shape[1]], [res.shape[0]/2 + y_off_gauss - daily_config.y_offsets[slit_name][1], res.shape[0]/2] + y_off_gauss - daily_config.y_offsets[slit_name][1], "k-")
		#		ax.plot([res.shape[1]/2, res.shape[1]/2], [0.0, res.shape[0]], "k--")
		#		ax.plot([0.0,res.shape[1]], [res.shape[0]/2 , res.shape[0]/2], "k--")

				plt.xlim([200.0,440.0])
				plt.ylim([140.0,340.0])

				if slit == 5:
					self.x_off_slit5 = x_off
					self.y_off_slit5 = y_off
				elif slit == 6:
					self.x_off_slit6 = x_off
					self.y_off_slit6 = y_off
				elif slit == 8:
					self.x_off_slit8 = x_off
					self.y_off_slit8 = y_off


				plt.title("Slit %i guide target: x = %i, y = %i" % (slit, daily_config.x_ref[slit_name] + x_off, daily_config.y_ref[slit_name] + y_off), size=15)
				plt.axis('off')			
				fig.savefig(daily_config.web_images_dir+"slit%i_cc_movement.jpg" % slit)

				plt.close(fig)
				plt.clf()
			except Exception,e:
				print e

		### inserting into database
		if update_db == 0:
			# determined good values:
			parameters = []
			values_to_insert = []
			poss = ["extra_value_1", "extra_value_2", "extra_value_3","extra_value_4", "extra_value_5", "extra_value_6"]
			ind = 0
			for p in [self.x_off_slit5, self.y_off_slit5, self.x_off_slit6, self.y_off_slit6, self.x_off_slit8, self.y_off_slit8]:
				if p != 99.0:
					parameters.append(poss[ind])
					values_to_insert.append(p)
				else:
					print poss[ind], " did not give a good position..."

				ind += 1

			try:
				update_song_database.update("maintenance", parameters, values_to_insert, "maintenance_id")
			except Exception, e:
				print "An error occured at update of data to database: ", e
	
		else:

			folder_date = folder_date	
			
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (host, db, user, password))
			curr = conn.cursor()

			stmt = "UPDATE maintenance SET (extra_value_1, extra_value_2, extra_value_3, extra_value_4, extra_value_5, extra_value_6) = (%s,%s,%s,%s,%s,%s) WHERE ins_at::DATE = '%s'" % (self.x_off_slit5, self.y_off_slit5, self.x_off_slit6, self.y_off_slit6, self.x_off_slit8, self.y_off_slit8, folder_now)
			curr.execute(stmt)		
			conn.commit()
			curr.close()			

		###### Making plots
		values_to_plot = [["extra_value_1", "extra_value_2"], ["extra_value_3", "extra_value_4"], ["extra_value_5", "extra_value_6"]]
		titles_to_plot = ["Slit 5 offsets", "Slit 6 offsets", "Slit 8 offsets"]

		def get_data(field_name, timeint):
			conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (host, db, user, password))
			curr = conn.cursor()
			curr.execute("SELECT %s, ins_at, maintenance_id FROM maintenance WHERE maintenance_id > (SELECT max(maintenance_id) FROM maintenance) - %s order by ins_at ASC" % (field_name, str(timeint)))
			output = curr.fetchall()
			curr.close()
			conn.close()
			return output


		## What should be added and subtracted to the max and min values on the y-axis?
		ylims2 = [20.0, 20.0, 20.0]

		j = 0
		for dic in values_to_plot:

			fig = plt.figure(figsize=(5.0, 4.0),facecolor='w', edgecolor='k')
			plt.subplots_adjust(left=0.17, bottom=0.20, right=0.95, top=0.90, wspace=0.4, hspace=0.3)

			ax=fig.add_subplot(111)
			daysFmt=matplotlib.dates.DateFormatter("%Y-%m-%d") #x-axis major tick labels for plot
			ax.xaxis.set_major_formatter(daysFmt)  #x-axis major tick labels

			ax.tick_params(axis='both', which='major', labelsize=8)

			for param in dic:
				maintenance_values = get_data(param, 14)

				db_values = []
				timestamps = []
				idm = []
				for line in maintenance_values:
					if "off1" in values_to_plot[j] or float(line[0]) != 99.0:
						db_values.append(float(line[0]))
						timestamps.append(line[1])
						idm.append(line[2])
				try:

					ax.plot_date(timestamps, db_values, '*-')

				except Exception,e:
					print e

			plt.ylim([-20.0, 20.0])

			plt.ylabel("Offset in pixels", size=10)
			plt.title(titles_to_plot[j] + " - " + folder_date, size=10)
			plt.xticks(rotation = 90) # Virker!!!!!
			#
			fig.savefig(daily_config.web_images_dir+titles_to_plot[j].replace(" ", "_").lower()+"_2weeks.jpg")

			plt.close(fig)
			plt.clf()
			plt.close()
			del timestamps, db_values, idm, maintenance_values

			j += 1

		### Copy images to srf:
		try:
			scp_string = "scp %sslit*.jpg madsfa@srf:/var/www/song_app/calib_plots/plots/" % (daily_config.web_images_dir)
			os.system(scp_string)
		except Exception,e:
			print "The plots were not copied over to srf!"
			print e

		return 1
