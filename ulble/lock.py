import asyncio
from .client import BleClient
from .utility import Utility

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

    def completed(self):
        return True if self.length > 3 and self.length >= self.package_len else False

    def append(self, bArr: bytearray):
        if self.buffer[0] == 0x7F or bArr[0] == 0x7F:
            self.buffer.append(bArr)

    def length(self):
        return len(self.buffer)
    
    def data_len(self):
        return Utility._2bytes_to_int(self.buffer, 1) if self.length > 3 else 0
    
    def package_len(self):
        return self.data_len + 3 if self.length > 3 else 0
    
    def command(self):
        return self.buffer[3] if self.length > 3 else 0
    
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
        self._username = username
        self._password = password
        self.key = None
        self.response = ULBleNotification(bytearray(0))

    async def Unlock(self):
        self._write_command(Utility.CMD_UNLOCK)

    async def _write_command(self, command):
        if not self.client.is_connected or self.key == None:
            self.key = await Utility.CreateMD5AccessKey(await self.read_characteristic(Utility.UID_CHAR_LOCK_KEY_MD5))
        data = await Utility.PackageMD5Command(command, self.username, self.password, self.key)
        await self.write_characteristic(Utility.UID_CHAR_LOCK_DATA, data)

    async def _write_request(self, command, username = "", password = ""):
        if not self.client.is_connected or self.key == None:
            self.key = await Utility.CreateMD5AccessKey(await self.read_characteristic(Utility.UID_CHAR_LOCK_KEY_MD5))
        data = await Utility.PackageMD5Command(command, self.username, self.password, self.key)
        await self.start_notify(Utility.UID_CHAR_LOCK_DATA, self._data_handler)
        await self.write_characteristic(Utility.UID_CHAR_LOCK_DATA, data)

    async def _update_data(self, response: ULBleNotification):
        print(f"Data for {response.command}:{[i for i in response.data]}")
    
    async def _data_handler(self, sender: int, data: bytearray):
        self.response.append(await Utility.UnpackageMD5Response(data, self.key))
        if self.response.completed:
            await self.stop_notify(sender)
            await self._update_data(ULBleNotification(self.buffer))
            self.response = ULBleNotification(bytearray(0))
        else:
            return
        
