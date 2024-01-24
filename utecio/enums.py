from enum import Enum


class ULDeviceModel(Enum):
    UL1BT = "UL1-BT"
    Latch5NFC = "Latch-5-NFC"
    Latch5F = "Latch-5-F"


class ULLockBatteryLevel(Enum):
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    ALERT = 0
    DEPLETED = -1


class ULWorkMode(Enum):
    NORMAL = 0
    PASSAGE = 1
    LOCKOUT = 2


class ULLockStatus(Enum):
    OOO = 0
    UNLOCKED = 1
    LOCKED = 2
    NOTAVAILABLE = 255


class BLECommandCode(Enum):
    LOCK_STATUS = 80
    GET_LOCK_STATUS = 81
    GET_BATTERY = 67
    GET_SN = 94
    GET_MUTE = 83
    UNLOCK = 85
    BOLT_LOCK = 86
    SET_LOCK_STATUS = 82
    REBOOT = 23
    DOORSENSOR = 117
    GET_AUTOLOCK = 90
    SET_AUTOLOCK = 89
    SET_WORK_MODE = 160
    ADMIN_LOGIN = 32
    READ_TIME = 65
    WRITE_TIME = 66


class BleResponseCode(Enum):
    LOCK_STATUS = 208
    GET_LOCK_STATUS = 209
    GET_BATTERY = 195
    UNLOCK = 213
    BOLT_LOCK = 214
    SET_LOCK_STATUS = 210
    GET_SN = 222
    GET_MUTE = 211
    DOORSENSOR = 245
    SET_AUTOLOCK = 217
    GET_AUTOLOCK = 218
    SET_WORK_MODE = 32
    ADMIN_LOGIN = 160
    READ_TIME = 193
    WRITE_TIME = 194


class ULServiceUUID(Enum):
    LOCK = "00007200-0000-1000-8000-00805f9b34fb"
    DATA = "00007201-0000-1000-8000-00805f9b34fb"


class ULKeyUUID(Enum):
    STATIC = "00007220-0000-1000-8000-00805f9b34fb"
    MD5 = "00007223-0000-1000-8000-00805f9b34fb"
    ECC = "00007221-0000-1000-8000-00805f9b34fb"


class BleRequestSchedule(Enum):
    IMMEDIATE = 0
    NEXT_RUN = 1
