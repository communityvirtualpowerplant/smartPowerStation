import asyncio
import signal
import requests
import json
from typing import cast
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta, time
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
    CONTROLS.setEventTimes(CONTROLS.rules['event']['start'],CONTROLS.rules['event']['duration'])
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

        CONTROLS.setpoint = 100 #battery max
        CONTROLS.dischargeTime = 20

        # if no event upcoming or ongoing
        if (CONTROLS.rules['event']['upcoming'] == 0) and (CONTROLS.rules['event']['ongoing'] == 0):

            # position A
            if le < lf: # last full is most recent - discharging
                positionMarker = 'B'
                #get upcoming discharge time

                upcomingDT = datetime.combine(datetime.date(lf),time(CONTROLS.dischargeTime,00))

                # position B
                if datetime.now() >= upcomingDT: # if discharge time, go ahead with discharge
                    positionMarker = 'C'
                    # position C
                    toMode = 5
                    CONTROLS.rules['status']['mode']=toMode #set to dicharge
                else: #connect load to grid, don't charge or discharge battery
                    toMode = 2
                    CONTROLS.rules['status']['mode']=toMode #set to charge

                # if discharging, but below DoD, charge it
                # position D
                if (CONTROLS.rules['status']['mode'] in [2,5,6]) & (now['powerstation_percentage'] <= CONTROLS.rules['battery']['min']):
                    toMode = 1
                    #SPS.log_debug(f"Mode changed from {CONTROLS.rules['status']['mode']} to {toMode}.")
                    CONTROLS.rules['status']['lastEmpty']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    CONTROLS.rules['status']['mode']=toMode #set to charge
            # position E
            else: # last empty is most recent - charging

                # convert end of sun window into DT object
                sWE = CONTROLS.sunWindowStart + CONTROLS.sunWindowDuration
                upcomingSunWindowEnd = datetime.combine(datetime.date(le),time(sWE,00))

                # position G
                if datetime.now() >= upcomingSunWindowEnd:
                    sp = CONTROLS.pvSetpoint
                else:
                    # position H
                    sp = 100

                # position F
                if now['powerstation_percentage'] <= sp:
                    toMode=1 #charge battery
                else:
                    toMode=5 #discharge battery
                CONTROLS.rules['status']['mode']=toMode #set to charge

                # if charging, but at set point, switch modes
                # position A
                if (CONTROLS.rules['status']['mode'] in [2,5,6]) & (now['powerstation_percentage'] == sp):
                    positionMarker = 'A'
                    toMode = 1
                    #SPS.log_debug(f"Mode changed from {CONTROLS.rules['status']['mode']} to {toMode}.")
                    CONTROLS.rules['status']['lastFull']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    CONTROLS.rules['status']['mode']=toMode #set to charge
        elif CONTROLS.rules['event']['upcoming'] != 0:
            # prep for event
            # if time to event < charge time set mode to 1
            CONTROLS.rules['status']['mode']=1 #set to charge
        elif CONTROLS.rules['event']['ongoing'] != 0:
            # manage event
            # if event is ongoing set mode to 5
            CONTROLS.rules['status']['mode']=5 #set to discharge

        console.log(f'Position {positionMarker}')

        SPS.writeJSON(CONTROLS.rules,rulesFile)

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
