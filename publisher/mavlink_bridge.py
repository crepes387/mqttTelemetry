"""
MAVLink Bridge untuk menerima data dari MAVProxy dan forward ke MQTT
Ini mendengarkan UDP stream dari MAVProxy dan convert ke telemetry JSON

PERBAIKAN dari versi lama:
- MAVLinkListener sekarang berjalan di thread terpisah (bukan async)
  sehingga socket.recvfrom() yang blocking tidak menghambat publish loop
- Semua method di MAVLinkListener tidak lagi async/await
- MAVLinkMQTTBridge.run() langsung panggil self.mavlink.start_listening()
  tanpa asyncio.create_task()
"""

import json
import socket
import logging
import os
import threading
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

from pymavlink.dialects.v10 import ardupilotmega as mavlink_module

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class GPSData:
    """GPS/Position data dari Pixhawk"""
    latitude: float
    longitude: float
    altitude_msl: float
    altitude_relative: float
    satellite_count: int

@dataclass
class AttitudeData:
    """Attitude (roll, pitch, yaw) dari Pixhawk"""
    roll: float
    pitch: float
    yaw: float

@dataclass
class VelocityData:
    """Velocity data dari Pixhawk"""
    x: float
    y: float
    z: float
    ground_speed: float

@dataclass
class BatteryData:
    """Battery data dari Pixhawk"""
    voltage_v: float
    current_a: Optional[float]
    remaining_percent: float
    health: Optional[float]

@dataclass
class StatusData:
    """System status dari Pixhawk"""
    armed: bool
    flight_mode: str
    in_air: bool
    is_connected: bool

@dataclass
class PixhawkTelemetry:
    """Complete telemetry payload"""
    timestamp: str
    gps: GPSData
    attitude: AttitudeData
    velocity: VelocityData
    battery: BatteryData
    status: StatusData
    sequence: int


# ============================================================================
# MAVLink UDP LISTENER — berjalan di thread terpisah (BUKAN async)
# ============================================================================

class MAVLinkListener:
    """
    Listen ke UDP stream dari MAVProxy dan parse MAVLink messages.

    PERUBAHAN UTAMA:
    Seluruh class ini sekarang SYNCHRONOUS (tidak ada async/await).
    start_listening() akan menjalankan _listen_loop() di thread daemon
    terpisah, sehingga blocking socket.recvfrom() tidak pernah memblokir
    asyncio event loop yang dipakai publish loop.
    """

    def __init__(self, listen_port: int = 14551):
        self.listen_port = listen_port
        self.socket = None
        self.running = False
        self._thread = None  # <-- thread listener disimpan di sini

        # Cache latest values — diupdate oleh thread listener,
        # dibaca oleh publish loop (main thread). Aman karena GIL Python.
        self.latest_gps      = GPSData(0.0, 0.0, 0.0, 0.0, 0)
        self.latest_attitude = AttitudeData(0.0, 0.0, 0.0)
        self.latest_velocity = VelocityData(0.0, 0.0, 0.0, 0.0)
        self.latest_battery  = BatteryData(0.0, None, 0.0, None)
        self.latest_status   = StatusData(False, "UNKNOWN", False, True)
        self.sequence = 0

        # MAVLink parser
        self.msg_buffer = bytearray()
        self.mavlink = mavlink_module.MAVLink(None)
        self.mavlink.robust_parsing = True

    # ------------------------------------------------------------------
    # SETUP SOCKET
    # ------------------------------------------------------------------

    def setup_socket(self) -> bool:
        """Buka UDP socket dan bind ke port listener."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.listen_port))
            self.socket.settimeout(1.0)  # timeout 1 detik agar loop bisa cek self.running
            logger.info(f"✅ Listening on UDP port {self.listen_port}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to setup socket: {e}")
            return False

    # ------------------------------------------------------------------
    # START — dipanggil dari MAVLinkMQTTBridge.run()
    # ------------------------------------------------------------------

    def start_listening(self):
        """
        Setup socket lalu jalankan _listen_loop() di thread daemon.
        Method ini LANGSUNG RETURN — tidak blocking.
        """
        if not self.setup_socket():
            return

        self.running = True
        self._thread = threading.Thread(
            target=self._listen_loop,
            name="mavlink-listener",
            daemon=True   # thread otomatis mati saat program selesai
        )
        self._thread.start()
        logger.info("🚀 MAVLink listener thread started")
        logger.info(f"🔔 Waiting for UDP data on port {self.listen_port}...")
        logger.info(f"💡 Pastikan MAVProxy mengirim ke port ini: --out=127.0.0.1:{self.listen_port}")

    # ------------------------------------------------------------------
    # LOOP UTAMA — berjalan di thread terpisah
    # ------------------------------------------------------------------

    def _listen_loop(self):
        """
        Loop blocking yang berjalan di thread-nya sendiri.
        Terus tunggu paket UDP, parse, update latest_* values.
        """
        packet_count = 0
        timeout_count = 0

        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                if data:
                    packet_count += 1
                    timeout_count = 0
                    logger.debug(f"📥 Packet #{packet_count} ({len(data)} bytes) from {addr}")
                    self._process_mavlink_data(data)

            except socket.timeout:
                # Tidak ada data dalam 1 detik — normal, lanjut loop
                timeout_count += 1
                if timeout_count >= 10:
                    logger.warning(
                        f"⚠️ Tidak ada UDP data selama {timeout_count} detik. "
                        f"Cek parameter --out MAVProxy!"
                    )
                    timeout_count = 0

            except OSError:
                # Socket ditutup dari luar (saat stop() dipanggil)
                break

            except Exception as e:
                logger.error(f"❌ Socket error: {e}")

        logger.info("🛑 MAVLink listener thread stopped")

    # ------------------------------------------------------------------
    # PARSE DATA
    # ------------------------------------------------------------------

    def _process_mavlink_data(self, data: bytes):
        """Parse bytes UDP menjadi MAVLink messages."""
        self.msg_buffer.extend(data)
        logger.debug(f"📦 Buffer size: {len(self.msg_buffer)} bytes")

        msg_count = 0
        try:
            msgs = self.mavlink.parse_buffer(bytes(self.msg_buffer))
            self.msg_buffer.clear()  # WAJIB dikosongkan setelah parse

            if msgs:
                logger.debug(f"📋 Got {len(msgs)} message(s)")
                for msg in msgs:
                    if msg is not None:
                        msg_count += 1
                        logger.debug(f"✅ Parsed: {msg.get_type()}")
                        self._handle_mavlink_message(msg)

        except Exception as e:
            logger.warning(f"⚠️ Parse error: {e}")
            self.msg_buffer.clear()

        if msg_count > 0:
            logger.debug(f"🎯 Successfully parsed {msg_count} message(s)")

    # ------------------------------------------------------------------
    # HANDLER PER TIPE PESAN
    # ------------------------------------------------------------------

    def _handle_mavlink_message(self, msg):
        """Update latest_* values sesuai tipe MAVLink message yang diterima."""
        try:
            msg_type = msg.get_type()
        except Exception as e:
            logger.error(f"❌ Cannot get message type: {e}")
            return

        try:
            if msg_type == "GLOBAL_POSITION_INT":
                self.latest_gps = GPSData(
                    latitude=msg.lat / 1e7,
                    longitude=msg.lon / 1e7,
                    altitude_msl=msg.alt / 1000.0,
                    altitude_relative=msg.relative_alt / 1000.0,
                    satellite_count=self.latest_gps.satellite_count  # jaga nilai satelit sebelumnya
                )
                logger.info(
                    f"📍 GPS: {self.latest_gps.latitude:.6f}, "
                    f"{self.latest_gps.longitude:.6f}, "
                    f"Alt: {self.latest_gps.altitude_relative:.1f}m"
                )

            elif msg_type == "ATTITUDE":
                self.latest_attitude = AttitudeData(
                    roll=msg.roll,
                    pitch=msg.pitch,
                    yaw=msg.yaw
                )
                logger.info(f"🔄 Attitude: R={msg.roll:.2f}° P={msg.pitch:.2f}° Y={msg.yaw:.2f}°")

            elif msg_type == "VFR_HUD":
                ground_speed = msg.groundspeed
                self.latest_velocity = VelocityData(
                    x=ground_speed * 0.7071,
                    y=ground_speed * 0.7071,
                    z=-msg.climb,
                    ground_speed=ground_speed
                )
                logger.info(f"⚡ Speed: {ground_speed:.2f} m/s, Climb: {msg.climb:.2f} m/s")

            elif msg_type == "BATTERY_STATUS":
                voltage = msg.voltages[0] / 1000.0
                current = msg.current_battery / 100.0 if msg.current_battery > 0 else None
                self.latest_battery = BatteryData(
                    voltage_v=voltage,
                    current_a=current,
                    remaining_percent=msg.battery_remaining,
                    health=None
                )
                logger.info(f"🔋 Battery: {voltage:.2f}V, {msg.battery_remaining}%, Current: {current}A")

            elif msg_type == "HEARTBEAT":
                base_mode = msg.base_mode
                armed = (base_mode & 0x80) != 0
                mode_map = {
                    0: "STABILIZE", 1: "ACRO", 2: "ALT_HOLD", 3: "AUTO",
                    4: "GUIDED",    5: "LOITER", 6: "RTL",    7: "CIRCLE",
                    8: "POSITION",  9: "LAND",  10: "OF_LOITER"
                }
                flight_mode = mode_map.get(msg.custom_mode, f"MODE_{msg.custom_mode}")
                self.latest_status = StatusData(
                    armed=armed,
                    flight_mode=flight_mode,
                    in_air=armed,
                    is_connected=True
                )
                logger.info(f"📡 Status: Armed={armed}, Mode={flight_mode}")

            elif msg_type == "GPS_RAW_INT":
                self.latest_gps.satellite_count = msg.satellites_visible
                logger.info(f"🛰️ Satellites: {msg.satellites_visible}")

            else:
                logger.debug(f"ℹ️ Received {msg_type} (not displayed)")

        except Exception as e:
            logger.error(f"❌ Error handling {msg_type}: {e}")

    # ------------------------------------------------------------------
    # GET SNAPSHOT & STOP
    # ------------------------------------------------------------------

    def get_telemetry(self) -> PixhawkTelemetry:
        """Ambil snapshot telemetry terbaru. Dipanggil dari publish loop."""
        telemetry = PixhawkTelemetry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            gps=self.latest_gps,
            attitude=self.latest_attitude,
            velocity=self.latest_velocity,
            battery=self.latest_battery,
            status=self.latest_status,
            sequence=self.sequence
        )
        self.sequence += 1
        return telemetry

    def stop(self):
        """Hentikan listener thread."""
        self.running = False
        if self.socket:
            self.socket.close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        logger.info("🛑 MAVLink listener stopped")


# ============================================================================
# MQTT PUBLISHER
# ============================================================================

class MQTTPublisher:
    """Publish telemetry data ke MQTT broker."""

    def __init__(self, broker_address: str, port: int, username: str, password: str, topic: str):
        self.broker_address = broker_address
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.client = None
        self.is_connected = False

    def setup_client(self) -> bool:
        """Setup MQTT client dengan TLS."""
        try:
            self.client = mqtt.Client(
                client_id="crepes387_mavlink_bridge",
                callback_api_version=CallbackAPIVersion.VERSION2
            )

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

            cert_path = Path(__file__).resolve().parent / "emqxsl-ca.crt"
            if cert_path.exists():
                try:
                    self.client.tls_set(ca_certs=str(cert_path))
                    logger.info("✅ TLS certificate loaded")
                except Exception as e:
                    logger.warning(f"⚠️ TLS error: {e}, fallback ke insecure TLS")
                    self.client.tls_set()
                    self.client.tls_insecure_set(True)
            else:
                self.client.tls_set()
                self.client.tls_insecure_set(True)

            self.client.username_pw_set(self.username, self.password)
            return True

        except Exception as e:
            logger.error(f"MQTT setup failed: {e}")
            return False

    def connect(self) -> bool:
        """Connect ke MQTT broker."""
        try:
            logger.info(f"🔗 Connecting to MQTT: {self.broker_address}:{self.port}")
            self.client.connect(self.broker_address, self.port, keepalive=15)
            self.client.loop_start()  # network loop di background thread paho
            return True
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect dari MQTT."""
        logger.info("Disconnecting from MQTT...")
        self.client.loop_stop()
        self.client.disconnect()

    def publish_telemetry(self, telemetry: PixhawkTelemetry) -> bool:
        """Serialize telemetry ke JSON dan publish ke MQTT."""
        try:
            payload_dict = {
                "ts":       telemetry.timestamp,
                "gps":      asdict(telemetry.gps),
                "attitude": asdict(telemetry.attitude),
                "velocity": asdict(telemetry.velocity),
                "battery":  asdict(telemetry.battery),
                "status":   asdict(telemetry.status),
                "seq":      telemetry.sequence
            }

            json_string = json.dumps(payload_dict, separators=(',', ':'))
            result = self.client.publish(self.topic, json_string, qos=0)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"🚀 Published seq {telemetry.sequence} ({len(json_string)} bytes)")
                return True
            else:
                logger.error(f"Publish failed rc={result.rc}")
                return False

        except Exception as e:
            logger.error(f"Publish error: {e}")
            return False

    def save_to_file(self, telemetry: PixhawkTelemetry, output_file: Path):
        """Simpan telemetry terbaru ke file JSON (overwrite)."""
        try:
            payload_dict = {
                "ts":       telemetry.timestamp,
                "gps":      asdict(telemetry.gps),
                "attitude": asdict(telemetry.attitude),
                "velocity": asdict(telemetry.velocity),
                "battery":  asdict(telemetry.battery),
                "status":   asdict(telemetry.status),
                "seq":      telemetry.sequence
            }
            json_string = json.dumps(payload_dict, separators=(',', ':'))
            with output_file.open("w", encoding="utf-8") as f:
                f.write(json_string)
        except Exception as e:
            logger.error(f"File save error: {e}")

    def _on_connect(self, client, userdata, flags, rc, prop):
        if rc == 0:
            logger.info("✅ Connected to MQTT broker")
            self.is_connected = True
        else:
            logger.error(f"❌ MQTT connection failed rc={rc}")

    def _on_disconnect(self, client, userdata, flags, rc, prop):
        if rc != 0:
            logger.warning("⚠️ MQTT disconnected unexpectedly")
        self.is_connected = False


# ============================================================================
# MAIN BRIDGE APPLICATION
# ============================================================================

class MAVLinkMQTTBridge:
    """Bridge antara MAVProxy (MAVLink UDP) dan MQTT broker."""

    def __init__(self):
        self.mavlink_listen_port = int(os.getenv("MAVLINK_LISTEN_PORT", "14551"))

        self.mqtt_broker   = os.getenv("MQTT_BROKER",   "ef6ff411.ala.asia-southeast1.emqxsl.com")
        self.mqtt_port     = int(os.getenv("MQTT_PORT", "8883"))
        self.mqtt_username = os.getenv("MQTT_USERNAME", "user1")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "public1")
        self.mqtt_topic    = os.getenv("MQTT_TOPIC",    "uav/telemetry/crepes387")
        self.publish_interval = float(os.getenv("PUBLISH_INTERVAL", "1.0"))

        default_output = Path(__file__).resolve().parent.parent / "data" / "latest.json"
        self.output_file = Path(os.getenv("TELEMETRY_OUTPUT_FILE", str(default_output)))
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        self.mavlink = MAVLinkListener(self.mavlink_listen_port)
        self.mqtt = MQTTPublisher(
            self.mqtt_broker,
            self.mqtt_port,
            self.mqtt_username,
            self.mqtt_password,
            self.mqtt_topic
        )

    async def run(self):
        """Main bridge loop."""
        try:
            if not self.mqtt.setup_client():
                logger.error("Failed to setup MQTT client")
                return

            if not self.mqtt.connect():
                logger.error("Failed to connect to MQTT")
                return

            logger.info("🌉 Starting MAVLink ↔ MQTT bridge...")

            # ✅ PERBAIKAN: start_listening() sekarang non-blocking
            # karena listener berjalan di thread terpisah
            self.mavlink.start_listening()

            # Beri sedikit waktu agar socket dan thread siap
            await asyncio.sleep(1)

            publish_count = 0
            try:
                while True:
                    try:
                        telemetry = self.mavlink.get_telemetry()
                        self.mqtt.publish_telemetry(telemetry)
                        self.mqtt.save_to_file(telemetry, self.output_file)

                        publish_count += 1
                        if publish_count % 5 == 0:
                            logger.info(
                                f"🎯 Published seq {telemetry.sequence} | "
                                f"GPS: {telemetry.gps.latitude:.4f}, {telemetry.gps.longitude:.4f}"
                            )

                        await asyncio.sleep(self.publish_interval)

                    except Exception as e:
                        logger.error(f"❌ Publish loop error: {e}")
                        await asyncio.sleep(1)

            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping bridge...")
                self.mavlink.stop()
                self.mqtt.disconnect()

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.mqtt.disconnect()


# ============================================================================
# ENTRY POINT
# ============================================================================

async def main():
    logger.info("=" * 80)
    logger.info("🌉 MAVLink ↔ MQTT Bridge Configuration")
    logger.info("=" * 80)
    logger.info(f"📡 MAVLink Listen Port : {os.getenv('MAVLINK_LISTEN_PORT', '14551')}")
    logger.info(f"🔗 MQTT Broker         : {os.getenv('MQTT_BROKER', 'ef6ff411.ala.asia-southeast1.emqxsl.com')}:{os.getenv('MQTT_PORT', '8883')}")
    logger.info(f"📝 MQTT Topic          : {os.getenv('MQTT_TOPIC', 'uav/telemetry/crepes387')}")
    logger.info(f"⏱️  Publish Interval    : {os.getenv('PUBLISH_INTERVAL', '1.0')}s")
    logger.info("=" * 80)

    app = MAVLinkMQTTBridge()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())