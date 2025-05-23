# Gets a list of device addresses, prints out a bunch of info, and saves as json

# based on:
# https://github.com/warhammerkid/bluetti_mqtt/blob/main/bluetti_mqtt/discovery_cli.py
# https://github.com/ALLTERCO/Utilities/blob/master/shelly-ble-rpc/shelly-ble-rpc.py

# run with "python -m utilities.ble_discover.py" from parent directory

import asyncio
#from bleak import BleakError, BleakScanner
import logging
import signal
from bleak import BleakClient, BleakError, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import argparse
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
import json
from components.Shelly import ShellyDevice as Shelly
import sys

deviceFile = 'config/devices.json'
configFile = 'config/config.json'

printInfo = True
printDebug = True
printError = True
scan_duration = 5
# ============================
# Shelly Configuration Constants
# ============================
SHELLY_GATT_SERVICE_UUID = "5f6d4f53-5f52-5043-5f53-56435f49445f"
RPC_CHAR_DATA_UUID = "5f6d4f53-5f52-5043-5f64-6174615f5f5f"
RPC_CHAR_TX_CTL_UUID = "5f6d4f53-5f52-5043-5f74-785f63746c5f"
RPC_CHAR_RX_CTL_UUID = "5f6d4f53-5f52-5043-5f72-785f63746c5f"
ALLTERCO_MFID = 0x0BA9  # Manufacturer ID for Shelly devices
shellySTR = 'Shelly'

# ============================
# Bluetti Configuration Constants
# ============================
bluettiSTR = ['AC180','AC2']

#if an arg has been passed
if len(sys.argv) > 1:
    location = sys.argv[len(sys.argv) - 1]
else:
    location = ''

async def scan_devices(scan_duration: int, saved_devices: Dict):
    #devices = saved_devices

    # get unique addresses
    addresses = set([entry.get("address") for entry in saved_devices])

    log_debug(f"{len(addresses)} saved addresses found.")

    def discovery_handler(device: BLEDevice, advertisement_data: AdvertisementData):
        mf = ''
        notFound = 1

        if device.name is None:
            return

        # print all devices
        #print(device)

        if shellySTR.lower() in device.name.lower(): #make case insentive
            # if ALLTERCO_MFID not in advertisement_data.manufacturer_data:
            #     continue
            mf = 'shelly'
            notFound = 0
        else:
            for b in bluettiSTR:
                if b.lower() in device.name.lower(): #make case insentive
                    mf = 'bluetti'
                    notFound = 0
                    continue

        # if shelly or bluetti strings aren't found in devices return
        if notFound == 1:
            return
        
        # Exclude devices with weak signal
        # if advertisement_data.rssi < -80:
        #     return
        print(device)
        
        #update rssi and timestamp if device is already known
        if device.address in addresses:
            # loop through and update rssi data
            for entry in saved_devices:
                if entry['address'] == device.address:
                    saved_devices.remove(entry)

                    try:
                        assignment = device.assignment
                    except:
                        assignment = ''

                    saved_devices.append({
                        "name": device.name,
                        "address": device.address,
                        "manufacturer":mf,
                        "rssi": advertisement_data.rssi,
                        "timestamp":datetime.now().isoformat(),
                        "location": location, #site
                        "assignment0": entry["assignment0"], #indiciates position in system (by channel if applicable)
                        "assignment1": entry["assignment1"] #indiciates position in system (by channel if applicable)
                    })
                    print(advertisement_data)
                    break
        else:
            #this might need to be done differently to deal with async...
            uResponse = input("Do you want to assign channels? (y/n): ")
            if uResponse.lower() == "y":
                print("Current assignment:")
            else:
                print("Continuing...")

            saved_devices.append({
                    "name": device.name,
                    "address": device.address,
                    "manufacturer":mf,
                    "rssi": advertisement_data.rssi,
                    "timestamp":datetime.now().isoformat(),
                    "location": location,
                    "assignment0":'', #this is manually entered
                    "assignment1":'' #this is manually entered
                })
            addresses.add(device.address)

    log_info(f"Scanning for BLE devices for {scan_duration} seconds...")

    async with BleakScanner(detection_callback=discovery_handler) as scanner:
        await asyncio.sleep(scan_duration)

    saved_devices.sort(key=lambda d: d["rssi"], reverse=True)
    return saved_devices

async def main():
    scan_duration = 5

    # Read data from a JSON file
    try:
        with open(deviceFile, "r") as json_file:
            savedDevices = json.load(json_file)
    except Exception as e:
        log_error(f"Error during reading devices.json file: {e}")
        savedDevices = []

    try:
        devices = await scan_devices(scan_duration, savedDevices)
    except Exception as e:
        log_error(f"Error during scanning: {e}")
        return

    if not devices:
        log_info("No devices found.")
    else:
        # Display devices
        log_info("Discovered devices:")
        print_devices(devices)
        save_devices(devices)

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


def print_devices(devices: List[Dict[str, str]]):
    """Prints the list of devices in a formatted table."""
    if not devices:
        print_error("No devices found.")
        return

    for index, device in enumerate(devices, start=1):
        print(f"Name: {device['name']}, Address: {device['address']}, RSSI: {device['rssi']}, Manufacturer: {device['manufacturer']}")

def save_devices(data):
    # Save data to a JSON file
    with open(deviceFile, "w") as json_file:
        json.dump(data, json_file, indent=4)

    print(f"JSON file saved successfully at {deviceFile}")

if __name__ == "__main__":

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_info("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        log_error(f"Unexpected error in main: {e}")
