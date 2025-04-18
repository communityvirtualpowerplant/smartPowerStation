import asyncio
import signal
import requests
import json
from typing import cast
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
import sys
from components.SmartPowerStation import SmartPowerStation, Controls


URL = 'localhost'
PORT = 5000
ENDPOINT = '/api/data?file=now'

configFile = '../config/config.json'
devicesFile = '../config/devices.json'
rulesFile = '../config/rules.json'


async def main(SPS) -> None:
    CONTROLS = Controls()

    rules = SPS.getConfig(rulesFile)
        #print(rules)

    await CONTROLS.estSunWindow()

   
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





