
def decode_api_password(password_string: str):
    byteArray = bytearray(int(password_string).to_bytes(4, "little"))
    str2 = ""
    for length in range(len(byteArray) - 1, -1, -1):
        hexString = format(byteArray[length] & 0xFF, '02x')
        str2 += hexString

    parseInt = int(str2[0])
    if parseInt == 0:
        return str

    str3 = str(int(str2[1:], 16))
    if parseInt != len(str3):
        str4 = str3
        for _ in range(parseInt - len(str3)):
            str4 = "0" + str4
        return str4
    return str3

