import asyncio
import signal
import requests
import json
from typing import cast
from typing import Any, Dict, Optional, List
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

# loop frequency
freqMin = 1

#async def setMode(mode: int)-> Any:
    #SPS.log_info(await CONTROLS.send_get_request(URL,5001,f'?mode={mode}','status_code'))

# def writeMode(data):
#     SPS.writeJSON(data,rulesFile)

async def main(SPS) -> None:
    CONTROLS = Controls()

    rules = SPS.getConfig(rulesFile)
        #print(rules)

    filteredDevices = SPS.getDevices(deviceFile)

    for d in filteredDevices:
        if d["role"] == "ps"
            CONTROLS.maxFlexibilityWh = d["capacityWh"]*.8
            print(CONTROLS.maxFlexibilityWh)
            break

    while True:

        # get most recent data
        now = await CONTROLS.send_get_request(URL, PORT, ENDPOINT,'json')
        SPS.log_debug(now['datetime'])

        CONTROLS.availableFlexibilityWh = CONTROLS.maxFlexibilityWh * now['powerstation_percentage']*.01
        print(f'available flex: {CONTROLS.availableFlexibilityWh}')

        #check if data is fresh
        #if SPS.isRecent(now['datetime']):
            #SPS.log_debug('data is fresh')

        if (rules['event']['upcoming'] == 0) and (rules['event']['ongoing'] == 0):
            # add code for PV priority - battery is depleted by the start of the sun window to ensure maximum PV utilization

            # daily cycle - battery is depleted and charged up to once a day
            if rules['battery']['cycle']=='daily':
                pass
            # constant cycle - battery is depleted and charged continuously. time of cycle depends on load
            elif rules['battery']['cycle']=='constant':
                # if it hits 100% and was in a charging state, switch to a draw down state
                if (now['powerstation_percentage'] == 100) and (rules['status']['mode'] in [1,3,4]):
                    toMode = 5
                    SPS.log_debug(f"Mode changed from {rules['status']['mode']} to {toMode}.")
                    rules['status']['lastFull']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    rules['status']['mode']=toMode #set to discharge
                # if it hits 20% and was in a drawdown state, charge it up
                elif (now['powerstation_percentage'] <= rules['battery']['min']) and (rules['status']['mode'] == 5):
                    toMode = 1
                    SPS.log_debug(f"Mode changed from {rules['status']['mode']} to {toMode}.")
                    rules['status']['lastEmpty']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    rules['status']['mode']=toMode #set to charge
                else:
                    SPS.log_debug(f"Mode {rules['status']['mode']} not changed.")
        elif rules['event']['upcoming'] != 0:
            # prep for event
            pass
        elif rules['event']['ongoing'] != 0:
            # manage event
            pass

        #writeMode(rules)
        SPS.writeJSON(rules,rulesFile)

        #await setMode(rules['status']['mode'])
        m=rules['status']['mode']
        await CONTROLS.send_get_request(URL,5001,f'?mode={m}','status_code')
        print('************ SLEEPING **************')
        await asyncio.sleep(60*freqMin)

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





