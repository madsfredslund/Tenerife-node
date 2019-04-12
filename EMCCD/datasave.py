'''This module contains a classes and functions for generating the SONG LuckyCam HDF5 format files that are used to spool the raw data from the LuckyCam. 
The Spool file will be a complete package that contains all relavant information for later reduction of the data.

HDF5 layout
#####################################

The std. layout of the SONG LuckyCam spool files is as follows:

File(filename=testspool.h5, title='', mode='r', rootUEP='/', filters=Filters(complevel=0, shuffle=False, fletcher32=False))
 
:/ (RootGroup): ''

    :/bias: (Array(512, 538)) ''
      atom := Float64Atom(shape=(), dflt=0.0)
      maindim := 0
      flavor := 'numpy'
      byteorder := 'little'
      chunkshape := None
    :/flat: (Array(512, 538)) ''
      atom := Float64Atom(shape=(), dflt=0.0)
      maindim := 0
      flavor := 'numpy'
      byteorder := 'little'
      chunkshape := None
    :/imageData: (Table(200,)) ''
      description := {
      "image": UInt16Col(shape=(512, 538), dflt=0, pos=0)}
      byteorder := 'little'
      chunkshape := (1,)
    :/reducedData: (Table(200,), shuffle, zlib(2)) 'LIDataTable'
      description := {
      "offset": Float32Col(shape=(), dflt=0.0, pos=0),
      "qFactor": Float32Col(shape=(), dflt=0.0, pos=1),
      "shift": Int32Col(shape=(2,), dflt=0, pos=2)}
      byteorder := 'little'
      chunkshape := (512,)
    :/spurious: (Array(512, 538)) ''
      atom := Float64Atom(shape=(), dflt=0.0)
      maindim := 0
      flavor := 'numpy'
      byteorder := 'little'
      chunkshape := None

This module needs access to numpy,threading,Queue (Python 2.6), pyfits, time, datetime, tables(PyTables) and logging'''


import numpy
import threading
import Queue
import pyfits
import andorsetup
import time
import datetime
import tables as tb
import logging
import shutil
import os

dataDirectory = andorsetup.dataDirectory
storageDirectory = andorsetup.storageDirectory
imageY = andorsetup.imageY #1024#512
imageX = andorsetup.imageX #1024#512
numOverscan = andorsetup.numOverscan #34#26
imageCoor = andorsetup.overscan #[34,1058]#[20,532]
fnPrefix = andorsetup.filenamePrefix
obslogDir = andorsetup.obslogDir

commentDict = andorsetup.commentDict

lookupString = '0123456789abcdefghijklmnopqrstuvxyzABCDEFGHIJKLMNOPQRSTUVXYZ='
monthString = 'abcdefghijklmnopqrstuvxyz'
daystring = 'abcdefghijklmnopqrstuvxyzABCDEFGHIJKLMNOPQRSTUVXYZ='

def wrtLog(ch,fileName,conf,nExp):
    '''Creates a logfile '''
    logname = obslogDir+'obslog_{0}_{1}.log'.format(datetime.date.today().isoformat(),ch.lower())
    if not os.path.exists(logname):
        with open(logname,'w') as f:
            f.write('#  filename  #  UTC start  #  RA  #  DEC  #  filter position  #  Single Exp time  #  Number of Exposures  # \n')
    with open(logname,'a') as f:
        f.write('{0} {1} {2} {3} {4} {5:1.2f} {6:d} \n'.format(
                 fileName.split('/')[-1],conf['UTSTART'], conf['TEL_RA'],conf['TEL_DEC'],
                 conf['FW_{0}'.format(ch.upper())],conf['EXP_TIME'], nExp) )
    f.closed

def WriteFitsImage(configuration,array,path):
    hdu = pyfits.PrimaryHDU(array)
    hdulist = pyfits.HDUList([hdu])
    for (key,value) in configuration.iteritems():
        try:
            hdulist[0].header.update(key,value,commentDict[key])
        except KeyError:
            pass
            #hdulist[0].header.update(key,value,'Unknown')
    hdulist.writeto(path,clobber=True)

class TableConfig(tb.IsDescription):
    '''Configuration class for the tables created by pytables when saving''' 
    image = tb.UInt16Col(shape=(imageY,imageX+numOverscan))
    
class TimingTableConfig(tb.IsDescription):
    time = tb.Time64Col()

def generatefilebody():
    d = datetime.datetime.utcnow()
    l = lookupString
    m = monthString
    ds = daystring
    return d.strftime('%y')+m[d.month-1]+ds[d.day-1]+d.strftime('%H')+l[d.minute]+l[d.second]

def GenerateSnapShotFileName(target, channel):
    fileName=dataDirectory+'SnapShot_{0}.fits'.format(channel)
    return fileName

def GenerateSpoolFileName(target, channel):
    temp = generatefilebody()
    fileName=storageDirectory+'Spool_{0}_l{1}_{2}.h5'.format(str(target).strip(),fnPrefix[channel],temp)
    return fileName

def DataSaver(inputQue, talkbackQue, bias, biasConfiguration, flat,flatConfiguration,spurious,spuriousConfiguration,exposureNumber,configuration):
    '''Function which makes a HDF5 file given the configuration (dictionaries), bias (array) and 
     flat (array) data. 
     It then listens for datacubes (arrays) on the inputQue which are saved in the 
     file in the table imageData timing data is stored in the timingData table. 
     The functions quits and cloases the file when the tuble ("Done",endtime (float) ) is recived.
     Can talk back to it parrent wit the talkBackQue, returns the spool filename'''
    channel = configuration['CHANNEL'].lower()
    config = inputQue.get(True,None)
    configuration.update(config)
    filters= tb.Filters(complevel=0,complib='lzo')
    fileName = GenerateSpoolFileName(configuration['OBJECT'], channel)
    print('Spooling to: '+fileName)
    try:
        h5file = tb.openFile(fileName+'.tmp',mode='w',filters=filters)
    except:
        print('Could not create H5 file')
    biasTable = h5file.createArray('/','bias',bias)
    try:
        for (key,value) in biasConfiguration.iteritems():
            biasTable.setAttr(key,value)
        biasTable.setAttr('configuration',biasConfiguration)
    except:
        pass
    flatTable = h5file.createArray('/','flat',flat)
    try:
        for (key,value) in flatConfiguration.iteritems():
            flatTable.setAttr(key,value)
        flatTable.setAttr('configuration',flatConfiguration)
    except:
        pass
    spuriousTable = h5file.createArray('/','spurious',spurious)
    try:
        for (key,value) in spuriousConfiguration.iteritems():
            spuriousTable.setAttr(key,value)
        spuriousTable.setAttr('configuration',spuriousConfiguration)
    except:
        pass
    print('DataSaver Started')
    dataTable = h5file.createTable('/','imageData', TableConfig, 'DataTable', expectedrows=exposureNumber)
    dataRow = dataTable.row
    timingTable = h5file.createTable('/','timingData',TimingTableConfig, 'TimingTable',expectedrows=int(exposureNumber/100))
    timingRow = timingTable.row
    print('Got configuration')
    for (key,value) in configuration.iteritems():
        dataTable.setAttr(key,value)
    dataTable.setAttr('overscan',imageCoor)
    dataTable.setAttr('configuration',configuration)
    index = 0
    while True:
        imageCube = inputQue.get(True,None)
        print('Got a image cube: '+str(index))
        index += 1
        if imageCube[0] == 'Done':
            print('Image processor done')
            #endtime = inputQue.get(True,None)
            configuration['EX_END'] = imageCube[1]
            dataTable.setAttr('configuration',configuration)
            break
        for i in range(imageCube[0].shape[0]):
            dataRow['image'] = imageCube[0][i,:,:]
            dataRow.append()
        timingRow['time'] = imageCube[1]
        timingRow.append()
    h5file.flush()
    h5file.close()
    wrtLog(channel,fileName,configuration,exposureNumber)
    shutil.move(fileName+'.tmp', fileName)
    print('Done: '+fileName)
    return fileName
