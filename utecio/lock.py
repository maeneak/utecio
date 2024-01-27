import datetime

from bleak.backends.device import BLEDevice

from . import logger
from .device import BleRequest, UtecBleDevice
from .enums import BLECommandCode, DeviceLockWorkMode
from .util import to_byte_array


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
            self._add_request(BleRequest(command=BLECommandCode.LOCK_STATUS))

        self._add_request(
            BleRequest(
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
            self._add_request(BleRequest(command=BLECommandCode.LOCK_STATUS))

        self._add_request(
            BleRequest(
                command=BLECommandCode.BOLT_LOCK,
                uid=self.uid,
                password=self.password,
                notify=True,
            ),
            priority=True,
        )

        return await self._process_queue(device)


    async def async_reboot(self, device: BLEDevice) -> bool:
        self._add_request(BleRequest(command=BLECommandCode.REBOOT))
        return await self._process_queue(device)


    async def async_set_workmode(self, mode: DeviceLockWorkMode, device: BLEDevice):
        self._add_request(BleRequest(command=BLECommandCode.ADMIN_LOGIN, uid=self.uid, password=self.password))
        if self.capabilities.bt264:
            self._add_request(BleRequest(command=BLECommandCode.SET_LOCK_STATUS, data=bytes([mode.value])))
        else:
            self._add_request(BleRequest(command=BLECommandCode.SET_WORK_MODE, data=bytes([mode.value])))

        return await self._process_queue(device)


    async def async_set_autolock(self, seconds: int, device: BLEDevice):
        if self.capabilities.autolock:
            self._add_request(BleRequest(command=BLECommandCode.ADMIN_LOGIN, uid=self.uid, password=self.password))
            self._add_request(
                BleRequest(
                    command=BLECommandCode.SET_AUTOLOCK, 
                    data=to_byte_array(seconds, 2) + bytes([0])
                )
            )
        return await self._process_queue(device)


    async def async_update_status(self, device: BLEDevice):
        logger.debug("(%s) %s - Updating lock data...", self.mac_uuid, self.name)
        self._add_request(BleRequest(command=BLECommandCode.ADMIN_LOGIN, uid=self.uid, password=self.password))
        self._add_request(BleRequest(command=BLECommandCode.LOCK_STATUS))
        if not self.capabilities.bt264:
            self._add_request(BleRequest(command=BLECommandCode.GET_BATTERY))
            self._add_request(BleRequest(command=BLECommandCode.GET_MUTE))
        if self.capabilities.autolock:
            self._add_request(BleRequest(command=BLECommandCode.GET_AUTOLOCK))

        # self.add_request(BleRequest(command=BLECommandCode.READ_TIME))

        return await self._process_queue(device)
