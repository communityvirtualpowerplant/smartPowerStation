# power cycles battery AC input
# presses button
# confirms status

import asyncio
from bleak import BleakClient

# Replace with your SwitchBot's MAC address
DEVICE_MAC_ADDRESS = "D2:C7:C5:C6:61:66"

# Press command in hex (Turn SwitchBot Bot ON/OFF or simulate press)
COMMAND_PRESS = bytearray([0x57, 0x01, 0x00])

# UUID for the SwitchBot Bot's write characteristic
SERVICE_UUID = '0000fd3d-0000-1000-8000-00805f9b34fb' #"cba20d00-224d-11e6-9fb8-0002a5d5c51b" #this UUID works too
CHAR_UUID = "cba20002-224d-11e6-9fb8-0002a5d5c51b"

async def main():
    response = False

    while not response:
    # get PS status

    # if status response works, return
        return

    # elif status response fails

        # check if pos 2 is on

            # if off, turn it on

            # if on, turn it off


        # press button


    # sleep for 20 seconds
    async.sleep(20)


async def press_switchbot():
    async with BleakClient(DEVICE_MAC_ADDRESS) as client:
        if await client.is_connected():
            print("Connected to SwitchBot")
            await client.write_gatt_char(CHAR_UUID, COMMAND_PRESS, response=True)
            print("Press command sent.")
        else:
            print("Failed to connect.")



if __name__ == "__main__":

    SPS = SmartPowerStation(configFile)

    try:
        asyncio.run(main(SPS))
    except KeyboardInterrupt:
        SPS.log_info("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        SPS.log_error(f"Unexpected error in main: {e}")
