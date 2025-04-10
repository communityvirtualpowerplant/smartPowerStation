class SmartPowerStation():
    def __init__(self, conf: Dict, name: str):
        # self.config = conf
        self.name = name
        self.location = config['location']
        self.promise = config['promise']
        self.network = config['network']
       
	def reset_bluetooth(self):
	    try:
	        subprocess.run(["sudo", "hciconfig", "hci0", "up"], check=True)
	        subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], check=True)
	    except subprocess.CalledProcessError as e:
	        log_error(f"Bluetooth interface reset failed: {e}")

	def broadcastIP(self):
		pass