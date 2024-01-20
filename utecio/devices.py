from .enums import ULDeviceModel


class BLEDeviceCapability:
    lock: bool = False
    door: bool = False
    keypad: bool = False
    fingprinter: bool = False
    doublefp: bool = False
    bluetooth: bool = False
    rfid: bool = False
    rfid_once: bool = False
    rfid_twice: bool = False
    autobolt: bool = False
    autolock: bool = False
    autounlock: bool = False
    direction: bool = False
    update_ota: bool = False
    update_oad: bool = False
    update_wifi: bool = False
    alerts: bool = False
    mutemode: bool = False
    passage: bool = False
    lockout: bool = False
    manual: bool = False
    shakeopen: bool = False
    moreadmin: bool = False
    morepwd: bool = False
    timelimit: bool = False
    morelanguage: bool = False
    needregristerpwd: bool = False
    locklocal: bool = False
    havesn: bool = False
    clone: bool = False
    customuserid: bool = False
    bt264: bool = False
    keepalive: bool = False
    passageautolock: bool = False
    doorsensor: bool = False
    zwave: bool = False
    needreadmodel: bool = False
    needsycbuser: bool = False
    bt_close: bool = False
    singlelatchboltmortic: bool = False
    smartphone_nfc: bool = False
    update_2642: bool = False
    isautodirection: bool = False
    ishomekit: bool = False
    isyeeuu: bool = False
    secondsarray = []
    mtimearray = []


class Latch5F(BLEDeviceCapability):
    def __init__(self) -> None:
        super().__init__()
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
    def __init__(self) -> None:
        super().__init__()
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
    def __init__(self) -> None:
        super().__init__()
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
    def __init__(self) -> None:
        super().__init__()
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
