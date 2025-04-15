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
		self.dataFilePrefix = 'sps'

	######### SETUP ###############

	# reads json config file and returns it as dict
	def getConfig(self, fn:str) -> dict:
		# Read data from a JSON file
		try:
			with open(fn, "r") as json_file:
				return json.load(json_file)
		except Exception as e:
			self.log_error(f"Error during reading {fn} file: {e}")
			if 'devices' in fn.lower():
				return []
			else:
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

	# ============================
	# Data
	# ============================
	def packageData(self, d, r, t):
	    try:
	        if d[1]['manufacturer'].lower() == 'bluetti':
	            #print('bluetti!')
	            t["powerstation_percentage"] = r['total_battery_percent']
	            t["powerstation_inputWAC"] = r['ac_input_power']
	            t["powerstation_inputWDC"] = r['dc_input_power']
	            t["powerstation_outputWAC"] = r['ac_output_power']
	            t["powerstation_outputWDC"] = r['dc_output_power']
	            t["powerstation_outputMode"] = r['output_mode']
	            t["powerstation_deviceType"] = r['device_type']
	        elif 'Shelly'.lower() in d[1]['name'].lower():
	            if '1PM'.lower() in d[1]['name'].lower():
	                #print('1pm!')
	                if d[1]['assignment0'] == 1:
	                    t['relay1_power'] = r[0]["apower"]
	                    t['relay1_current'] =r[0]["current"]
	                    t['relay1_voltage'] =r[0]["voltage"]
	                    t['relay1_status'] =str(r[0]["output"]) #must be cast to str because the dict interprets the bool as an int
	                    t['relay1_device'] = d[1]['name']
	                else:
	                    t['relay2_power'] = r[0]["apower"]
	                    t['relay2_current'] =r[0]["current"]
	                    t['relay2_voltage'] =r[0]["voltage"]
	                    t['relay2_status'] =str(r[0]["output"]) #must be cast to str because the dict interprets the bool as an int
	                    t['relay2_device'] = d[1]['name']
	            elif '2PM'.lower() in d[1]['name'].lower():
	                #print('2pm!')
	                t['relay1_power'] = r[0]["apower"]
	                t['relay1_current'] =r[0]["current"]
	                t['relay1_voltage'] =r[0]["voltage"]
	                t['relay1_status'] =str(r[0]["output"]) #must be cast to str because the dict interprets the bool as an int
	                t['relay1_device'] = d[1]['name']
	                t['relay2_power'] = r[1]["apower"]
	                t['relay2_current'] =r[1]["current"]
	                t['relay2_voltage'] =r[1]["voltage"]
	                t['relay2_status'] =str(r[1]["output"]) #must be cast to str because the dict interprets the bool as an int
	                t['relay2_device'] = d[1]['name']
	    except Exception as e:
	        print(e)

	    return t