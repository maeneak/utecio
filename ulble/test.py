import asyncio
from ul1bt import UL1BT

def main():
    device = UL1BT(device_name="Front Door", password= "", username="", mac_address="4C:24:98:A2:D1:37")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(device.unlock())
    loop.close()

if __name__ == '__main__':
    main()