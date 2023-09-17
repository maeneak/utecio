import asyncio
from ul1bt import UL1BT
from api import api_get_devices


EMAIL = "" # Your U-tec username/email
PASSWORD = "" # Your U-tec password

async def main():
    devices = await api_get_devices(EMAIL, PASSWORD)
    await devices[0].unlock()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()