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
        "daily pv wh": "25",
        "flex wh": "150",
        "id": "123"}
    }]}

    url='https://api.airtable.com/v0/appZI2AenYNrfVqCL/live'
    await CONTROLS.send_get_request(url,data )


if __name__ == "__main__":
    asyncio.run(main())
