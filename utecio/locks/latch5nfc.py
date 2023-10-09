import asyncio

from utecio.__init__ import logger
from utecio.lock import UtecBleLock
from utecio.enums import BLECommandCode, ULDeviceModel
from utecio.device import BleRequest
from utecio.constants import Latch5_NFC, BLE_RETRY_DELAY_DEF, BLE_RETRY_MAX_DEF

class Latch5NFC(UtecBleLock):
    def __init__(self,  uid: str, password: str, mac_uuid: str, device_name: str = Latch5_NFC, wurx_uuid: str = None, max_retries: float = BLE_RETRY_MAX_DEF, retry_delay: float = BLE_RETRY_DELAY_DEF):
        super().__init__(uid=uid, 
                         password=password, 
                         mac_uuid=mac_uuid,
                         wurx_uuid=wurx_uuid,
                         device_name=device_name, 
                         max_retries=max_retries, 
                         retry_delay=retry_delay)
        
        self.model = ULDeviceModel.Latch5NFC.value
        self.capabilities.bluetooth = True
        self.capabilities.autolock = True
        self.capabilities.update_wifi = True
        self.capabilities.alerts = True
        self.capabilities.mutemode = True
        self.capabilities.rfid = True
        self.capabilities.rfid_twice = True
        self.capabilities.keypad = True
        self.capabilities.needRegristerPWD = True
        self.capabilities.haveSN = True
        self.capabilities.moreAdmin = True
        self.capabilities.timeLimit = True
        self.capabilities.passage = True
        self.capabilities.lockout = True
        self.capabilities.bt2640 = True
        self.capabilities.keepAlive = True
        self.capabilities.passageAutoLock = True
        self.capabilities.singlelatchboltmortic = True
        self.capabilities.smartphone_nfc = True
        self.capabilities.bt_close = True

    async def unlock(self):
        self.add_request(BleRequest(command=BLECommandCode.LOCK_STATUS))
        return await super().unlock()

    async def update(self):
        try:
            self.add_request(BleRequest(command=BLECommandCode.LOCK_STATUS))
            await self.process_queue()
            
            logger.debug(f"({self.mac_uuid}) Update request completed.")
        except Exception as e:
            logger.error(f"({self.mac_uuid}) Error during update request: {e}")
            
        return await super().update()
        

