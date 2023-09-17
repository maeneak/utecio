"""Python script for fetching account ID and password."""
### Original code courtesy of RobertD502
from __future__ import annotations

import asyncio
import json
import secrets
import string
import time
from typing import Any
from ul1bt import UL1BT
from enums import ULDeviceModel
from aiohttp import ClientResponse, ClientSession
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

class UTecClient:
    """U-Tec Client"""

    def __init__(self, session: ClientSession, email: str = "", password: str = "") -> None:
        """Initialize U-Tec client using the user provided email and password.

        session: aiohttp.ClientSession
        """

        self.mobile_uuid: str | None = None
        self.email: str = email
        self.password: str = password
        self.session: ClientSession = session
        self.token: str | None = None
        self.timeout: int = 5 * 60
        self.address_ids: list = []
        self.room_ids: list = []
        self.devices: list = []
        self.generate_random_mobile_uuid(32)


    def generate_random_mobile_uuid(self, length: int) -> None:
        """Generates a random mobile device UUID."""

        letters_nums = string.ascii_uppercase + string.digits
        self.mobile_uuid = "".join(secrets.choice(letters_nums) for i in range(length))

    async def fetch_token(self) -> None:
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
            self.address_ids.append(address_id["id"])

    async def get_rooms_at_address(self, address_id: int) -> None:
        """Get all the room IDs within an address."""

        url = "https://cloud.u-tec.com/app/room"
        headers = HEADERS
        body_data = {
            "id": address_id,
            "timestamp": str(time.time())
        }
        data = {
            "data": json.dumps(body_data),
            "token": self.token
        }

        response = await self._post(url, headers, data)
        for room_id in response["data"]:
            self.room_ids.append(room_id["id"])

    async def get_devices_in_room(self, room_id: int) -> None:
        """Fetches all the devices that are located in a room."""

        url = "https://cloud.u-tec.com/app/device/list"
        headers = HEADERS
        body_data = {
            "room_id": room_id,
            "timestamp": str(time.time())
        }
        data = {
            "data": json.dumps(body_data),
            "token": self.token
        }

        response = await self._post(url, headers, data)
        for device in response["data"]:
            self.devices.append(device)

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


async def api_get_devices(username: str, password: str):
    async with ClientSession() as session:
        client = UTecClient(session=session, email=username, password=password)
        await client.fetch_token()
        await client.login()
        await client.get_addresses()
        for address_id in client.address_ids:
            await client.get_rooms_at_address(address_id)
        for room_id in client.room_ids:
            await client.get_devices_in_room(room_id)
            
        locks = []
        devices = [x for x in client.devices if x['model'] == ULDeviceModel.UL1BT.value]
        for dev in devices:
            locks.append(UL1BT(dev['name'], 
                               str(dev['user']['uid']), 
                               await client.decode_pass(dev['user']['password']), 
                               dev['uuid']))
        return locks
