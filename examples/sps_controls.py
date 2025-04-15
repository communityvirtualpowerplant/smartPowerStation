# get most recent status

import asyncio
import signal
import requests
import json
from components.SmartPowerStation import SmartPowerStation

eventUpcoming = False
eventOngoing = False

URL = 'localhost'
PORT = 5000
ENDPOINT = '/api/data/file=now'

configFile = '../config/config.json'
devicesFile = '../config/devices.json'
rulesFile = '../config/rules.json'

def send_get_request(ip=URL, port=PORT,endpoint=ENDPOINT,timeout=1):
    """Send GET request to the IP."""
    try:
        response = requests.get(f"http://{ip}:{port}{endpoint}", timeout=timeout)
        return response
    except Exception as e:
        SPS.log_error(e)
        return None

def main(SPS):

    rules = SPS.getConfig(rulesFile)
    print(rules)

    while True:
        print(send_get_request(URL, PORT, ENDPOINT))

        print('************ SLEEPING **************')
        await asyncio.sleep(60)

if __name__ == "__main__":
    SPS = SmartPowerStation(configFile)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(main(SPS))
    except KeyboardInterrupt:
        SPS.log_info("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        SPS.log_error(f"Unexpected error in main: {e}")





