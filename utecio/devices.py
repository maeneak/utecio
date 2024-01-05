from .enums import ULDeviceModel


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
    bt264: bool = True
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


class Latch5F(BLEDeviceCapability):
    model = ULDeviceModel.Latch5F.value
    bluetooth = True
    autolock = True
    update_wifi = True
    alerts = True
    mutemode = True
    doubleFP = True
    keypad = True
    fingprinter = True
    needRegristerPWD = True
    haveSN = True
    moreAdmin = True
    timeLimit = True
    passage = True
    lockout = True
    bt264 = True
    keepAlive = True
    passageAutoLock = True
    singlelatchboltmortic = True
    smartphone_nfc = True
    bt_close = True


class Latch5NFC(BLEDeviceCapability):
    model = ULDeviceModel.Latch5NFC.value
    bluetooth = True
    autolock = True
    update_wifi = True
    alerts = True
    mutemode = True
    rfid = True
    rfid_twice = True
    keypad = True
    needRegristerPWD = True
    haveSN = True
    moreAdmin = True
    timeLimit = True
    passage = True
    lockout = True
    bt264 = True
    keepAlive = True
    passageAutoLock = True
    singlelatchboltmortic = True
    smartphone_nfc = True
    bt_close = True


class UL1BT(BLEDeviceCapability):
    bluetooth = True
    model = ULDeviceModel.UL1BT.value
    rfid = True
    rfid_twice = True
    fingprinter = True
    autobolt = True
    update_ota = True
    update_oad = True
    alerts = True
    shakeopen = True
    mutemode = True
    passage = True
    lockout = True
    haveSN = True
    direction = True
    keepAlive = True
    singlelatchboltmortic = True


defined_capabilities: dict[str, BLEDeviceCapability] = {
    ULDeviceModel.Latch5F.value: Latch5F(),
    ULDeviceModel.Latch5NFC.value: Latch5NFC(),
    ULDeviceModel.UL1BT.value: UL1BT(),
}
