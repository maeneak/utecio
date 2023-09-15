import asyncio
from client import BleClient, BleResponse
from ul import UL
from enums import RequestResponse, RequestCommand, UUID

class ULBleLock(BleClient):
    def __init__(self, device_name: str, username: str, password: str, mac_address: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__(mac_address, max_retries, retry_delay, bleakdevice_callback)
        self._device_name = device_name
        self.username = username
        self.password = password
        self.key = None
        self.response = BleResponse(bytearray(0))
        self.lock_status = -1
        self.bolt_status = -1
        self.battery = -1
        self.work_mode = -1
        self.sound = False
        #self.calendar = None
        self.sn = None
        #self.direction = False

    async def unlock(self):
        await self.send_encrypted(RequestCommand.UNLOCK)

    async def update(self):
        await self.start_notify(UUID.WRITE_DATA.value, self.__receive_write_response)
        
        await self.send_encrypted(RequestCommand.LOCK_STATUS)
        await self.send_encrypted(RequestCommand.BATTERY)
        
        await asyncio.sleep(2)
        await self.stop_notify(UUID.WRITE_DATA.value)

    async def send_encrypted(self, command: RequestCommand):
        if not self.client or not self.client.is_connected or self.key == None:
            self.key = await UL.key_md5(await self.read_characteristic(UUID.READ_KEY_MD5.value))

        data = await UL.pack_request(command.value, self.username, self.password, self.key)
        await self.write_characteristic(UUID.WRITE_DATA.value, data)

    async def __update_data(self, response: BleResponse):
        print(f"package {response.command}: {response.buffer}")

        if response.command == RequestResponse.LOCK_STATUS.value:
            print(f"data:{response.data} | lock:{int(response.data[1])} bolt:{int(response.data[2])}")
        elif response.command == RequestResponse.BATTERY.value:
            print(f"data:{response.data} | param:{response.parameter(1)}")
            
    async def __receive_write_response(self, sender: int, data: bytearray):
        self.response.append(await UL.unpack_response(data, self.key))
        if self.response.completed:
            await self.__update_data(self.response)
            self.response = BleResponse(bytearray(0))
        else:
            return
        
