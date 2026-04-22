import asyncio
from mavsdk import System

async def run():
    # 1. Koneksi ke Pixhawk (Ganti COM3 dengan port-mu)
    drone = System()
    await drone.connect(system_address="serial:///COM3:57600")

    print("Menunggu drone terkoneksi...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone terdeteksi!")
            break

    # 2. Mengambil Data Posisi (GPS) secara Real-time
    async def print_gps():
        async for position in drone.telemetry.position():
            print(f"GPS: {position.latitude_deg}, {position.longitude_deg}")

    # 3. Mengambil Data Baterai
    async def print_battery():
        async for battery in drone.telemetry.battery():
            print(f"Baterai: {battery.remaining_percent * 100}%")

    # Jalankan pengambilan data secara bersamaan
    await asyncio.gather(print_gps(), print_battery())

if __name__ == "__main__":
    asyncio.run(run())