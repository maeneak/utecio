import asyncio
import hashlib
import struct
from typing import Any

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from Crypto.Cipher import AES
from ecdsa import SECP128r1, SigningKey
from ecdsa.ellipticcurve import Point

from . import logger
from .constants import CRC8Table
from .enums import BLECommandCode, BleResponseCode, ULKeyUUID, ULServiceUUID


class BleDeviceKey:
    @staticmethod
    async def get_aes_key(client: BleakClient) -> bytes:
        if client.services.get_characteristic(ULKeyUUID.STATIC.value):
            return bytearray(b"Anviz.ut") + await client.read_gatt_char(
                ULKeyUUID.STATIC.value
            )
        elif client.services.get_characteristic(ULKeyUUID.MD5.value):
            return await BleDeviceKey.get_md5_key(client)
        elif client.services.get_characteristic(ULKeyUUID.ECC.value):
            return await BleDeviceKey.get_ecc_key(client)
        else:
            raise NotImplementedError(f"({client.address}) Unknown encryption.")

    @staticmethod
    async def get_ecc_key(client: BleakClient) -> bytes:
        try:
            private_key = SigningKey.generate(curve=SECP128r1)
            received_pubkey = []
            public_key = private_key.get_verifying_key()  # type: ignore # noqa
            pub_x = public_key.pubkey.point.x().to_bytes(16, "little")  # type: ignore # noqa
            pub_y = public_key.pubkey.point.y().to_bytes(16, "little")  # type: ignore # noqa

            notification_event = asyncio.Event()

            def notification_handler(sender, data):
                # logger.debug(f"({client._mac_address}) ECC data:{data.hex()}")
                received_pubkey.append(data)
                if len(received_pubkey) == 2:
                    notification_event.set()

            await client.start_notify(ULKeyUUID.ECC.value, notification_handler)
            await client.write_gatt_char(ULKeyUUID.ECC.value, pub_x)
            await client.write_gatt_char(ULKeyUUID.ECC.value, pub_y)
            await notification_event.wait()

            await client.stop_notify(ULKeyUUID.ECC.value)

            rec_key_point = Point(
                SECP128r1.curve,
                int.from_bytes(received_pubkey[0], "little"),
                int.from_bytes(received_pubkey[1], "little"),
            )
            shared_point = private_key.privkey.secret_multiplier * rec_key_point  # type: ignore # noqa
            shared_key = int.to_bytes(shared_point.x(), 16, "little")
            logger.debug(f"({client.address}) ECC key updated.")
            return shared_key
        except Exception as e:
            logger.error(f"({client.address}) Failed to update ECC key: {e}")
            raise

    @staticmethod
    async def get_md5_key(client: BleakClient) -> bytes:
        try:
            secret = await client.read_gatt_char(ULKeyUUID.MD5.value)

            logger.debug(f"({client.address}) Secret: {secret.hex()}")

            if len(secret) != 16:
                raise ValueError(f"({client.address}) Expected secret of length 16.")

            part1 = struct.unpack("<Q", secret[:8])[0]  # Little-endian
            part2 = struct.unpack("<Q", secret[8:])[0]

            xor_val1 = (
                part1 ^ 0x716F6C6172744C55
            )  # this value corresponds to 'ULtraloq' in little-endian
            xor_val2_part1 = (part2 >> 56) ^ (part1 >> 56) ^ 0x71
            xor_val2_part2 = ((part2 >> 48) & 0xFF) ^ ((part1 >> 48) & 0xFF) ^ 0x6F
            xor_val2_part3 = ((part2 >> 40) & 0xFF) ^ ((part1 >> 40) & 0xFF) ^ 0x6C
            xor_val2_part4 = ((part2 >> 32) & 0xFF) ^ ((part1 >> 32) & 0xFF) ^ 0x61
            xor_val2_part5 = ((part2 >> 24) & 0xFF) ^ ((part1 >> 24) & 0xFF) ^ 0x72
            xor_val2_part6 = ((part2 >> 16) & 0xFF) ^ ((part1 >> 16) & 0xFF) ^ 0x74
            xor_val2_part7 = ((part2 >> 8) & 0xFF) ^ ((part1 >> 8) & 0xFF) ^ 0x4C
            xor_val2_part8 = (part2 & 0xFF) ^ (part1 & 0xFF) ^ 0x55

            xor_val2 = (
                (xor_val2_part1 << 56)
                | (xor_val2_part2 << 48)
                | (xor_val2_part3 << 40)
                | (xor_val2_part4 << 32)
                | (xor_val2_part5 << 24)
                | (xor_val2_part6 << 16)
                | (xor_val2_part7 << 8)
                | xor_val2_part8
            )

            xor_result = struct.pack("<QQ", xor_val1, xor_val2)

            m = hashlib.md5()
            m.update(xor_result)
            result = m.digest()

            bVar2 = (part1 & 0xFF) ^ 0x55
            if bVar2 & 1:
                m = hashlib.md5()
                m.update(result)
                result = m.digest()

            logger.debug(f"({client.address}) MD5 key:{result.hex()}")
            return result

        except Exception as e:
            logger.error(f"({client.address}) Failed to update MD5 key: {e}")
            raise


class BleRequest:
    def __init__(
        self,
        command: BLECommandCode,
        uid: str = "",
        password: str = "",
        data: bytes = bytes(),
        notify: bool = True,
    ):
        self.command = command
        self.uuid = ULServiceUUID.DATA.value
        self.notify = notify
        self.response = BleResponse(self)
        self.aes_key: bytes
        self.mac_uuid = ""
        self.sent = False
        self.data = data

        self.buffer = bytearray(5120)
        self.buffer[0] = 0x7F
        byte_array = bytearray(int.to_bytes(2, 2, "little"))
        self.buffer[1] = byte_array[0]
        self.buffer[2] = byte_array[1]
        self.buffer[3] = command.value
        self._write_pos = 4

        if uid:
            self._append_auth(uid, password)
        if data:
            self._append_data(data)
        self._append_length()
        self._append_crc()

    def _append_data(self, data):
        data_len = len(data)
        self.buffer[self._write_pos : self._write_pos + data_len] = data
        self._write_pos += data_len

    def _append_auth(self, uid: str, password: str = ""):
        if uid:
            byte_array = bytearray(int(uid).to_bytes(4, "little"))
            self.buffer[self._write_pos : self._write_pos + 4] = byte_array
            self._write_pos += 4
        if password:
            byte_array = bytearray(int(password).to_bytes(4, "little"))
            byte_array[3] = (len(password) << 4) | byte_array[3]
            self.buffer[self._write_pos : self._write_pos + 4] = byte_array[:4]
            self._write_pos += 4

    def _append_length(self):
        byte_array = bytearray(int(self._write_pos - 2).to_bytes(2, "little"))
        self.buffer[1] = byte_array[0]
        self.buffer[2] = byte_array[1]

    def _append_crc(self):
        b = 0
        for i2 in range(3, self._write_pos):
            m_index = (b ^ self.buffer[i2]) & 0xFF
            b = CRC8Table[m_index]

        self.buffer[self._write_pos] = b
        self._write_pos += 1

    @property
    def package(self) -> bytearray:
        return self.buffer[: self._write_pos]

    def encrypted_package(self, aes_key: bytes):
        bArr2 = bytearray(self._write_pos)
        bArr2[: self._write_pos] = self.buffer[: self._write_pos]
        num_chunks = (self._write_pos // 16) + (1 if self._write_pos % 16 > 0 else 0)
        pkg = bytearray(num_chunks * 16)

        i2 = 0
        while i2 < num_chunks:
            i3 = i2 + 1
            if i3 < num_chunks:
                bArr = bArr2[i2 * 16 : (i2 + 1) * 16]
            else:
                i4 = self._write_pos - ((num_chunks - 1) * 16)
                bArr = bArr2[i2 * 16 : i2 * 16 + i4]

            initialValue = bytearray(16)
            encrypt_buffer = bytearray(16)
            encrypt_buffer[: len(bArr)] = bArr
            cipher = AES.new(aes_key, AES.MODE_CBC, initialValue)
            encrypt = cipher.encrypt(encrypt_buffer)
            if encrypt is None:
                encrypt = bytearray(16)

            pkg[i2 * 16 : (i2 + 1) * 16] = encrypt
            i2 = i3
        return pkg


class BleResponse:
    def __init__(self, request: BleRequest):
        self.buffer = bytearray()
        self.request = request
        self.response_completed = asyncio.Event()

    async def receive_write_response_callback(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ):
        try:
            self._append(data, bytearray(self.request.aes_key))
            if self.completed and self.is_valid:
                self.response_completed.set()
        except Exception as e:
            logger.error(
                "(%s) Error receiving write response: %s", self.request.mac_uuid, e
            )

    def reset(self):
        self.buffer = bytearray(0)

    def _append(self, bArr: bytearray, aes_key: bytearray):
        f495iv = bytearray(16)
        cipher = AES.new(aes_key, AES.MODE_CBC, f495iv)
        output = cipher.decrypt(bArr)

        if (self.length > 0 and self.buffer[0] == 0x7F) or output[0] == 0x7F:
            self.buffer += output

    def _parameter(self, index):
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
        return (
            True
            if (self.completed and cmd and isinstance(cmd, BleResponseCode))
            else False
        )

    @property
    def completed(self):
        return True if self.length > 3 and self.length >= self.package_len else False

    @property
    def length(self):
        return len(self.buffer)

    @property
    def data_len(self):
        return (
            int.from_bytes(self.buffer[1:3], byteorder="little")
            if self.length > 3
            else 0
        )

    @property
    def package_len(self):
        return self.data_len + 4 if self.length > 3 else 0

    @property
    def package(self):
        return self.buffer[: self.package_len - 1]

    @property
    def command(self) -> BleResponseCode | Any:
        return BleResponseCode(self.buffer[3]) if self.completed else None

    @property
    def success(self) -> bool:
        return True if self.completed and self.buffer[4] == 0 else False

    @property
    def data(self) -> bytearray:
        if self.is_valid:
            return self.buffer[5:self.data_len + 5]
        else:
            return bytearray()

