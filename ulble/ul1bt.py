from lock import BleLock
from enums import BLECommand
from ble import BLERequest, BLEKeyMD5

class UL1BT(BleLock):
    def __init__(self, device_name: str, username: str, password: str, mac_uuid: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__(device_name, username, password, mac_uuid, max_retries, retry_delay, bleakdevice_callback)
        self.key = BLEKeyMD5()
        
    async def lock_bolt(self):
        await self.send_encrypted(BLERequest(BLECommand.BOLT_LOCK, self.uid, self.password))
        
    # async def unlock_bolt(self):
    #     await self.send_encrypted(BLERequest(BLECommand.SET_LOCK_STATUS, None, None, bytearray([0,0,0])))
