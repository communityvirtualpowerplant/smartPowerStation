import asyncio
import signal
import requests
import json
from typing import cast
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta, time
import sys
import os
from dotenv import load_dotenv
from components.SmartPowerStation import SmartPowerStation, Controls
#import csv


load_dotenv()
key = os.getenv('AIRTABLE_PARTICIPANTS')

URL = 'localhost'
PORT = 5000
ENDPOINT = '/api/data?file=now'

configFile = '../config/config.json'
devicesFile = '../config/devices.json'
rulesFile = '../config/rules.json'
analysisDirectory = '../analysis'

async def updateAirtableAnalysis(CONTROLS, fields):

    try:
        # get list of records filtered by name
        url = f'https://api.airtable.com/v0/appZI2AenYNrfVqCL/analysis?maxRecords=3&view=Grid%20view&filterByFormula=name%3D%22{name}%22'
        res = await CONTROLS.send_secure_get_request(url, key)
        print(res)

        # pull the id for the first record
        recordID = str(res['records'][0]['id'])

        data={
            "fields": fields
            # {
            #     "name": str(f"{name}"),
            #     "datetime":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            #     "event baseline WhAC": "",
            #     "avg PV WhDC":"",
            #     "max flex WhAC":"",
            #     "avg daily grid demand WhAC":"",
            #     "avg daily load demand WhAC":"",
            #     "avg event performance Wh":str(0),
            #     # "event value $":"",
            #     "event start time":str(CONTROLS.eventStartT),
            #     "network": str(f"{network}")}
            }

        try:
            url=f'https://api.airtable.com/v0/appZI2AenYNrfVqCL/analysis/{recordID}'

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

async def main(SPS) -> None:
    CONTROLS = Controls()

    CONTROLS.getRules(rulesFile)
    
    filteredDevices = SPS.getDevices(devicesFile)

    for d in filteredDevices:
        if d["role"] == "ps":
            CONTROLS.setBatCap(d["capacityWh"])
            print(f'Max flex: {CONTROLS.maxFlexibilityWh} WhAC')
            break

    files = await CONTROLS.getRecentData(30)

    rBaseline, rSolar, rWh = await asyncio.gather(
        CONTROLS.estBaseline(files=files),
        CONTROLS.analyzeSolar(files=files),
        CONTROLS.analyzeDailyWh(files=files)
    )

    print(rBaseline)

    print(rSolar)

    print(rWh)

    # # estimate the baseline Wh AC during event window
    # bl = await CONTROLS.estBaseline(10)
    # print(bl)

    # pv = await CONTROLS.analyzeSolar()
    # print(pv)

    # dWh = await CONTROLS.analyzeDailyWh()
    # print(dWh)

    # estimate sun window based on available recent data

    # past solar production DC - returns solar energy production DC for each day of the past month + %
    # past solar production AC 

    # estimate solar charging efficiency

    # estimate AC charging efficiency

    # estimate AC charging roundtrip efficiency

    # battery time remaining

    fields = {
                "name": str(SPS.config['location'].lower()),
                "datetime":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "event baseline WhAC": str(rBaseline),
                "avg PV WhDC":"",
                "max flex WhAC":"",
                "avg daily grid demand WhAC":"",
                "avg daily load demand WhAC":"",
                "avg event performance Wh":str(0),
                # "event value $":"",
                "event start time":str(CONTROLS.eventStartT),
                "network": str(SPS.config['network'])
            }

    #(battery cap Wh * Dod * invEff)/AC W
    await updateAirtableAnalysis(CONTROLS,fields)


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
