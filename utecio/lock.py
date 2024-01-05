import datetime

from . import logger
from .constants import BLE_RETRY_DELAY_DEF, BLE_RETRY_MAX_DEF
from .device import BleRequest, UtecBleDevice
from .enums import BLECommandCode


class UtecBleLock(UtecBleDevice):
    def __init__(
        self,
        uid: str,
        password: str,
        mac_uuid: str,
        device_name: str,
        wurx_uuid: str = "",
        max_retries: int = BLE_RETRY_MAX_DEF,
        retry_delay: float = BLE_RETRY_DELAY_DEF,
        device_model: str = "",
    ):
        super().__init__(
            uid=uid,
            password=password,
            mac_uuid=mac_uuid,
            wurx_uuid=wurx_uuid,
            device_name=device_name,
            max_retries=max_retries,
            retry_delay=retry_delay,
            device_model=device_model,
        )

        self.lock_status: int = -1
        self.bolt_status: int = -1
        self.battery: int = -1
        self.work_mode: int = -1
        self.mute: bool = False
        self.sn: str
        self.calendar: datetime.datetime

    async def unlock(self):
        try:
            self.add_request(BleRequest(command=BLECommandCode.LOCK_STATUS))
            self.add_request(
                BleRequest(
                    command=BLECommandCode.UNLOCK,
                    uid=self.uid,
                    password=self.password,
                    notify=True,
                ),
                priority=True,
            )

            await self.process_queue()
            # logger.info(f"({self.mac_uuid}) Commands Completed.")

        except Exception as e:
            logger.error(f"({self.mac_uuid}) Error while sending command: {e}")

    async def lock(self):
        try:
            self.add_request(BleRequest(command=BLECommandCode.LOCK_STATUS))
            self.add_request(
                BleRequest(
                    command=BLECommandCode.BOLT_LOCK,
                    uid=self.uid,
                    password=self.password,
                    notify=True,
                ),
                priority=True,
            )

            await self.process_queue()
            # logger.info(f"({self.mac_uuid}) Lock Bolt command sent successfully.")

        except Exception as e:
            logger.error(f"({self.mac_uuid}) Error while sending lock command: {e}")

    async def reboot(self):
        try:
            self.add_request(BleRequest(command=BLECommandCode.REBOOT))
            await self.process_queue()

        except Exception as e:
            logger.error(f"({self.mac_uuid}) Error while sending lock command: {e}")

    async def update(self):
        try:
            logger.info(f"({self.mac_uuid}) {self.name} - Updating lock data...")
            self.add_request(BleRequest(command=BLECommandCode.LOCK_STATUS))
            if not self.capabilities.bt264:
                self.add_request(BleRequest(command=BLECommandCode.GET_BATTERY))
                self.add_request(
                    BleRequest(command=BLECommandCode.GET_SN, data=bytearray([16]))
                )
                self.add_request(BleRequest(command=BLECommandCode.GET_MUTE))

            await self.process_queue()
            logger.info(f"({self.mac_uuid}) {self.name} - Lock data updated.")

        except Exception as e:
            logger.error(f"({self.mac_uuid}) Error during update request: {e}")
