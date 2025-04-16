# get most recent status

import asyncio
import signal
import requests
import json
from components.SmartPowerStation import SmartPowerStation
from typing import cast
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
from components.Shelly import ShellyDevice

eventUpcoming = False
eventOngoing = False

URL = 'localhost'
PORT = 5000
ENDPOINT = '/api/data?file=now'

configFile = '../config/config.json'
devicesFile = '../config/devices.json'
rulesFile = '../config/rules.json'

def send_get_request(ip=URL, port=PORT,endpoint=ENDPOINT,timeout=1) -> Dict:
    """Send GET request to the IP."""
    try:
        response = requests.get(f"http://{ip}:{port}{endpoint}", timeout=timeout)
        return response.json()
    except Exception as e:
        SPS.log_error(e)
        return None

async def setMode(mode: int, SPS: SmartPowerStation)-> Any:
    # these assignments should be listed in the rules file
    if mode == 1:
        assign = {1:1,2:1,3:0} #with an autotransfer, if pos 1 is on pos 3 is automatically off
    elif mode == 2:
        assign = {1:1,2:0,3:0} #with an autotransfer, if pos 1 is on pos 3 is automatically off
    elif mode == 3:
        assign = {1:0,2:1,3:1}
    elif mode == 4:
        assign = {1:0,2:1,3:0}
    elif mode == 5:
        assign = {1:0,2:0,3:1}
    elif mode == 6:
        assign = {1:0,2:0,3:0}

    SPS.reset_bluetooth()

    # get saved devicecs, filtered by location
    savedDevices = SPS.getDevices(devicesFile)

    # filter devices by role
    filteredDevices = []
    for entry in savedDevices:
        if entry['role'] == 'relay':
            filteredDevices.append(entry)

    if len(filteredDevices) >= 1:
        try:
            # scan devices to get BLE object
            devices = await SPS.scan_devices(filteredDevices)
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

def writeMode(data):
    SPS.writeJSON(data,rulesFile)

async def main(SPS) -> None:

    rules = SPS.getConfig(rulesFile)
    print(rules)

    while True:
        # get most recent data
        now = send_get_request(URL, PORT, ENDPOINT)
        SPS.log_debug(now['datetime'])

        #check if data is fresh
        #if SPS.isRecent(now['datetime']):
            #SPS.log_debug('data is fresh')

        #ensure there isn't an ongoing or upcoming event
        lastFull = rules['status']['lastFull']
        if (lastFull != "") and (isinstance(lastFull, str)):
            lastFull = datetime.strptime(lastFull, "%Y-%m-%d %H:%M:%S") #check if the ts is a string and convert
        lastEmpty = rules['status']['lastEmpty']
        if (lastEmpty != "") and (isinstance(lastEmpty, str)):
            lastEmpty = datetime.strptime(lastEmpty, "%Y-%m-%d %H:%M:%S") #check if the ts is a string and convert

        if  (rules['event']['upcoming'] == 0) and (rules['event']['ongoing'] == 0):
            if (now['powerstation_percentage'] == 100) and (rules['status']['mode'] == 1):
                toMode = 5
                SPS.log_debug(f"Mode changed from {rules['status']['mode']} to {toMode}.")
                lastFull== datetime.now()
                rules['status']['mode']=toMode #set to discharge
            elif (now['powerstation_percentage'] <= rules['battery']['min']) and (rules['status']['mode'] == 5):
                toMode = 1
                SPS.log_debug(f"Mode changed from {rules['status']['mode']} to {toMode}.")
                lastEmpty== datetime.now()
                rules['status']['mode']=toMode #set to charge
            else:
                SPS.log_debug(f"Mode {rules['status']['mode']} not changed.")

        writeMode(rules)

        await setMode(rules['status']['mode'],SPS)
        print('************ SLEEPING **************')
        await asyncio.sleep(60*5)

if __name__ == "__main__":
    SPS = SmartPowerStation(configFile)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, SPS.handle_signal)
    signal.signal(signal.SIGTERM, SPS.handle_signal)

    try:
        asyncio.run(main(SPS))
    except KeyboardInterrupt:
        SPS.log_info("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        SPS.log_error(f"Unexpected error in main: {e}")





