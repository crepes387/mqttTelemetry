# test_publisher.py — jalankan di terminal terpisah
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import json, time, ssl

client = mqtt.Client(client_id="test_pub", callback_api_version=CallbackAPIVersion.VERSION2)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)
client.tls_insecure_set(True)
client.username_pw_set("user1", "public1")
client.connect("ef6ff411.ala.asia-southeast1.emqxsl.com", 8883)
client.loop_start()

seq = 0
while True:
    payload = {
        "ts": "2026-06-02T00:00:00Z",
        "seq": seq,
        "gps": {"latitude": -7.9797, "longitude": 112.6304, "altitude_msl": 100.0, "altitude_relative": 50.0, "satellite_count": 12},
        "attitude": {"roll": 0.5, "pitch": -0.3, "yaw": 90.0},
        "velocity": {"x": 1.0, "y": 0.5, "z": 0.0, "ground_speed": 1.1},
        "battery": {"voltage_v": 12.4, "current_a": 5.0, "remaining_percent": 80.0, "health": None},
        "status": {"armed": True, "flight_mode": "LOITER", "in_air": True, "is_connected": True}
    }
    client.publish("uav/telemetry/crepes387", json.dumps(payload))
    print(f"Published seq {seq}")
    seq += 1
    time.sleep(0.5)