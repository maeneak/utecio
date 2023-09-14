
from lock import ULBleLock

class UL1BT(ULBleLock):
    def __init__(self, device_name: str, username: str, password: str, mac_address: str, max_retries: float = 3, retry_delay: float = 0.5, bleakdevice_callback: callable = None):
        super().__init__(device_name, username, password, mac_address, max_retries, retry_delay, bleakdevice_callback)
        