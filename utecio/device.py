import asyncio
import datetime
from collections.abc import Awaitable, Callable
from typing import Any

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from . import logger
from .ble import BleDeviceKey, BleRequest, BleResponse
from .constants import (
    BATTERY_LEVEL,
    BLE_RETRY_DELAY_DEF,
    BLE_RETRY_MAX_DEF,
    BOLT_STATUS,
    LOCK_MODE,
)
from .devices import BLEDeviceCapability, GenericLock, defined_capabilities
from .enums import BleResponseCode
from .util import DeviceNotAvailable, decode_password, bytes_to_int2, date_from_4bytes


class AddressProfile:
    def __init__(self, json_config: dict[str, Any]) -> None:
        self.id = json_config["id"]
        self.name = json_config["name"]
        self.address = json_config["address"]
        self.latitude = json_config["lat"]
        self.longitude = json_config["lng"]
        self.timezone = json_config["timezone_name"]
        self.rooms: list = []
        self.devices: list = []


class RoomProfile:
    def __init__(self, json_config: dict[str, Any], address: AddressProfile) -> None:
        self.id = json_config["id"]
        self.name = json_config["name"]
        self.address = address
        self.devices: list = []


class UtecBleDevice:
    def __init__(
        self,
        uid: str,
        password: str,
        mac_uuid: Any,
        device_name: str,
        wurx_uuid: Any = None,
        max_retries: int = BLE_RETRY_MAX_DEF,
        retry_delay: float = BLE_RETRY_DELAY_DEF,
        device_model: str = "",
    ):
        self.mac_uuid = mac_uuid
        self.wurx_uuid = wurx_uuid
        self.uid = uid
        self.password: str = password
        self.name = device_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.model: str = device_model
        self.capabilities: BLEDeviceCapability | Any = defined_capabilities.get(
            device_model, GenericLock
        )
        self._request_queue: list[BleRequest] = []
        self.room: RoomProfile
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

    async def update(self):
        pass

    def add_request(self, request: "BleRequest", priority: bool = False):
        if priority:
            self._request_queue.insert(0, request)
        else:
            self._request_queue.append(request)
        return self._request_queue

    async def process_queue(self) -> bool:
        if len(self._request_queue) < 1:
            return False
        self.is_busy = True
        using_bledevice = False
        for attempt in range(self.max_retries):
            try:
                device = await self._async_get_bleak_device(self.mac_uuid)
                using_bledevice = device is None or device is BLEDevice
                # if bledevice is none call the wake-up receiver before continue
                if device is None and self.wurx_uuid:
                    if not await self.wakeup_device():
                        break
                    else:
                        device = await self._async_get_bleak_device(self.mac_uuid)
                elif device is None:
                    raise DeviceNotAvailable(
                        "Device not currently discoverable or out of range."
                    )

                async with BleakClient(device) as client:
                    aes_key = await BleDeviceKey.get_aes_key(client=client)
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
                            await self._send_request(client, request)
                            if request.notify:
                                await self._process_response(request.response)

                    self.is_busy = False
                    self._request_queue.clear()
                    return True
            except DeviceNotAvailable as e:
                logger.error("(%s) %s - %s", self.mac_uuid, self.name, e)
                break
            except Exception as e:
                if attempt == 0 and self.wurx_uuid and not using_bledevice:
                    await self.wakeup_device()
                elif attempt + 1 == self.max_retries:
                    logger.error(
                        "(%s) Failed to connect with error: %s", self.mac_uuid, e
                    )
                    break
                else:
                    logger.debug(
                        "(%s) Connection attempt %s failed with error: %s",
                        self.mac_uuid,
                        attempt + 1,
                        e,
                    )

                await asyncio.sleep(self.retry_delay)

        self.is_busy = False
        return False

    async def _send_request(self, client: BleakClient, request: BleRequest):
        if request.notify:
            await client.start_notify(
                request.uuid, request.response.receive_write_response_callback
            )
            await client.write_gatt_char(
                request.uuid, request.encrypted_package(request.aes_key)
            )
            await request.response.response_completed.wait()
            await client.stop_notify(request.uuid)
        else:
            await client.write_gatt_char(
                request.uuid, request.encrypted_package(request.aes_key)
            )

    async def wakeup_device(self):
        if not self.wurx_uuid:
            return False

        for attempt in range(self.max_retries):
            try:
                device = await self._async_get_bleak_device(self.wurx_uuid)
                if device is None:
                    raise DeviceNotAvailable(
                        f"Wake-up Reciever {self.wurx_uuid} not currently discoverable or out of range."
                    )
                async with BleakClient(device) as wurx_client:
                    logger.debug(
                        f"({self.mac_uuid}) Wake-up reciever {self.wurx_uuid} connected."
                    )

                return True
            except DeviceNotAvailable as e:
                logger.error(f"({self.mac_uuid}) {self.name} - {e}")
                return False
            except Exception as e:
                logger.debug(
                    f"({self.mac_uuid}) Wake-up reciever {self.wurx_uuid} connection attempt {attempt + 1} failed. {e}"
                )
                if attempt + 1 == self.max_retries:
                    logger.error(
                        f"({self.mac_uuid}) Failed to connect to Wake-up reciever {self.wurx_uuid}. {e}"
                    )

                await asyncio.sleep(self.retry_delay)

        return False

    async def _async_get_bleak_device(self, device: str) -> BLEDevice | str:
        return (
            device
            if not callable(self.async_device_callback)
            else await self.async_device_callback(device)
        )

    async def _process_response(self, response: BleResponse):
        try:
            logger.debug(
                "(%s) Response %s (%s): %s",
                self.mac_uuid,
                response.command.name,
                "Success" if response.success else "Failed",
                response.package.hex(),
            )
            if response.command == BleResponseCode.GET_LOCK_STATUS:
                self.lock_mode = int(response.data[0])
                self.bolt_status = int(response.data[1])
                logger.debug(
                    f"({self.mac_uuid}) lock:{self.lock_mode} ({LOCK_MODE[self.lock_mode]}) |  bolt:{self.bolt_status} ({BOLT_STATUS[self.bolt_status]})"
                )
            elif response.command == BleResponseCode.SET_LOCK_STATUS:
                self.lock_mode = response.data[0]
                logger.debug(f"({self.mac_uuid}) workmode:{self.lock_mode}")
            elif response.command == BleResponseCode.GET_BATTERY:
                self.battery = int(response.data[0])
                logger.debug(
                    f"({self.mac_uuid}) power level:{self.battery}, {BATTERY_LEVEL[self.battery]}"
                )
            elif response.command == BleResponseCode.GET_AUTOLOCK:
                self.autolock_time = bytes_to_int2(response.data[:2])
                logger.debug("(%s) autolock:%s", self.mac_uuid, self.autolock_time)
            elif response.command == BleResponseCode.SET_AUTOLOCK:
                if response.success:
                    self.autolock_time = bytes_to_int2(response.request.data[:2])
                    logger.debug("(%s) autolock:%s", self.mac_uuid, self.autolock_time)
            elif response.command == BleResponseCode.GET_BATTERY:
                self.battery = int(response.data[0])
                logger.debug(
                    f"({self.mac_uuid}) power level:{self.battery}, {BATTERY_LEVEL[self.battery]}"
                )
            elif response.command == BleResponseCode.GET_SN:
                self.sn = response.data.decode("ISO8859-1")
                logger.debug("(%s) serial:%s", self.mac_uuid, self.sn)
            elif response.command == BleResponseCode.GET_MUTE:
                self.mute = bool(response.data[0])
                logger.debug(f"({self.mac_uuid}) mute:{self.mute}")
            # elif response.command == BleResponseCode.READ_TIME:
            #     device_time = date_from_4bytes(response.data)
            #     self.device_time_offset = device_time - datetime.datetime.utcnow()
            #     logger.debug(f"({self.mac_uuid}) time offset:{self.device_time_offset}")
            elif response.command == BleResponseCode.SET_WORK_MODE:
                if response.success:
                    self.lock_mode = response.request.data[0]
                    logger.debug(f"({self.mac_uuid}) workmode:{self.lock_mode}")
            elif response.command == BleResponseCode.UNLOCK:
                # self.mute = bool(response.data[1])
                logger.info(f"({self.mac_uuid}) {self.name} - Unlocked.")
            elif response.command == BleResponseCode.BOLT_LOCK:
                # self.mute = bool(response.data[1])
                logger.info(f"({self.mac_uuid}) {self.name} - Bolt Locked")
            elif response.command == BleResponseCode.LOCK_STATUS:
                self.lock_status = int(response.data[0])
                self.bolt_status = int(response.data[1])
                logger.debug(
                    f"({self.mac_uuid}) lock:{self.lock_status} |  bolt:{self.bolt_status}"
                )
                if response.length > 16:
                    self.battery = int(response.data[2])
                    self.lock_mode = int(response.data[3])
                    self.mute = bool(response.data[4])
                    # self.calendar = date_from_4bytes(response.data[6:10])
                    # self.sn = bytes_to_ascii(response.data[10:26])
                    logger.debug(
                        f"({self.mac_uuid}) power level:{self.battery} | mute:{self.mute} | mode:{self.lock_mode}"
                    )

            logger.debug(
                f"({self.mac_uuid}) Command Completed - {response.command.name}"
            )

        except Exception as e:
            logger.error(
                f"({self.mac_uuid}) Error updating lock data ({response.command.name}): {e}"
            )
