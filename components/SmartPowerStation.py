import json
import subprocess
import logging
from typing import cast
from typing import Any, Dict, Optional, Tuple, List
from bleak import BleakClient, BleakError, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import asyncio

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

    ######### BLUETOOTH ############
    def reset_bluetooth(self) -> None:
        try:
            subprocess.run(["sudo", "hciconfig", "hci0", "up"], check=True)
            subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], check=True)
        except subprocess.CalledProcessError as e:
            self.log_error(f"Bluetooth interface reset failed: {e}")

    # get list of saved devices from device file, filtered by location
    def getDevices(self, dF:str, location:str)->list[Dict]:

        self.reset_bluetooth()

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

    #filter by assignment
    def filterDevices(self, saved_devices:list[Dict], assignment:list[Dict])->list[Dict]:
        filteredEntries = []

        ch = list(assignment.keys())[0]

        #filter by position
        for entry in saved_devices:
            if entry['relay1'] == assignment['pos']:
                filteredEntries.append(entry)
            elif entry['relay2'] == assignment['pos']:
                filteredEntries.append(entry)
        return filteredEntries

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

    # ============================
    # Control
    # ============================

    async def gridToBattery(self, state: bool) -> None:
        SPS.reset_bluetooth()

        location = SPS.location
        print(location)

        scan_duration = 5
        # Read data from a JSON file
        try:
            with open(deviceFile, "r") as json_file:
                savedDevices = json.load(json_file)
        except Exception as e:
            log_error(f"Error during reading devices.json file: {e}")
            savedDevices = []

        filteredEntries = []
        for entry in savedDevices:
            if entry['location'] == location:
                filteredEntries.append(entry)

        try:
            devices = await scan_devices(scan_duration, filteredEntries)
        except Exception as e:
            log_error(f"Error during scanning: {e}")
            return

        if not devices:
            log_error("No devices found. Exiting")
            sys.exit(0)

        for d in devices:
            print(d)
            # shDevice = await statusUpdate(d)
            # if shDevice:
            #     print(shDevice.status)
            #     c = list(range(shDevice.channels))
            #     print(await shDevice.execute_command(10,c))
            bleDev = d[0]
            savedDev = d[1]

            if savedDev['manufacturer'] == 'shelly':

                shDevice = ShellyDevice(savedDev["address"], savedDev["name"])
                try:
                    await shDevice.setState(toState,0)
                except Exception as e:
                    log_error(f"Error setting state")


    # turn grid to load connection on or off
    async def gridToLoad(self, state: bool) -> None:
        # go through device list

        #grab device assigned to position 2


        #set state based on bool
        if state:
            #turn on
            pass
        else:
            #turn off 
            pass