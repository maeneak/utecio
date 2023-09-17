from lock import BleLock
from enums import BLECommand
from client import BLERequest, BLEKeyMD5

class UL1BT(BleLock):
    def __init__(self, device_name: str, username: str, password: str, mac_address: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__(device_name, username, password, mac_address, max_retries, retry_delay, bleakdevice_callback)
        self.key = BLEKeyMD5()
        
    async def bolt_lock(self):
        await self.send_encrypted(BLERequest(BLECommand.BOLT_LOCK))
