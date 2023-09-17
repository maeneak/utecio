from enum import Enum

class BatteryLevel(Enum):
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    ALERT = 0
    DEPLETED = -1

class LockMode(Enum):
    NORMAL = 0
    PASSAGE = 1
    LOCKOUT = 2
    
class BoltMode(Enum):
    UNLOCKED = 0
    LOCKED = 1

class BLECommand(Enum):
    LOCK_STATUS = 80
    BATTERY = 67
    UNLOCK = 85
    BOLT_LOCK = 86
    
class RequestResponse(Enum):
    LOCK_STATUS = 208
    BATTERY = 195
    BOLT_LOCK = 214

class UUID(Enum):
    WRITE_DATA = "00007201-0000-1000-8000-00805f9b34fb"
    READ_KEY = "00007220-0000-1000-8000-00805f9b34fb"
    READ_KEY_MD5 = "00007223-0000-1000-8000-00805f9b34fb"