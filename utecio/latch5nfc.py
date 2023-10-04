import asyncio

from __init__ import logger
from lock import UtecBleLock
from enums import BleResponseCode, BLECommandCode, ServiceUUID
from device import BleDeviceKeyECC, BleRequest, BleResponse
from constants import Latch5_NFC, BLE_RETRY_DELAY_DEF, BLE_RETRY_MAX_DEF

class Latch5NFC(UtecBleLock):
    def __init__(self,  uid: str, password: str, mac_uuid: str, device_name: str = Latch5_NFC, wurx_uuid: str = None, max_retries: float = BLE_RETRY_MAX_DEF, retry_delay: float = BLE_RETRY_DELAY_DEF, bleakdevice_callback: callable = None):
        super().__init__(uid=uid, 
                         password=password, 
                         mac_uuid=mac_uuid,
                         wurx_uuid=wurx_uuid,
                         device_name=device_name, 
                         max_retries=max_retries, 
                         retry_delay=retry_delay, 
                         bleakdevice_callback=bleakdevice_callback)
        
        self.key = BleDeviceKeyECC()
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

    async def update(self):
        try:
            await self.start_notify(ServiceUUID.DATA.value, self._receive_write_response)
            await self.send_encrypted(BleRequest(BLECommandCode.LOCK_STATUS))
            await asyncio.sleep(2)
            await self.stop_notify(ServiceUUID.DATA.value)
            logger.debug(f"({self.client.address}) Update request completed.")
        except Exception as e:
            logger.error(f"({self.client.address}) Error during update request: {e}")
            
        return await super().update()
        

