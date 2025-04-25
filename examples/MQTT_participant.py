from components.MQTT import Participant, mqtt_message, lock
import asyncio
import signal
from datetime import datetime

# this comes from config file
network = "BoroughHall"

async def test():
    while True:
        async with lock:
            print(mqtt_message)
        print(f'test {datetime.now()}')
        await asyncio.sleep(30)

async def main():
    participant = Participant(network)
    await participant.start()
    #mq = asyncio.create_task(participant.start())

    t = asyncio.create_task(test())

    while True:

        print(f'main loop {datetime.now()}')
        #print(participant.message)
        await asyncio.sleep(15)

if __name__ == '__main__':
    # Setup signal handlers for graceful shutdown
    # signal.signal(signal.SIGINT, SPS.handle_signal)
    # signal.signal(signal.SIGTERM, SPS.handle_signal)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Script interrupted by user via KeyboardInterrupt.")
    except Exception as e:
        print(f"Unexpected error in main: {e}")
