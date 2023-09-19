import asyncio
from ul1bt import UL1BT
from api import api_get_devices


EMAIL = "" # Your U-tec username/email
PASSWORD = "" # Your U-tec password
LOCK_PWD = "" # Lock UID (int)
LOCK_UID = "" # Lock Password (int)
DEVICE_ADDRESS = "" # Lock Mac Address (UUID on MacOS)

async def main():
    #await test_api()
    await test_lib()
    return

async def test_lib():
    device = UL1BT("Front", LOCK_UID, LOCK_PWD, DEVICE_ADDRESS)
    await device.unlock()
    await device.update()
    return

async def test_api():
    devices = await api_get_devices(EMAIL, PASSWORD)
    await devices[0].unlock()
    await devices[0].update()
    return

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
