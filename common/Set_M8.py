#             FOR calibration exposures use the following M8 positions:
#  ------------------------------------------------------------------------------
#             <------------------------ SLIT POSITION -------------------------->
#
#     sigu moveto y x
#
#
#  Res(ThAr)
#  Width(")
#  Width(um)   FREE     oe100/20    oe20   100   60    45    36   30    25
#  Slit --->    2mm      1          2     3     4     5     6    7    8
#  ------------------------------------------------------------------------------
#  FLAT-x               55         55    45    40    40    35   35    35
#  FLAT-y               40         40    40    35    35    35   35    35
#  Texp_FLAT           5.0
#  ------------------------------------------------------------------------------		Table updated by Mads on 2013-03-15
#  THAR-x               85         80    75    75    75    70   70    65
#  THAR-y               35         35    35    35    35    35   35    35
#  Texp_THAR           2.0
#  ------------------------------------------------------------------------------
#  SUN-x                60         50    50    45    45    40   35    35
#  SUN-y                40         40    40    40    40    40   40    40
#  Texp_SUN            0.5
#  ------------------------------------------------------------------------------
#
#  - Spec camera focus depending on what slit is used.
#  - Offset between order locations depending on the slit...


###
###
# Position of M8 is determined by: [ThAr, Halo, Sun] = [pst -m4], [slit position] = [pst -m6]
###
###
import sys
import get_db_values
import M8_pos_table
import psycopg2
import slit_module
import master_config as m_conf

sigu = slit_module.SIGU()

########################################################################
########## TO BE SURE THAT PATHS ARE CORRECT ###########################
DMC_PATH =  "/home/obs/programs/DMC/"
sys.path.append(DMC_PATH) 
import pst		
import lamp

# Database values:
#db_host = "192.168.66.65"	# Tenerife machine
#db_user = "postgres"
#db_password = ""
#db = "db_tenerife"
db_host = m_conf.db_host	# Tenerife machine
db_user = m_conf.db_user
db_password = m_conf.db_password
db = m_conf.data_db

def get_db_values(table_name, fields=[]):
	"""
	 @brief: This function collects data from given table in database to a specific observation request.
	 @param req_no: The observation request number.
	"""

	conn = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (db_host, db, db_user, db_password))

	curr = conn.cursor()

	field_str = ''
	for field in fields:
		field_str += field
		field_str += ','
	field_str = field_str[0:-1]

	stmt = 'SELECT %s FROM %s WHERE ins_at = (SELECT max(ins_at) FROM %s)' % (field_str, table_name, table_name)
	curr.execute(stmt)
	results = curr.fetchone()
	curr.close()
	conn.close()

	res_dict = {}
	if results != None:
		for i in range(len(results)):
			res_dict[fields[i]] = results[i]
		return res_dict
	else:
		return None

def set_m8_pos():
	"""
		@brief: This function reads the spectrograph mirrors, slit and other settings to determine and positioning the M8 mirror.  
	"""
	
	### Read the different values:
	
	try:
		coude_values = get_db_values("coude_unit", ["calib_mirror_pos", "slit_pos", "spectrograph_foc"])
	except Exception,e:
		print "WHATT!!"
		print e
		sys.exit()

	calib_m_pos = coude_values["calib_mirror_pos"]
	slit_pos = coude_values["slit_pos"]
	spec_focus = coude_values["spectrograph_foc"]

	# Halogen mode:
	if calib_m_pos == 2:
		set_x,set_y = M8_pos_table.halo[slit_pos]
	# ThAr mode:
	elif calib_m_pos == 3:
		set_x,set_y = M8_pos_table.thar[slit_pos]
	# Sun mode:
	elif calib_m_pos == 4:
		set_x,set_y = M8_pos_table.sun[slit_pos]

	else:
		return 1

	#move M8:
	try:
		sigu.exec_action(action="moveto", args=[str(set_y),str(set_x)])
	except Exception,e:
		print "What is going on?"
		print e

	return 1







