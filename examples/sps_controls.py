# get most recent status

import asyncio
import signal
import requests
import json
from components.SmartPowerStation import SmartPowerStation, SPS_BLE
from typing import cast
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime, timedelta

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

def setMode(mode: int, SPS=SPS)-> Any:
    # reset bluetooth

    filteredEntries = SPS.devices

    try:
        devices = await scan_devices(scan_duration, filteredEntries)
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

        if savedDev['manufacturer'] == 'shelly':

            shDevice = ShellyDevice(savedDev["address"], savedDev["name"])
            try:
                await shDevice.setState(toState,0)
            except Exception as e:
                SPS.log_error(f"Error setting state")

    if mode == 1:

    elif mode == -1:

async def main(SPS) -> None:

    rules = SPS.getConfig(rulesFile)
    print(rules)

    while True:
        # get most recent data
        now = send_get_request(URL, PORT, ENDPOINT)

        #check if data is fresh
        if SPS.isRecent(now):
            SPS.log_debug('data is fresh')

        #ensure there isn't an ongoing or upcoming event
        if  (rules['event']['eventUpcoming'] == 0) and (rules['event']['eventOngoing'] == 0)
            if (now['powerstation_percentage'] == 100) and (rules['status']['direction'] == 1):
                rules['status']['lastFull']== datetime.now()
                rules['status']['direction']==-1 #set to discharge
            elif (now['powerstation_percentage'] <= 20) and (rules['status']['direction'] == -1):
                rules['status']['lastEmpty']== datetime.now()
                rules['status']['direction']==1 #set to charge

        setMode(rules['status']['direction'])

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


        print('************ SLEEPING **************')
        await asyncio.sleep(60)

if __name__ == "__main__":
    SPS = SmartPowerStation(configFile, devicesFile)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, SPS.handle_signal)
    signal.signal(signal.SIGTERM, SPS.handle_signal)

    try:
        asyncio.run(main(SPS))
    except KeyboardInterrupt:
        SPS.log_info("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        SPS.log_error(f"Unexpected error in main: {e}")





