#!/usr/bin/python
"""
   Created on Jun 04, 2010

   @author: Mads Fredslund Andersen

"""

import netsnmp
import sys
import pdu_config
import song_timeclass

class APC(object):
   """
      @brief: This class will control the APC PDU device.
   """
   def SetPower(self,unit,outlet,state):
      """
         @brief: This function changes the state of the specified outlet. 

         @param outlet: The ID-number of the outlet which will be switched on/off.
         @param state: The state to which to outlet will be switched.
      """
      
      if unit == "nasmyth": dest_host = pdu_config.DestHost_nasmyth
      elif unit == "container": dest_host = pdu_config.DestHost_container
      elif unit == "side_ports": dest_host = pdu_config.DestHost_side_ports
      elif unit == "nasmyth_2": dest_host = pdu_config.DestHost_nasmyth_2
      else: print "Error, wrong unit provided!"
        
      clock = song_timeclass.TimeClass()
        
      OID = ".1.3.6.1.4.1.318.1.1.4.4.2.1.3.%i" % int(outlet) # .1.3.6.1.4.1.318 defines that the connection is to a APC device. 
                                                                # the .1.1.4.4.2.1.3 is defining that changes is made to the power outlet.
                                                                # %i % int(outlet) is the outlet number which will be chanced.
      var = netsnmp.Varbind(".1.3.6.1.4.1.318.1.1.4.4.2.1.3.%i" % int(outlet))
      res = netsnmp.snmpget(var,
                              Version = 1,
                              DestHost=dest_host,
                              Community=pdu_config.Community)

      var.tag = OID
      var.val = int(state) # The value of the outlet is set to the given state.
      
      setpower = "" 
      try:  
         setpower = netsnmp.snmpset(var, Version = 1, DestHost = dest_host, Community=pdu_config.Community) # Here the outlet, number int(outlet), is chanced to int(state
      except Exception, e:
         sys.exit("ERROR, connection to PDU could not be made!")

      if setpower == "" or setpower == None:
         sys.exit("ERROR, connection to PDU could not be made!")
      else:
         if int(setpower) == 1 and int(state) == 1:
            #print 'The power on outlet nr: '+str(outlet)+' on the %s is now switched to: On ' % unit
            return 'The power on outlet nr: '+str(outlet)+' on the %s is now switched to: On' % unit
         elif int(setpower) == 1 and int(state) == 2:
            #print 'The power on outlet nr: '+str(outlet)+' on the %s is now switched to: Off ' % unit
            return 'The power on outlet nr: '+str(outlet)+' on the %s is now switched to: Off' % unit
         else:
	    print "setpower= ", setpower
            print 'Something is wrong with the APC PDU! ', clock.whattime()
            return 'Something is wrong with the APC PDU!'
    
   def GetPower(self,unit,outlet):
      """
         @brief: This function returns the state of the specified outlet.

         @param outlet: The ID-number of the outlet for which the state will be returned.
      """
       
      if unit == "nasmyth": dest_host = pdu_config.DestHost_nasmyth
      elif unit == "container": dest_host = pdu_config.DestHost_container
      elif unit == "side_ports": dest_host = pdu_config.DestHost_side_ports
      elif unit == "nasmyth_2": dest_host = pdu_config.DestHost_nasmyth_2
      else: print "Error, wrong unit provided!"

      clock = song_timeclass.TimeClass()
      
      OID = ".1.3.6.1.4.1.318.1.1.4.4.2.1.3.%i" % int(outlet)

      powerstatus = ""
      try:
         powerstatus = netsnmp.snmpget(OID, Version = 1, DestHost = dest_host, Community=pdu_config.Community)
      except Exception, e:
         sys.exit("ERROR, connection to PDU could not be made!")

      if powerstatus == "" or powerstatus[0] == None:
         sys.exit("ERROR, connection to PDU could not be made!")
      else:
         if int(powerstatus[0]) == 1:
            #return 'Power status on outlet nr: '+str(outlet)+' is: On'
            return 1
         elif int(powerstatus[0]) == 2:
            #return 'Power status on outlet nr: '+str(outlet)+' is: Off'
            return 2
         else:
            return 'Something is wrong with the APC PDU!'

   def GetInfo(self,unit):
      """
         @brief: This function will return some info about the APC-PDU device. 

         @todo: This function could be filled with possibilities. 
      """

      if unit == "nasmyth": 
         dest_host = pdu_config.DestHost_nasmyth
         pdu_names = pdu_config.names_nasmyth	 	
      elif unit == "container": 
         dest_host = pdu_config.DestHost_container
         pdu_names = pdu_config.names_container
      elif unit == "side_ports": 
         dest_host = pdu_config.DestHost_side_ports
         pdu_names = pdu_config.names_side_ports
      elif unit == "nasmyth_2": 
         dest_host = pdu_config.DestHost_nasmyth_2
         pdu_names = pdu_config.names_nasmyth_2
      else: print "Error, wrong unit provided!"
        
      clock = song_timeclass.TimeClass()
      OID = ".1.3.6.1.4.1.318.1.1.4.5.1.0" # Returns the total number of outlets (24 with this PDU)

      powerstatus = ""
      try:
         powerstatus = netsnmp.snmpget(OID, Version = 1, DestHost = dest_host, Community=pdu_config.Community)
      except Exception, e:
         sys.exit("ERROR, connection to PDU could not be made!")

      if powerstatus == "" or powerstatus[0] == None:
         sys.exit("ERROR, connection to PDU could not be made!")
      else:
         print "\nStatus on all outlets for the %s PDU:" % unit

         for i in range(1,int(powerstatus[0])+1):
            outlet = int(i)
            try:
               powervalue = self.GetPower(unit,outlet)
            except Exception, e:
               print 'Could not connect to the PDU!'
               print e

            if powervalue == 1:
               print str(outlet) + ' ' + str(pdu_names[outlet - 1]) + '	:	On '
            elif powervalue == 2:
               print str(outlet) + ' ' + str(pdu_names[outlet - 1]) + '	:	Off '
            else:
               print powervalue

      return 1

