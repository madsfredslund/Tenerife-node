#!/usr/bin/python
'''
Created on October 10, 2017

@author: madsfa
'''
import xmlrpclib
import sys
from optparse import OptionParser
import time
sys.path.append("/home/madsfa/subversion/trunk/common/")
sys.path.append("/home/madsfa/subversion/trunk/phot/vis/")
import master_config as m_conf
import vis_ccd_config as vis_conf
import comm2tcs_read
import comm2tcs_write
import numpy
import image_smoother
import numpy.polynomial.polynomial as poly
import pyfits
import song_timeclass
from multiprocessing import Process
import os
import mfa
import datetime
import matplotlib
matplotlib.use('AGG')
import matplotlib.pylab as plt
import update_song_database

clock = song_timeclass.TimeClass()
cleaner = image_smoother.SMOOTH()

gettsi = comm2tcs_read.GET_TSI()
settsi = comm2tcs_write.SET_TSI()

#attempt connection to server
vis_server = xmlrpclib.ServerProxy('http://%s:%s' % (vis_conf.serverhost, vis_conf.port))



parser = OptionParser()
parser.add_option("-e", "--exptime", type="float", dest="exptime", default=1.0, help="Set exposure time in seconds: ex. --exptime=2.5 or -e2.5")
parser.add_option("-z", "--hexapod-z", type="string", dest="focus", default="", help="Set focus start guess of telescope in offset millimeter: ex. -z1.44")
parser.add_option("-r", "--focus_range", type="float", dest="range", default=0.1, help="Set focus range to check: ex. -r0.2")
parser.add_option("-s", "--step_size", type="float", dest="step", default=0.01, help="Set focus step size in millimeter: ex. -s0.01")
(options, args) = parser.parse_args()

if options.exptime != None:
	exptime = options.exptime
else:
	exptime = 10.0

if options.focus != None and options.focus != "":
	tel_focus = float(options.focus)
elif options.focus == "":
	tel_focus = float(gettsi.get_position_instrumental_hexapod_z_offset())

	
hsspeed = 0
pregain = 0
highcap = 0
hbin = 1
vbin = 1
acmode = 1


### This call is only to make sure the image folder is created:
try:
	value = vis_server.acquire_an_image_thread("test.fits", "", 0.1, hsspeed, pregain, highcap, hbin, vbin, acmode, "", "", "", "", "star", "", "", "", "", "", "vis")
except Exception, e:
	print 'error'
else:
	print "Acquired a test image: ", value

image_dir = os.path.dirname(value) + "/"

print "Checking directory: ", image_dir
folder_number = 1
focus_folder = "focus_%i" % folder_number
while os.path.exists(image_dir+focus_folder):
	print image_dir+focus_folder, " existed"
	focus_folder = focus_folder.split("_")[0] + "_%i" % (folder_number+1)
	folder_number += 1 
os.mkdir(image_dir + focus_folder)
os.chmod(image_dir + focus_folder, 0777)

image_dir =  image_dir + focus_folder + "/"


###########

try:
	settsi.set_position_instrumental_hexapod_z_offset(param=float(tel_focus - options.range))
except Exception,e:
	print e
	print "Could not preset focus value of hexapod"
else:
	time.sleep(3)
	t_focus = gettsi.get_position_instrumental_focus_currpos(sender="focus_script")
	t_focus_offset = gettsi.get_position_instrumental_hexapod_z_offset(sender="focus_script")
	update_song_database.update("tel_dome", ["tel_focus"], [float(t_focus)+float(t_focus_offset)], "tel_dome_id")
	print "Focus set to: ", float(t_focus)+float(t_focus_offset)



number_of_steps = int(numpy.round(float(options.range) / float(options.step)) * 2)
tel_focus_start_val = float(tel_focus - options.range)

for step in range(number_of_steps):

	vis_filename = "vis_focus_%i.fits" % (step+1)

	try:
		value_vis = vis_server.acquire_an_image_thread(image_dir+vis_filename, "", exptime, hsspeed, pregain, highcap, hbin, vbin, acmode, "", "", "", "", "star", "", "", "", "", "focus", "vis")
	except Exception, e:
		print 'error'

	time.sleep(exptime+2)

	print "Image saved: ", value_vis

	try:
		settsi.set_position_instrumental_hexapod_z_offset(param=float(tel_focus_start_val + (float(options.step)*(step+1))))
	except Exception,e:
		print e
		print "Could not preset focus value of hexapod"
	else:
		time.sleep(1)
		t_focus = gettsi.get_position_instrumental_focus_currpos(sender="focus_script")
		t_focus_offset = gettsi.get_position_instrumental_hexapod_z_offset(sender="focus_script")
		update_song_database.update("tel_dome", ["tel_focus"], [float(t_focus)+float(t_focus_offset)], "tel_dome_id")
		print "Focus set to: ", float(t_focus)+float(t_focus_offset)

	time.sleep(2)



def calculate_best_focus(path_to_folder, im_list, ccd):

	focus_arr = []
	fwhm_arr = []
	number_used = [0,0]
	for file_name in im_list:
		if ".fits" in file_name:
			print "Computing: ", file_name
			e = ""

			new_im, tmp_hdr = pyfits.getdata(path_to_folder+file_name, header=True)
			new_im = cleaner.clean_im_array(new_im, 1)
	
			y,x = numpy.where(numpy.array(new_im) == numpy.max(new_im))
			if len(y) > 1:
				y = y[0]
				x = x[0]
			its = 0
			while numpy.mean([new_im[y+1,x],new_im[y-1,x],new_im[y-1,x-1],new_im[y,x-1],new_im[y+1,x+1],new_im[y,x+1],new_im[y-1,x+1],new_im[y+1,x-1]]) < new_im[y,x] * (1./3.):
				new_im[y,x] = 0
				y,x = numpy.where(numpy.array(new_im) == numpy.max(new_im))
				if len(y) > 1:
					y = y[0]
					x = x[0]

				if its > 100:				
					break

				its += 1

			print "Removed %i hot pixels before proceeding" % (int(its)-1)				

			if numpy.mean([new_im[y+1,x],new_im[y-1,x],new_im[y-1,x-1],new_im[y,x-1],new_im[y+1,x+1],new_im[y,x+1],new_im[y-1,x+1],new_im[y+1,x-1]]) >= new_im[y,x] * (1./3.):

				print "Used coordinates for gauss fit: ", x, y

				param = 0
				try:
					param = mfa.fit_gauss_circular([y-30,x-30],new_im[y-30:y+30, x-30:x+30])
				except Exception,e:
					print e

				if e == "" and param != 0:

					print "Max value: ", param[0]
					print "Background value: ", param[1]
					print "Height: ", param[2]
					print "X-Pos: ", param[4]
					print "Y-Pos: ", param[3]
					print "Gaus FWHM: ", param[5]

					fwhm_arr.append(param[5] * 0.08)		## multiplying by 0.08 to get values in arcseconds
					focus_arr.append(float(tmp_hdr["TEL_FOC"]))

					number_used[0] += 1
			number_used[1] += 1



	print "Used images %i of %i" % (number_used[0], len(im_list))

	try:
		#### First fit
		poly_fit = poly.polyfit(numpy.array(focus_arr), numpy.array(fwhm_arr), 2, full=True)

		print "Fit quality values: ", poly_fit[1]
		print "Succes of fit was: ", poly_fit[1][0][0]

		x = (numpy.array(range(1500)) / 1000. ) * 2.0 + 1.0

		coeffs = poly_fit[0]
		g_data = coeffs[2]*x**2 + coeffs[1]*x + coeffs[0]

		eval_fit = coeffs[2]*numpy.array(focus_arr)**2 + coeffs[1]*numpy.array(focus_arr) + coeffs[0]

		ii = numpy.where(g_data == numpy.min(g_data))
	except Exception,e:
		print e


	try:
		#### Remove outliers
		std_value = numpy.std(numpy.array(fwhm_arr)-numpy.array(eval_fit))
		print "Standard deviation is: ", std_value
		devi_arr = numpy.abs(numpy.array(fwhm_arr)-numpy.array(eval_fit))
		jj = numpy.where(devi_arr < std_value)
		new_focus_arr = numpy.array(focus_arr)[jj[0]]
		new_fwhm_arr = numpy.array(fwhm_arr)[jj[0]]
		print "Using %i images for second fit" % len(new_focus_arr)
	except Exception,e:
		print e


	######
	try:
		#### Second fit:

		poly_fit2 = poly.polyfit(numpy.array(new_focus_arr), numpy.array(new_fwhm_arr), 2, full=True)

		print "Fit quality values: ", poly_fit2[1]
		print "Succes of fit was: ", poly_fit2[1][0][0]

		coeffs2 = poly_fit2[0]
		g_data2 = coeffs2[2]*x**2 + coeffs2[1]*x + coeffs2[0]
		######

		iii = numpy.where(g_data2 == numpy.min(g_data2))
		optimum_focus = x[iii]
		print "Best focus on first fit: ", x[ii]
		print "Best focus on second fit: ", optimum_focus
		print 'Optimum star size: %f"' % numpy.min(g_data2)
	except Exception,e:
		print e

#	try:	
#		# Apply the newly found best focus value:
#		if float(optimum_focus) > 1.5 and float(optimum_focus) < 3.5:
#			try:
#				print set_tsi.set_position_instrumental_hexapod_z_offset(param=float(optimum_focus))
#			except Exception,e:
#				print e
#				print "Could not preset focus value of hexapod"	
#		else:
#			print "The focus found was not within accepted values..."
#	except Exception,e:
#		print e

	plt.figure(figsize=(10.0, 8.0),dpi=40,facecolor='w', edgecolor='k')
	plt.subplots_adjust(left=0.15, bottom=0.20, right=0.95, top=0.90, wspace=0.4, hspace=0.3)

	plt.plot(numpy.array(focus_arr), numpy.array(fwhm_arr), 'r*')

	plt.plot(numpy.array(new_focus_arr), numpy.array(new_fwhm_arr), 'b*')

	plt.xlim([min(focus_arr)-0.1,max(focus_arr)+0.1])
	plt.ylim([min(numpy.array(fwhm_arr))-1.0,max(numpy.array(fwhm_arr))+1.0])

	plt.ylabel("FWHM [arcseconds]")
	plt.xlabel("Focus [mm]")

	try:
		plt.plot(x, g_data,'g-')
	except Exception,e:
		print e
	try:
		plt.plot(x, g_data2,'b-')
	except Exception,e:
		print e

	plt.savefig(path_to_folder+"focus_%s_fit.jpg" % ccd)		

	return optimum_focus



### Prepare to calculate best focus:

list_dir_files = os.listdir(image_dir)

red_images = []
vis_images = []
for filename in list_dir_files:
	if "red" in filename:
		red_images.append(filename)
	elif "vis" in filename:
		vis_images.append(filename)


####
print "Calculate best forcus for VIS CCD"
best_focus_vis = calculate_best_focus(image_dir, vis_images, "vis")

print "Done determining focus..."
print "Best focus for vis: ", best_focus_vis


print "Setting focus to match VIS CCD..."
t_focus = gettsi.get_position_instrumental_focus_currpos(sender="focus_script")
settsi.set_position_instrumental_hexapod_z_offset(param=float(best_focus_vis-float(t_focus)))

