import asyncio

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from .ble.lock import UtecBleLock
from .api import UtecClient, logger as liblogger

EMAIL = "your@email.com" # Your Utec app username/email
PASSWORD = "your_password" # Your Utec App Password

bleak_scanner = BleakScanner()

async def async_bledevice_callback(address:str) -> BLEDevice:
    # we need to provide a valid BLEDevice for the mac address when asked, or return None
    # in Home Assistant we should call 'bluetooth.async_ble_device_from_address' to return the BLEDevice.
    if bleak_scanner:
        device = await bleak_scanner.find_device_by_address(address)
        return device
    return None

async def unlock_lock(lockname: str):
    # enable debug output
    liblogger.setLevel(10)
    # connect to webapi and retrieve locks
    client = UtecClient(EMAIL, PASSWORD)
    ble_devices = await client.get_ble_devices()

    # select a lock based on a known property (e.g. name)
    l5: UtecBleLock = list(filter(lambda lock: lock.name == lockname, ble_devices))[0]
    # register a callback to provide bleak BLEDevice objects
    l5.async_bledevice_callback = async_bledevice_callback
    try:
        # start the scanner for the BLEDevice callback
        await bleak_scanner.start()
        # unlock the lock and retrieve a status update
        await l5.async_unlock(update=True)
    except Exception as e:
        print("Unlock failed.", e)
    else:
        print("Unlock successfull.")
    finally:
        # cleanup
        await bleak_scanner.stop()

asyncio.run(unlock_lock("Office Door"))
    