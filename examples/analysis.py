import asyncio
import signal
import requests
import json
from typing import cast
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta, time
import sys
from components.SmartPowerStation import SmartPowerStation, Controls
#import csv


URL = 'localhost'
PORT = 5000
ENDPOINT = '/api/data?file=now'

configFile = '../config/config.json'
devicesFile = '../config/devices.json'
rulesFile = '../config/rules.json'

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

    # flexibility at event start - returns a list of estimated Wh for each day in the past month

    # estimates event window baselines - returns a list of estimated Wh baselines for each day in the past month
    print(await CONTROLS.estBaseline(7))

    # estimate sun window based on available recent data

    # past solar production DC - returns solar energy production DC for each day of the past month + %
    # past solar production AC 

    # estimate solar charging efficiency

    # estimate AC charging efficiency

    # estimate AC charging roundtrip efficiency

    # battery time remaining

    #(battery cap Wh * Dod * invEff)/AC W


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
