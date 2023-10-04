import asyncio
from __init__ import logger
from bleak import BleakClient, BleakScanner
from enums import ServiceUUID

class UtecBleClient:
    def __init__(self, mac_address: str, wurx_address: str = None, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__()
        self.mac_address = mac_address
        self.wurx_address = wurx_address
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._bleakdevice_cb = bleakdevice_callback
        self.client = None

    async def wakeup_client(self):
        if not self.wurx_address:
            return

        try:
            logger.debug(f"({self.wurx_address}) Wakeing up {self.mac_address}...")
            async with BleakClient(self.wurx_address) as client:
                logger.debug(f"({self.wurx_address}) {self.mac_address} is awake.")
        except Exception as e:
            return

    async def connect(self):
        attempt = 0
        while attempt < self.max_retries:
            try:
                if not self.client or not self.client.is_connected:
                    ble_device = self._bleakdevice_cb() if self._bleakdevice_cb != None else self.mac_address
                    self.client = BleakClient(ble_device)
                    logger.debug(f"({self.mac_address}) Connecting...")

                    if attempt == 1:
                        asyncio.create_task(self.wakeup_client())
                        await asyncio.sleep(1)

                    await self.client.connect()
                    logger.debug(f"({self.mac_address}) Connected.")
                    
                    await self.on_connected()
                    return
            except NotImplementedError as e:
                logger.error(e)
                raise
            except Exception as e:
                logger.warning(f"({self.mac_address}) Connection failed ({attempt + 1}). {e}")
                if attempt + 1 < self.max_retries:
                    logger.info(f"({self.mac_address}) Waiting {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"({self.mac_address}) Failed to connect.")
                    raise 
            attempt += 1

    async def on_connected(self):
        return
    
    async def on_disconnected(self):
        logger.debug(f"({self.mac_address}) Disconnected.")
        return

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    async def read_characteristic(self, uuid):
        await self.connect()
        return await self.client.read_gatt_char(uuid)

    async def write_characteristic(self, uuid, data):
        await self.connect()
        await self.client.write_gatt_char(uuid, data)

    async def find_characteristic(self, uuid):
        await self.connect()
        result = self.client.services.get_characteristic(uuid)
        return result

    async def start_notify(self, uuid, callback):
        await self.connect()
        await self.client.start_notify(uuid, callback)

    async def stop_notify(self, uuid):
        await self.connect()
        await self.client.stop_notify(uuid)


