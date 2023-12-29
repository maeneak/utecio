import datetime
import struct

def date_from_4bytes(bArr:bytes):
    byteToInt4, = struct.unpack('>I', bArr)
    
    second = byteToInt4 & 63
    minute = (byteToInt4 >> 6) & 63
    hour = (byteToInt4 >> 12) & 31
    day = (byteToInt4 >> 17) & 31
    month = ((byteToInt4 >> 22) & 15) - 1
    year = ((byteToInt4 >> 26) & 63) + 2000
    
    return datetime.datetime(year, month, day, hour, minute, second)

def bytes_to_ascii(bArr: bytearray):
    i = 0
    i2 = len(bArr)
    if not bArr or i < 0 or i2 <= 0 or i >= len(bArr) or len(bArr) - i < i2:
        return None

    substring = bArr[i:i+i2]
    if 0 in substring:
        substring = substring[:substring.index(0)]
    try:
        return substring.decode("ISO8859-1")
    except UnicodeDecodeError:
        return None

def decode_password(password: int) -> str:
    """Decode the password that the API returns to the Admin Password."""

    try:
        byte_array = bytearray(4)
        i3 = 0
        while i3 < 4:
            byte_array[i3] = (password >> (i3 * 8)) & 255
            i3 += 1

        str2 = ""
        length = len(byte_array) - 1
        while length >= 0:
            hex_string = format(byte_array[length] & 0xFF, '02x')
            length -= 1
            if len(hex_string) == 1:
                hex_string = "0" + hex_string
            str2 = str2 + hex_string
        parse_int = int(str2[0])
        if parse_int == 0:
            return str(password)
        str3 = str(int(str2[1:], 16))
        if parse_int != len(str3):
            str4 = str3
            count = 0
            while count < (parse_int - len(str3)):
                str4 = "0" + str4
                count += 1
            return str4
        return str3
    except Exception as e:
        print(e)

class DeviceNotAvailable(Exception):
    """Device not visible on Bluetooth Network."""
