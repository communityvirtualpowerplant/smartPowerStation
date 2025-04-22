import asyncio
import signal
import requests
import json
from typing import cast
from typing import Any, Dict, Optional, List
from datetime import datetime
import sys
from components.SmartPowerStation import SmartPowerStation, Controls
#import csv

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
                #get upcoming discharge time

                upcomingDT = datetime.combine(datetime.date(lf),time(CONTROLS.dischargeTime,00))

                if datetime.now() >= upcomingDT: # if discharge time, go ahead with discharge
                    # position C
                    pPosition = 'C'
                    toMode = 5
                else: #connect load to grid, don't charge or discharge battery
                    # position B
                    pPosition = 'B'
                    toMode = 2
                # if discharging, but below DoD, charge it
                if (CONTROLS.rules['status']['mode'] in [2,5,6]) & (now['powerstation_percentage'] <= CONTROLS.rules['battery']['min']):
                    # position D
                    pPosition = 'D'
                    toMode = 1
                    #SPS.log_debug(f"Mode changed from {CONTROLS.rules['status']['mode']} to {toMode}.")
                    CONTROLS.rules['status']['lastEmpty']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else: # last empty is most recent - charging
                # position E
                pPosition = 'E'
                # convert end of sun window into DT object
                sWE = CONTROLS.sunWindowStart + CONTROLS.sunWindowDuration
                upcomingSunWindowEnd = datetime.combine(datetime.date(le),time(sWE,00))

                if datetime.now() < upcomingSunWindowEnd:
                    # position F
                    pPosition = 'F'
                    sp = CONTROLS.pvSetpoint
                else:
                    # position G
                    pPosition = 'G'
                    sp = 100

                if now['powerstation_percentage'] <= sp:
                    toMode=1 #charge battery
                else:
                    toMode=5 #discharge battery

                # if charging, but at set point, switch modes
                # position A
                if (CONTROLS.rules['status']['mode'] in [2,5,6]) & (now['powerstation_percentage'] == sp):
                    toMode = 1
                    #SPS.log_debug(f"Mode changed from {CONTROLS.rules['status']['mode']} to {toMode}.")
                    CONTROLS.rules['status']['lastFull']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
        elif CONTROLS.rules['event']['ongoing'] != 0:
            # manage event
            # if event is ongoing set mode to 5
            toMode = 5 #set to discharge
            # check if event is over and reset to 0
            eventDT = datetime.strptime(CONTROLS.rules['event']['ongoing'], "%Y-%m-%d %H:%M:%S")
            if datetime.now() > eventDT:
                CONTROLS.rules['event']['ongoing'] = 0
        elif CONTROLS.rules['event']['upcoming'] != 0:
            # prep for event
            toMode = 1 #set to charge
            # check if event is no longer upcoming and reset to 0
            upcomingDT = datetime.strptime(CONTROLS.rules['event']['upcoming'], "%Y-%m-%d %H:%M:%S")
            if datetime.now() > upcomingDT:
                CONTROLS.rules['event']['upcoming'] = 0


        CONTROLS.rules['status']['mode']=toMode #set to charge
        SPS.writeJSON(CONTROLS.rules,rulesFile)
        printPos(pPosition)

        m=CONTROLS.rules['status']['mode']
        await CONTROLS.send_get_request(URL,5001,f'?mode={m}','status_code')
        print('************ SLEEPING **************')
        await asyncio.sleep(60*freqMin)

def printPos(p):
    showPosition = True
    if showPosition:
        print(f'Position: {p}')

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
