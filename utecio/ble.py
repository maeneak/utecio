import asyncio
from __init__ import logger
from bleak import BleakClient
from enums import ServiceUUID

class UtecBleClient:
    def __init__(self, mac_address: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__()
        self._mac_address = mac_address
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._bleakdevice_cb = bleakdevice_callback
        self.client = None
        
    async def connect(self):
        attempt = 0
        while attempt < self._max_retries:
            try:
                if not self.client or not self.client.is_connected:
                    ble_device = self._bleakdevice_cb() if self._bleakdevice_cb != None else self._mac_address
                    self.client = BleakClient(ble_device)
                    await self.client.connect()
                    await self.on_connected()
                    return
            except NotImplementedError as e:
                logger.error(e)
                raise
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed. Reason: {e}")
                if attempt + 1 < self._max_retries:
                    logger.info(f"Retrying in {self._retry_delay} seconds...")
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error(f"Max retries reached. Failed to connect to device {self._mac_address}.")
                    raise 
            attempt += 1

    async def on_connected(self):
        return
    
    async def on_disconnected(self):
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


