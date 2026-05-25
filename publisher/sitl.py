import collections
import collections.abc

# Fix untuk Python 3.10+ compatibility dengan DroneKit
collections.MutableMapping = collections.abc.MutableMapping
from dronekit import connect

# Hubungkan ke alamat yang sudah ditentukan di SITL
connection_string = '127.0.0.1:14540'

print(f"Menghubungkan ke: {connection_string}")

vehicle = connect(connection_string, wait_ready=True)

print("Berhasil Terhubung!")
print(f"GPS: {vehicle.location.global_frame}")