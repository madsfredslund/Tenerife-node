'''Simple module that supplies setup parameters for the LuckyCam system. 
Also contains a dictionary of error codes that the Andor SDK can emit'''

dataDirectory = '/tmp/'
calibrationDirectory =  {'vis':'/mnt/data/calibration/vis/','red':'/mnt/data/calibration/red/'}
storageDirectory = '/tmp/'
snapshotPath = '/tmp/snapshot.fits'

convFitsPath = "/scratch/li_images/conv/"	# Modified by Mads

#serverurl   = {'vis':"http://10.8.0.142:8087/RPC2",'red':"http://10.8.0.250:8087/RPC2"}
serverurl   = {'red':"http://10.8.0.142:8087/RPC2",'vis':"http://10.8.0.250:8087/RPC2"}
localIP = "192.168.67.43" # IP-address of luckypipe
localPort = {'vis':1500, 'red': 1501}  # Port on luckypipe
filenamePrefix = {'vis':'v1','red':'r1'}
obslogDir = '/tmp/'

#Setup of the camera, and the calibration

imageY = 512
imageX = 512
numOverscan = 18
overscan =  [20,532] #[34,1058] 
nBias = 1000
nFlat = 20
expTime =  [0.02,0.5]
flatTime = 120
flatbiasTime = 0.1
nFlatbias = 20
refNumber = 100
subExposure = 100	# Normal 100
UTCtoTT = 34 + 32.1845
EMgain = 0

# Database values:
db_host = "site02.ss3n1.prv"
db_user = "postgres"
db_password = ""

# Header paths:
#database from where to get data to header:
db_table = "obs_request_1"
db_header = "song"
db_info_header = "db_tenerife"
db_weather_table = "weather_station"
db_tel_dome_table = "tel_dome"
db_nasmyth_unit = "nasmyth_unit"

# Star checker. Insert other coordinates here if another site then Teide is used.
site_name = 'Tenerife'
lat_obs = 28.2983 #latitude of the observatory
lon_obs = -16.5094 #longitude of the observatory with base "west"
elev_obs = 2395 #elevation of the observatory
telescope = 'SONG@Tenerife'
inst_name = 'SONG HighSpeed Camera'

commentDict = {}
commentDict['TYPE']     = 'Type of exposure'
commentDict['TELESCOP'] = 'Telescope name'
commentDict['INST']     = 'Instrument name' 
commentDict['CHANNEL']  = 'Color channel (VIS or RED camera)'
commentDict['SITE']     = 'Telescope site'
commentDict['LAT']      = 'Telescope latitude'
commentDict['LON']      = 'Telescope longitude'
commentDict['ELEV']     = 'Telescope elevation'
commentDict['BLK_SIZE'] = 'Exposure block size'
commentDict["TEMP"]     =  "Temperature of sensor"
commentDict["SETTEMP"]  =  "Target temperature of sensor"
commentDict["EM_GAIN"]  =  "Electron multiplication gain"
commentDict["PRE_AMP"]  =  "Preamplifier gain"
commentDict["BITDEPTH"] =  "Bit depth at readout"
commentDict["OUT_AMP"]  =  "EM or conventional readout, 0 = EM"
commentDict["HS_SPEED"] =  "Horizontal shift speed (readout speed) in MHz"
commentDict["VS_SPEED"] =  "Vertical shift speed in uSec"
commentDict["SERIAL"]   =  "Serial number of camera"
commentDict["EXP_TIME"] =  "Exposure time of individual images in s"
commentDict["ACC_TIME"] =  "Accumulation time"
commentDict["KIN_CY"]   =  "Kinetic cycle time in s"
commentDict["FT"]       =  "CCD frametransfer"
commentDict["OBJECT"]   =  "Selected Target"
commentDict['EX_START'] =  "Start exposure in YYYY-MM-DD UTC"
commentDict['UTSTART']  =  "Start exposure in UTC isoformat"
commentDict['MJD_ST']   =  "Start exposure MJD(UTC)"
commentDict['TEL_RA']   =  'Telescope RA'
commentDict['TEL_DEC']  =  'Telescope Dec'
commentDict['TEL_AZ']   =  'Telescope Azimut'
commentDict['TEL_ALT']  =  'Telescope Altitude'
commentDict['TEL_FOC']  =  'Telescope Focus'
commentDict['TEL_TM']   =  'Telescope Third Mirror'
commentDict['TEL_ST']   =  'Telescope star time'
commentDict['HA']       =  'Hour Angle'
commentDict['ZDIST']    =  'Zenit distance'
commentDict['IDR_A']    =  'Image derotator angle'
commentDict['IDR_O']    =  'Image derotator orientation'
commentDict['IDR_T']    =  'Image derotator tracking'
commentDict['ADC_1']    =  'ADC angle 1'
commentDict['ADC_2']    =  'ADC angle 2'
commentDict['ADC_T']    =  'ADC tracking'
commentDict['FW_RED']   =  'Filterwheel position red arm'
commentDict['FW_VIS']   =  'Filterwheel position vis arm'
commentDict['BEAM_S']   =  'Nasmyth beamselector pos'

ERROR_CODE = {
    20001: "DRV_ERROR_CODES",
    20002: "DRV_SUCCESS",
    20003: "DRV_VXNOTINSTALLED",
    20006: "DRV_ERROR_FILELOAD",
    20007: "DRV_ERROR_VXD_INIT",
    20010: "DRV_ERROR_PAGELOCK",
    20011: "DRV_ERROR_PAGE_UNLOCK",
    20013: "DRV_ERROR_ACK",
    20024: "DRV_NO_NEW_DATA",
    20026: "DRV_SPOOLERROR",
    20034: "DRV_TEMP_OFF",
    20035: "DRV_TEMP_NOT_STABILIZED",
    20036: "DRV_TEMP_STABILIZED",
    20037: "DRV_TEMP_NOT_REACHED",
    20038: "DRV_TEMP_OUT_RANGE",
    20039: "DRV_TEMP_NOT_SUPPORTED",
    20040: "DRV_TEMP_DRIFT",
    20050: "DRV_COF_NOTLOADED",
    20053: "DRV_FLEXERROR",
    20066: "DRV_P1INVALID",
    20067: "DRV_P2INVALID",
    20068: "DRV_P3INVALID",
    20069: "DRV_P4INVALID",
    20070: "DRV_INIERROR",
    20071: "DRV_COERROR",
    20072: "DRV_ACQUIRING",
    20073: "DRV_IDLE",
    20074: "DRV_TEMPCYCLE",
    20075: "DRV_NOT_INITIALIZED",
    20076: "DRV_P5INVALID",
    20077: "DRV_P6INVALID",
    20079: "DRV_INVALID_FILTER",
    20083: "P7_INVALID",
    20089: "DRV_USBERROR",
    20091: "DRV_NOT_SUPPORTED",
    20099: "DRV_BINNING_ERROR",
    20100: "DRV_INVALID_AMPLIFIER",
    20990: "DRV_NOCAMERA",
    20991: "DRV_NOT_SUPPORTED",
    20992: "DRV_NOT_AVAILABLE",
    20131: "DRV_FPGA_VOLTAGE_ERROR"}


