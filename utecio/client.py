"""Python script for fetching account ID and password."""
### Original code courtesy of RobertD502
from __future__ import annotations

import json
import secrets
import string
import time
from typing import Any
from aiohttp import ClientResponse, ClientSession
from .ble.device import RoomProfile, AddressProfile
from .ble.lock import UtecBleLock
### Headers

CONTENT_TYPE = "application/x-www-form-urlencoded"
ACCEPT_ENCODING = "gzip, deflate, br"
USER_AGENT = "U-tec/2.1.14 (iPhone; iOS 15.1; Scale/3.00)"
ACCEPT_LANG = "en-US;q=1, it-US;q=0.9"
HEADERS = {
    "accept": "*/*",
    "content-type": CONTENT_TYPE,
    "accept-encoding": ACCEPT_ENCODING,
    "user-agent": USER_AGENT,
    "accept-language": ACCEPT_LANG
}

### Token Body
APP_ID = "13ca0de1e6054747c44665ae13e36c2c"
CLIENT_ID = "1375ac0809878483ee236497d57f371f"
TIME_ZONE = "-4"
VERSION = "V3.2"

class UtecClient:
    """U-Tec Client"""

    def __init__(self, email: str, password: str, session: ClientSession = ClientSession()) -> None:
        """Initialize U-Tec client using the user provided email and password.

        session: aiohttp.ClientSession
        """

        self.mobile_uuid: str | None = None
        self.email: str = email
        self.password: str = password
        self.session = session
        self.token: str | None = None
        self.timeout: int = 5 * 60
        self.addresses: list = []
        self.rooms: list = []
        self.devices: list = []
        self.devices_json: list = []
        self._generate_random_mobile_uuid(32)


    def _generate_random_mobile_uuid(self, length: int) -> None:
        """Generates a random mobile device UUID."""

        letters_nums = string.ascii_uppercase + string.digits
        self.mobile_uuid = "".join(secrets.choice(letters_nums) for i in range(length))

    async def _fetch_token(self) -> None:
        """Fetch the token that is used to log into the app."""

        url = "https://uemc.u-tec.com/app/token"
        headers = HEADERS
        data = {
            "appid": APP_ID,
            "clientid": CLIENT_ID,
            "timezone": TIME_ZONE,
            "uuid": self.mobile_uuid,
            "version": VERSION
        }

        response = await self._post(url, headers, data)
        self.token = response["data"]["token"]

    async def login(self) -> None:
        """Log in to account using previous token obtained."""

        url = "https://cloud.u-tec.com/app/user/login"
        headers = HEADERS
        auth_data = {
            "email": self.email,
            "timestamp": str(time.time()),
            "password": self.password
        }
        data = {
            "data": json.dumps(auth_data),
            "token": self.token
        }

        await self._post(url, headers, data)

    async def get_addresses(self) -> None:
        """Fetch all addresses associated with an account."""

        url = "https://cloud.u-tec.com/app/address"
        headers = HEADERS
        body_data = {
            "timestamp": str(time.time())
        }
        data = {
            "data": json.dumps(body_data),
            "token": self.token
        }

        response = await self._post(url, headers, data)
        for address_id in response["data"]:
            self.addresses.append(AddressProfile(address_id))
            #self.address_ids.append(address_id["id"])

    async def get_rooms_at_address(self, address: AddressProfile) -> None:
        """Get all the room IDs within an address."""

        url = "https://cloud.u-tec.com/app/room"
        headers = HEADERS
        body_data = {
            "id": address.id,
            "timestamp": str(time.time())
        }
        data = {
            "data": json.dumps(body_data),
            "token": self.token
        }

        response = await self._post(url, headers, data)
        for room in response["data"]:
            self.rooms.append(RoomProfile(room, address))

    async def get_devices_in_room(self, room: RoomProfile) -> None:
        """Fetches all the devices that are located in a room."""

        url = "https://cloud.u-tec.com/app/device/list"
        headers = HEADERS
        body_data = {
            "room_id": room.id,
            "timestamp": str(time.time())
        }
        data = {
            "data": json.dumps(body_data),
            "token": self.token
        }

        response = await self._post(url, headers, data)
        for api_device in response["data"]:
            device = UtecBleLock.from_json(api_device)
            device.room = room
            self.devices.append(device)
            self.devices_json.append(api_device)
            room.devices.append(device)
            room.address.devices.append(device)

    @staticmethod
    async def decode_pass(password: int) -> str:
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
            return ""

    async def _post(self, url: str, headers: dict[str, str], data: dict[str, str]) -> dict[str, Any]:
        """Make POST API call."""

        async with self.session.post(url, headers=headers, data=data, timeout=self.timeout) as resp:
            return await self._response(resp)

    @staticmethod
    async def _response(resp: ClientResponse) -> dict[str, Any]:
        """Return response from API call."""

        try:
            response: dict[str, Any] = await resp.json()
        except Exception as e:
            print(e)
        else:
            return response
        return {}

    async def update(self): 
        await self._fetch_token()
        await self.login()
        await self.get_addresses()
        for address in self.addresses:
            await self.get_rooms_at_address(address)
        for room in self.rooms:
            await self.get_devices_in_room(room)

    async def get_all_devices(self) -> list[UtecBleLock]: 
        await self.update()
        return self.devices

    async def get_all_devices_json(self) -> list: 
        await self.update()
        return self.devices_json
