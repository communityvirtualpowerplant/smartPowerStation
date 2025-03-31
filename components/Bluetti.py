import argparse
import asyncio
import base64
from bleak import BleakError
#from io import TextIOWrapper
import json
import sys
import textwrap
import time
from typing import cast
from bluetti_mqtt.bluetooth import (
    check_addresses, scan_devices, BluetoothClient, ModbusError,
    ParseError, BadConnectionError
)
from bluetti_mqtt.core import (
    BluettiDevice, ReadHoldingRegisters, DeviceCommand
)

class Bluetti():
    def __init__(self, address: str, name: str):
        self.address = address
        self.name = name
        self.manufacturer = 'bluetti'
        self.data = {'total_battery_percent':0,'ac_output_power':0,'ac_input_power':0,'dc_output_power':0,'dc_input_power':0}
        self.charge = False
        self.BLUETTI_GATT_SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb" #not in use
    
    # def manageCharge(self, charge: self.charge, percent: self.data['total_battery_percent']):
    # # update charge state flag
    #     # if battery is <= 20 start charging until full
    #     if percent <= 20:
    #         chargeState = 1
    #     elif battery.percentage == 100:
    #         chargeState = 0

    async def log_command(self, client: BluetoothClient, device: BluettiDevice, command: DeviceCommand):
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

    async def run(self):

        devices = await check_addresses({self.mac})
        if len(devices) == 0:
            sys.exit('Could not find the given device to connect to')
        device = devices[0]

        print(f'Connecting to {device.address}')
        client = BluetoothClient(device.address)
        #asyncio.get_running_loop().create_task(client.run())
        client.run()
        
        # Wait for device connection
        while not client.is_ready:
            print('Waiting for connection...')
            await asyncio.sleep(1)
            continue
        print('Bluetti device is ready')

        # Poll device
        #while True:
        for command in device.logging_commands:
            commandResponse = await self.log_command(client, device, command)
            for k,v in commandResponse.items():
                #print(k + ": " + str(v))
                self.data[k]=v
            #await asyncio.sleep(freq)