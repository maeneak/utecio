import asyncio
from bleak import BleakClient

class BleClient:
    def __init__(self, mac_address: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__()
        self._mac_address = mac_address
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._bleakdevice_cb = bleakdevice_callback
        
    async def connect(self):
        attempt = 0
        while attempt < self._max_retries:
            try:
                if not self.client or not self.client.is_connected:
                    ble_device = self._bleakdevice_cb() if self._bleakdevice_cb != None else self._mac_address
                    self.client = BleakClient(ble_device)
                    await self.client.connect()
                    return
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed. Reason: {e}")
                if attempt + 1 < self._max_retries:
                    print(f"Retrying in {self._retry_delay} seconds...")
                    await asyncio.sleep(self._retry_delay)  # Wait before retrying
                else:
                    raise  # Raise the exception if max retries have been exhausted
            attempt += 1
            
    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    async def read_characteristic(self, uuid):
        await self.connect()
        return await self.client.read_gatt_char(uuid)

    async def write_characteristic(self, uuid, data):
        await self.connect()
        await self.client.write_gatt_char(uuid, data)

    async def start_notify(self, uuid, callback):
        await self.connect()
        await self.client.start_notify(uuid, callback)

    async def stop_notify(self, uuid):
        await self.connect()
        await self.client.stop_notify(uuid)


