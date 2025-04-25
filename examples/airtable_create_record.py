#source: https://python-kasa.readthedocs.io/en/latest/tutorial.html

import asyncio
from dotenv import load_dotenv
import os
from components.SmartPowerStation import Controls

load_dotenv()
key = os.getenv('AIRTABLE_PARTICIPANTS')


async def main():
    CONTROLS = Controls()

    now = await CONTROLS.send_get_request('localhost', 5000, '/api/data?file=now','json',timeout=2)


    print(now)

    data={"records": [{
      "fields": {
        "name": "home",
        "pv w": now["powerstation_inputWDC"],
        "battery":now["powerstation_percentage"],
        "flex wh": "150",
        "id": "123"}
    }]}

    url='https://api.airtable.com/v0/appZI2AenYNrfVqCL/live'
    r = await CONTROLS.send_post_request(url,data, key)
    print(r)

if __name__ == "__main__":
    asyncio.run(main())
