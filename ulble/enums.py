from enum import Enum

class ULDeviceModel(Enum):
    UL1BT = "UL1-BT"

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
    GET_LOCK_STATUS = 81
    GET_BATTERY = 67
    GET_SN = 94
    GET_MUTE = 83
    UNLOCK = 85
    BOLT_LOCK = 86
    SET_LOCK_STATUS = 82
    
class RequestResponse(Enum):
    LOCK_STATUS = 209
    BATTERY = 195
    BOLT_LOCK = 214
    SN = 222
    MUTE = 211

class ServiceUUID(Enum):
    LOCK = "00007200-0000-1000-8000-00805f9b34fb"
    DATA = "00007201-0000-1000-8000-00805f9b34fb"
    READ_KEY = "00007220-0000-1000-8000-00805f9b34fb"
    READ_KEY_MD5 = "00007223-0000-1000-8000-00805f9b34fb"
    
class KeyUUID(Enum):
    STATIC = "00007220-0000-1000-8000-00805f9b34fb"
    MD5 = "00007223-0000-1000-8000-00805f9b34fb"
    ECC = "00007221-0000-1000-8000-00805f9b34fb"
