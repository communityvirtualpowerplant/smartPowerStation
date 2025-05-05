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
import logging

# logging.basicConfig(
#     format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
#     level=logging.INFO
# )

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

    # get analysis data from airtable - if this is
    analysisURL = 'https://communityvirtualpowerplant.com/api/gateway.php?table=analysis'
    try:
        analysisResponse = await CONTROLS.send_secure_get_request(analysisURL)
        print(analysisResponse)

        locationAnalysis = {}
        for r in analysisResponse['records']:
            if not r['fields'] == {}:
                if r['fields']['name'].lower()==SPS.config['location'].lower():
                    locationAnalysis = r['fields']
                    break
        p = CONTROLS.whToPerc(float(locationAnalysis['max PV WhDC']))
        CONTROLS.rules['battery']['maxSetPoint'] = int(100 - (p*1.05))# give it a 5% buffer
    except Exception as e:
        print(f'Error: {e}')

    print(f'Upcoming discharge time: {CONTROLS.upcomingDischargeDT}')

    # controls loop frequency
    freqMin = 1

    mqtt_data = {"data":{}}

    dod = 20

    while True:

        # re-get analysis if date isn't today (could also rerun if data is old...)

        if mqtt_data['data'] != participant.data:
            print(f'new data! {participant.data}')
            mqtt_data['data'] = participant.data

            # shoud be expanded to include event type too!
            CONTROLS.rules['event']['eventDate'] = mqtt_data['data']['start_time']

        if CONTROLS.rules['event']['eventDate'] != "":
            edDT = datetime.strptime(CONTROLS.rules['event']['eventDate'], "%Y-%m-%d %H:%M:%S")
            if datetime.now() < edDT:
                CONTROLS.rules['event']['ongoing'] = 0
                CONTROLS.rules['event']['upcoming'] = 1
                print('EVENT UPCOMING!')
            elif datetime.now() < edDT + timedelta(hours=4):
                CONTROLS.rules['event']['ongoing'] = 1
                CONTROLS.rules['event']['upcoming'] = 0
                print('EVENT ONGOING!')

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

        # le should be ahead of the LF test, so that it defaults to mode 1 if both are blank
        le = parse_datetime(CONTROLS.rules['status']['lastEmpty'])
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
                    maintenanceBuffer = 15
                    if now['powerstation_percentage'] < max(sp-maintenanceBuffer,dod): #make sure it doesn't drop below DoD
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
                elif now['powerstation_percentage'] <= dod:
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
            if now['powerstation_percentage'] <= dod:
                positionMarker = 'ED'
                if CONTROLS.rules['event']['curtailment'] == 0: #if not curtailing
                    toMode = 2
                    positionMarker = 'EE'
                else:
                    toMode = 0
                    positionMarker = 'EH'

            # should there be an emergency backstop for the battery even in an event?
            if now['powerstation_percentage'] < 10:
                pass

            # check if event is over and reset to 0
            if datetime.now() > (CONTROLS.eventDT + timedelta(hours=CONTROLS.eventDurationH)):
                CONTROLS.rules['event']['ongoing'] = 0
        elif CONTROLS.rules['event']['upcoming'] != 0:
            # prep for event

            #check is event is after sun window
            if edDT:
                if CONTROLS.isAfterSun(edDT):
                    bMax = 100
                else:
                    bMax = 95 # set this dynamically

            #if battery is full
            if now['powerstation_percentage'] == bMax:
                toMode = 2 #charge with load to AC
                positionMarker = 'EB'
            elif now['powerstation_percentage'] < bMax:
                toMode = 1 #charge with load to AC
                positionMarker = 'EF'
            elif now['powerstation_percentage'] > bMax:
                toMode = 5 #charge with load to AC
                positionMarker = 'EG'

            # check if event is no longer upcoming and reset to 0
            # this variable is redundant
            if datetime.now() > CONTROLS.eventDT:
                CONTROLS.rules['event']['upcoming'] = 0

        print(f'Position {positionMarker}')# remove flush arg for performance

        #is adding some logic to always charge if below 20% necessary?

        CONTROLS.rules['status']['mode']=toMode #set to charge
        #CONTROLS.rules['event']['eventDate'] = CONTROLS.rules['event']['eventDate'].strftime("%Y-%m-%d %H:%M:%S")
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
    name = config['location'].lower()
    myID = config['id']
    network = config['network']

    try:
        # get list of records filtered by name
        url = f'https://api.airtable.com/v0/appZI2AenYNrfVqCL/live?maxRecords=3&view=Grid%20view&filterByFormula=name%3D%22{name}%22'
        res = await CONTROLS.send_secure_get_request(url, key)
        #print(res)

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
                "sensor 1 wac":str(now["relay1_power"]),
                "sensor 2 wac":str(now["relay2_power"]),
                "sensor 3 wac":str(now["relay3_power"]),
                "sensor 4 wdc":str(now["powerstation_inputWDC"]),
                "grid vac":str(now["relay1_voltage"]),
                "mode":str(now["mode"]),
                "network":network,
                "position":str(now["position"]),
                "event upcoming":str(CONTROLS.rules['event']['upcoming']),
                "event ongoing":str(CONTROLS.rules['event']['ongoing']),
                "event date":str(CONTROLS.rules['event']['eventDate'])
                }
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
            #print(r)
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
