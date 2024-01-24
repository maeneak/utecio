import asyncio

from .client import UtecClient
from .lock import UtecBleLock

EMAIL = "your@email.com"  # Your Utec app username/email
PASSWORD = "app password"  # Your Utec App Password
UL1_LOCK_PWD = ""
UL1_LOCK_UID = ""
L5_LOCK_PWD = ""
L5_LOCK_UID = ""
UL1_DEVICE_ADDRESS = ""
L5_DEVICE_ADDRESS = ""
L5_DEVICE_ADDRESS_2 = ""


async def main():
    await test_lib()
    return


async def test_lib():
    client = UtecClient(EMAIL, PASSWORD)
    await client.get_all_devices()
    l5: UtecBleLock = list(
        filter(lambda lock: lock.name == "Office Door", client.devices)
    )[0]
    await l5.lock()

    return


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
