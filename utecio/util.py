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
