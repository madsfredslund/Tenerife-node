import psycopg2 as dbMod
import time
import ConfigParser
import sys
import subprocess
import threading
import xmlrpclib
import sys
import comm2tcs_write
import comm2tcs_read
import song_timeclass
import master_config as m_conf

settsi = comm2tcs_write.SET_TSI()
gettsi = comm2tcs_read.GET_TSI()
clock = song_timeclass.TimeClass()

#attempt connection to server
server2 = xmlrpclib.ServerProxy('http://%s:%s' % (m_conf.ccd_server, m_conf.ccd_abort_port))

class ExtCommand(object):
	def __init__(self, cmd):
		self.cmd = cmd 
		self.process = None

	def run(self, timeout):
		def target():
			self.process = subprocess.Popen(self.cmd, shell=False)
			self.process.communicate()

		thread = threading.Thread(target=target)
		thread.start()
		thread.join(timeout)
		if thread.is_alive():
			## Send abort message to make the obs script finish more 

			# Check if OR is executing and telescope is tracking:
			print clock.timename(), "Trying to get the telescope tracking state"
			try:
				track_state = gettsi.get_pointing_track(sender="Observer")
			except Exception, e:
				print clock.timename(), "Could not get the telescope tracking state."
				print e			

			if float(track_state) == float(0.0):
				print clock.timename(), "The telescope was already stopped!"
				return 0

			e = None
			print clock.timename(), "Aborting the observation... from the timeout thread."
			print clock.timename(), "Sending an abort request to the camera."
			try:
				value = server2.abort_function()
			except Exception, e:
				print clock.timename(), "Could not connect to the camera."
				print e

			print clock.timename(), "Trying to stop the telescope"
			try:
				track_state = settsi.set_pointing_track(param=0,sender="Observer")
			except Exception, e:
				print clock.timename(), "Could not stop the telescope from tracking."
				print e

			if e != None:
				try:
					self.process.terminate()
					thread.join()
				except Exception, e:
					print clock.timename(), "The process did not exist 1, Errorcode: ", e
					return 0
			else:
				print clock.timename(), "Waiting for OR script to finish correctly or else it will be terminated!"
				time.sleep(60)
				try:
					self.process.terminate()
					thread.join()				
				except Exception, e:
					print clock.timename(), "The process did not exist 2, Errorcode: ", e
					return 0

			return -1 # If timeout is reached!
		else:
			return 0 # If process finishes before timeout.


class ObservationStatus(object):
    """
	@brief Abstraction for a OR-status-entry in the database.
	When instantiated this class will check if an status-entry with the given req_no exists in the database,
	and insert it if it does not. It also provides methods for updating the status.
	@TODO: Update the dictionary of allowed status-values. Specifically, fix the spelling-error, once the error in the database has been fixed.
    """
    


    #Enum of the allowed status-values for an OR
#    OR_status_enum = {'wait': 'wait', 'exec': 'exec', 'done': 'done', 'abort': 'abort', 'unknown': 'unknown'}
    OR_status_enum = ['wait', 'exec', 'done', 'abort', 'unknown']
 
    def __init__(self, table_name, req_no, conn):
        """ 
        @brief Initialise the object.
        The status is represented as a row in a table in the database, and as such, this row will have to be inserted,
        if it is not already present in the database.
        @param table_name The name of the status-table to use.
        @param req_no The req_no of the OR.
        """

        self.table_name = table_name
        if req_no < 0:
            raise AssertionError("Bad req-no-argument. Must be at least 0!")
        
        #self.db_connection = Connect(host=config.get("db", "dbHostStatus"), db=config.get("db", "dbNameStatus"), user=config.get("db", "dbUserStatus"), password=config.get("db", "dbPassStatus"))
        self.req_no = req_no
        self.conn = conn
        curr = self.conn.cursor()
        
        curr.execute("SELECT * FROM %s WHERE req_no=%s" % (self.table_name, self.req_no))

        if curr.rowcount == 0:
            try:
                #stmt = "INSERT INTO %s (req_no, status, ins_at) VALUES (%s, '%s', CURRENT_TIMESTAMP)" % (self.table_name, self.req_no, "wait")
		stmt = "INSERT INTO %s (req_no, status, ins_at) VALUES (%s, '%s', CURRENT_TIMESTAMP AT TIME ZONE 'UTC-0')" % (self.table_name, self.req_no, "wait") # Modified with TIME ZONE by Mads
                curr.execute(stmt)
            except Exception as e:
                self.conn.rollback()
                print("Could not create status in the database. Changes to the status-data has been rolled back.")
                print(e)
                
            self.conn.commit()
        curr.close()
            
    def __del__(self):
        """
        Function is called when the an instance of this class is deleted.
        """
	pass
        
    def update(self, status, ins_time=None):
        """
        @brief Update the status.
        Updates the status in the database. Since the req_no is locked to the instance of the ObservationStatus object, all you need to supply here is the new status. The ins_at-field in the database will be updated as well.
            
        @param status The new value for the status.
        @exception AssertionError Bad value of status provided.
        
        """
        if(ins_time==None):
            ins_time = time.time()

	if status not in list(self.OR_status_enum):
            raise AssertionError("Could not update status. The values '%s' is not among the allowed values." % (status))
        curr = self.conn.cursor()
        try:
	    stmt = "UPDATE %s SET status='%s', ins_at='%s' WHERE req_no=%s" % (self.table_name, status, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ins_time)), self.req_no) # Modified with gmtime() by Mads
            curr.execute(stmt)
        except Exception as e:
            self.conn.rollback()
            print("Could not create status in the database. Changes to the status-data has been rolled back.")
            raise e

        self.conn.commit()
        curr.close()
        
    def read(self):
        curr = self.conn.cursor()
        curr.execute("SELECT status FROM %s WHERE req_no=%s" % (self.table_name, self.req_no))
        stat = curr.fetchone()[0]
        curr.close()
        return stat
    
    def __str__(self):
        """
        Provides a string-representation of the current OR-status.
        @return A string representing this OR-status.
        """
        str_rep = "ObservationStatus(req_no=%s)" % (self.req_no)
        return(str_rep)

