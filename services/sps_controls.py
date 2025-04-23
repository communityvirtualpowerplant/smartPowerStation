import asyncio
import signal
import requests
import json
import sys
from typing import cast
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta, time
from components.SmartPowerStation import SmartPowerStation, Controls
#import csv
#from components.MQTT import Participant

eventUpcoming = False
eventOngoing = False

URL = 'localhost'
PORT = 5000
ENDPOINT = '/api/data?file=now'

configFile = '../config/config.json'
devicesFile = '../config/devices.json'
rulesFile = '../config/rules.json'
analysisDirectory = '../analysis/'

# loop frequency
freqMin = 1

async def main(SPS) -> None:
    CONTROLS = Controls()


    CONTROLS.getRules(rulesFile)
    #CONTROLS.setEventTimes(CONTROLS.rules['event']['start'],CONTROLS.rules['event']['duration'])
    filteredDevices = SPS.getDevices(devicesFile)

    for d in filteredDevices:
        if d["role"] == "ps":
            CONTROLS.setBatCap(d["capacityWh"])
            print(f'Max flex: {CONTROLS.maxFlexibilityWh} WhAC')
            break

    # if the analysis file for today hasn't been created yet, do it
    #print(await CONTROLS.estBaseline(7))

    while True:

        # get most recent data
        now = await CONTROLS.send_get_request(URL, PORT, ENDPOINT,'json',timeout=2)
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

        # this block should be ahead of the LF test, so that it defaults to mode 1 if both are blank
        try:
            le = datetime.strptime(CONTROLS.rules['status']['lastEmpty'], "%Y-%m-%d %H:%M:%S")
        except:
            # if there isn't any saved data, set last empty to 10 years back
            le = datetime.now() - timedelta(days=(10*365))

        try:
            lf = datetime.strptime(CONTROLS.rules['status']['lastFull'], "%Y-%m-%d %H:%M:%S")
        except:
            # if there isn't any saved data, set last full to 10 years back
            lf = datetime.now() - timedelta(days=(10*365))


        # if no event upcoming or ongoing
        if (CONTROLS.rules['event']['upcoming'] == 0) and (CONTROLS.rules['event']['ongoing'] == 0):

            # position A
            if le < lf: # last full is most recent - discharging
                positionMarker = 'B'
                #get upcoming discharge time

                upcomingDT = datetime.combine(datetime.date(lf),CONTROLS.dischargeT)
                print(f'Upcoming discharge time: {upcomingDT}')

                if datetime.now() >= upcomingDT: # if discharge time, go ahead with discharge
                    positionMarker = 'C'
                    # position C
                    toMode = 5
                else: #connect load to grid, don't charge or discharge battery
                    # position B
                    positionMarker = 'B'
                    toMode = 2
                # if discharging, but below min set point, charge it
                if (CONTROLS.rules['status']['mode'] in [2,5,6]) & (now['powerstation_percentage'] <= CONTROLS.rules['battery']['minSetPoint']):
                    # position D
                    positionMarker = 'E'
                    toMode = 1
                    #SPS.log_debug(f"Mode changed from {CONTROLS.rules['status']['mode']} to {toMode}.")
                    CONTROLS.rules['status']['lastEmpty']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else: # last empty is most recent, start charging- Position D
                # position E
                positionMarker = 'E'
                # convert end of sun window into time object
                sWE = time(hour=int(CONTROLS.sunWindowStart + CONTROLS.sunWindowDuration))

                #if its after sun window 
                upcomingSunWindowEnd = datetime.combine(datetime.date(le),sWE)
                print(f'Sun window: {upcomingSunWindowEnd}')

                if datetime.now() > upcomingSunWindowEnd:
                    # position G
                    positionMarker = 'G'
                    sp = 100
                else:
                    # this kicks in at midnight
                    # position F
                    positionMarker = 'E'
                    sp = CONTROLS.pvSetPoint

                if now['powerstation_percentage'] < sp:
                    toMode=1 #charge battery
                else:
                    toMode=5 #discharge battery

                # if charging, but at set point, switch modes
                # position A
                # 2,5,6 are discharge modes # CONTROLS.rules['status']['mode'] in [2,5,6]) &
                if (sp == 100) & (now['powerstation_percentage'] == sp):
                    positionMarker = 'A'
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

        print(f'Position {positionMarker}',flush=True)# remove flush arg for performance

        #is adding some logic to always charge if below 20% necessary?

        CONTROLS.rules['status']['mode']=toMode #set to charge
        SPS.writeJSON(CONTROLS.rules,rulesFile)

        m=CONTROLS.rules['status']['mode']
        await CONTROLS.send_get_request(URL,5001,f'?mode={m}&position={positionMarker}','status_code')
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
