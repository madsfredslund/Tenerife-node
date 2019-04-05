import signal
import time

class TimeoutFunctionException(Exception): 
	"""Exception to raise on a timeout"""
	pass 

class TimeoutFunction(): 

	def __init__(self, function=None, timeout=5, time_out_return_value=1): 
		self.timeout = timeout 
		self.function = function 
		self.time_out_return_value = time_out_return_value

	def handle_timeout(self, signum, frame):
        	raise TimeoutFunctionException()

	def __call__(self, *args): 
		old = signal.signal(signal.SIGALRM, self.handle_timeout) 
		signal.alarm(self.timeout) 
		try: 
			result = self.function(*args)
		except TimeoutFunctionException:
			return self.time_out_return_value # This is the return value if timeout is reached. Should be set to 1 or something given.
		finally: 
			signal.signal(signal.SIGALRM, old)
		signal.alarm(0)
		return result # this is the return value from the function and will be returned if timeout is not reached.
