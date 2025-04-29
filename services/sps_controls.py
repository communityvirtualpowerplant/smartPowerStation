import asyncio
import signal
import json
import sys
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta, time
from components.SmartPowerStation import SmartPowerStation, Controls
from components.MQTT import Participant
import threading
from dotenv import load_dotenv
import os
import random

# eventUpcoming = False
# eventOngoing = False

URL = 'localhost'
PORT = 5000
ENDPOINT = '/api/data?file=now'

configFile = '../config/config.json'
devicesFile = '../config/devices.json'
rulesFile = '../config/rules.json'
analysisDirectory = '../analysis/'

load_dotenv()
key = os.getenv('AIRTABLE_PARTICIPANTS')

async def controlLoop(SPS) -> None:
    network = SPS.config['network']
    participant = Participant(network)
    participant.start()
    #participant.client.connect_async(participant.broker, port=participant.port, keepalive=60)
    #participant.client.loop_start()

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

    print(f'Upcoming discharge time: {CONTROLS.upcomingDischargeDT}')

    # controls loop frequency
    freqMin = 1

    old_mqtt_data = {"message":""}

    while True:

        if old_mqtt_data['message'] != participant.message:
            print(f'new data! {participant.message}')
            old_mqtt_data['message'] = participant.message

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

        # # this block should be ahead of the LF test, so that it defaults to mode 1 if both are blank
        # try:
        #     le = datetime.strptime(CONTROLS.rules['status']['lastEmpty'], "%Y-%m-%d %H:%M:%S")
        # except:
        #     # if there isn't any saved data, set last empty to 10 years back
        #     le = datetime.now() - timedelta(days=(10*365))
        le = parse_datetime(CONTROLS.rules['status']['lastEmpty'])
        # try:
        #     lf = datetime.strptime(CONTROLS.rules['status']['lastFull'], "%Y-%m-%d %H:%M:%S")
        # except:
        #     # if there isn't any saved data, set last full to 10 years back
        #     lf = datetime.now() - timedelta(days=(10*365))
        lf = parse_datetime(CONTROLS.rules['status']['lastFull'])

        # if no event upcoming or ongoing
        if (CONTROLS.rules['event']['upcoming'] == 0) and (CONTROLS.rules['event']['ongoing'] == 0):

            # position A
            if le < lf: # last full is most recent - discharging
                positionMarker = 'B'
                #get upcoming discharge time

                if datetime.now() >= CONTROLS.upcomingDischargeDT: # if discharge time, go ahead with discharge
                    positionMarker = 'C'
                    toMode = 5
                else: #connect load to grid, don't charge or discharge battery
                    positionMarker = 'B'
                    toMode = 2

                    # # charge up if after sun window
                    # if CONTROLS.isAfterSun(datetime.now()): # if after sun window
                    #     sp = 95
                    # else:
                    sp = CONTROLS.rules['battery']['maxSetPoint']

                    # maintenance charge - optional
                    maintenanceBuffer = 5
                    if now['powerstation_percentage'] < (sp-maintenanceBuffer):
                        positionMarker = 'F'
                        toMode = 1
                    # switch back from maintenance charge with a little buffer
                    elif (positionMarker == 'F') and (now['powerstation_percentage'] > (sp)):
                        positionMarker = 'B'
                        toMode = 1
                    # create space for solar - update this to be dynamically based on prediction/ reality, not 90
                    elif (now['powerstation_percentage'] >90) & (not CONTROLS.isAfterSun(datetime.now())):
                        positionMarker = 'G'
                        toMode = 5

                # if discharging, but below min set point, charge it
                if (int(CONTROLS.rules['status']['mode']) in [0,2,5]) & (now['powerstation_percentage'] <= CONTROLS.rules['battery']['minSetPoint']):
                    positionMarker = 'D'
                    toMode = 1
                    #SPS.log_debug(f"Mode changed from {CONTROLS.rules['status']['mode']} to {toMode}.")
                    CONTROLS.rules['status']['lastEmpty']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    CONTROLS.setNextDischargeDT()
                    ### WRITE START TIME HERE! ###
            else: # last empty is most recent, start charging
                positionMarker = 'D'
                toMode = 1

                #if CONTROLS.isAfterChargeTime(datetime.now()):
                if True:
                    positionMarker = 'F'

                    if now['powerstation_percentage'] >= CONTROLS.rules['battery']['maxSetPoint']:
                        positionMarker = 'A'
                        toMode = 1
                        CONTROLS.rules['status']['lastFull']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # if not time to discharge, but below DoD, maintain DoD level
                elif now['powerstation_percentage'] <= 20:
                    positionMarker = 'H'
                else:
                    toMode = 2
                    positionMarker = 'E'

            # if the battery data is mia
            if now['powerstation_percentage']  == "":
                toMode = 1

        elif CONTROLS.rules['event']['ongoing'] != 0:
            # manage event
            # if event is ongoing set mode to 5
            toMode = 5 #set to discharge
            positionMarker = 'EC'

            # if depleted, turn on battery and connect back to grid
            if now['powerstation_percentage'] < 20:
                positionMarker = 'ED'
                if CONTROLS.rules['event']['curtailment'] == 0:
                    toMode = 2
                    positionMarker = 'EG'
                else:
                    toMode = 0

            # check if event is over and reset to 0
            if datetime.now() > (CONTROLS.eventDT + timedelta(hours=CONTROLS.eventDurationH)):
                CONTROLS.rules['event']['ongoing'] = 0
        elif CONTROLS.rules['event']['upcoming'] != 0:
            # prep for event
            toMode = 1 #charge with load to AC

            #if battery is full
            if now['powerstation_percentage'] == 100:
                positionMarker = 'EB'
            else:
                positionMarker = 'EF'

            #if sun window hasn't ended make sure there is room for solar
            if CONTROLS.isAfterSun(datetime.now()):
                # this should be changed based on time and solar intensity
                if now['powerstation_percentage'] > 90:
                    toMode = 5
                    positionMarker = 'EE'


            # check if event is no longer upcoming and reset to 0
            if datetime.now() > CONTROLS.eventDT:
                CONTROLS.rules['event']['upcoming'] = 0

        print(f'Position {positionMarker}')# remove flush arg for performance

        #is adding some logic to always charge if below 20% necessary?

        CONTROLS.rules['status']['mode']=toMode #set to charge
        SPS.writeJSON(CONTROLS.rules,rulesFile)

        # pass control data to device manager
        m=CONTROLS.rules['status']['mode']
        await CONTROLS.send_get_request(URL,5001,f'?mode={m}&position={positionMarker}','status_code')

        # update airtable with live data
        await updateAirtable(CONTROLS,SPS.config, now)

        print('************ SLEEPING **************')
        await asyncio.sleep(int(60*freqMin)+random.randint(0,30))

def parse_datetime(date_str: str, fallback_years: int = 10) -> datetime:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now() - timedelta(days=fallback_years * 365)

def printPos(p):
    showPosition = True
    if showPosition:
        print(f'Position: {p}')

async def updateAirtable(CONTROLS, config, now):
    name = config['location']
    myID = config['id']
    network = config['network']

    try:
        # get list of records filtered by name
        url = f'https://api.airtable.com/v0/appZI2AenYNrfVqCL/live?maxRecords=3&view=Grid%20view&filterByFormula=name%3D%22{name}%22'
        res = await CONTROLS.send_secure_get_request(url, key)
        print(res)

        # pull the id for the first record
        recordID = res['records'][0]['id']

        # patch record
        data={"records": [{
            "id": str(recordID),
            "fields": {
                "name": str(f"{name}"),
                "datetime":now['datetime'],
                "pv w": str(now["powerstation_inputWDC"]),
                "battery":str(now["powerstation_percentage"]),
                "flex wh": str(CONTROLS.getAvailableFlex(now["powerstation_percentage"])),
                "id": str(f"{myID}"),
                "network": str(f"{network}")}
            }]}

        try:
            url='https://api.airtable.com/v0/appZI2AenYNrfVqCL/live'

            patch_status = 0
            while patch_status < 3:
                # note that patch leaves unchanged data in place, while a post would delete old data in the record even if not being updated
                r = await CONTROLS.send_patch_request(url,data, key)
                if r != False:
                    break
                await asyncio.sleep(1+patch_status)
                patch_status += 1
            print(r)
        except Exception as e:
            print(f'Exception with patching Airtable: {e}')
    except Exception as e:
        print(f'Exception with getting Airtable records: {e}')

async def main(SPS: SmartPowerStation)->None:
    await controlLoop(SPS)

if __name__ == "__main__":
    SPS = SmartPowerStation(configFile)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, SPS.handle_signal)
    signal.signal(signal.SIGTERM, SPS.handle_signal)

    try:
        asyncio.run(main(SPS))
    except KeyboardInterrupt:
        print("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        print(f"Unexpected error in main: {e}")
