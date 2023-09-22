from __init__ import logger
from lock import UtecBleLock
from enums import BLECommandCode
from device import BleDeviceKeyECC, BleRequest

class Latch5NFC(UtecBleLock):
    def __init__(self, device_name: str, username: str, password: str, mac_uuid: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__(device_name, username, password, mac_uuid, max_retries, retry_delay, bleakdevice_callback)
        self.key = BleDeviceKeyECC()
        

