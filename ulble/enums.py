from enum import Enum


class RequestCommand(Enum):
    LOCK_STATUS = 80
    BATTERY = 67
    UNLOCK = 85
    
class RequestResponse(Enum):
    LOCK_STATUS = 208
    BATTERY = 195

class UUID(Enum):
    WRITE_DATA = "00007201-0000-1000-8000-00805f9b34fb"
    READ_KEY_MD5 = "00007223-0000-1000-8000-00805f9b34fb"