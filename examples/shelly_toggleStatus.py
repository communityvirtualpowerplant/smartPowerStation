# reads the devices.json file and retrieves the status of all devices at the specified location
# run with "python -m utilities.ble_getStatus.py" + location from parent directory

import sys
import subprocess
import asyncio
import json
import signal
import logging
import time
from typing import cast
from typing import Any, Dict, Optional, Tuple, List
from components.Shelly import ShellyDevice
from bleak import BleakClient, BleakError, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from components.SmartPowerStation import SmartPowerStation

shellySTR = 'Shelly'

printInfo = True
printDebug = True
printError = True
#logging.basicConfig(level=logging.DEBUG)

deviceFile = '../config/devices.json'
configFile = '../config/config.json'

#changed based on hardware
bleAdapter = "hci0"

# ============================
# Logging Helper
# ============================
def log_info(message: str) -> None:
    """Logs an info message."""
    logging.info(message)
    log_print(message, printInfo)

def log_error(message: str) -> None:
    """Logs an error message."""
    logging.error(message)
    log_print(message, printError)

def log_debug(message: str) -> None:
    """Logs a debug message."""
    logging.debug(message)
    log_print(message, printDebug)

def log_print(message:str, b:bool):
    if b:
        print(message)

# ============================
# Utilities
# ============================
def handle_signal(signal_num: int, frame: Any) -> None:
    """Handles termination signals for graceful shutdown."""
    log_info(f"Received signal {signal_num}, shutting down gracefully...")
    sys.exit(0)

# ============================
# Main
# ============================        
async def main(SPS: SmartPowerStation) -> None:
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
            if entry['manufacturer'] == 'shelly':
                filteredEntries.append(entry)

    try:
        devices = await scan_devices(scan_duration, filteredEntries)
    except Exception as e:
        log_error(f"Error during scanning: {e}")
        return

    if not devices:
        log_error("No devices found. Exiting")
        sys.exit(0)

    for e in devices:
        try:
            sDevice = ShellyDevice(e[1]["address"], e[1]["name"])
            print(sDevice)
            c = list(range(sDevice.channels))
            print('channels: ' + str(c))
            await sDevice.execute_command(10,c) 
        except Exception as e:
            print(e)

# returns list of BLE objects and matching saved devices i.e. [BLE, saved]
async def scan_devices(scan_duration: int, saved_devices: Dict):
    filteredDevices = []

    addressList = []
    def discovery_handler(device: BLEDevice, advertisement_data: AdvertisementData):
        # mf = ''
        # notFound = 1

        if device.name is None:
            return

        for sd in saved_devices:
            #print(sd)
            if device.address == sd['address'] and device.address not in addressList:    
                print(device)
                addressList.append(device.address)
                filteredDevices.append([device,sd])

    log_info(f"Scanning for BLE devices for {scan_duration} seconds...")

    async with BleakScanner(adapter=bleAdapter, detection_callback=discovery_handler) as scanner:
        await asyncio.sleep(scan_duration)
    
    print(addressList)

    # Some BLE chipsets (especially on Raspberry Pi) need a few seconds between scanning and connecting.
    await asyncio.sleep(2)
    
    return filteredDevices

async def statusUpdate(device):
    bleDev = device[0]
    savedDev = device[1]

    print("")
    if savedDev['manufacturer'] == 'shelly':

        savedDev['device'] = ShellyDevice(savedDev["address"], savedDev["name"])
        try:
            result = await savedDev['device'].getStatus()

            if result:
                print(f"RPC Method executed successfully. Result:")
                print(json.dumps(result))

            else:
                print(f"RPC Method executed successfully. No data returned.")
        except Exception as e:
            log_error(f"Error getting Shelly status: {e}")

if __name__ == "__main__":
    # Suppress FutureWarnings
    import warnings

    warnings.simplefilter("ignore", FutureWarning)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    SPS = SmartPowerStation(configFile)

    try:
        asyncio.run(main(SPS))
    except KeyboardInterrupt:
        log_info("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        log_error(f"Unexpected error in main: {e}")