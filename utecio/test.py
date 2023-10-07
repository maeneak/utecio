import asyncio
from ul1bt import UL1BT
from latch5nfc import Latch5NFC
from api import api_get_devices

EMAIL = ''
PASSWORD = ''
UL1_LOCK_PWD = ''
UL1_LOCK_UID = ''
L5_LOCK_PWD = ''
L5_LOCK_UID = ''
UL1_DEVICE_ADDRESS = ''
L5_DEVICE_ADDRESS = ''
L5_DEVICE_ADDRESS_2 = ''

async def main():
    await test_lib()
    return

async def test_lib():
    ul1 = UL1BT(uid=UL1_LOCK_UID, 
                       password=UL1_LOCK_PWD, 
                       mac_uuid=UL1_DEVICE_ADDRESS)
    
    l5 = Latch5NFC(uid=L5_LOCK_UID, 
                    password=L5_LOCK_PWD, 
                    mac_uuid=L5_DEVICE_ADDRESS, 
                    wurx_uuid=L5_DEVICE_ADDRESS_2)

    await l5.unlock()
    await ul1.unlock()
    return

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
    