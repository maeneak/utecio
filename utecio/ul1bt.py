import asyncio

from __init__ import logger
from lock import UtecBleLock
from enums import BLECommandCode, ULDeviceModel
from device import BleRequest
from constants import UL1_BT, BLE_RETRY_DELAY_DEF, BLE_RETRY_MAX_DEF

class UL1BT(UtecBleLock):
    def __init__(self, uid: str, password: str, mac_uuid: str, device_name: str = UL1_BT, max_retries: float = BLE_RETRY_MAX_DEF, retry_delay: float = BLE_RETRY_DELAY_DEF):
        super().__init__(device_name=device_name, 
                         uid=uid, 
                         password=password, 
                         mac_uuid=mac_uuid, 
                         max_retries=max_retries, 
                         retry_delay=retry_delay)
        
        self.model = ULDeviceModel.UL1BT.value
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

    async def unlock(self):
        self.add_request(BleRequest(command=BLECommandCode.GET_LOCK_STATUS))
        self.add_request(BleRequest(command=BLECommandCode.GET_BATTERY))
        self.add_request(BleRequest(command=BLECommandCode.GET_SN, data=bytearray([16])))
        self.add_request(BleRequest(command=BLECommandCode.GET_MUTE))
        return await super().unlock()

    async def update(self):
        try:
            self.add_request(BleRequest(command=BLECommandCode.GET_LOCK_STATUS))
            self.add_request(BleRequest(command=BLECommandCode.GET_BATTERY))
            self.add_request(BleRequest(command=BLECommandCode.GET_SN, data=bytearray([16])))
            self.add_request(BleRequest(command=BLECommandCode.GET_MUTE))
            await self.process_queue()    

            logger.debug(f"({self.mac_uuid}) Update request completed.")
        except Exception as e:
            logger.error(f"({self.mac_uuid}) Error during update request: {e}")
            
        return await super().update()
