from .enums import DeviceLockModel


class DeviceDefinition:
    def __init__(self) -> None:
        self.model = ""
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
        self.adduserremovenum = 4


class DeviceLockLatch5Finger(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()

        self.model = "Latch-5-F"
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


class DeviceLockLatch5NFC(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()

        self.model = "Latch-5-NFC"
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


class DeviceLockUL1(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()

        self.model = "Ultraloq-UL1"
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

class DeviceLockBoltNFC(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()

        self.model = "Bolt-NFC"
        self.lock = True
        self.bluetooth = True
        self.autolock = True
        self.update_ota = True
        self.update_wifi = True
        self.direction = True
        self.alerts = True
        self.mutemode = True
        self.manual = True
        self.shakeopen = True
        self.havesn = True
        self.rfid = True
        self.keypad = True
        self.needregristerpwd = True
        self.timelimit = True
        self.moreadmin = True
        self.lockout = True
        self.bt264 = True
        self.doorsensor = True
        self.keepalive = True
        self.autounlock = True
        self.smartphone_nfc = True
        self.update_2642 = True
        self.isautodirection = True
        self.ishomekitmeKit = True

class DeviceLockLever(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()
        self.model = "LEVER"
        self.bluetooth = True
        self.autolock = True
        self.update_ota = True
        self.alerts = True
        self.mutemode = True
        self.shakeopen = True
        self.fingprinter = True
        self.keypad = True
        self.doublefp = True
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

class DeviceLockUBolt(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()
        self.model = "U-Bolt"
        self.lock = True
        self.bluetooth = True
        self.autolock = True
        self.autounlock = True
        self.update_ota = True
        self.direction = True
        self.alerts = True
        self.mutemode = True
        self.manual = True
        self.shakeopen = True
        self.havesn = True
        self.moreadmin = True
        self.needreadmodel = True
        self.keypad = True
        self.lockout = True
        self.timelimit = True
        self.needregristerpwd = True
        self.bt264 = True
        self.keepalive = True

class DeviceLockUboltWiFi(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()
        self.model = "U-Bolt-WiFi"
        self.lock = True
        self.bluetooth = True
        self.autolock = True
        self.update_ota = True
        self.update_wifi = True
        self.direction = True
        self.alerts = True
        self.mutemode = True
        self.manual = True
        self.shakeopen = True
        self.havesn = True
        self.needreadmodel = True
        self.keypad = True
        self.needregristerpwd = True
        self.timelimit = True
        self.moreadmin = True
        self.lockout = True
        self.bt264 = True
        self.doorsensor = True
        self.keepalive = True
        self.autounlock = True

class DeviceLockUBoltZwave(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()
        self.model = "U-Bolt-ZWave"
        self.lock = True
        self.bluetooth = True
        self.autolock = True
        self.update_ota = True
        self.direction = True
        self.alerts = True
        self.mutemode = True
        self.manual = True
        self.shakeopen = True
        self.havesn = True
        self.needreadmodel = True
        self.keypad = True
        self.needregristerpwd = True
        self.timelimit = True
        self.moreadmin = True
        self.lockout = True
        self.bt264 = True
        self.doorsensor = True
        self.keepalive = True
        self.autounlocklock = True
        self.zwave = True

class DeviceLockUL3(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()
        self.model = "SmartLockByBle"
        self.bluetooth = True
        self.keypad = True
        self.fingprinter = True
        self.shakeopen = True
        self.morepwd = True
        self.passage = True
        self.lockout = True
        self.locklocal = True
        self.needsycbuser = True
        self.clone = True
        self.customuserid = True
        self.singlelatchboltmortic = True
        self.keepalive = True

class DeviceLockUL32ND(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()
        self.model = "UL3-2ND"
        self.bluetooth = True
        self.autolock = True
        self.update_ota = True
        self.alerts = True
        self.mutemode = True
        self.shakeopen = True
        self.fingprinter = True
        self.keypad = True
        self.doublefp = True
        self.needregristerpwd = True
        self.havesn = True
        self.locklocal = True
        self.needsycbuser = True
        self.moreadmin = True
        self.customuserid = True
        self.timelimit = True
        self.passage = True
        self.lockout = True
        self.bt264 = True
        self.keepalive = True
        self.passageautolock = True
        self.singlelatchboltmortic = True

class DeviceLockUL300(DeviceDefinition):
    def __init__(self) -> None:
        super().__init__()
        self.model = "UL300"
        self.bluetooth = True
        self.rfid = True
        self.rfid_once = True
        self.keypad = True
        self.fingprinter = True
        self.update_ota = True
        self.update_oad = True
        self.alerts = True
        self.shakeopen = True
        self.mutemode = True
        self.moreadmin = True
        self.timelimit = True
        self.passage = True
        self.lockout = True
        self.morelanguage = True
        self.locklocal = True
        self.needsycbuser = True
        self.havesn = True
        self.keepalive = True
        self.singlelatchboltmortic = True
        self.adduserremovenum = 5


class GenericLock(DeviceDefinition):
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


defined_capabilities: dict[str, DeviceDefinition] = {
    DeviceLockModel.Latch5F.value: DeviceLockLatch5Finger(),
    DeviceLockModel.Latch5NFC.value: DeviceLockLatch5NFC(),
    DeviceLockModel.UL1BT.value: DeviceLockUL1(),
}
