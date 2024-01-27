import asyncio

from bleak import BleakScanner

from .ble import UtecBleLock
from .api import UtecClient

EMAIL = "your@email.com" # Your Utec app username/email
PASSWORD = "your_password" # Your Utec App Password

async def update_lock(lockname: str):
    # connect to webapi and retrieve locks
    client = UtecClient(EMAIL, PASSWORD)
    ble_devices = await client.get_ble_devices()

    # select a lock based on a known property (e.g. name)
    l5: UtecBleLock = list(filter(lambda lock: lock.name == lockname, ble_devices))[0]

    # scan for the device (will use a short timmeout because lock is likely asleep)
    async with BleakScanner() as scanner:
        device = await scanner.find_device_by_address(l5.mac_uuid, 3)

        # if not discoverable check if it has a wakeup receiver and wake it up and/else try again with long timeout
        if not device:
            if l5.wurx_uuid:
                device = await scanner.find_device_by_address(l5.wurx_uuid, 20)
                if not device:
                    raise ConnectionAbortedError("Wakeup controller not available")
                await l5.async_wakeup_device(device)
            device = await scanner.find_device_by_address(l5.mac_uuid)

    # if device discoverable request a status update else abort 
    if device:
        await l5.async_update_status(device)
    else:
        raise ConnectionAbortedError("Device not available")

    return

asyncio.run(update_lock("Office Door"))
    