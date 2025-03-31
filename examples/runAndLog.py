# this script just runs the hardware, manages charging and discharging, and logs data.

import asyncio
from deviceClasses.Shelly import ShellyDevice
#from componentClasses.powerstation import BluettiAC180 as AC180


fileName = 'data/devices.json'

async def main()
    chargeState = 0 #initialize state as not charging

    devices = getDevices(fileName)

    while True:
        # retrieve data


        # update charge state flag
        # if battery is <= 20 start charging until full
        if chargeState == 0 and battery.percentage <= 20:
            chargeState = 1
        elif battery.percentage == 100:
            chargeState = 0

        # check charge state

        # toggle state if needed 


        break
        
# ============================
# Utilities
# ============================

# graceful shutdown when terminated
def handle_signal(signal_num: int, frame: Any) -> None:
    log_info(f"Received signal {signal_num}, shutting down gracefully...")
    sys.exit(0)

# read json and get device list
def getDevices(fileName):

    # Read data from a JSON file
    try:
        with open(fileName, "r") as json_file:
            savedDevices = json.load(json_file)
    except Exception as e:
        log_error(f"Error during reading devices.json file: {e}")
        savedDevices = []

    return savedDevices

if __name__ == "__main__":
    # Suppress FutureWarnings
    import warnings

    warnings.simplefilter("ignore", FutureWarning)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_info("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        log_error(f"Unexpected error in main: {e}")