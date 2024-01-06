from .enums import ULDeviceModel


class BLEDeviceCapability:
    lock: bool
    door: bool
    keypad: bool
    fingprinter: bool
    doublefp: bool
    bluetooth: bool
    rfid: bool
    rfid_once: bool
    rfid_twice: bool
    autobolt: bool
    autolock: bool
    autounlock: bool
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
    moreadmin: bool
    morepwd: bool
    timelimit: bool
    morelanguage: bool
    needregristerpwd: bool
    locklocal: bool
    havesn: bool
    clone: bool
    customuserid: bool
    bt264: bool = True
    keepalive: bool
    passageautolock: bool
    doorsensor: bool
    zwave: bool
    needreadmodel: bool
    needsycbuser: bool
    bt_close: bool
    singlelatchboltmortic: bool
    smartphone_nfc: bool
    update_2642: bool
    isautodirection: bool
    ishomekit: bool
    isyeeuu: bool
    secondsarray = []
    mtimearray = []


class Latch5F(BLEDeviceCapability):
    bluetooth = True
    autolock = True
    update_wifi = True
    alerts = True
    mutemode = True
    doublefp = True
    keypad = True
    fingprinter = True
    needregristerpwd = True
    havesn = True
    moreadmin = True
    timelimit = True
    passage = True
    lockout = True
    bt264 = True
    keepalive = True
    passageautolock = True
    singlelatchboltmortic = True
    smartphone_nfc = True
    bt_close = True


class Latch5NFC(BLEDeviceCapability):
    bluetooth = True
    autolock = True
    update_wifi = True
    alerts = True
    mutemode = True
    rfid = True
    rfid_twice = True
    keypad = True
    needregristerpwd = True
    havesn = True
    moreadmin = True
    timelimit = True
    passage = True
    lockout = True
    bt264 = True
    keepalive = True
    passageautolock = True
    singlelatchboltmortic = True
    smartphone_nfc = True
    bt_close = True


class UL1BT(BLEDeviceCapability):
    bluetooth = True
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
    havesn = True
    direction = True
    keepalive = True
    singlelatchboltmortic = True


class GenericLock(BLEDeviceCapability):
    bluetooth = True
    autolock = True
    mutemode = True
    havesn = True
    timelimit = True
    passage = True
    lockout = True
    bt264 = True
    keepalive = True
    bt_close = True


defined_capabilities: dict[str, BLEDeviceCapability] = {
    ULDeviceModel.Latch5F.value: Latch5F(),
    ULDeviceModel.Latch5NFC.value: Latch5NFC(),
    ULDeviceModel.UL1BT.value: UL1BT(),
}
