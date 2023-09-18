import asyncio
from ble import BleClient, BleResponse, BLERequest, BLEKey

from enums import RequestResponse, BLECommand, ServiceUUID
from constants import BATTERY_LEVEL, LOCK_MODE, LOCK_STATUS

class BleLock(BleClient):
    def __init__(self, device_name: str, uid: str, password: str, mac_address: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__(mac_address, max_retries, retry_delay, bleakdevice_callback)
        self._device_name = device_name
        self.uid = uid
        self.password = password
        self.response = BleResponse(bytearray(0))
        self.lock_status = -1
        self.bolt_status = -1
        self.battery = -1
        self.work_mode = -1
        self.mute = False
        #self.calendar = None
        self.sn = None
        #self.direction = False

    async def unlock(self):
        await self.send_encrypted(BLERequest(BLECommand.UNLOCK, self.uid, self.password))

    async def update(self):
        await self.start_notify(ServiceUUID.DATA.value, self.__receive_write_response)
        await self.send_encrypted(BLERequest(BLECommand.GET_LOCK_STATUS))
        await self.send_encrypted(BLERequest(BLECommand.GET_BATTERY))
        await self.send_encrypted(BLERequest(BLECommand.GET_SN, None, None, bytearray([16])))
        await self.send_encrypted(BLERequest(BLECommand.GET_MUTE))
        await asyncio.sleep(2)
        await self.stop_notify(ServiceUUID.DATA.value)

    async def _update_data(self, response: BleResponse):
        print(f"package {response.command}: {response.package.hex()}")
        if response.command == RequestResponse.LOCK_STATUS.value:
            self.lock_status = int(response.data[1])
            self.bolt_status = int(response.data[2])
            print(f"data:{response.data.hex()} | lock:{self.lock_status}, {LOCK_MODE[self.lock_status]} |  bolt:{self.bolt_status}, {LOCK_STATUS[self.bolt_status]}")
        elif response.command == RequestResponse.BATTERY.value:
            self.battery = int(response.data[1])
            print(f"data:{response.data.hex()} | level:{self.battery}, {BATTERY_LEVEL[self.battery]}")
        elif response.command == RequestResponse.SN.value:
            self.sn = response.data.decode('ISO8859-1')
            print(f"data:{response.data.hex()} | serial:{self.sn}")
        elif response.command == RequestResponse.MUTE.value:
            self.mute = bool(response.data[1])
            print(f"data:{response.data.hex()} | sound:{self.mute}")
            
    async def __receive_write_response(self, sender: int, data: bytearray):
        self.response.append(data, self.secret_key.aes_key)
        if self.response.completed:
            await self._update_data(self.response)
            self.response.reset()
        
