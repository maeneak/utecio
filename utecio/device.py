import asyncio
import hashlib
import struct

from __init__ import logger
from Crypto.Cipher import AES
from ble import UtecBleClient
from enums import KeyUUID, BLECommandCode, ServiceUUID, BleResponseCode
from constants import CRC8Table

class UtecBleDevice(UtecBleClient):
    def __init__(self, device_name: str, mac_address: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__(mac_address, max_retries, retry_delay, bleakdevice_callback)
        self._device_name = device_name
        self.secret_key = None

    async def update(self):
        return
    
    async def _get_device_encryption(self):
        if await self.find_characteristic(KeyUUID.STATIC.value):
            self.secret_key = BleDeviceKey()
        elif await self.find_characteristic(KeyUUID.MD5.value):
            self.secret_key = BleDeviceKeyMD5()
        elif await self.find_characteristic(KeyUUID.ECC.value):
            raise NotImplementedError(f"Device at address {self.client.address} uses ECC encryption which is not currenty supported.")
        else:
            raise NotImplementedError(f"Device at address {self.client.address} uses an unknown encryption.")

    async def on_connected(self):
        if not self.secret_key:
            await self._get_device_encryption()
        await self.secret_key.update(self)
        return await super().on_connected()

    async def send_encrypted(self, request: 'BleRequest'):
        try:
            await self.connect()
            await self.write_characteristic(ServiceUUID.DATA.value, request.encrypted_package(self.secret_key.aes_key))
        except Exception as e:
            logger.error(f"Failed to send encrypted data: {e}")


class BleDeviceKey:
    def __init__(self):
        self.secret = bytearray(b'Anviz.ut')
        self._key = bytearray(0)

    @property    
    def aes_key(self):
        return self._key
        
    async def update(self, client: UtecBleClient):
        self.key = self.secret + await client.read_characteristic(KeyUUID.STATIC.value)

class BleDeviceKeyMD5(BleDeviceKey):
    def __init__(self):
        super().__init__()
    
    async def update(self, client: UtecBleClient):
        try:
            secret = await client.read_characteristic(KeyUUID.MD5.value)
            
            logger.debug(f"Secret:{secret.hex()}")

            if len(secret) != 16:
                raise ValueError("Expected secret of length 16")
            # assert len(secret) == 16

            # Split the data into two 8-byte parts
            part1 = struct.unpack('<Q', secret[:8])[0]  # Little-endian
            part2 = struct.unpack('<Q', secret[8:])[0]  # Little-endian

            # XOR operations
            xor_val1 = part1 ^ 0x716f6c6172744c55  # this value corresponds to 'ULtraloq' in little-endian
            xor_val2_part1 = (part2 >> 56) ^ (part1 >> 56) ^ 0x71
            xor_val2_part2 = ((part2 >> 48) & 0xFF) ^ ((part1 >> 48) & 0xFF) ^ 0x6f
            xor_val2_part3 = ((part2 >> 40) & 0xFF) ^ ((part1 >> 40) & 0xFF) ^ 0x6c
            xor_val2_part4 = ((part2 >> 32) & 0xFF) ^ ((part1 >> 32) & 0xFF) ^ 0x61
            xor_val2_part5 = ((part2 >> 24) & 0xFF) ^ ((part1 >> 24) & 0xFF) ^ 0x72
            xor_val2_part6 = ((part2 >> 16) & 0xFF) ^ ((part1 >> 16) & 0xFF) ^ 0x74
            xor_val2_part7 = ((part2 >> 8) & 0xFF) ^ ((part1 >> 8) & 0xFF) ^ 0x4c
            xor_val2_part8 = (part2 & 0xFF) ^ (part1 & 0xFF) ^ 0x55

            xor_val2 = (xor_val2_part1 << 56) | (xor_val2_part2 << 48) | (xor_val2_part3 << 40) | (xor_val2_part4 << 32) | \
                    (xor_val2_part5 << 24) | (xor_val2_part6 << 16) | (xor_val2_part7 << 8) | xor_val2_part8

            # Convert the result back to bytes
            xor_result = struct.pack('<QQ', xor_val1, xor_val2)

            # Compute MD5 hash
            m = hashlib.md5()
            m.update(xor_result)
            result = m.digest()

            # Check for the condition to apply the MD5 hash again
            bVar2 = (part1 & 0xFF) ^ 0x55
            if bVar2 & 1:  # Checking the least significant bit is set
                m = hashlib.md5()
                m.update(result)
                result = m.digest()

            self.secret = secret
            self._key = result
            logger.debug(f"MD5 key:{result.hex()}")
            
        except Exception as e:
            logger.error(f"Failed to update MD5 key: {e}")
        
class BleRequest:
    def __init__(self, command: BLECommandCode, uid: str = None, password: str = None, data: bytearray = None):
        self.command = command
        self.buffer = bytearray(5120)
        
        self.buffer[0] = 0x7F  
        byte_array = bytearray(int.to_bytes(2, 2, "little"))
        self.buffer[1] = byte_array[0]
        self.buffer[2] = byte_array[1]
        self.buffer[3] = command.value
        self._write_pos = 4
        
        if uid:
            self.append_auth(uid, password)
        if data:
            self.append_data(data)
        self.append_length()
        self.append_crc()
            
        logger.debug(f"Request {command.name}: {self.package.hex()}")
 
    def append_data(self, data):
        data_len = len(data)
        self.buffer[self._write_pos:self._write_pos+data_len] = data
        self._write_pos += data_len        
    
    def append_auth(self, uid: str, password: str = None):
        if uid:
            byte_array = bytearray(int(uid).to_bytes(4, "little"))
            self.buffer[self._write_pos:self._write_pos+4] = byte_array
            self._write_pos += 4
        if password:
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
            b = CRC8Table[m_index]

        self.buffer[self._write_pos] = b
        self._write_pos += 1
        
    @property
    def package(self) -> bytearray:
        return self.buffer[:self._write_pos]
        
    def encrypted_package(self, aes_key):
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

    def append(self, bArr: bytearray, aes_key: bytearray):
        f495iv = bytearray(16)        
        cipher = AES.new(aes_key, AES.MODE_CBC, f495iv)
        output = cipher.decrypt(bArr)

        if (self.length > 0 and self.buffer[0] == 0x7F) or output[0] == 0x7F:
            self.buffer += output
     
    def parameter(self, index):
        data_len = self.data_len
        if data_len < 3:
            return None
        
        param_size = (data_len - 2) - index
        bArr2 = bytearray([0] * param_size)
        bArr2[:] = self.buffer[index + 4 : index + 4 + param_size]
        
        return bytearray(bArr2)

    @property
    def is_valid(self):
        cmd = self.command
        return True if (self.completed and cmd and isinstance(cmd, BleResponseCode)) else False

    @property
    def completed(self):
        return True if self.length > 3 and self.length >= self.package_len else False

    @property
    def length(self):
        return len(self.buffer)
    
    @property
    def data_len(self):
        return int.from_bytes(self.buffer[1:3], byteorder='little') if self.length > 3 else 0
    
    @property
    def package_len(self):
        return self.data_len + 3 if self.length > 3 else 0
    
    @property
    def package(self):
        return self.buffer[:self.package_len]
    
    @property
    def command(self) -> BleResponseCode:
        return BleResponseCode(self.buffer[3]) if self.completed else None
    
    @property
    def data(self):
        data_len = self.data_len
        return bytearray(self.buffer[4 : 4 + (data_len - 2)]) if data_len > 3 else None
