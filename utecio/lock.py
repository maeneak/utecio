import asyncio
import datetime

from __init__ import logger
from device import UtecBleDevice, BleResponse, BleRequest
from enums import BleResponseCode, BLECommandCode, ServiceUUID
from constants import BATTERY_LEVEL, LOCK_MODE, LOCK_STATUS
from util import date_from_4bytes, bytes_to_ascii

class UtecBleLock(UtecBleDevice):
    def __init__(self, uid: str, password: str, mac_uuid: str, device_name: str, wurx_uuid: str = None, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__(uid=uid, 
                         password=password, 
                         mac_uuid=mac_uuid, 
                         wurx_uuid=wurx_uuid,
                         device_name=device_name, 
                         max_retries=max_retries, 
                         retry_delay=retry_delay, 
                         bleakdevice_callback=bleakdevice_callback)
        self.response:BleResponse = BleResponse(bytearray(0))
        self.lock_status:int = -1
        self.bolt_status:int = -1
        self.battery:int = -1
        self.work_mode:int = -1
        self.mute:bool = False
        self.sn:str = None
        self.calendar:datetime = None

    async def unlock(self):
        try:
            await self.send_encrypted(BleRequest(BLECommandCode.UNLOCK, self.uid, self.password))
            logger.info(f"({self.client.address}) Unlock command sent successfully.")
        except Exception as e:
            logger.error(f"({self.client.address}) Error while sending unlock command: {e}")

    async def lock(self):
        await self.send_encrypted(BleRequest(BLECommandCode.BOLT_LOCK, self.uid, self.password))

    async def _process_response(self, response: BleResponse):
        try:
            logger.debug(f"({self.client.address}) Response {response.command.name}: {response.package.hex()}")
            if response.command == BleResponseCode.GET_LOCK_STATUS:
                self.lock_status = int(response.data[1])
                self.bolt_status = int(response.data[2])
                logger.debug(f"({self.client.address}) lock:{self.lock_status}, {LOCK_MODE[self.lock_status]} |  bolt:{self.bolt_status}, {LOCK_STATUS[self.bolt_status]}")
            elif response.command == BleResponseCode.GET_BATTERY:
                self.battery = int(response.data[1])
                logger.debug(f"({self.client.address}) power level:{self.battery}, {BATTERY_LEVEL[self.battery]}")
            elif response.command == BleResponseCode.GET_SN:
                self.sn = response.data.decode('ISO8859-1')
                logger.debug(f"({self.client.address}) serial:{self.sn}")
            elif response.command == BleResponseCode.GET_MUTE:
                self.mute = bool(response.data[1])
                logger.debug(f"({self.client.address}) sound:{self.mute}")
            elif response.command == BleResponseCode.LOCK_STATUS:
                self.lock_status = int(response.data[1])
                self.bolt_status = int(response.data[2])
                self.battery = int(response.data[3])
                self.work_mode = bool(response.data[4])
                self.mute = bool(response.data[5])
                #self.calendar = date_from_4bytes(response.data[6:10])
                #self.sn = bytes_to_ascii(response.data[10:26])
                logger.debug(f"({self.client.address}) lock:{self.lock_status} |  bolt:{self.bolt_status} | power level:{self.battery} | sound:{self.mute}")

        except Exception as e:
            logger.error(f"({self.client.address}) Error updating lock data ({response.command.name}): {e}")

    async def _receive_write_response(self, sender: int, data: bytearray):
        try:
            self.response.append(data, self.secret_key.aes_key)
            if self.response.completed:
                if self.response.is_valid:
                    await self._process_response(self.response)
                self.response.reset()
        except Exception as e:
            logger.error(f"({self.client.address}) Error receiving write response: {e}")

