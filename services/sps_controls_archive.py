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

async def main(SPS) -> None:
    CONTROLS = Controls()


    CONTROLS.getRules(rulesFile)
    CONTROLS.setEventTimes(rules['event']['start'],rules['event']['duration'])
    filteredDevices = SPS.getDevices(devicesFile)

    for d in filteredDevices:
        if d["role"] == "ps":
            CONTROLS.setBatCap(d["capacityWh"])
            print(f'Max flex: {CONTROLS.maxFlexibilityWh} WhAC')
            break

    print(await CONTROLS.estBaseline(7))

    while True:

        # get most recent data
        now = await CONTROLS.send_get_request(URL, PORT, ENDPOINT,'json')
        SPS.log_debug(now['datetime'])
        try:
            CONTROLS.availableFlexibilityWh = CONTROLS.getAvailableFlex(now['powerstation_percentage'])
        except Exception as e:
            print(e)
            CONTROLS.availableFlexibilityWh = 0

        print(f'Available flex: {CONTROLS.availableFlexibilityWh} WhAC')

        #check if data is fresh
        #if SPS.isRecent(now['datetime']):
            #SPS.log_debug('data is fresh')

        lf = datetime.strptime(CONTROLS.rules['status']['lastFull'], "%Y-%m-%d %H:%M:%S")
        le = datetime.strptime(CONTROLS.rules['status']['lastEmpty'], "%Y-%m-%d %H:%M:%S")

        # if no event upcoming or ongoing
        if (CONTROLS.rules['event']['upcoming'] == 0) and (CONTROLS.rules['event']['ongoing'] == 0):
            #CONTROLS.normalLoop(now)
            # charge time specification
            CONTROLS.setpoint = 100 #battery max

            # daily cycle - battery is depleted and charged up to once a day
            if CONTROLS.rules['battery']['cycle']=='daily':
                # if last empty was today
                if (datetime.now() - le) <= timedelta(days=1):
                    if (now['powerstation_percentage'] == CONTROLS.setpoint) and (CONTROLS.rules['status']['mode'] in [1,3,4]):
                        toMode = 5
                        SPS.log_debug(f"Mode changed from {CONTROLS.rules['status']['mode']} to {toMode}.")
                        CONTROLS.rules['status']['lastFull']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        CONTROLS.rules['status']['mode']=toMode #set to discharge
                        # deplete!
                        toMode = 5
                elif (now['powerstation_percentage'] <= CONTROLS.rules['battery']['min']) and (CONTROLS.rules['status']['mode'] in [2,5,6]):
                    toMode = 1
                    SPS.log_debug(f"Mode changed from {CONTROLS.rules['status']['mode']} to {toMode}.")
                    CONTROLS.rules['status']['lastEmpty']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    CONTROLS.rules['status']['mode']=toMode #set to charge
                else:
                    SPS.log_debug(f"Mode {CONTROLS.rules['status']['mode']} not changed.")
            # PV priority - battery is depleted by the start of the sun window to ensure maximum PV utilization
            # the goal is to be at about 50% when the sun window begins (exact amount changes based on past PV production)
            elif CONTROLS.rules['battery']['cycle']=='pv':
                if CONTROLS.rules['status']['lastEmpty']
                if datetime.now().hour < 13: #before 1pm, dont charge from grid greater than 50% to ensure opportunity for PV
                    CONTROLS.setpoint = 50
                #if after PV window, charge it up
                elif datetime.now().hour > 13: #after 1pm, charge from grid
                    CONTROLS.setpoint = 100

                #estimate discharge time

            # constant cycle - battery is depleted and charged continuously. time of cycle depends on load
            elif CONTROLS.rules['battery']['cycle']=='constant':
                # if it hits 100% and was in a charging state, switch to a draw down state
                if (now['powerstation_percentage'] == setpoint) and (CONTROLS.rules['status']['mode'] in [1,3,4]):
                    toMode = 5
                    SPS.log_debug(f"Mode changed from {CONTROLS.rules['status']['mode']} to {toMode}.")
                    CONTROLS.rules['status']['lastFull']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    CONTROLS.rules['status']['mode']=toMode #set to discharge
                # if it hits 20% and was in a drawdown state, charge it up
                elif (now['powerstation_percentage'] <= CONTROLS.rules['battery']['min']) and (CONTROLS.rules['status']['mode'] == 5):
                    toMode = 1
                    SPS.log_debug(f"Mode changed from {CONTROLS.rules['status']['mode']} to {toMode}.")
                    CONTROLS.rules['status']['lastEmpty']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    CONTROLS.rules['status']['mode']=toMode #set to charge
                else:
                    SPS.log_debug(f"Mode {rules['status']['mode']} not changed.")
        elif CONTROLS.rules['event']['upcoming'] != 0:
            # prep for event
            # if time to event < charge time set mode to 1
            CONTROLS.rules['status']['mode']=1 #set to charge
        elif CONTROLS.rules['event']['ongoing'] != 0:
            # manage event
            # if event is ongoing set mode to 5
            CONTROLS.rules['status']['mode']=5 #set to charge

        #writeMode(rules)
        SPS.writeJSON(CONTROLS.rules,rulesFile)

        #await setMode(rules['status']['mode'])
        m=CONTROLS.rules['status']['mode']
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
