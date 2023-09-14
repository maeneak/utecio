import asyncio
from .ul1bt import UL1BT

async def main():
    
    device = UL1BT("Front Door", "4026531840", "95956536", "4C:24:98:A2:D1:37")
    await device.Unlock()

if __name__ == '__main__':
    main()