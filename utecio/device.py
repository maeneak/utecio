import asyncio

from __init__ import logger
from bleak import BleakClient
from Crypto.Cipher import AES
from enums import BleResponseCode
from constants import BLE_RETRY_DELAY_DEF, BLE_RETRY_MAX_DEF, LOCK_MODE, LOCK_STATUS, BATTERY_LEVEL
from ble import BleDeviceKey, BleRequest, BleResponse

class UtecBleDevice:
    def __init__(self, uid: str, password: str, mac_uuid: any, device_name: str, wurx_uuid: any = None, max_retries: float = BLE_RETRY_MAX_DEF, retry_delay: float = BLE_RETRY_DELAY_DEF):
        self.mac_address = mac_uuid
        self.wurx_address = wurx_uuid
        self.uid = uid
        self.password:str = password
        self.name = device_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.capabilities = BLEDeviceCapability()
        self.request_queue: list[BleRequest] = []

    async def update(self):
        return

    def queue_request(self, request: 'BleRequest'):
        self.request_queue.append(request)
        return self.request_queue
 
    async def process_queue(self):
        for attempt in range(self.max_retries):
            try:
                async with BleakClient(self.mac_address) as client:
                    aes_key = await BleDeviceKey.get_aes_key(client=client)
                    for request in self.request_queue:
                        request.aes_key = aes_key
                        request.mac_uuid = self.mac_address
                        await self._send_request(client, request)
                        if request.notify:
                            await self._process_response(request.response)

                    self.request_queue.clear()
                    return
            except Exception as e:
                logger.warning(f"({self.mac_address}) Connection attempt {attempt + 1} failed with error: {e}")
                if attempt == 0: # connect to master and wake up slave
                    logger.debug(f"({self.wurx_address}) Wakeing up {self.mac_address}...")
                    async with BleakClient(self.wurx_address) as wurx_client:
                        logger.debug(f"({wurx_client.address}) {self.mac_address} is awake.")
                elif attempt + 1 == self.max_retries:
                    logger.error(f"({self.mac_address}) Failed to connect with error: {e}")
                
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
            logger.debug(f"({self.mac_address}) Response {response.command.name}: {response.package.hex()}")
            if response.command == BleResponseCode.GET_LOCK_STATUS:
                self.lock_status = int(response.data[1])
                self.bolt_status = int(response.data[2])
                logger.debug(f"({self.mac_address}) lock:{self.lock_status}, {LOCK_MODE[self.lock_status]} |  bolt:{self.bolt_status}, {LOCK_STATUS[self.bolt_status]}")
            elif response.command == BleResponseCode.GET_BATTERY:
                self.battery = int(response.data[1])
                logger.debug(f"({self.mac_address}) power level:{self.battery}, {BATTERY_LEVEL[self.battery]}")
            elif response.command == BleResponseCode.GET_SN:
                self.sn = response.data.decode('ISO8859-1')
                logger.debug(f"({self.mac_address}) serial:{self.sn}")
            elif response.command == BleResponseCode.GET_MUTE:
                self.mute = bool(response.data[1])
                logger.debug(f"({self.mac_address}) sound:{self.mute}")
            elif response.command == BleResponseCode.LOCK_STATUS:
                self.lock_status = int(response.data[1])
                self.bolt_status = int(response.data[2])
                self.battery = int(response.data[3])
                self.work_mode = bool(response.data[4])
                self.mute = bool(response.data[5])
                #self.calendar = date_from_4bytes(response.data[6:10])
                #self.sn = bytes_to_ascii(response.data[10:26])
                logger.debug(f"({self.mac_address}) lock:{self.lock_status} |  bolt:{self.bolt_status} | power level:{self.battery} | sound:{self.mute}")

        except Exception as e:
            logger.error(f"({self.mac_address}) Error updating lock data ({response.command.name}): {e}")

class BLEDeviceCapability:
    lock: bool
    door: bool
    keypad: bool
    fingprinter: bool
    doubleFP: bool
    bluetooth: bool
    rfid: bool
    rfid_once: bool
    rfid_twice: bool
    autobolt: bool
    autolock: bool
    autoUnlock: bool
    direction: bool
    update_ota: bool
    update_oad: bool
    update_wifi: bool
    alerts: bool
    mutemode: bool
    passage: bool
    lockout: bool
    manual: bool
    shakeopen: bool
    moreAdmin: bool
    morePWD: bool
    timeLimit: bool
    moreLanguage: bool
    needRegristerPWD: bool
    lockLocal: bool
    haveSN: bool
    clone: bool
    customUserid: bool
    bt2640: bool
    keepAlive: bool
    passageAutoLock: bool
    doorsensor: bool
    zwave: bool
    needReadModel: bool
    needSycbUser: bool
    bt_close: bool
    singlelatchboltmortic: bool
    smartphone_nfc: bool
    update_2642: bool
    isAutoDirection: bool
    isHomeKit: bool
    isYeeuu: bool
    secondsArray = []
    mTimeArray = []

