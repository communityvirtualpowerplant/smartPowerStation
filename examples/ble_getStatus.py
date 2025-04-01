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

fileName = 'data/devices.json'

#if an arg has been passed
if len(sys.argv) > 1:
    location = sys.argv[len(sys.argv)-1]
else:
    location = ''

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
        with open(fileName, "r") as json_file:
            saveDevices = json.load(json_file)
    except Exception as e:
        log_error(f"Error during reading devices.json file: {e}")
        savedDevices = []

    filteredEntries = []
    for entry in saveDevices:
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

    tasks = [statusUpdate(e) for e in devices]
    #await asyncio.gather(*tasks)     # causes an error on RPi, so using the below sequential method instead    
    for task in tasks:
        await task

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

    async with BleakScanner(adapter="hci0", detection_callback=discovery_handler) as scanner:
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
                print(json.dumps(result))

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
            print(result)

        #   for k,v in commandResponse.items():
        #     print(k + ": " + str(v))
        #     myData[k]=v

        else:
            print(f"Method executed successfully. No data returned.")
    #await asyncio.sleep(20)


    # result = await execute_toggle(device)

    # if result:
    #     print(f"RPC Method '{rpc_method}' executed successfully. Result:")
    #     print_with_jq(result.get("result", {}))
    # else:
    #     print(f"RPC Method executed successfully. No data returned.")

# get status
async def getStatusShelly(device: ShellyDevice):

    #id_input = 0
    params = None
    rpc_method='Shelly.GetStatus'
    
    retries = 3
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
            if attempt < retries:
                print(f"Retrying in 1 second...")
                await asyncio.sleep(1)
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