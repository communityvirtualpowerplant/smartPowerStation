import json
import subprocess
import logging
from typing import cast
from typing import Any, Dict, Optional, Tuple, List
from bleak import BleakClient, BleakError, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import asyncio
from datetime import datetime, date, timedelta
import requests

class SmartPowerStation():
    def __init__(self, conf: str,info=True, debug=True,error=True):
        self.config = self.getConfig(conf)
        self.name = self.config['location']
        self.location = self.config['location']
        self.promise = self.config['promise']
        self.network = self.config['network']
        self.printInfo = info
        self.printDebug = debug
        self.printError = error
        self.dataFilePrefix = 'sps'
        self.shellySTR = 'Shelly'
        self.bluettiSTR = ['AC180','AC2']
        self.devices = []
        self.bleAdapter = "hci0" #changed based on hardware

    ######### SETUP ###############

    # reads json config file and returns it as dict
    def getConfig(self, fn:str) -> Any:
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
    
    # get list of saved devices from device file, filtered by location
    def getDevices(self, dF:str, location:Optional[str] = None)->list[Dict]:
        if location is None:
            location = self.location

        self.log_debug(location)

        # Read data from a JSON file
        try:
            with open(dF, "r") as json_file:
                savedDevices = json.load(json_file)
        except Exception as e:
            log_error(f"Error during reading devices.json file: {e}")
            savedDevices = []

        filteredEntries = []

        #filter by location
        for entry in savedDevices:
            if entry['location'] == location:
                filteredEntries.append(entry)

        self.devices=filteredEntries

        return self.devices

    def writeJSON(self, data:Any, fn:str)-> None:
        # Save data to a JSON file
        try:
            with open(fn, "w") as json_file:
                json.dump(data, json_file, indent=4)

            print(f"JSON file saved successfully at {fn}")
        except Exception as e:
            self.log_error(f"Error during saving {fn} file: {e}")

    ######### BLUETOOTH ############
    def reset_bluetooth(self) -> None:
        try:
            subprocess.run(["sudo", "hciconfig", "hci0", "up"], check=True)
            subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], check=True)
        except subprocess.CalledProcessError as e:
            self.log_error(f"Bluetooth interface reset failed: {e}")

    # scans for BLE devices and filters them by the saved device list (already filtered by location)
    # returns list of BLE objects and matching saved devices i.e. [BLE, saved]
    async def scan_devices(self, saved_devices: list[Dict])->list[Dict]:
        filteredDevices = []
        scan_duration = 5

        addressList = []
        def discovery_handler(device: BLEDevice, advertisement_data: AdvertisementData):
            # mf = ''
            # notFound = 1

            if device.name is None:
                return

            for sd in saved_devices:
                #print(sd)
                if device.address == sd['address'] and device.address not in addressList:    
                    self.log_debug(device)
                    addressList.append(device.address)
                    filteredDevices.append([device,sd])

        self.log_info(f"Scanning for BLE devices for {scan_duration} seconds...")

        async with BleakScanner(adapter=self.bleAdapter, detection_callback=discovery_handler) as scanner:
            await asyncio.sleep(scan_duration)
        
        self.log_debug(addressList)

        # Some BLE chipsets (especially on Raspberry Pi) need a few seconds between scanning and connecting.
        await asyncio.sleep(2)
        
        return filteredDevices

    # ============================
    # Utilities
    # ============================
    def handle_signal(self, signal_num: int, frame: Any) -> None:
        """Handles termination signals for graceful shutdown."""
        self.log_info(f"Received signal {signal_num}, shutting down gracefully...")
        sys.exit(0)

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

    def log_print(self, message:str, b:bool) -> None:
        if b:
            print(message)

    # ============================
    # Data
    # ============================
    #Check if the timestamp is within the last 10 minutes.
    def isRecent(ts, seconds=600)->bool:
        if isinstance(ts, str):
            ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") #check if the ts is a string and convert
        now = datetime.now()
        return now - ts <= timedelta(seconds)

    def packageData(self, d, r, t) -> Dict:
        try:
            if d[1]['manufacturer'].lower() == 'bluetti':
                #print('bluetti!')
                t["powerstation_percentage"] = round(r['total_battery_percent'], 2)
                t["powerstation_inputWAC"] = r['ac_input_power']
                t["powerstation_inputWDC"] = r['dc_input_power']
                t["powerstation_outputWAC"] = r['ac_output_power']
                t["powerstation_outputWDC"] = r['dc_output_power']
                t["powerstation_outputMode"] = r['output_mode']
                t["powerstation_deviceType"] = r['device_type']
            elif 'Shelly'.lower() in d[1]['name'].lower():
                if '1PM'.lower() in d[1]['name'].lower():
                    #print('1pm!')
                    if d[1]['relay1'] == 1:
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

# ============================
# Control
# ============================
class Controls():
    def __init__(self):
        self.goalWh = 0
        self.duration = 4
        self.batCapWh = 0
        self.maxFlexibilityWh = 0
        self.availableFlexibilityWh = 0
        self.invEff = .85 #assumes 85% efficient inverter
        self.dod = .8 # assumes 80% depth of discharge
        self.avgPvWh = 0 # recent daily average
        self.maxPvWh = 0 # recent daily max
        self.eventStartH = 0
        self.eventDurationH = 4
        self.baseline = 0
        self.modeOne = {1:1,2:1,3:0} #with an autotransfer, if pos 1 is on pos 3 is automatically off
        self.modeTwo = {1:1,2:0,3:0} #with an autotransfer, if pos 1 is on pos 3 is automatically off
        self.modeThree = {1:0,2:1,3:1}
        self.modeFour = {1:0,2:1,3:0}
        self.modeFive = {1:0,2:0,3:1}
        self.modeSix = {1:0,2:0,3:0}
        self.Kp = 0
        self.Ki = 0
        #self.Kd = Kd
        self.setpoint = 0
        self.previous_error = 0
        self.integral = 0
        self.sunWindowStart = 10
        self.sunWindowDuration = 2
        self.url = 'localhost'
        self.port = 5000
        self.fileList = []
        self.rules = {}

    # reads json config file and returns it as dict
    def getRules(self, fn:str) -> Any:
        # Read data from a JSON file
        try:
            with open(fn, "r") as json_file:
                self.rules = json.load(json_file)
                return self.rules
        except Exception as e:
            print(f"Error during reading {fn} file: {e}")
            return {}

    # type = json, text, or status_code
    async def send_get_request(self, ip:str, port:int,endpoint:str,type:str,timeout=1) -> Dict:
        """Send GET request to the IP."""
        try:
            response = requests.get(f"http://{ip}:{port}{endpoint}", timeout=timeout)
            if type == 'json':
                return response.json()
            elif type == 'text':
                return response.text
            else:
                return response.status_code
        except Exception as e:
            return e

    # sets battery capacity and determines maximum automatable flexibility
    def setBatCap(self,Wh):
        CONTROLS.batCapWh = Wh
        CONTROLS.maxFlexibilityWh = CONTROLS.getAvailableFlex(100)

    # returns the available flexibility in WhAC
    # pass in battery percentage
    def getAvailableFlex(self,perc):
        if perc > 1.0:#convert percentage to decimal if needed
            perc = perc * .01
        return ((self.batCapWh * perc) - (self.batCapWh * (1-self.dod))) * self.invEff


    # returns all file names within the last X days
    async def getRecentFileList(self,duration=30):
        self.fileList = await self.send_get_request(self.url, self.port,'/api/files','json')
        self.fileList = sorted(self.fileList, reverse=True)

        # start with todays date
        checkFile = date.today()
        recentFileNames = [] #store most recent found file names

        #look for files within the last X days
        for d in range(1,duration):
            for f in self.fileList: # loop through file list to get recent
                if str(checkFile) in f:
                    # add file to recent files
                    recentFileNames.append(f)
                    break
            checkFile = checkFile - timedelta(days=1)

        return recentFileNames

    # estimate DR baseline for the specified event window
    async def estBaseline(self, d=30):
        recentFileNames = self.getRecentFileList(d)

        # get earliest, latest, and max sun times for each file
        data = []
        for f in recentFileNames:
            fn = f.split('.')[0]
            data.append(await self.send_get_request(self.url, self.port,f"/api/data?files={fn}",'json'))

    def pi_controller(self, pv, kp, ki,):
        error = self.setpoint - pv
        self.integral += error * dt
        control = kp * error + ki * self.integral
        return control, error, integral

    def pid_controller(self, pv, kp, ki, kd, dt):
        error = self.setpoint - pv
        self.integral += error * dt
        derivative = (error - self.previous_error) / dt
        control = kp * error + ki * self.integral + kd * derivative
        return control, error, integral

    #estimate when the PV will start producing and for how long
    async def estSunWindow(self):
        # get recent files
        recentFileNames = self.getRecentFileList()

        # if len(recentFileNames) >= 2:
        #     break

        # if there are no recent files, set defaults and return
        if len(recentFileNames)==0:
            self.sunWindowStart = 10 
            self.sunWindowDuration = 4
            return

        # get earliest, latest, and max sun times for each file
        for f in recentFileNames:
            fn = f.split('.')[0]
            self.fileList = await self.send_get_request(self.url, self.port,f"/api/data?files={fn}",'json')

        # average

        #temp
        self.sunWindowStart = 10 
        self.sunWindowDuration = 4
        return
    
    # get tomorrows weather
    def getWeather(self):
        pass

    #estimate recent daily average and max PV production(Wh)
    def estPV(self):
        # get 
        pass

    # maintains battery at level to utilize PV
    def utilizePV(self):
        pass

    def checkMode(self):
        pass
