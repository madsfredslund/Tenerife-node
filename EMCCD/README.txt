This code was written to be able to acquire images using two Andor EMCCD's in both normal mode and EM mode. 

The part for writing a proper header was never finished. 

For each camera (red and vis) a background process daemon is written (***_ccd_server.py). 
This daemon should run on the machine to which the EMCCD is connected to (either USB or PCI).

The daemon then handles all communication to the camera. 
Commands are send using the "client" scripts. These uses XML RPC (remote procedure calls) and can be used from
any machine which are able to see the "daemon machine" from the network (Ethernet). 

There are different client scripts for different purposes. 

c_***_acq.py and
li_***_acq.py
are the main client scripts for acquiring images. 
client_***_stop.py can be used to stop the daemon.
client_***_settemp.py is used for cooling or heating the CCD.
client_***_getsettings.py can be used to read some settings from the CCD.
client_***_getvalues.py can be used to read some values from the CCD.
client_***_acquire_threaded.py can be used to start acquisition of images without waiting for the job to end to return.
client_***_abort_acq.py can be used to abort an acquisition.

Running the client scripts (from the command line) with the option "-h" will print out the different options to provide to the client script and command.


***: "red" or "vis"
