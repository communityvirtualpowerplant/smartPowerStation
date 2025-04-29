#import argparse
import asyncio
#import base64
import signal
from bleak import BleakError
#from io import TextIOWrapper
#import json
import sys
#import textwrap
#import time
from typing import cast
from bluetti_mqtt.bluetooth import (
    check_addresses, build_device, scan_devices, BluetoothClient, ModbusError,
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
        #self.charge = False
        self.BLUETTI_GATT_SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb" #not in use
        self.maxTries = 20

    async def log_command(self, client: BluetoothClient, device: BluettiDevice, command: DeviceCommand):
        try:
            response_future = await client.perform(command)
            response = cast(bytes, await response_future)
            if isinstance(command, ReadHoldingRegisters):
                body = command.parse_response(response)
                parsed = device.parse(command.starting_address, body)
                return parsed #print(parsed.keys())
        except (BadConnectionError, BleakError, ModbusError, ParseError) as err:
            print(f'Got an error running command {command}: {err}')

    # async def run(self):

    #     try:
    #         devices = await check_addresses({self.mac})
    #         if not devices:
    #             sys.exit('Could not find the given device to connect to')
    #         device = devices[0]

    #         print(f'Connecting to {device.address}')
    #         client = BluetoothClient(device.address)
    #         #asyncio.get_running_loop().create_task(client.run())
    #         async with asyncio.TaskGroup() as tg:
    #             tg.create_task(client.run())

    #             # # Wait for device connection
    #             # while not client.is_ready:
    #             #     print('Waiting for connection...')
    #             #     await asyncio.sleep(1)
    #             #     continue


    #             for _ in range(self.maxTries):
    #                 if client.is_ready:
    #                     break
    #                 print('Waiting for connection...')
    #                 await asyncio.sleep(1)
    #             else:
    #                 print('Connection timeout')
    #                 return

    #             print('Bluetti device is ready')

    #             # Poll device
    #             #while True:
    #             for command in device.logging_commands:
    #                 commandResponse = await self.log_command(client, device, command)
    #                 if commandResponse:
    #                     for k,v in commandResponse.items():
    #                         #print(k + ": " + str(v))
    #                         self.data[k]=v
    #                 #await asyncio.sleep(freq)
    #     finally:
    #         try:
    #             if client.client:# and client.client.is_connected:
    #                 await client.client.disconnect()
    #                 print("Disconnected BLE client")
    #         except Exception as e:
    #             print(f"Error during BLE disconnect: {e}")

    async def getStatus(self):
        myData={
        }

        try:
            device = build_device(self.address, self.name)

            print(f'Connecting to {self.address}')
            client = BluetoothClient(self.address)
            #await client.run()

            # stop_event = asyncio.Event()

            # loop = asyncio.get_running_loop()
            # #bTask = loop.create_task(client.run())

        #try:
            # async with asyncio.TaskGroup() as tg:
            #     # Start the client
            #     t = tg.create_task(client.run())

                # Wait for a shutdown signal
                #await stop_event.wait()

                # # Wait for device connection
                # t = 0
                # while not client.is_ready:
                #     print('Waiting for connection...')
                #     await asyncio.sleep(1)
                #     t = t +1
                #     if t > 10:
                #         break
                #     continue

                # for _ in range(self.maxTries):
                #     if client.is_ready:
                #         break
                #     print('Waiting for connection...')
                #     await asyncio.sleep(1)
                # else:
                #     print('Connection timeout')
                #     # return myData
                # Wait for client.is_ready with timeout

                # try:
                #     await asyncio.wait_for(self._wait_for_ready(client), timeout=10)
                # except asyncio.TimeoutError:
                #     print("Timeout: Device did not become ready.")
                #     run_task.cancel()  # Cancel client.run()
                #     await asyncio.gather(run_task, return_exceptions=True)  # Clean cancellation
                #     return myData
            t = asyncio.get_running_loop().create_task(client.run())

            try:
                async with asyncio.timeout(15):
                    await self._wait_for_ready(client)
            except TimeoutError:
                print("The task group timed out")
                t.cancel()
                return myData

            # Poll device
            for command in device.logging_commands:
                commandResponse = await self.log_command(client, device, command)
                if commandResponse:
                    for k,v in commandResponse.items():
                        myData[k]=v
            #print(myData)
        except Exception as e:
            print(f"Unexpected error during command execution: {e}")
        finally:
            try:
                if client.client: # and client.client.is_connected:
                    await client.client.disconnect()
                    print("Disconnected BLE client")
            except Exception as e:
                print(f"Error during BLE disconnect: {e}")

        return myData


    async def _wait_for_ready(self, client: BluetoothClient):
        """Helper: wait until the client is ready."""
        while not client.is_ready:
            print('Waiting for connection...')
            await asyncio.sleep(1)
