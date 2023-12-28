import asyncio
from typing import Any


from .. import logger
from bleak import BleakClient
from bleak.backends.device import BLEDevice
from ..enums import BleResponseCode
from ..constants import BLE_RETRY_DELAY_DEF, BLE_RETRY_MAX_DEF, LOCK_MODE, BOLT_STATUS, BATTERY_LEVEL
from .devices import BLEDeviceCapability, defined_capabilities
from .ble import BleDeviceKey, BleRequest, BleResponse
from ..util import decode_password

class AddressProfile:
    def __init__(self, json_config: dict[str, Any]) -> None:
        self.id = json_config['id']
        self.name = json_config['name']
        self.address = json_config['address']
        self.latitude = json_config['lat']
        self.longitude = json_config['lng']
        self.timezone = json_config['timezone_name']
        self.rooms: list = []
        self.devices: list = []

class RoomProfile:
    def __init__(self, json_config: dict[str, Any], address: AddressProfile) -> None:
        self.id = json_config['id']
        self.name = json_config['name']
        self.address = address
        self.devices: list = []

class UtecBleDevice:
    def __init__(self, uid: str, password: str, mac_uuid: Any, device_name: str, wurx_uuid: Any = None, max_retries: int = BLE_RETRY_MAX_DEF, retry_delay: float = BLE_RETRY_DELAY_DEF, device_model: str = ""):
        self.mac_uuid = mac_uuid
        self.wurx_uuid = wurx_uuid
        self.uid = uid
        self.password:str = password
        self.name = device_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.model: str = device_model
        self.capabilities: BLEDeviceCapability | Any = defined_capabilities.get(device_model)
        self._request_queue: list[BleRequest] = []
        self.room: RoomProfile
        self.config: dict[str, Any]
        

    @classmethod
    def from_json(cls, json_config: dict[str, Any]):
        new_device = cls(
            device_name = json_config['name'], 
            uid = str(json_config['user']['uid']), 
            password = decode_password(json_config['user']['password']), 
            mac_uuid = json_config['uuid'],
            device_model = json_config['model'])
        if json_config['params']['extend_ble']:
            new_device.wurx_uuid = json_config['params']['extend_ble']
        new_device.sn = json_config['params']['serialnumber']
        new_device.model = json_config['model']
        new_device.config = json_config

        return new_device

    async def update(self):
        pass

    def add_request(self, request: 'BleRequest', priority: bool = False):
        if priority:
            self._request_queue.insert(0, request)
        else:
            self._request_queue.append(request)
        return self._request_queue
 
    async def process_queue(self, device: BLEDevice | str = None) -> bool:
        if len(self._request_queue) < 1:
            return False
        
        for attempt in range(self.max_retries):
            try:
                async with BleakClient(self.mac_uuid if not device else device) as client:
                    aes_key = await BleDeviceKey.get_aes_key(client=client)
                    for request in self._request_queue:
                        if not request.sent or not request.response.completed:
                            logger.debug(f"({self.mac_uuid}) Sending command - {request.command.name}")
                            request.aes_key = aes_key
                            request.mac_uuid = self.mac_uuid
                            request.sent = True
                            await self._send_request(client, request)
                            if request.notify:
                                await self._process_response(request.response)

                    self._request_queue.clear()
                    return True
            except Exception as e:
                if attempt == 0:
                    await self.wakeup_device()
                elif attempt + 1 == self.max_retries:
                    logger.error(f"({self.mac_uuid}) Failed to connect with error: {e}")
                    return False
                else:
                    logger.debug(f"({self.mac_uuid}) Connection attempt {attempt + 1} failed with error: {e}")
                
                await asyncio.sleep(self.retry_delay)
        
        return False

    async def wakeup_device(self):
        if not self.wurx_uuid:
            return
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"({self.wurx_uuid}) Wakeing up {self.mac_uuid}...")
                async with BleakClient(self.wurx_uuid) as wurx_client:
                    logger.debug(f"({wurx_client.address}) {self.mac_uuid} is awake.")

                return
            except Exception as e:
                logger.warning(f"({self.wurx_uuid}) Connection attempt {attempt + 1} failed with error: {e}")
                if attempt + 1 == self.max_retries:
                    logger.error(f"({self.wurx_uuid}) Failed to connect with error: {e}")
                
                await asyncio.sleep(self.retry_delay)

    async def _send_request(self, client: BleakClient, request: BleRequest):
                    if request.notify:
                        await client.start_notify(request.uuid, request.response._receive_write_response)
                        await client.write_gatt_char(request.uuid, request.encrypted_package(request.aes_key))
                        await request.response.response_completed.wait()
                        await client.stop_notify(request.uuid)
                    else:
                        await client.write_gatt_char(request.uuid, request.encrypted_package(request.aes_key))

    async def _process_response(self, response: BleResponse):
        try:
            logger.debug(f"({self.mac_uuid}) Response {response.command.name}: {response.package.hex()}")
            if response.command == BleResponseCode.GET_LOCK_STATUS:
                self.lock_mode = int(response.data[1])
                self.bolt_status = int(response.data[2])
                logger.debug(f"({self.mac_uuid}) lock:{self.lock_mode} ({LOCK_MODE[self.lock_mode]}) |  bolt:{self.bolt_status} ({BOLT_STATUS[self.bolt_status]})")
            elif response.command == BleResponseCode.GET_BATTERY:
                self.battery = int(response.data[1])
                logger.debug(f"({self.mac_uuid}) power level:{self.battery}, {BATTERY_LEVEL[self.battery]}")
            elif response.command == BleResponseCode.GET_SN:
                self.sn = response.data.decode('ISO8859-1')
                logger.debug(f"({self.mac_uuid}) serial:{self.sn}")
            elif response.command == BleResponseCode.GET_MUTE:
                self.mute = bool(response.data[1])
                logger.debug(f"({self.mac_uuid}) mute:{self.mute}")
            elif response.command == BleResponseCode.UNLOCK:
                #self.mute = bool(response.data[1])
                logger.debug(f"({self.mac_uuid}) Unlocked")
            elif response.command == BleResponseCode.BOLT_LOCK:
                #self.mute = bool(response.data[1])
                logger.debug(f"({self.mac_uuid}) Bolt Locked")
            elif response.command == BleResponseCode.LOCK_STATUS:
                self.lock_mode = int(response.data[1])
                self.bolt_status = int(response.data[2])
                logger.debug(f"({self.mac_uuid}) lock:{self.lock_mode} |  bolt:{self.bolt_status}")
                if response.length > 16:
                    self.battery = int(response.data[3])
                    self.lock_mode = int(response.data[4])
                    self.mute = bool(response.data[5])
                    #self.calendar = date_from_4bytes(response.data[6:10])
                    #self.sn = bytes_to_ascii(response.data[10:26])
                    logger.debug(f"({self.mac_uuid}) power level:{self.battery} | mute:{self.mute}")
            
            logger.info(f"({self.mac_uuid}) Command Completed - {response.command.name}")

        except Exception as e:
            logger.error(f"({self.mac_uuid}) Error updating lock data ({response.command.name}): {e}")
