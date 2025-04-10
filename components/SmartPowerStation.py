import json
import subprocess
import logging

class SmartPowerStation():
	def __init__(self, conf: str):
		self.config = self.getConfig(conf)
		self.name = self.config['location']
		self.location = self.config['location']
		self.promise = self.config['promise']
		self.network = self.config['network']
		self.printInfo = True
		self.printDebug = True
		self.printError = True

	######### SETUP ###############

	# reads json config file and returns it as dict
	def getConfig(self, fn:str) -> dict:
		# Read data from a JSON file
		try:
			with open(fn, "r") as json_file:
				return json.load(json_file)
		except Exception as e:
			self.log_error(f"Error during reading config file: {e}")
			return {}

	######### BLUETOOTH ############
	def reset_bluetooth(self):
		try:
			subprocess.run(["sudo", "hciconfig", "hci0", "up"], check=True)
			subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], check=True)
		except subprocess.CalledProcessError as e:
			self.log_error(f"Bluetooth interface reset failed: {e}")

	def broadcastIP(self):
		pass

	# ============================
	# Logging Helper
	# ============================
	def log_info(self, message: str) -> None:
	    """Logs an info message."""
	    logging.info(message)
	    self.log_print(message, self.printInfo)

	def log_error(self, message: str) -> None:
	    """Logs an error message."""
	    logging.error(message)
	    self.log_print(message, self.printError)

	def log_debug(self, message: str) -> None:
	    """Logs a debug message."""
	    logging.debug(message)
	    self.log_print(message, self.printDebug)

	def log_print(self, message:str, b:bool):
	    if b:
	        print(message)