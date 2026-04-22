import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import psutil
import time
import json 
import os
from pathlib import Path
import threading

# Variabel global untuk tracking reconnect
reconnect_delay = 1
reconnect_lock = threading.Lock()

# Callbacks
def on_connect(client, userdata, flags, rc, prop):
    global reconnect_delay
    if rc == 0:
        print("✅ Berhasil terhubung ke Broker EMQX!")
        reconnect_delay = 1  # Reset backoff
    else:
        print(f"❌ Gagal terhubung dengan kode: {rc}")

def on_disconnect(client, userdata, flags, rc, prop):
    if rc != 0:
        print(f"⚠️  Disconnected, akan reconnect otomatis...")

def on_publish(client, userdata, mid, rc, prop):
    # Callback saat publish selesai (VERSION2 perlu 5 parameter)
    pass

class UavTelemetry:
    def __init__(self):
        self.baterai = 100
        self.speed = -10
        self.acuan_waktu = time.time()
        self.topic = "uav/telemetry/crepes387"
        default_output = Path(__file__).resolve().parent.parent / "data" / "latest.json"
        self.output_file = Path(os.getenv("TELEMETRY_OUTPUT_FILE", str(default_output)))
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.publish_count = 0
        
    def update_baterai(self):
        now = time.time()
        if now - self.acuan_waktu >= 5:
            if (self.baterai <= 0 and self.speed < 0) or (self.baterai >= 100 and self.speed > 0):
                self.speed *= -1
            self.baterai += self.speed
            self.acuan_waktu = now

    def publish_data(self, mqtt_client):
        self.update_baterai()
        
        # Gunakan unix timestamp (float) untuk presisi microsecond
        current_time = time.time()
        
        payload = {
            "ts": current_time,  # Unix timestamp dengan presisi tinggi
            "battery": self.baterai,
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent
            },
            "seq": self.publish_count  # Sequence number untuk tracking
        }
        
        json_string = json.dumps(payload, separators=(',', ':'))  # Compact JSON, minimal size
        
        # Save to file
        with self.output_file.open("w", encoding="utf-8") as file_handle:
            file_handle.write(json_string)
        
        # Publish ke MQTT dengan QoS=0 (paling cepat, tanpa acknowledge)
        result = mqtt_client.publish(self.topic, json_string, qos=0)
        
        self.publish_count += 1
        print(f"🚀 [{self.publish_count}] Publish: {json_string}")


# Setup Koneksi dengan optimasi performa
broker_address = "ef6ff411.ala.asia-southeast1.emqxsl.com"
port = 8883
username = "user1"
password = "public1"
use_tls = True
publish_interval = float(os.getenv("PUBLISH_INTERVAL", "0.5"))  # Default 100ms, bisa adjust via env var

# Inisialisasi MQTT Client dan connect ke broker
client = mqtt.Client(client_id="crepes387", callback_api_version=CallbackAPIVersion.VERSION2)

# Optimasi performa
client.max_inflight_messages_set(5)  # Reduce queue, lebih cepat untuk QoS=0
client._sock_connect_alarm = 5  # Timeout connect lebih pendek

# Setup TLS
client.tls_set()
client.tls_insecure_set(True)

# Setup credentials
client.username_pw_set(username, password)

# Register callbacks
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish


# Connect dengan keepalive lebih pendek (15 detik) untuk faster detection
print(f"🔗 Connecting ke {broker_address}:{port}...")
client.connect(broker_address, port, keepalive=15)
client.loop_start()

uav = UavTelemetry()

# Loop Utama
try:
    print(f"🚀 Mulai publish data setiap {publish_interval}s...")
    while True:
        uav.publish_data(client)
        time.sleep(publish_interval)
except KeyboardInterrupt:
    print("\n🛑 Menghentikan pengiriman data...")
    client.loop_stop()
    client.disconnect()
    print("✅ Disconnected.")