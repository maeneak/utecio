import asyncio
from client import BleClient
from ul import UL
from enums import BLERequestResponse, BLERequestCommand, UUID

class ULBleLockStatus:
    def __init__(self):
        self.lock_status = -1
        self.bolt_status = -1
        self.battery = -1
        self.work_mode = -1
        self.sound = False
        #self.calendar = None
        self.sn = None
        #self.direction = False

    def reset(self):
        self.lock_status = -1
        self.bolt_status = -1
        self.battery = -1
        self.work_mode = -1
        self.sound = False
        #self.calendar = None
        self.sn = None
        #self.direction = False

class ULBleNotification:
    def __init__(self, buffer: bytearray):
        self.buffer = buffer

    def reset(self):
        self.buffer = bytearray(0)

    @property
    def completed(self):
        return True if self.length > 3 and self.length >= self.package_len else False

    def append(self, bArr: bytearray):
        if (self.length > 0 and self.buffer[0] == 0x7F) or bArr[0] == 0x7F:
            self.buffer += bArr

    @property
    def length(self):
        return len(self.buffer)
    
    @property
    def data_len(self):
        return UL._2bytes_to_int(self.buffer, 1) if self.length > 3 else 0
    
    @property
    def package_len(self):
        return self.data_len + 3 if self.length > 3 else 0
    
    @property
    def command(self):
        return self.buffer[3] if self.length > 3 else 0
    
    @property
    def data(self):
        data_len = self.data_len
        return bytearray(self.buffer[4 : 4 + (data_len - 2)]) if data_len > 3 else None
     
    def parameter(self, index):
        data_len = self.data_len
        if data_len < 3:
            return None
        
        param_size = (data_len - 2) - index
        bArr2 = bytearray([0] * param_size)
        bArr2[:] = self.buffer[index + 4 : index + 4 + param_size]
        
        return bytearray(bArr2)

class ULBleLock(BleClient, ULBleLockStatus):
    def __init__(self, device_name: str, username: str, password: str, mac_address: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__(mac_address, max_retries, retry_delay, bleakdevice_callback)
        self._device_name = device_name
        self.username = username
        self.password = password
        self.key = None
        self.response = ULBleNotification(bytearray(0))

    async def unlock(self):
        await self.__write_encrypted(BLERequestCommand.UNLOCK)

    async def update(self):
        await self.start_notify(UUID.WRITE_DATA.value, self.__receive_write_response)
        
        await self.__write_encrypted(BLERequestCommand.LOCK_STATUS)
        await self.__write_encrypted(BLERequestCommand.BATTERY)
        
        await self.stop_notify(UUID.WRITE_DATA.value)

    async def __write_encrypted(self, command: BLERequestCommand):
        if not self.client or not self.client.is_connected or self.key == None:
            self.key = await UL.key_md5(await self.read_characteristic(UUID.READ_KEY_MD5.value))

        data = await UL.pack_request(command.value, self.username, self.password, self.key)
        await self.write_characteristic(UUID.WRITE_DATA.value, data)

    async def __update_data(self, response: ULBleNotification):
        print(f"package {response.command}: {response.buffer}")

        if response.command == BLERequestResponse.LOCK_STATUS.value:
            print(f"data:{response.data} | lock:{int(response.data[1])} bolt:{int(response.data[2])}")
        elif response.command == BLERequestResponse.BATTERY.value:
            print(f"data:{response.data} | param:{response.parameter(1)}")
            
    async def __receive_write_response(self, sender: int, data: bytearray):
        self.response.append(await UL.unpack_response(data, self.key))
        if self.response.completed:
            await self.__update_data(self.response)
            self.response = ULBleNotification(bytearray(0))
        else:
            return
        
