import asyncio
from .locks.ul1bt import UL1BT
from .locks.latch5nfc import Latch5NFC
from .client import UtecClient

EMAIL = '' # Your Utec app username/email
PASSWORD = '' # Your Utec App Password
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
    client = UtecClient(EMAIL, PASSWORD)
    await client.get_all_devices()
    l5: Latch5NFC = list(filter(lambda lock: lock.name == "Front Door", client.devices))[0]
    await l5.unlock()

    # l5 = Latch5NFC(uid=L5_LOCK_UID, 
    #                 password=L5_LOCK_PWD, 
    #                 mac_uuid=L5_DEVICE_ADDRESS, 
    #                 wurx_uuid=L5_DEVICE_ADDRESS_2)
    # l5.unlock()

    return

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
    