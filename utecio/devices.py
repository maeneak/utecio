from .enums import ULDeviceModel


class BLEDeviceCapability:
    def __init__(self) -> None:
        self.lock: bool = False
        self.door: bool = False
        self.keypad: bool = False
        self.fingprinter: bool = False
        self.doublefp: bool = False
        self.bluetooth: bool = False
        self.rfid: bool = False
        self.rfid_once: bool = False
        self.rfid_twice: bool = False
        self.autobolt: bool = False
        self.autolock: bool = False
        self.autounlock: bool = False
        self.direction: bool = False
        self.update_ota: bool = False
        self.update_oad: bool = False
        self.update_wifi: bool = False
        self.alerts: bool = False
        self.mutemode: bool = False
        self.passage: bool = False
        self.lockout: bool = False
        self.manual: bool = False
        self.shakeopen: bool = False
        self.moreadmin: bool = False
        self.morepwd: bool = False
        self.timelimit: bool = False
        self.morelanguage: bool = False
        self.needregristerpwd: bool = False
        self.locklocal: bool = False
        self.havesn: bool = False
        self.clone: bool = False
        self.customuserid: bool = False
        self.bt264: bool = False
        self.keepalive: bool = False
        self.passageautolock: bool = False
        self.doorsensor: bool = False
        self.zwave: bool = False
        self.needreadmodel: bool = False
        self.needsycbuser: bool = False
        self.bt_close: bool = False
        self.singlelatchboltmortic: bool = False
        self.smartphone_nfc: bool = False
        self.update_2642: bool = False
        self.isautodirection: bool = False
        self.ishomekit: bool = False
        self.isyeeuu: bool = False
        self.secondsarray = []
        self.mtimearray = []


class Latch5F(BLEDeviceCapability):
    def __init__(self) -> None:
        super().__init__()

        self.bluetooth = True
        self.autolock = True
        self.update_wifi = True
        self.alerts = True
        self.mutemode = True
        self.doublefp = True
        self.keypad = True
        self.fingprinter = True
        self.needregristerpwd = True
        self.havesn = True
        self.moreadmin = True
        self.timelimit = True
        self.passage = True
        self.lockout = True
        self.bt264 = True
        self.keepalive = True
        self.passageautolock = True
        self.singlelatchboltmortic = True
        self.smartphone_nfc = True
        self.bt_close = True


class Latch5NFC(BLEDeviceCapability):
    def __init__(self) -> None:
        super().__init__()

        self.bluetooth = True
        self.autolock = True
        self.update_wifi = True
        self.alerts = True
        self.mutemode = True
        self.rfid = True
        self.rfid_twice = True
        self.keypad = True
        self.needregristerpwd = True
        self.havesn = True
        self.moreadmin = True
        self.timelimit = True
        self.passage = True
        self.lockout = True
        self.bt264 = True
        self.keepalive = True
        self.passageautolock = True
        self.singlelatchboltmortic = True
        self.smartphone_nfc = True
        self.bt_close = True


class UL1BT(BLEDeviceCapability):
    def __init__(self) -> None:
        super().__init__()

        self.bluetooth = True
        self.rfid = True
        self.rfid_twice = True
        self.fingprinter = True
        self.autobolt = True
        self.update_ota = True
        self.update_oad = True
        self.alerts = True
        self.shakeopen = True
        self.mutemode = True
        self.passage = True
        self.lockout = True
        self.havesn = True
        self.direction = True
        self.keepalive = True
        self.singlelatchboltmortic = True


class GenericLock(BLEDeviceCapability):
    def __init__(self) -> None:
        super().__init__()

        self.bluetooth = True
        self.autolock = True
        self.mutemode = True
        self.havesn = True
        self.timelimit = True
        self.passage = True
        self.lockout = True
        self.bt264 = True
        self.keepalive = True
        self.bt_close = True


defined_capabilities: dict[str, BLEDeviceCapability] = {
    ULDeviceModel.Latch5F.value: Latch5F(),
    ULDeviceModel.Latch5NFC.value: Latch5NFC(),
    ULDeviceModel.UL1BT.value: UL1BT(),
}
