import asyncio
import hashlib
import struct
from Crypto.Cipher import AES
from enums import BLECommand

class UL:
    CRC8Table = [0, 94, 188, 226, 97, 63, 221, 131, 194, 156, 126, 32, 163, 253, 31, 65, 157, 195, 33, 127, 252, 162, 64, 30, 95, 1, 227, 189, 62, 96, 130, 220, 35, 125, 159, 193, 66, 28, 254, 160, 225, 191, 93, 3, 128, 222, 60, 98, 190, 224, 2, 92, 223, 129, 99, 61, 124, 34, 192, 158, 29, 67, 161, 255, 70, 24, 250, 164, 39, 121, 155, 197, 132, 218, 56, 102, 229, 187, 89, 7, 219, 133, 103, 57, 186, 228, 6, 88, 25, 71, 165, 251, 120, 38, 196, 154, 101, 59, 217, 135, 4, 90, 184, 230, 167, 249, 27, 69, 198, 152, 122, 36, 248, 166, 68, 26, 153, 199, 37, 123, 58, 100, 134, 216, 91, 5, 231, 185, 140, 210, 48, 110, 237, 179, 81, 15, 78, 16, 242, 172, 47, 113, 147, 205, 17, 79, 173, 243, 112, 46, 204, 146, 211, 141, 111, 49, 178, 236, 14, 80, 175, 241, 19, 77, 206, 144, 114, 44, 109, 51, 209, 143, 12, 82, 176, 238, 50, 108, 142, 208, 83, 13, 239, 177, 240, 174, 76, 18, 145, 207, 45, 115, 202, 148, 118, 40, 171, 245, 23, 73, 8, 86, 180, 234, 105, 55, 213, 139, 87, 9, 235, 181, 54, 104, 138, 212, 149, 203, 41, 119, 244, 170, 72, 22, 233, 183, 85, 11, 136, 214, 52, 106, 43, 117, 151, 201, 74, 20, 246, 168, 116, 42, 200, 150, 21, 75, 169, 247, 182, 232, 10, 84, 215, 137, 107, 53]

    @staticmethod
    def _2bytes_to_int(bArr, i):
        i2 = 0
        for i3 in range(i + 1, i - 1, -1):
            i2 = (i2 << 8) | (bArr[i3] & 0xFF)
        return i2

    @staticmethod
    async def key_md5(data: bytearray): # Input the byte array returned from UID_CHAR_LOCK_KEY_MD5
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

        # print(f"md5 key:{result.hex()}")
        return result

    @staticmethod
    async def pack_request(command: int, uid: str, password: str, aes_key: bytearray):
        full_auth = [85]
        user_auth = [94]
        buffer = bytearray(5120)
        if len(password) == 10: password = UL.decode_api_password(password)
        try:
            # Create Buffer (tcb_req)
            buffer[0] = 0x7F  
            byte_array = bytearray(int.to_bytes(2, 2, "little"))
            buffer[1] = byte_array[0]
            buffer[2] = byte_array[1]
            buffer[3] = command
            m_write_pos = 4

            # Check if auth required
            if command in full_auth:
                # Append user id
                byte_array = bytearray(int(uid).to_bytes(4, "little"))
                buffer[m_write_pos:m_write_pos+4] = byte_array
                m_write_pos += 4
                # Append password bytes
                byte_array = bytearray(int(password).to_bytes(4, "little"))
                byte_array[3] = (len(password) << 4) | byte_array[3]
                buffer[m_write_pos:m_write_pos+4] = byte_array[:4]
                m_write_pos += 4
            elif command in user_auth:
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
                b = UL.CRC8Table[m_index]

            buffer[m_write_pos] = b
            m_write_pos += 1
            
            # print(f"packaging:{buffer[:m_write_pos].hex()}")
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
                cipher = AES.new(aes_key, AES.MODE_CBC, initialValue)
                encrypt = cipher.encrypt(encrypt_buffer)
                if encrypt is None:
                    encrypt = bytearray(16)
                
                # print(f"encrypted package:{encrypt.hex()}")
                bArr3[i2 * 16:(i2 + 1) * 16] = encrypt
                i2 = i3
            return bArr3
        except Exception as e:
            print("Error creating Frame:", str(e))
            _LOGGER.warning(str(e))
            return bytearray(16)
        
    @staticmethod
    async def unpack_response(response: bytearray, aes_key: bytearray):
        # print(f"decrypt:{response.hex()} with: {aes_key.hex()}")
        f495iv = bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])        
        cipher = AES.new(aes_key, AES.MODE_CBC, f495iv)
        return cipher.decrypt(response)
        
    def decode_api_password(password_string: str):
        byteArray = bytearray(int(password_string).to_bytes(4, "little"))
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

