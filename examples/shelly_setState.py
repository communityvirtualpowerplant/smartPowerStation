# gets data and saves it in a CSV file
# run with "python -m examples.ble_logStatus" + location from parent directory

import sys
import subprocess
# import numpy as np
import pandas as pd
import csv
import asyncio
import json
import signal
import logging
import time
import datetime
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

dataDirectory = '../data/'
deviceFile = '../config/devices.json'
configFile = '../config/config.json'

#if an arg has been passed
if len(sys.argv) > 1:
    toState = bool(int(sys.argv[len(sys.argv)-1]))
else:
    toState = bool(0)

print('Setting state: ' + str(toState))

# ============================
# Logging Helper
# ============================
# def log_info(message: str) -> None:
#     """Logs an info message."""
#     logging.info(message)
#     log_print(message, printInfo)

# def log_error(message: str) -> None:
#     """Logs an error message."""
#     logging.error(message)
#     log_print(message, printError)

# def log_debug(message: str) -> None:
#     """Logs a debug message."""
#     logging.debug(message)
#     log_print(message, printDebug)

# def log_print(message:str, b:bool):
#     if b:
#         print(message)

# ============================
# Utilities
# ============================
def handle_signal(signal_num: int, frame: Any) -> None:
    """Handles termination signals for graceful shutdown."""
    SPS.log_info(f"Received signal {signal_num}, shutting down gracefully...")
    sys.exit(0)

# ============================
# Main
# ============================        
async def main(SPS: SmartPowerStation) -> None:
    SPS.reset_bluetooth()

    assign = [{"pos": 1, "state":toState}]

    positions = []
    for a in assign:
        positions.append(a['pos'])

    # get saved devicecs, filtered by location
    savedDevices = SPS.getDevices(deviceFile,SPS.location)
    # filter devices list by assigned position
    #filteredEntries = []
    # for entry in savedDevices:
    #         if entry['relay1'] in positions:
    #             filteredEntries.append(entry)
    #         elif entry['relay2'] in positions:
    #             filteredEntries.append(entry)

    if len(savedDevices) >= 1:
        try:
            # scan devices to get BLE object
            devices = await SPS.scan_devices(savedDevices)
        except Exception as e:
            log_error(f"Error during scanning: {e}")
            return

        if not devices:
            SPS.log_error("No devices found. Exiting")
            sys.exit(0)

        for d in devices:
            SPS.log_debug(d)
            bleDev = d[0]
            savedDev = d[1]

            # filter by shelly device
            if savedDev['manufacturer'] == 'shelly':

                shDevice = ShellyDevice(savedDev["address"], savedDev["name"])

                # set ID based on position
                if int(savedDev['relay1'])==int(assign[0]['pos']):
                    r =0 
                elif int(savedDev['relay2'])==int(assign[0]['pos']):
                    r =1
                try:
                    # set relay state
                    await shDevice.setState(toState,r)
                except Exception as e:
                    SPS.log_error(f"Error setting state")
    
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
        SPS.log_info("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        SPS.log_error(f"Unexpected error in main: {e}")
