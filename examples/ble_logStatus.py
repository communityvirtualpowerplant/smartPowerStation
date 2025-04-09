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
from components.Bluetti import Bluetti
from bluetti_mqtt.bluetooth import (
    check_addresses, build_device, scan_devices, BluetoothClient, ModbusError,
    ParseError, BadConnectionError
)
from bluetti_mqtt.core import (
    BluettiDevice, ReadHoldingRegisters, DeviceCommand
)
from bleak import BleakClient, BleakError, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

shellySTR = 'Shelly'
bluettiSTR = ['AC180','AC2']

printInfo = True
printDebug = True
printError = True
#logging.basicConfig(level=logging.DEBUG)

dataDirectory = 'data/'
deviceFile = 'config/devices.json'
configFile = 'config/config.json'

#if an arg has been passed
if len(sys.argv) > 1:
    location = sys.argv[len(sys.argv)-1]
else:
    location = ''

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

def reset_bluetooth():
    try:
        subprocess.run(["sudo", "hciconfig", "hci0", "up"], check=True)
        subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], check=True)
    except subprocess.CalledProcessError as e:
        log_error(f"Bluetooth interface reset failed: {e}")

# ============================
# Main
# ============================        
async def main(location) -> None:
    reset_bluetooth()

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

    # tasks = [statusUpdate(e) for e in devices]
    # for task in tasks:
    #     await task

    # resultsDF = pd.DataFrame(data={
    #                     "datetime" : [datetime.datetime.now()],
    #                     "powerstation_percentage": [],
    #                     "powerstation_inputWAC": [],
    #                     "powerstation_inputWDC": [],
    #                     "powerstation_outputWAC": [],
    #                     "powerstation_outputWDC":[],
    #                     "powerstation_outputMode":[],
    #                     "powerstation_deviceType":[],
    #                     "relay1_power": [],
    #                     "relay1_current":[],
    #                     "relay1_voltage": [],
    #                     "relay1_status": [],
    #                     "relay1_device": [],
    #                     "relay2_power": [],
    #                     "relay2_current":[],
    #                     "relay2_voltage": [],
    #                     "relay2_status": [],
    #                     "relay2_device": []})

    tempResults = {
                    "datetime" : datetime.datetime.now(),
                    "powerstation_percentage": '',
                    "powerstation_inputWAC": '',
                    "powerstation_inputWDC": '',
                    "powerstation_outputWAC": '',
                    "powerstation_outputWDC":'',
                    "powerstation_outputMode":'',
                    "powerstation_deviceType":'',
                    "relay1_power": '',
                    "relay1_current":'',
                    "relay1_voltage": '',
                    "relay1_status": '',
                    "relay1_device": '',
                    "relay2_power": '',
                    "relay2_current":'',
                    "relay2_voltage": '',
                    "relay2_status": '',
                    "relay2_device": ''}

    #results = []
    for e in devices:
        result = await statusUpdate(e)
        if result:
            print(result)
            tempResults = packageData(e, result, tempResults)
            #results.append(result)
    
    fileName = dataDirectory + location + 'sps_'+str(datetime.date.today())+'.csv'

    await writeData(fileName, pd.DataFrame([tempResults]))

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
            result = await getStatusShelly(savedDev['device'])

            if result:
                print(f"RPC Method executed successfully. Result:")
                #print(json.dumps(result))
            else:
                print(f"RPC Method executed successfully. No data returned.")
        except Exception as e:
            log_error(f"Error getting Shelly status: {e}")

    elif savedDev['manufacturer'] == 'bluetti':
        savedDev['device'] = Bluetti(savedDev["address"],savedDev["name"])
        try:
            result = await getStatusBluetti(savedDev['device'])
        except Exception as e:
            log_error(f"Error getting Bluetti status: {e}")

        if result:
            print(f"Method executed successfully. Result:")
            #print(result)
            
        #   for k,v in commandResponse.items():
        #     print(k + ": " + str(v))
        #     myData[k]=v

        else:
            print(f"Method executed successfully. No data returned.")

    return result

# get status
async def getStatusShelly(device: ShellyDevice):

    #id_input = 0
    params = None
    rpc_method='Shelly.GetStatus'
    
    retries = 4
    for attempt in range(1, retries + 1):
        try:
            result = await device.call_rpc(rpc_method, params=params)
            if result:
                print(f"RPC Method '{rpc_method}' executed successfully. Result:")
                result = device.parse_response(result)
                return result
            else:
                print(f"RPC Method '{rpc_method}' executed successfully. No data returned.")
                return None

        except Exception as e:
            print(f"Unexpected error during attempt {attempt} command execution: {e}")
            if attempt <= retries:
                print(f"Retrying in {2 * attempt} second...")
                await asyncio.sleep(2 * attempt)
            else:
                print(f"All {retries} attempts failed.")
                raise

    #return

async def getStatusBluetti(myDevice: str):
    address = myDevice.address
    myData={
    }

    try:
        # devices = await check_addresses({address})
        # #if len(devices) == 0:
        #   #  sys.exit('Could not find the given device to connect to')
        # device = devices[0]
        device = build_device(myDevice.address, myDevice.name)

        print(f'Connecting to {device.address}')
        client = BluetoothClient(device.address)
        #await client.run()
        asyncio.get_running_loop().create_task(client.run())

        # Wait for device connection
        maxTries = 10
        t = 0
        while not client.is_ready:
            print('Waiting for connection...')
            await asyncio.sleep(1)
            t = t +1
            if t > 10:
                break
            continue

        # Poll device
        for command in device.logging_commands:
            commandResponse = await log_command(client, device, command)
            for k,v in commandResponse.items():
                myData[k]=v
        #print(myData)
        return myData

        #client.client.disconnect()

    except Exception as e:
        print(f"Unexpected error during command execution: {e}")

async def log_command(client: BluetoothClient, device: BluettiDevice, command: DeviceCommand):
    response_future = await client.perform(command)
    try:
        response = cast(bytes, await response_future)
        if isinstance(command, ReadHoldingRegisters):
            body = command.parse_response(response)
            parsed = device.parse(command.starting_address, body)
            return parsed #print(parsed.keys())
        #log_packet(log_file, response, command)
    except (BadConnectionError, BleakError, ModbusError, ParseError) as err:
        print(f'Got an error running command {command}: {err}')
        #log_invalid(log_file, err, command)

def packageData(d, r, t):
    try:
        if d[1]['manufacturer'].lower() == 'bluetti':
            print('bluetti!')
            t["powerstation_percentage"] = r['total_battery_percent']
            t["powerstation_inputWAC"] = r['ac_input_power']
            t["powerstation_inputWDC"] = r['dc_input_power']
            t["powerstation_outputWAC"] = r['ac_output_power']
            t["powerstation_outputWDC"] = r['dc_output_power']
            t["powerstation_outputMode"] = r['output_mode']
            t["powerstation_deviceType"] = r['device_type']
        elif 'Shelly'.lower() in d[1]['name'].lower():
            if '1PM'.lower() in d[1]['name'].lower():
                print('1pm!')
                if d[1]['assignment0'] == 1:
                    t['relay1_power'] = r[0]["apower"]
                    t['relay1_current'] =r[0]["current"]
                    t['relay1_voltage'] =r[0]["voltage"]
                    t['relay1_status'] =str(r[0]["output"])
                    t['relay1_device'] = d[1]['name']
                else:
                    t['relay2_power'] = r[0]["apower"]
                    t['relay2_current'] =r[0]["current"]
                    t['relay2_voltage'] =r[0]["voltage"]
                    t['relay2_status'] =str(r[0]["output"])
                    t['relay2_device'] = d[1]['name']
            elif '2PM'.lower() in d[1]['name'].lower():
                print('2pm!')
                t['relay1_power'] = r[0]["apower"]
                t['relay1_current'] =r[0]["current"]
                t['relay1_voltage'] =r[0]["voltage"]
                t['relay1_status'] =r[0]["output"]
                t['relay1_device'] = e[1]['name']
                t['relay2_power'] = r[1]["apower"]
                t['relay2_current'] =r[1]["current"]
                t['relay2_voltage'] =r[1]["voltage"]
                t['relay2_status'] =str(r[1]["output"])
                t['relay2_device'] = d[1]['name']
    except Exception as e:
        print(e)

    return t

async def writeData(fn, df):
    # create a new file daily to save data
    # or append if the file already exists
    try:
        with open(fn) as csvfile:
            savedDf = pd.read_csv(fn)
            savedDf = pd.concat([savedDf,df], ignore_index = True)
            #df = df.append(newDF, ignore_index = True)
            savedDf.to_csv(fn, sep=',',index=False)
    except Exception as e:
        print(e)
        df.to_csv(fn, sep=',',index=False)

    print("csv writing: " + str(datetime.datetime.now()))

if __name__ == "__main__":
    # Suppress FutureWarnings
    import warnings

    warnings.simplefilter("ignore", FutureWarning)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(main(location))
    except KeyboardInterrupt:
        log_info("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        log_error(f"Unexpected error in main: {e}")