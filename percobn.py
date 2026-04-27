import asyncio
from mavsdk import System

async def print_battery():
    drone = System()
    await drone.connect(system_address="serial:///COM11:115200")

    async for battery in drone.telemetry.battery():
        print(f"Battery: {battery.remaining_percent * 100:.2f}%")

asyncio.run(print_battery())