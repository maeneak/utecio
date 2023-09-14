import asyncio
import hashlib
import struct
import logging
from bleak import BleakClient
from Crypto.Cipher import AES

_LOGGER = logging.getLogger(__name__)

class Utility:
    CRC8Java = [0, 94, -68, -30, 97, 63, -35, -125, -62, -100, 126, 32, -93, -3, 31, 65, -99, -61, 33, 127, -4, -94, 64, 30, 95, 1, -29, -67, 62, 96, -126, -36, 35, 125, -97, -63, 66, 28, -2, -96, -31, -65, 93, 3, -128, -34, 60, 98, -66, -32, 2, 92, -33, -127, 99, 61, 124, 34, -64, -98, 29, 67, -95, -1, 70, 24, -6, -92, 39, 121, -101, -59, -124, -38, 56, 102, -27, -69, 89, 7, -37, -123, 103, 57, -70, -28, 6, 88, 25, 71, -91, -5, 120, 38, -60, -102, 101, 59, -39, -121, 4, 90, -72, -26, -89, -7, 27, 69, -58, -104, 122, 36, -8, -90, 68, 26, -103, -57, 37, 123, 58, 100, -122, -40, 91, 5, -25, -71, -116, -46, 48, 110, -19, -77, 81, 15, 78, 16, -14, -84, 47, 113, -109, -51, 17, 79, -83, -13, 112, 46, -52, -110, -45, -115, 111, 49, -78, -20, 14, 80, -81, -15, 19, 77, -50, -112, 114, 44, 109, 51, -47, -113, 12, 82, -80, -18, 50, 108, -114, -48, 83, 13, -17, -79, -16, -82, 76, 18, -111, -49, 45, 115, -54, -108, 118, 40, -85, -11, 23, 73, 8, 86, -76, -22, 105, 55, -43, -117, 87, 9, -21, -75, 54, 104, -118, -44, -107, -53, 41, 119, -12, -86, 72, 22, -23, -73, 85, 11, -120, -42, 52, 106, 43, 117, -105, -55, 74, 20, -10, -88, 116, 42, -56, -106, 21, 75, -87, -9, -74, -24, 10, 84, -41, -119, 107, 53]
    CRC8Table = [(value & 0xFF) for value in CRC8Java]

    ENCRYPT_PACKAGE_LEN = 16
    PACKAGE_LEN = 16
    PACKAGE_LEN_128 = 128
    UID_SERVICE_UTEC_LOCK = "00007200-0000-1000-8000-00805f9b34fb"
    UID_SERVICE_UTEC_DEVINFO = "0000180A-0000-1000-8000-00805f9b34fb"
    UID_SERVICE_BRIDGE_DEVINFO = "0000180A-0000-1000-8000-00805f9b34fb"
    UID_CHAR_BRIDGE_MAC = "00002a23-0000-1000-8000-00805f9b34fb"
    UID_SERVICE_OAD = "f000ffc0-0451-4000-b000-000000000000"
    UID_SERVICE_CC = "0000ccc0-0000-1000-8000-00805f9b34fb"
    UID_CHAR_LOCK_DATA = "00007201-0000-1000-8000-00805f9b34fb"
    UID_CHAR_LOCK_KEY = "00007220-0000-1000-8000-00805f9b34fb"
    UID_CHAR_LOCK_KEY_ECC = "00007221-0000-1000-8000-00805f9b34fb"
    UID_CHAR_LOCK_KEY_MD5 = "00007223-0000-1000-8000-00805f9b34fb"
    UID_CHAR_SYSTEM_ID = "00002A23-0000-1000-8000-00805f9b34fb"
    UID_CHAR_MODEL_NUMBER = "00002A24-0000-1000-8000-00805f9b34fb"
    UID_CHAR_FIRMWARE = "00002A26-0000-1000-8000-00805f9b34fb"
    UID_CHAR_SN = "00002A25-0000-1000-8000-00805f9b34fb"
    UID_CHAR_OAD_IDENTIFY = "f000ffc1-0451-4000-b000-000000000000"
    UID_CHAR_OAD_BLOCK = "f000ffc2-0451-4000-b000-000000000000"
    UID_CHAR_OAD_CONTROL = "f000ffc5-0451-4000-b000-000000000000"
    UID_DESCRIPTOR_CONFIG = "00002902-0000-1000-8000-00805f9b34fb"

    CMD_UNLOCK =85 # "Unlock"
    CMD_BOLTLOCK = 86 # "boltLock"
    CMD_READ_PLEVEL = 67 # "Read power level"
    CMD_GET_LATCH_UL1 = 114 # "Get Latch lock UL1"
    CMD_SET_LATCH_UL1 = 115 # "Set Latch lock UL1"
    CMD_DOORSENSOR = 117 # "door sensor"
    CMD_READ_LOCK_SN = 94 # "Read lock SN"
    CMD_LOCK_STATUS = 80 # Lock Status"
    CMD_READ_LOCK_STATUS = 81 # Read lock setStatus"
    CMD_SET_LOCK_STATUS = 82 # Set lock setStatus"

    RES_READ_PLEVEL = 195 # Power Level Response

    @staticmethod
    def _2bytes_to_int(bArr, i):
        i2 = 0
        for i3 in range(i + 1, i - 1, -1):
            i2 = (i2 << 8) | (bArr[i3] & 0xFF)
        return i2

    @staticmethod
    async def CreateMD5AccessKey(data: bytearray): # Input the byte array returned from UID_CHAR_LOCK_KEY_MD5
        # Ensure data is 16 bytes
        assert len(data) == 16

        # Split the data into two 8-byte parts
        part1 = struct.unpack('<Q', data[:8])[0]  # Little-endian
        part2 = struct.unpack('<Q', data[8:])[0]  # Little-endian

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

        print(f"md5 key:{result.hex()}")
        return result

    @staticmethod
    async def PackageMD5Command(command: int, uid: str, password: str, aesKey: bytearray):
        buffer = bytearray(5120)
        if len(password) == 10: password = Utility.DecodeAPIPassword(password)
        try:
            # Create Buffer (tcb_req)
            buffer[0] = 0x7F  
            byte_array = bytearray(int.to_bytes(2, 2, "little"))
            buffer[1] = byte_array[0]
            buffer[2] = byte_array[1]
            buffer[3] = command
            m_write_pos = 4

            # Check if auth required
            if command in [Utility.CMD_BOLTLOCK, Utility.CMD_UNLOCK]:
                # Append user id
                byte_array = bytearray(int(uid).to_bytes(4, "little"))
                buffer[m_write_pos:m_write_pos+4] = byte_array
                m_write_pos += 4
                # Append password bytes
                byte_array = bytearray(int(password).to_bytes(4, "little"))
                byte_array[3] = (len(password) << 4) | byte_array[3]
                buffer[m_write_pos:m_write_pos+4] = byte_array[:4]
                m_write_pos += 4
            elif command == Utility.CMD_READ_LOCK_SN:
                # Append user id
                buffer[m_write_pos] = 16
                m_write_pos += 1
            
            # Append data package length to bytes 1 & 2
            byte_array = bytearray(int(m_write_pos - 2).to_bytes(2,"little"))
            buffer[1] = byte_array[0]
            buffer[2] = byte_array[1]

            # Append CRC byte
            b = 0
            for i2 in range(3, m_write_pos):
                m_index = (b ^ buffer[i2]) & 0xFF
                # print(f'Index:{m_index}')
                b = Utility.CRC8Table[m_index]

            buffer[m_write_pos] = b
            m_write_pos += 1
            
            print(f"packaging:{buffer[:m_write_pos].hex()}")
            # Build Bluetooth Frame/s
            bArr2 = bytearray(m_write_pos)
            bArr2[:m_write_pos] = buffer[:m_write_pos]
            num_chunks = (m_write_pos // 16) + (1 if m_write_pos % 16 > 0 else 0)
            bArr3 = bytearray(num_chunks * 16)

            i2 = 0
            while i2 < num_chunks:
                i3 = i2 + 1
                if i3 < num_chunks:
                    bArr = bArr2[i2 * 16:(i2 + 1) * 16]
                else:
                    i4 = m_write_pos - ((num_chunks - 1) * 16)
                    bArr = bArr2[i2 * 16:i2 * 16 + i4]
                
                initialValue = bytearray(16)
                encrypt_buffer = bytearray([0] * 16)
                encrypt_buffer[:len(bArr)] = bArr
                cipher = AES.new(aesKey, AES.MODE_CBC, initialValue)
                encrypt = cipher.encrypt(encrypt_buffer)
                if encrypt is None:
                    encrypt = bytearray(16)
                
                print(f"encrypted package:{encrypt.hex()}")
                bArr3[i2 * 16:(i2 + 1) * 16] = encrypt
                i2 = i3
            return bArr3
        except Exception as e:
            print("Error creating Frame:", str(e))
            _LOGGER.warning(str(e))
            return bytearray(16)
        
    @staticmethod
    def UnpackageMD5Response(response: bytearray, aesKey: bytearray):
        print(f"decrypt:{response.hex()} with: {aesKey.hex()}")
        f495iv = bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])        
        cipher = AES.new(aesKey, AES.MODE_CBC, f495iv)
        return cipher.decrypt(response)
        
    def DecodeAPIPassword(passwordAsString: str):
        byteArray = bytearray(int(passwordAsString).to_bytes(4, "little"))
        str2 = ""
        for length in range(len(byteArray) - 1, -1, -1):
            hexString = format(byteArray[length] & 0xFF, '02x')
            str2 += hexString

        parseInt = int(str2[0])
        if parseInt == 0:
            return str

        str3 = str(int(str2[1:], 16))
        if parseInt != len(str3):
            str4 = str3
            for _ in range(parseInt - len(str3)):
                str4 = "0" + str4
            return str4
        return str3


