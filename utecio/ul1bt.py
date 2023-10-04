import asyncio

from __init__ import logger
from lock import UtecBleLock
from enums import BLECommandCode, ServiceUUID, ULDeviceModel
from device import BleDeviceKeyMD5, BleRequest
from constants import UL1_BT, BLE_RETRY_DELAY_DEF, BLE_RETRY_MAX_DEF

class UL1BT(UtecBleLock):
    def __init__(self, uid: str, password: str, mac_uuid: str, wurx_uuid: str = None, device_name: str = UL1_BT, max_retries: float = BLE_RETRY_MAX_DEF, retry_delay: float = BLE_RETRY_DELAY_DEF, bleakdevice_callback: callable = None):
        super().__init__(device_name=device_name, 
                         uid=uid, 
                         password=password, 
                         mac_uuid=mac_uuid, 
                         wurx_uuid=wurx_uuid,
                         max_retries=max_retries, 
                         retry_delay=retry_delay, 
                         bleakdevice_callback=bleakdevice_callback)
        
        self.key = BleDeviceKeyMD5()
        self.model = ULDeviceModel.UL1BT
        self.capabilities.bluetooth = True
        self.capabilities.rfid = True
        self.capabilities.rfid_twice = True
        self.capabilities.fingprinter = True
        self.capabilities.autobolt = True
        self.capabilities.update_ota = True
        self.capabilities.update_oad = True
        self.capabilities.alerts = True
        self.capabilities.shakeopen = True
        self.capabilities.mutemode = True
        self.capabilities.passage = True
        self.capabilities.lockout = True
        self.capabilities.haveSN = True
        self.capabilities.direction = True
        self.capabilities.keepAlive = True
        self.capabilities.singlelatchboltmortic = True


    async def update(self):
        try:
            await self.start_notify(ServiceUUID.DATA.value, self._receive_write_response)
            await self.send_encrypted(BleRequest(BLECommandCode.GET_LOCK_STATUS))
            await self.send_encrypted(BleRequest(BLECommandCode.GET_BATTERY))
            await self.send_encrypted(BleRequest(BLECommandCode.GET_SN, None, None, bytearray([16])))
            await self.send_encrypted(BleRequest(BLECommandCode.GET_MUTE))
            await asyncio.sleep(2)
            await self.stop_notify(ServiceUUID.DATA.value)
            logger.debug(f"({self.client.address}) Update request completed.")
        except Exception as e:
            logger.error(f"({self.client.address}) Error during update request: {e}")
            
        return await super().update()
