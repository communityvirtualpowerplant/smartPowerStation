# get most recent status

import asyncio
import signal
import requests
import json
from typing import cast
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
import sys
from components.SmartPowerStation import SmartPowerStation, Controls

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
        return response #.json()
    except Exception as e:
        SPS.log_error(e)
        return None

async def setMode(mode: int)-> Any:
    SPS.log_info(send_get_request(URL,5001,f'?mode={mode}'))

def writeMode(data):
    SPS.writeJSON(data,rulesFile)

async def main(SPS) -> None:

    rules = SPS.getConfig(rulesFile)
    print(rules)

    while True:
        # get most recent data
        now = send_get_request(URL, PORT, ENDPOINT).json()
        SPS.log_debug(now['datetime'])

        #check if data is fresh
        #if SPS.isRecent(now['datetime']):
            #SPS.log_debug('data is fresh')

        if  (rules['event']['upcoming'] == 0) and (rules['event']['ongoing'] == 0):
            # add code for PV priority - battery is depleted by the start of the sun window to ensure maximum PV utilization

            # daily cycle - battery is depleted and charged up to once a day
            if rules['battery']['cycle']=='daily':
                pass
            # constant cycle - battery is depleted and charged continuously. time of cycle depends on load
            elif rules['battery']['cycle']=='constant':
                if (now['powerstation_percentage'] == 100) and (rules['status']['mode'] == 1):
                    toMode = 5
                    SPS.log_debug(f"Mode changed from {rules['status']['mode']} to {toMode}.")
                    rules['status']['lastFull']== datetime.now()
                    rules['status']['mode']=toMode #set to discharge
                elif (now['powerstation_percentage'] <= rules['battery']['min']) and (rules['status']['mode'] == 5):
                    toMode = 1
                    SPS.log_debug(f"Mode changed from {rules['status']['mode']} to {toMode}.")
                    rules['status']['lastEmpty']== datetime.now()
                    rules['status']['mode']=toMode #set to charge
                else:
                    SPS.log_debug(f"Mode {rules['status']['mode']} not changed.")
        elif(rules['event']['upcoming'] != 0):
            # prep for event
            pass
        elif(rules['event']['ongoing'] != 0):
            # manage event
            pass

        writeMode(rules)

        await setMode(rules['status']['mode'])
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





