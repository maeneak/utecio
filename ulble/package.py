import asyncio
import hashlib
import struct
from Crypto.Cipher import AES
from enums import BLECommand

class CommandPackage:
    def __init__(self, command: BLECommand):
        self.command = command
        
        self.buffer = bytearray(5120)
        self.buffer[0] = 0x7F  
        byte_array = bytearray(int.to_bytes(2, 2, "little"))
        self.buffer[1] = byte_array[0]
        self.buffer[2] = byte_array[1]
        self.buffer[3] = command.value
        self._write_pos = 4
