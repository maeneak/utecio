import asyncio
from bleak import BleakClient
from ul import UL
from enums import BLECommand
from Crypto.Cipher import AES

class BleClient:
    def __init__(self, mac_address: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__()
        self._mac_address = mac_address
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._bleakdevice_cb = bleakdevice_callback
        self.client = None
        
    async def connect(self):
        attempt = 0
        while attempt < self._max_retries:
            try:
                if not self.client or not self.client.is_connected:
                    ble_device = self._bleakdevice_cb() if self._bleakdevice_cb != None else self._mac_address
                    self.client = BleakClient(ble_device)
                    await self.client.connect()
                    return
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed. Reason: {e}")
                if attempt + 1 < self._max_retries:
                    print(f"Retrying in {self._retry_delay} seconds...")
                    await asyncio.sleep(self._retry_delay)  # Wait before retrying
                else:
                    raise  # Raise the exception if max retries have been exhausted
            attempt += 1
            
    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    async def read_characteristic(self, uuid):
        await self.connect()
        return await self.client.read_gatt_char(uuid)

    async def write_characteristic(self, uuid, data):
        await self.connect()
        await self.client.write_gatt_char(uuid, data)

    async def start_notify(self, uuid, callback):
        await self.connect()
        await self.client.start_notify(uuid, callback)

    async def stop_notify(self, uuid):
        await self.connect()
        await self.client.stop_notify(uuid)

class BLERequest:
    def __init__(self, command: BLECommand, uid: str = "", password: str = "", data: bytearray = None):
        self.command = command
        self.data = data
        self.buffer = bytearray(5120)
        
        self.buffer[0] = 0x7F  
        byte_array = bytearray(int.to_bytes(2, 2, "little"))
        self.buffer[1] = byte_array[0]
        self.buffer[2] = byte_array[1]
        self.buffer[3] = command.value
        self._write_pos = 4
        
        if command in [BLECommand.UNLOCK]:
            self.append_auth(uid, password)
            self.append_length
            self.append_crc
            print(self.buffer[:self._write_pos].hex())
    
    def append_auth(self, uid: str, password: str):
        byte_array = bytearray(int(uid).to_bytes(4, "little"))
        self.buffer[self._write_pos:self._write_pos+4] = byte_array
        self._write_pos += 4
        byte_array = bytearray(int(password).to_bytes(4, "little"))
        byte_array[3] = (len(password) << 4) | byte_array[3]
        self.buffer[self._write_pos:self._write_pos+4] = byte_array[:4]
        self._write_pos += 4

    def append_length(self):
        byte_array = bytearray(int(self._write_pos - 2).to_bytes(2, "little"))
        self.buffer[1] = byte_array[0]
        self.buffer[2] = byte_array[1]
        
    def append_crc(self):
        b = 0
        for i2 in range(3, self._write_pos):
            m_index = (b ^ self.buffer[i2]) & 0xFF
            # print(f'Index:{m_index}')
            b = UL.CRC8Table[m_index]

        self.buffer[self._write_pos] = b
        self._write_pos += 1
        
    def package(self, aes_key):
        bArr2 = bytearray(self._write_pos)
        bArr2[:self._write_pos] = self.buffer[:self._write_pos]
        num_chunks = (self._write_pos // 16) + (1 if self._write_pos % 16 > 0 else 0)
        pkg = bytearray(num_chunks * 16)

        i2 = 0
        while i2 < num_chunks:
            i3 = i2 + 1
            if i3 < num_chunks:
                bArr = bArr2[i2 * 16:(i2 + 1) * 16]
            else:
                i4 = self._write_pos - ((num_chunks - 1) * 16)
                bArr = bArr2[i2 * 16:i2 * 16 + i4]
            
            initialValue = bytearray(16)
            encrypt_buffer = bytearray(16)
            encrypt_buffer[:len(bArr)] = bArr
            cipher = AES.new(aes_key, AES.MODE_CBC, initialValue)
            encrypt = cipher.encrypt(encrypt_buffer)
            if encrypt is None:
                encrypt = bytearray(16)
            
            pkg[i2 * 16:(i2 + 1) * 16] = encrypt
            i2 = i3
        return pkg
        
class BleResponse:
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
    def package(self):
        return self.buffer[:self.package_len]
    
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


