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


    print('')

    # get list of records
    name = 'home'
    url = f'https://api.airtable.com/v0/appZI2AenYNrfVqCL/live?maxRecords=3&view=Grid%20view&filterByFormula=name%3D%22{name}%22'
    res = await CONTROLS.send_secure_get_request(url, key)
    print(res)
    # filter record of interest

    # pull the id for the first item
    #for r in res:
    recordID = res['records'][0]['id']


    # patch record
    data={"records": [{
        "id": str(recordID),
        "fields": {
            "name": "home",
            "datetime":now['datetime'],
            "pv w": str(now["powerstation_inputWDC"]),
            "battery":str(now["powerstation_percentage"]),
            "flex wh": str(150),
            "id": str(123)}
        }]}

    url='https://api.airtable.com/v0/appZI2AenYNrfVqCL/live'

    patch_status = 0
    while patch_status < 3:
        r = await CONTROLS.send_patch_request(url,data, key)
        if r != False:
            break
        await asyncio.sleep(1+patch_status)
        patch_status += 1

    print('out of the loop!')
    print(r)


if __name__ == "__main__":
    asyncio.run(main())
