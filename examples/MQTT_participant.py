from components.MQTT import Participant
import asyncio
import signal

# this comes from config file
network = "BoroughHall"

async def main():
    participant = Participant(network)
    #await participant.start()
    mq = asyncio.create_task(participant.start())


    while True:
        print(participant.message)
        await asyncio.sleep(30)

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
