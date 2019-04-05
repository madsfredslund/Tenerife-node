import numpy
import pyfits
import sys

path_to_flat = "/scratch/skycam_images/master_flat.fits"

class SMOOTH(object):
   """
      @brief: his class cleans an image from hot pixels.
   """
   def clean(self, path, filename):

	"""
           This function finds all pixels where the value is greater then 2 times (adjustable) the standard deviation from the mean value. 
           For these pixels it calculates the mean value of the 8 pixels around the one with the high value and sets the middle one the this mean value. 
           This will result in a removal of all hot pixels with a higher value then 2 times std. It will also affect the real stars, but since these are 
           covering more then one pixel the effect is small enough to keep stars visible. 
	"""

	# image is the path to the image file.
	im,hdr = pyfits.getdata(path+filename,header=True)	
	#try:
	#	tmp_fits = pyfits.open(filename, int16=True)#, do_not_scale_image_data = True) 
	#	im = tmp_fits[0].data
	#	hdr = tmp_fits[0].header
	#except Exception, e:
	#	print e
	#	print "Error: ", e
		
	dimx,dimy = im.shape # The dimensions of the image.
	mean_value = numpy.mean(im)
	std_value = numpy.std(im)

	#new_im = im

	ii = numpy.where(im >= mean_value + (2*std_value)) # this finds all pixels with value bigger then two times the standard deviation.

	ix,iy = ii

	px_1 = ix + numpy.ones(len(ix), dtype=numpy.int)
	py_1 = iy + numpy.ones(len(ix), dtype=numpy.int)
	bad_x = numpy.where(px_1 >= (dimx-1)) # These two lines checks that the index remains inside image dimensions.
	bad_y = numpy.where(py_1 >= (dimy-1)) # These two lines checks that the index remains inside image dimensions.
	px_1[bad_x] = 0 # And sets index value to zero if outside of image dimensions.
	py_1[bad_y] = 0 # And sets index value to zero if outside of image dimensions.	

	px_2 = ix + numpy.ones(len(ix), dtype=numpy.int)
	py_2 = iy
	bad_x = numpy.where(px_2 >= (dimx-1))
	bad_y = numpy.where(py_2 >= (dimy-1))
	px_2[bad_x] = 0 
	py_2[bad_y] = 0 

	px_3 = ix + numpy.ones(len(ix), dtype=numpy.int)
	py_3 = iy - numpy.ones(len(ix), dtype=numpy.int)
	bad_x = numpy.where(px_3 >= (dimx-1))
	bad_y = numpy.where(py_3 >= (dimy-1))
	px_3[bad_x] = 0 
	py_3[bad_y] = 0 

	px_4 = ix - numpy.ones(len(ix), dtype=numpy.int)
	py_4 = iy - numpy.ones(len(ix), dtype=numpy.int)
	bad_x = numpy.where(px_4 >= (dimx-1))
	bad_y = numpy.where(py_4 >= (dimy-1))
	px_4[bad_x] = 0
	py_4[bad_y] = 0

	px_5 = ix - numpy.ones(len(ix), dtype=numpy.int)
	py_5 = iy + numpy.ones(len(ix), dtype=numpy.int)
	bad_x = numpy.where(px_5 >= (dimx-1))
	bad_y = numpy.where(py_5 >= (dimy-1))
	px_5[bad_x] = 0
	py_5[bad_y] = 0

	px_6 = ix
	py_6 = iy + numpy.ones(len(ix), dtype=numpy.int)
	bad_x = numpy.where(px_6 >= (dimx-1))
	bad_y = numpy.where(py_6 >= (dimy-1))
	px_6[bad_x] = 0
	py_6[bad_y] = 0  

	px_7 = ix
	py_7 = iy - numpy.ones(len(ix), dtype=numpy.int)
	bad_x = numpy.where(px_7 >= (dimx-1))
	bad_y = numpy.where(py_7 >= (dimy-1))
	px_7[bad_x] = 0
	py_7[bad_y] = 0 

	px_8 = ix - numpy.ones(len(ix), dtype=numpy.int)
	py_8 = iy
	bad_x = numpy.where(px_8 >= (dimx-1))
	bad_y = numpy.where(py_8 >= (dimy-1))
	px_8[bad_x] = 0
	py_8[bad_y] = 0

	# Here the mean value of the 8 evaluated pixels is calculated. In the first and last row and column the values is not correct, but this does not matter.
        cal_around = numpy.zeros((dimx,dimy))
	cal_around[ii] = (im[px_1,py_1] + im[px_2,py_2]+ im[px_3,py_3] + im[px_4,py_4] + im[px_5,py_5] + im[px_6,py_6] + im[px_7,py_7] + im[px_8,py_8]) / 8.0
	jj = numpy.where(cal_around <= (mean_value + 2 * std_value))
	new_cal_array = numpy.zeros((dimx,dimy))
	new_cal_array[jj] = cal_around[jj]
	tt = numpy.where(new_cal_array > 0.0)
	im[tt] = cal_around[tt]
	new_im = im


################################### This divides with the flat field ############################
	try:
		flat = pyfits.getdata(path_to_flat)
		new_im = (new_im / flat).astype(numpy.int16)
	except Exception, e:
		print e
#################################################################################################

        f_name, f_end = filename.split('.')
        try:
	   pyfits.update(path+f_name+'_s.fits',new_im,hdr)
        except Exception, e:
	   pyfits.writeto(path+f_name+'_s.fits',new_im,hdr)

   def clean_image(self, filename, test_value):
        """
           This function does the same as the one above but instead of making a new file it overwrites the original one. 
        """
	# image is the path to the image file.
	im, hdr = pyfits.getdata(filename,header=True)	
		
	dimx,dimy = im.shape # The dimensions of the image.
	mean_value = numpy.mean(im)		
	std_value = numpy.std(im)

	ii = numpy.where(im >= mean_value + (2*std_value)) # this finds all pixels with value bigger then two times the standard deviation.
	ix,iy = ii

	# Here the 8 pixels around the ones with high values are selected for evaluation
	px_1 = ix + numpy.ones(len(ix), dtype=numpy.int)
	py_1 = iy + numpy.ones(len(ix), dtype=numpy.int)
	px_2 = ix + numpy.ones(len(ix), dtype=numpy.int)
	py_2 = numpy.array(iy)
	px_3 = ix + numpy.ones(len(ix), dtype=numpy.int)
	py_3 = iy - numpy.ones(len(ix), dtype=numpy.int)
	px_4 = ix - numpy.ones(len(ix), dtype=numpy.int)
	py_4 = iy - numpy.ones(len(ix), dtype=numpy.int)
	px_5 = ix - numpy.ones(len(ix), dtype=numpy.int)
	py_5 = iy + numpy.ones(len(ix), dtype=numpy.int)
	px_6 = numpy.array(ix)
	py_6 = iy + numpy.ones(len(ix), dtype=numpy.int)
	px_7 = numpy.array(ix)
	py_7 = iy - numpy.ones(len(ix), dtype=numpy.int)
	px_8 = ix - numpy.ones(len(ix), dtype=numpy.int)
	py_8 = numpy.array(iy)

	# Pixels that are close to the image borders are not used. 
	px_1[px_1<0] = 0
	px_1[px_1>dimx-1] = 0
	py_1[py_1<0] = 0
	py_1[py_1>dimy-1] = 0
	px_2[px_2<0] = 0
	px_2[px_2>dimx-1] = 0
	py_2[py_2<0] = 0
	py_2[py_2>dimy-1] = 0
	px_3[px_3<0] = 0
	px_3[px_3>dimx-1] = 0
	py_3[py_3<0] = 0
	py_3[py_3>dimy-1] = 0
	px_4[px_4<0] = 0
	px_4[px_4>dimx-1] = 0
	py_4[py_4<0] = 0
	py_4[py_4>dimy-1] = 0
	px_5[px_5<0] = 0
	px_5[px_5>dimx-1] = 0
	py_5[py_5<0] = 0
	py_5[py_5>dimy-1] = 0
	px_6[px_6<0] = 0
	px_6[px_6>dimx-1] = 0
	py_6[py_6<0] = 0
	py_6[py_6>dimy-1] = 0
	px_7[px_7<0] = 0
	px_7[px_7>dimx-1] = 0
	py_7[py_7<0] = 0
	py_7[py_7>dimy-1] = 0
	px_8[px_8<0] = 0
	px_8[px_8>dimx-1] = 0
	py_8[py_8<0] = 0
	py_8[py_8>dimy-1] = 0

	cal_around = numpy.zeros((dimx,dimy))
	cal_around[ii] = (im[px_1,py_1] + im[px_2,py_2]+ im[px_3,py_3] + im[px_4,py_4] + im[px_5,py_5] + im[px_6,py_6] + im[px_7,py_7] + im[px_8,py_8]) / 8.0

	# This evaluates the area around the "hot pixel" if mean value around is low then it is properly a hot pixel.
	jj = numpy.where(cal_around <= (mean_value + std_value))
	new_cal_array = numpy.zeros((dimx,dimy))
	new_cal_array[jj] = cal_around[jj]
	tt = numpy.where(new_cal_array > 0.0)
	im[tt] = cal_around[tt]
	new_im = im


################################### This divides with the flat field ############################
	if test_value == 0:
		try:
			flat = pyfits.getdata(path_to_flat)
			### Strange that I have to multiply with the flat field.... maybe the way I made it is wrong.
			new_im = (new_im / flat).astype(numpy.int16)
		except Exception, e:
			print e
#################################################################################################

#	if test_value == 1:
#	   try:
#	      pyfits.update("/home/madsfa/SkyCam/images/astrometry/test_smooth.fits",new_im,hdr)
 #          except Exception, e:
#	      pyfits.writeto("/home/madsfa/SkyCam/images/astrometry/test_smooth.fits",new_im,hdr)
#	else:
        try:
	   pyfits.update(filename, new_im, hdr)
        except Exception, e:
	   pyfits.writeto(filename, new_im, hdr, uint=True)


   def clean_im_array(self, im_arr, test_value):
        """
           This function does the same as the one above but instead of making a new file it overwrites the original one. 
        """
		
	dimx,dimy = im_arr.shape 		# The dimensions of the image.
	mean_value = numpy.mean(im_arr)		
	std_value = numpy.std(im_arr)

	ii = numpy.where(im_arr >= mean_value + (std_value)) # this finds all pixels with value bigger then two times the standard deviation.
	ix,iy = ii

	# Here the 8 pixels around the ones with high values are selected for evaluation
	px_1 = ix + numpy.ones(len(ix), dtype=numpy.int)
	py_1 = iy + numpy.ones(len(ix), dtype=numpy.int)
	px_2 = ix + numpy.ones(len(ix), dtype=numpy.int)
	py_2 = numpy.array(iy)
	px_3 = ix + numpy.ones(len(ix), dtype=numpy.int)
	py_3 = iy - numpy.ones(len(ix), dtype=numpy.int)
	px_4 = ix - numpy.ones(len(ix), dtype=numpy.int)
	py_4 = iy - numpy.ones(len(ix), dtype=numpy.int)
	px_5 = ix - numpy.ones(len(ix), dtype=numpy.int)
	py_5 = iy + numpy.ones(len(ix), dtype=numpy.int)
	px_6 = numpy.array(ix)
	py_6 = iy + numpy.ones(len(ix), dtype=numpy.int)
	px_7 = numpy.array(ix)
	py_7 = iy - numpy.ones(len(ix), dtype=numpy.int)
	px_8 = ix - numpy.ones(len(ix), dtype=numpy.int)
	py_8 = numpy.array(iy)

	# Pixels that are close to the image borders are not used. 
	px_1[px_1<0] = 0
	px_1[px_1>dimx-1] = 0
	py_1[py_1<0] = 0
	py_1[py_1>dimy-1] = 0
	px_2[px_2<0] = 0
	px_2[px_2>dimx-1] = 0
	py_2[py_2<0] = 0
	py_2[py_2>dimy-1] = 0
	px_3[px_3<0] = 0
	px_3[px_3>dimx-1] = 0
	py_3[py_3<0] = 0
	py_3[py_3>dimy-1] = 0
	px_4[px_4<0] = 0
	px_4[px_4>dimx-1] = 0
	py_4[py_4<0] = 0
	py_4[py_4>dimy-1] = 0
	px_5[px_5<0] = 0
	px_5[px_5>dimx-1] = 0
	py_5[py_5<0] = 0
	py_5[py_5>dimy-1] = 0
	px_6[px_6<0] = 0
	px_6[px_6>dimx-1] = 0
	py_6[py_6<0] = 0
	py_6[py_6>dimy-1] = 0
	px_7[px_7<0] = 0
	px_7[px_7>dimx-1] = 0
	py_7[py_7<0] = 0
	py_7[py_7>dimy-1] = 0
	px_8[px_8<0] = 0
	px_8[px_8>dimx-1] = 0
	py_8[py_8<0] = 0
	py_8[py_8>dimy-1] = 0

	cal_around = numpy.zeros((dimx,dimy))
	cal_around[ii] = (im_arr[px_1,py_1] + im_arr[px_2,py_2]+ im_arr[px_3,py_3] + im_arr[px_4,py_4] + im_arr[px_5,py_5] + im_arr[px_6,py_6] + im_arr[px_7,py_7] + im_arr[px_8,py_8]) / 8.0

	# This evaluates the area around the "hot pixel" if mean value around is low then it is properly a hot pixel.
	jj = numpy.where(cal_around <= (mean_value + 2. * std_value))
	new_cal_array = numpy.zeros((dimx,dimy))
	new_cal_array[jj] = cal_around[jj]
	tt = numpy.where(new_cal_array > 0.0)
	im_arr[tt] = cal_around[tt]
	new_im = im_arr

	return new_im






