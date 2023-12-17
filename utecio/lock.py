import asyncio
import datetime

from .__init__ import logger
from .device import UtecBleDevice, BleRequest
from .enums import BLECommandCode
from .constants import BLE_RETRY_DELAY_DEF, BLE_RETRY_MAX_DEF

class UtecBleLock(UtecBleDevice):
    def __init__(self, uid: str, password: str, mac_uuid: str, device_name: str, wurx_uuid: str = None, max_retries: float = BLE_RETRY_MAX_DEF, retry_delay: float = BLE_RETRY_DELAY_DEF):
        super().__init__(uid=uid, 
                         password=password, 
                         mac_uuid=mac_uuid, 
                         wurx_uuid=wurx_uuid,
                         device_name=device_name, 
                         max_retries=max_retries, 
                         retry_delay=retry_delay)
        
        self.lock_status:int = -1
        self.bolt_status:int = -1
        self.battery:int = -1
        self.work_mode:int = -1
        self.mute:bool = False
        self.sn:str = None
        self.calendar:datetime = None

    async def unlock(self):
        try:
            self.add_request(BleRequest(command=BLECommandCode.UNLOCK, 
                                          uid=self.uid, 
                                          password=self.password,
                                          notify=False), 
                                          priority=True)
            await self.process_queue()
            logger.info(f"({self.mac_uuid}) Unlock command sent successfully.")

        except Exception as e:
            logger.error(f"({self.mac_uuid}) Error while sending unlock command: {e}")

    async def lock(self):
        try:
            self.add_request(BleRequest(command=BLECommandCode.BOLT_LOCK, 
                                          uid=self.uid, 
                                          password=self.password,
                                          notify=False),
                                          priority=True)
            await self.process_queue()
            logger.info(f"({self.mac_uuid}) Lock Bolt command sent successfully.")
            
        except Exception as e:
            logger.error(f"({self.mac_uuid}) Error while sending lock command: {e}")


