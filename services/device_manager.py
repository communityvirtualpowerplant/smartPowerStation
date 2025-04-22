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
from datetime import datetime, date
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
from components.SmartPowerStation import SmartPowerStation
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

toMode = {'mode':1}
lock = threading.Lock()

@app.route("/")
def getCommand():
    with lock:
        toMode['mode'] = int(request.args.get("mode"))
    return "Success", 200

shellySTR = 'Shelly'
bluettiSTR = ['AC180','AC2']

printInfo = True
printDebug = True
printError = True
#logging.basicConfig(level=logging.DEBUG)

dataDirectory = '../data/'
deviceFile = '../config/devices.json'
configFile = '../config/config.json'

#changed based on hardware
bleAdapter = "hci0"

# ============================
# Utilities
# ============================
def handle_signal(signal_num: int, frame: Any) -> None:
    """Handles termination signals for graceful shutdown."""
    print(f"Received signal {signal_num}, shutting down gracefully...")
    sys.exit(0)

# ============================
# Main
# ============================        
async def bleLoop(SPS: SmartPowerStation) -> None:
    #global toMode

    while True:
        SPS.reset_bluetooth()

        location = SPS.location
        SPS.log_info(location)

        scan_duration = 5
        
        filteredEntries = SPS.getDevices(deviceFile)

        try:
            devices = await scan_devices(scan_duration, filteredEntries)
        except Exception as e:
            SPS.log_error(f"Error during scanning: {e}")
            return

        if not devices:
            SPS.log_error("No devices found. Exiting")
            sys.exit(0)

        # tasks = [statusUpdate(e) for e in devices]
        # for task in tasks:
        #     await task

        await setMode(devices, SPS)

        tempResults = {
                        "datetime" : datetime.now(),
                        "powerstation_percentage": "",
                        "powerstation_inputWAC": "",
                        "powerstation_inputWDC": "",
                        "powerstation_outputWAC": "",
                        "powerstation_outputWDC":"",
                        "powerstation_outputMode":"",
                        "powerstation_deviceType":"",
                        "relay1_power": "",
                        "relay1_current":"",
                        "relay1_voltage": "",
                        "relay1_status": "",
                        "relay1_device": "",
                        "relay2_power": "",
                        "relay2_current":"",
                        "relay2_voltage": "",
                        "relay2_status": "",
                        "relay2_device": "",
                        "relay3_power": "",
                        "relay3_current":"",
                        "relay3_voltage": "",
                        "relay3_status": "",
                        "relay3_device": "",
                        "mode":int(toMode['mode'])} 

        #results = []
        for d in devices:
            print(d)
            result = await statusUpdate(d)
            if result:
                print(result)
                tempResults = SPS.packageData(d, result, tempResults)
                #results.append(result)
        
        fileName = dataDirectory + str(location) + '_' +str(date.today())+'.csv'

        await writeData(fileName, pd.DataFrame([tempResults]))

        # there is definitely a better way to do this - something where it forces a wakeup if the mode is changed...
        await setMode(devices, SPS)

        print('************ SLEEPING **************')
        await asyncio.sleep(120)

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

    SPS.log_info(f"Scanning for BLE devices for {scan_duration} seconds...")

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

            # if result:
            #     print(f"RPC Method executed successfully. Result:")
            #     #print(json.dumps(result))
            # else:
            #     print(f"RPC Method executed successfully. No data returned.")
        except Exception as e:
            SPS.log_error(f"Error getting Shelly status: {e}")

    elif savedDev['manufacturer'] == 'bluetti':
        savedDev['device'] = Bluetti(savedDev["address"],savedDev["name"])
        try:
            result = await savedDev['device'].getStatus() #getStatusBluetti(savedDev['device'])
        except Exception as e:
            SPS.log_error(f"Error getting Bluetti status: {e}")

        if result:
            SPS.log_debug(f"Method executed successfully. Result:")
            #print(result)
            
        #   for k,v in commandResponse.items():
        #     print(k + ": " + str(v))
        #     myData[k]=v

        else:
            SPS.log_debug(f"Method executed successfully. No data returned.")

    return result

async def writeData(fn, df):
    # create a new file daily to save data
    # or append if the file already exists

    SPS.log_debug(df)

    try:
        with open(fn) as csvfile:
            savedDf = pd.read_csv(fn)
            savedDf = pd.concat([savedDf,df], ignore_index = True)
            #df = df.append(newDF, ignore_index = True)
            savedDf.to_csv(fn, sep=',',index=False)
    except Exception as err:
        SPS.log_error(err)
        df.to_csv(fn, sep=',',index=False)

    SPS.log_debug("csv writing: " + str(datetime.now()))

async def setMode(devices: list[list[Dict]], SPS: SmartPowerStation)-> Any:
    # move into setMode function
    async with asyncio.Lock():
        mode = toMode['mode']
        if mode != 0:
            toMode['mode'] = 0
        else:
            return

    # these assignments should be listed in the rules file
    if mode == 0:
        assign = {1:0,2:0,3:0}
    elif mode == 1:
        assign = {1:1,2:1,3:0} #with an autotransfer, if pos 1 is on pos 3 is automatically off
    elif mode == 2:
        assign = {1:1,2:0,3:0} #with an autotransfer, if pos 1 is on pos 3 is automatically off
    elif mode == 3:
        assign = {1:0,2:1,3:1}
    elif mode == 4:
        assign = {1:0,2:1,3:0}
    elif mode == 5:
        assign = {1:0,2:0,3:1}
    
    
    SPS.log_info(f'Setting mode to {mode}')

    for d in devices:
        SPS.log_debug(d)
        bleDev = d[0]
        savedDev = d[1]

        # filter devices by role
        if savedDev['role'] == 'relay':
            # filter by shelly device
            if savedDev['manufacturer'] == 'shelly':

                shDevice = ShellyDevice(savedDev["address"], savedDev["name"])

                async def trySetState(toState:bool,ch: int):
                    try:
                        # set relay state
                        await shDevice.setState(toState,ch)
                    except Exception as e:
                        SPS.log_error(f"Error setting state")
 
                if savedDev['relay1'] in [1,2,3]:
                    SPS.log_debug(f"trying to set relay 1 on device {savedDev['name']}")
                    await trySetState(assign[savedDev['relay1']],0)
                if savedDev['relay2'] in [1,2,3]:
                    SPS.log_debug(f"trying to set relay 2 on device {savedDev['name']}")
                    await trySetState(assign[savedDev['relay2']],1)

def main(SPS: SmartPowerStation,loop)-> None:
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bleLoop(SPS))

if __name__ == "__main__":
    # Suppress FutureWarnings
    import warnings

    warnings.simplefilter("ignore", FutureWarning)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


    SPS = SmartPowerStation(configFile)

    try:
        #asyncio.run(main(SPS)) # old async code - now running async in seperate thread
        # Create a new event loop for the async function
        loop = asyncio.new_event_loop()
        t = threading.Thread(target=main, args=(SPS,loop))
        t.start()

        app.run(host="0.0.0.0", port=5001, debug=False)
    except KeyboardInterrupt:
        SPS.log_info("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        SPS.log_error(f"Unexpected error in main: {e}")
