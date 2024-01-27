import asyncio
import hashlib
import struct
import datetime
from collections.abc import Awaitable, Callable
from typing import Any

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
from Crypto.Cipher import AES
from ecdsa import SECP128r1, SigningKey
from ecdsa.ellipticcurve import Point

from . import logger
from .const import CRC8Table, LOCK_MODE, BOLT_STATUS, BATTERY_LEVEL
from .enums import BLECommandCode, BleResponseCode, DeviceKeyUUID, DeviceLockWorkMode, DeviceServiceUUID
from .util import bytes_to_int2, decode_password, to_byte_array
from . import DeviceDefinition, GenericLock, known_devices


class UtecBleDevice:
    def __init__(
        self,
        uid: str,
        password: str,
        mac_uuid: Any,
        device_name: str,
        wurx_uuid: Any = None,
        device_model: str = "",
    ):
        self.mac_uuid = mac_uuid
        self.wurx_uuid = wurx_uuid
        self.uid = uid
        self.password: str = password
        self.name = device_name
        self.model: str = device_model
        self.capabilities: DeviceDefinition | Any = known_devices.get(
            device_model, GenericLock
        )
        self._request_queue: list[UtecBleRequest] = []
        self.config: dict[str, Any]
        self.async_device_callback: Callable[[str], Awaitable[BLEDevice | str]] = None
        self.lock_status: int
        self.lock_mode: int
        self.autolock_time: int
        self.battery: int
        self.mute: bool
        self.bolt_status: int
        self.sn: str
        self.is_busy = False
        self.device_time_offset:datetime.timedelta

    @classmethod
    def from_json(cls, json_config: dict[str, Any]):
        new_device = cls(
            device_name=json_config["name"],
            uid=str(json_config["user"]["uid"]),
            password=decode_password(json_config["user"]["password"]),
            mac_uuid=json_config["uuid"],
            device_model=json_config["model"],
        )
        if json_config["params"]["extend_ble"]:
            new_device.wurx_uuid = json_config["params"]["extend_ble"]
        new_device.sn = json_config["params"]["serialnumber"]
        new_device.model = json_config["model"]
        new_device.config = json_config

        return new_device

    async def async_update_status(self):
        pass

    def _add_request(self, request: "UtecBleRequest", priority: bool = False):
        if priority:
            self._request_queue.insert(0, request)
        else:
            self._request_queue.append(request)
        return self._request_queue

    async def _process_queue(self, device: BLEDevice) -> bool:
        if len(self._request_queue) < 1 or not device: 
            return False

        self.is_busy = True

        try:
            client = await establish_connection(client_class=BleakClient, device=device, name=device.address, max_attempts=3)
            aes_key = await UtecBleDeviceKey.get_aes_key(client=client)
            for request in self._request_queue:
                if not request.sent or not request.response.completed:
                    logger.debug(
                        "(%s) Sending command - %s (%s)",
                        self.mac_uuid,
                        request.command.name,
                        request.package.hex()
                    )
                    request.aes_key = aes_key
                    request.mac_uuid = self.mac_uuid
                    request.sent = True
                    await request._send_request(client)
        finally:
            await client.disconnect()
            self.is_busy = False
            self._request_queue.clear()

        return True

    async def async_wakeup_device(self, wakeup_device: BLEDevice):
        try:
            wclient = await establish_connection(client_class=BleakClient, device=wakeup_device, name=wakeup_device.address, max_attempts=3)
            logger.debug(
                f"({self.mac_uuid}) Wake-up reciever {self.wurx_uuid} connected."
            )
        finally:
            await wclient.disconnect()
        

class UtecBleLock(UtecBleDevice):
    def __init__(
        self,
        uid: str,
        password: str,
        mac_uuid: str,
        device_name: str,
        wurx_uuid: str = "",
        device_model: str = "",
    ):
        super().__init__(
            uid=uid,
            password=password,
            mac_uuid=mac_uuid,
            wurx_uuid=wurx_uuid,
            device_name=device_name,
            device_model=device_model,
        )

        self.lock_status: int = -1
        self.bolt_status: int = -1
        self.battery: int = -1
        self.work_mode: int = -1
        self.mute: bool = False
        self.sn: str
        self.calendar: datetime.datetime

    async def async_unlock(self, device: BLEDevice, update: bool = True) -> bool:
        if update:
            self._add_request(UtecBleRequest(device=self, command=BLECommandCode.LOCK_STATUS))

        self._add_request(
            UtecBleRequest(
                command=BLECommandCode.UNLOCK,
                uid=self.uid,
                password=self.password,
                notify=True,
            ),
            priority=True,
        )

        return await self._process_queue(device)


    async def async_lock(self, device: BLEDevice, update: bool = True) -> bool:
        if update:
            self._add_request(UtecBleRequest(device=self, command=BLECommandCode.LOCK_STATUS))

        self._add_request(
            UtecBleRequest(
                command=BLECommandCode.BOLT_LOCK,
                uid=self.uid,
                password=self.password,
            ),
            priority=True,
        )

        return await self._process_queue(device)


    async def async_reboot(self, device: BLEDevice) -> bool:
        self._add_request(UtecBleRequest(device=self, command=BLECommandCode.REBOOT))
        return await self._process_queue(device)


    async def async_set_workmode(self, mode: DeviceLockWorkMode, device: BLEDevice):
        self._add_request(UtecBleRequest(device=self, command=BLECommandCode.ADMIN_LOGIN))
        if self.capabilities.bt264:
            self._add_request(UtecBleRequest(device=self, command=BLECommandCode.SET_LOCK_STATUS, data=bytes([mode.value])))
        else:
            self._add_request(UtecBleRequest(device=self, command=BLECommandCode.SET_WORK_MODE, data=bytes([mode.value])))

        return await self._process_queue(device)


    async def async_set_autolock(self, seconds: int, device: BLEDevice):
        if self.capabilities.autolock:
            self._add_request(UtecBleRequest(device=self, command=BLECommandCode.ADMIN_LOGIN))
            self._add_request(
                UtecBleRequest(
                    command=BLECommandCode.SET_AUTOLOCK, 
                    data=to_byte_array(seconds, 2) + bytes([0])
                )
            )
        return await self._process_queue(device)


    async def async_update_status(self, device: BLEDevice):
        logger.debug("(%s) %s - Updating lock data...", self.mac_uuid, self.name)
        self._add_request(UtecBleRequest(device=self, command=BLECommandCode.ADMIN_LOGIN))
        self._add_request(UtecBleRequest(device=self, command=BLECommandCode.LOCK_STATUS))
        if not self.capabilities.bt264:
            self._add_request(UtecBleRequest(device=self, command=BLECommandCode.GET_BATTERY))
            self._add_request(UtecBleRequest(device=self, command=BLECommandCode.GET_MUTE))
        if self.capabilities.autolock:
            self._add_request(UtecBleRequest(device=self, command=BLECommandCode.GET_AUTOLOCK))

        # self.add_request(BleRequest(device=self, command=BLECommandCode.READ_TIME))

        return await self._process_queue(device)

class UtecBleDeviceKey:
    @staticmethod
    async def get_aes_key(client: BleakClient) -> bytes:
        if client.services.get_characteristic(DeviceKeyUUID.STATIC.value):
            return bytearray(b"Anviz.ut") + await client.read_gatt_char(
                DeviceKeyUUID.STATIC.value
            )
        elif client.services.get_characteristic(DeviceKeyUUID.MD5.value):
            return await UtecBleDeviceKey.get_md5_key(client)
        elif client.services.get_characteristic(DeviceKeyUUID.ECC.value):
            return await UtecBleDeviceKey.get_ecc_key(client)
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

            await client.start_notify(DeviceKeyUUID.ECC.value, notification_handler)
            await client.write_gatt_char(DeviceKeyUUID.ECC.value, pub_x)
            await client.write_gatt_char(DeviceKeyUUID.ECC.value, pub_y)
            await notification_event.wait()

            await client.stop_notify(DeviceKeyUUID.ECC.value)

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
            raise e

    @staticmethod
    async def get_md5_key(client: BleakClient) -> bytes:
        try:
            secret = await client.read_gatt_char(DeviceKeyUUID.MD5.value)

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
            raise e


class UtecBleRequest:
    def __init__(
        self,
        device: UtecBleDevice,
        command: BLECommandCode,
        data: bytes = bytes(),
        auth_required: bool = False
    ):
        self.command = command
        self.device = device
        self.uuid = DeviceServiceUUID.DATA.value
        self.response = UtecBleResponse(self)
        self.aes_key: bytes
        self.sent = False
        self.data = data
        self.auth_required = auth_required

        self.buffer = bytearray(5120)
        self.buffer[0] = 0x7F
        byte_array = bytearray(int.to_bytes(2, 2, "little"))
        self.buffer[1] = byte_array[0]
        self.buffer[2] = byte_array[1]
        self.buffer[3] = command.value
        self._write_pos = 4

        if auth_required:
            self._append_auth(device.uid, device.password)
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

    async def _send_request(self, client: BleakClient):
        try:
            await client.start_notify(
                self.uuid, self.response._receive_write_response
            )
            await client.write_gatt_char(
                self.uuid, self.encrypted_package(self.aes_key)
            )
            await self.response.response_completed.wait()
        finally:
            await client.stop_notify(self.uuid)


class UtecBleResponse:
    def __init__(self, request: UtecBleRequest):
        self.buffer = bytearray()
        self.request = request
        self.response_completed = asyncio.Event()

    async def _receive_write_response(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ):
        try:
            self._append(data, bytearray(self.request.aes_key))
            if self.completed and self.is_valid:
                await self._read_response()
                self.response_completed.set()
        except Exception as e:
            logger.error(
                "(%s) Error receiving write response: %s", self.request.mac_uuid, e
            )
            raise e

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
        
    async def _read_response(self):
        try:
            logger.debug(
                "(%s) Response %s (%s): %s",
                self.request.device.mac_uuid,
                self.command.name,
                "Success" if self.success else "Failed",
                self.package.hex(),
            )

            if self.command == BleResponseCode.GET_LOCK_STATUS:
                self.lock_mode = int(self.data[0])
                self.bolt_status = int(self.data[1])
                logger.debug(
                    f"({self.request.device.mac_uuid}) lock:{self.lock_mode} ({LOCK_MODE[self.lock_mode]}) |  bolt:{self.bolt_status} ({BOLT_STATUS[self.bolt_status]})"
                )

            elif self.command == BleResponseCode.SET_LOCK_STATUS:
                self.lock_mode = self.data[0]
                logger.debug(f"({self.request.device.mac_uuid}) workmode:{self.lock_mode}")

            elif self.command == BleResponseCode.GET_BATTERY:
                self.battery = int(self.data[0])
                logger.debug(
                    f"({self.request.device.mac_uuid}) power level:{self.battery}, {BATTERY_LEVEL[self.battery]}"
                )

            elif self.command == BleResponseCode.GET_AUTOLOCK:
                self.autolock_time = bytes_to_int2(self.data[:2])
                logger.debug("(%s) autolock:%s", self.request.device.mac_uuid, self.autolock_time)

            elif self.command == BleResponseCode.SET_AUTOLOCK:
                if self.success:
                    self.autolock_time = bytes_to_int2(self.request.data[:2])
                    logger.debug("(%s) autolock:%s", self.request.device.mac_uuid, self.autolock_time)

            elif self.command == BleResponseCode.GET_BATTERY:
                self.battery = int(self.data[0])
                logger.debug(
                    f"({self.request.device.mac_uuid}) power level:{self.battery}, {BATTERY_LEVEL[self.battery]}"
                )

            elif self.command == BleResponseCode.GET_SN:
                self.sn = self.data.decode("ISO8859-1")
                logger.debug("(%s) serial:%s", self.request.device.mac_uuid, self.sn)

            elif self.command == BleResponseCode.GET_MUTE:
                self.mute = bool(self.data[0])
                logger.debug(f"({self.request.device.mac_uuid}) mute:{self.mute}")

            elif self.command == BleResponseCode.SET_WORK_MODE:
                if self.success:
                    self.lock_mode = self.request.data[0]
                    logger.debug(f"({self.request.device.mac_uuid}) workmode:{self.lock_mode}")

            elif self.command == BleResponseCode.UNLOCK:
                logger.info(f"({self.request.device.mac_uuid}) {self.request.device.name} - Unlocked.")

            elif self.command == BleResponseCode.BOLT_LOCK:
                logger.info(f"({self.request.device.mac_uuid}) {self.request.device.name} - Bolt Locked")

            elif self.command == BleResponseCode.LOCK_STATUS:
                self.lock_status = int(self.data[0])
                self.bolt_status = int(self.data[1])
                logger.debug(
                    f"({self.request.device.mac_uuid}) lock:{self.lock_status} |  bolt:{self.bolt_status}"
                )
                if self.length > 16:
                    self.battery = int(self.data[2])
                    self.lock_mode = int(self.data[3])
                    self.mute = bool(self.data[4])
                    logger.debug(
                        f"({self.request.device.mac_uuid}) power level:{self.battery} | mute:{self.mute} | mode:{self.lock_mode}"
                    )

            logger.debug(
                f"({self.request.device.mac_uuid}) Command Completed - {self.command.name}"
            )

        except Exception as e:
            logger.error(
                f"({self.request.device.mac_uuid}) Error updating lock data ({self.command.name}): {e}"
            )

