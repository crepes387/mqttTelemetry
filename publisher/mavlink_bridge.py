"""
MAVLink Bridge untuk menerima data dari MAVProxy dan forward ke MQTT
Ini mendengarkan UDP stream dari MAVProxy dan convert ke telemetry JSON
"""

import asyncio
import json
import socket
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Tuple

import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

# Import pymavlink untuk parse MAVLink messages
from pymavlink.dialects.v10 import ardupilotmega as mavlink_module

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS (sama seperti di publisher.py)
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
# MAVLink UDP LISTENER
# ============================================================================

class MAVLinkListener:
    """
    Listen ke UDP stream dari MAVProxy dan parse MAVLink messages
    MAVProxy output dengan --out=udpserver:0.0.0.0:14551
    """
    
    def __init__(self, listen_port: int = 14551):
        self.listen_port = listen_port
        self.socket = None
        self.running = False
        
        # Cache latest values
        self.latest_gps = GPSData(0.0, 0.0, 0.0, 0.0, 0)
        self.latest_attitude = AttitudeData(0.0, 0.0, 0.0)
        self.latest_velocity = VelocityData(0.0, 0.0, 0.0, 0.0)
        self.latest_battery = BatteryData(0.0, None, 0.0, None)
        self.latest_status = StatusData(False, "UNKNOWN", False, True)
        self.sequence = 0
        
        # MAVLink message buffer
        self.msg_buffer = bytearray()
        self.mavlink = mavlink_module.MAVLink(None)
        self.mavlink.robust_parsing = True
        
    def setup_socket(self) -> bool:
        """Setup UDP socket untuk listen"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.listen_port))
            self.socket.settimeout(1.0)
            logger.info(f"✅ Listening on UDP port {self.listen_port}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to setup socket: {e}")
            return False
    
    async def start_listening(self):
        """Start listening for MAVLink packets"""
        if not self.setup_socket():
            return
        
        self.running = True
        logger.info("🚀 Starting MAVLink listener...")
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                if data:
                    await self._process_mavlink_data(data)
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Socket error: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_mavlink_data(self, data: bytes):
        """Parse MAVLink messages dari UDP stream"""
        self.msg_buffer.extend(data)
        
        # Parse all complete messages in buffer
        while len(self.msg_buffer) > 0:
            try:
                msg = self.mavlink.parse_buffer(self.msg_buffer)
                if msg is None:
                    break
                
                await self._handle_mavlink_message(msg)
            except Exception as e:
                logger.debug(f"Parse error: {e}")
                break
    
    async def _handle_mavlink_message(self, msg):
        """Handle specific MAVLink message types"""
        msg_type = msg.get_type()
        
        try:
            if msg_type == "GLOBAL_POSITION_INT":
                # GPS dan altitude data
                self.latest_gps = GPSData(
                    latitude=msg.lat / 1e7,  # Convert from 1e-7 degrees
                    longitude=msg.lon / 1e7,
                    altitude_msl=msg.alt / 1000.0,  # Convert from mm to m
                    altitude_relative=msg.relative_alt / 1000.0,
                    satellite_count=0
                )
                logger.debug(f"📍 GPS: {self.latest_gps.latitude}, {self.latest_gps.longitude}")
                
            elif msg_type == "ATTITUDE":
                # Attitude (roll, pitch, yaw)
                self.latest_attitude = AttitudeData(
                    roll=msg.roll,
                    pitch=msg.pitch,
                    yaw=msg.yaw
                )
                logger.debug(f"🔄 Attitude: R={msg.roll:.2f}, P={msg.pitch:.2f}, Y={msg.yaw:.2f}")
                
            elif msg_type == "VFR_HUD":
                # Velocity dan speed data
                ground_speed = msg.groundspeed
                self.latest_velocity = VelocityData(
                    x=ground_speed * 0.7071,  # Approximation
                    y=ground_speed * 0.7071,
                    z=-msg.climb,
                    ground_speed=ground_speed
                )
                logger.debug(f"⚡ Speed: {ground_speed:.2f} m/s")
                
            elif msg_type == "BATTERY_STATUS":
                # Battery status
                voltage = msg.voltages[0] / 1000.0  # Convert from mV to V
                current = msg.current_battery / 100.0 if msg.current_battery > 0 else None
                
                self.latest_battery = BatteryData(
                    voltage_v=voltage,
                    current_a=current,
                    remaining_percent=msg.battery_remaining,
                    health=None
                )
                logger.debug(f"🔋 Battery: {voltage:.2f}V, {msg.battery_remaining}%")
                
            elif msg_type == "HEARTBEAT":
                # Status & mode
                base_mode = msg.base_mode
                armed = (base_mode & 0x80) != 0  # Check armed bit
                
                mode_map = {
                    0: "STABILIZE", 1: "ACRO", 2: "ALT_HOLD", 3: "AUTO",
                    4: "GUIDED", 5: "LOITER", 6: "RTL", 7: "CIRCLE",
                    8: "POSITION", 9: "LAND", 10: "OF_LOITER"
                }
                flight_mode = mode_map.get(msg.custom_mode, f"MODE_{msg.custom_mode}")
                
                self.latest_status = StatusData(
                    armed=armed,
                    flight_mode=flight_mode,
                    in_air=armed,  # Simplified assumption
                    is_connected=True
                )
                logger.debug(f"📡 Status: Armed={armed}, Mode={flight_mode}")
                
            elif msg_type == "GPS_RAW_INT":
                # GPS satellites
                self.latest_gps.satellite_count = msg.satellites_visible
                logger.debug(f"🛰️ Satellites: {msg.satellites_visible}")
                
        except Exception as e:
            logger.debug(f"Error handling {msg_type}: {e}")
    
    def get_telemetry(self) -> PixhawkTelemetry:
        """Get current telemetry snapshot"""
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
        """Stop listening"""
        self.running = False
        if self.socket:
            self.socket.close()


# ============================================================================
# MQTT PUBLISHER (sama seperti sebelumnya)
# ============================================================================

class MQTTPublisher:
    """Publish telemetry data ke MQTT broker"""
    
    def __init__(self, broker_address: str, port: int, username: str, password: str, topic: str):
        self.broker_address = broker_address
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.client = None
        self.is_connected = False
    
    def setup_client(self) -> bool:
        """Setup MQTT client"""
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
                    logger.warning(f"⚠️ TLS error: {e}")
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
        """Connect ke MQTT broker"""
        try:
            logger.info(f"🔗 Connecting to MQTT: {self.broker_address}:{self.port}")
            self.client.connect(self.broker_address, self.port, keepalive=15)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect dari MQTT"""
        logger.info("Disconnecting from MQTT...")
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish_telemetry(self, telemetry: PixhawkTelemetry) -> bool:
        """Publish telemetry ke MQTT"""
        try:
            payload_dict = {
                "ts": telemetry.timestamp,
                "gps": asdict(telemetry.gps),
                "attitude": asdict(telemetry.attitude),
                "velocity": asdict(telemetry.velocity),
                "battery": asdict(telemetry.battery),
                "status": asdict(telemetry.status),
                "seq": telemetry.sequence
            }
            
            json_string = json.dumps(payload_dict, separators=(',', ':'))
            result = self.client.publish(self.topic, json_string, qos=0)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"🚀 Published seq {telemetry.sequence} ({len(json_string)} bytes)")
                return True
            else:
                logger.error(f"Publish failed: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Publish error: {e}")
            return False
    
    def save_to_file(self, telemetry: PixhawkTelemetry, output_file: Path):
        """Save telemetry ke file"""
        try:
            payload_dict = {
                "ts": telemetry.timestamp,
                "gps": asdict(telemetry.gps),
                "attitude": asdict(telemetry.attitude),
                "velocity": asdict(telemetry.velocity),
                "battery": asdict(telemetry.battery),
                "status": asdict(telemetry.status),
                "seq": telemetry.sequence
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
            logger.error(f"❌ MQTT connection failed: {rc}")
    
    def _on_disconnect(self, client, userdata, flags, rc, prop):
        if rc != 0:
            logger.warning("⚠️ MQTT disconnected")
        self.is_connected = False


# ============================================================================
# MAIN BRIDGE APPLICATION
# ============================================================================

class MAVLinkMQTTBridge:
    """Bridge antara MAVProxy (MAVLink) dan MQTT broker"""
    
    def __init__(self):
        # MAVLink listener config
        self.mavlink_listen_port = int(os.getenv("MAVLINK_LISTEN_PORT", "14551"))
        
        # MQTT config (dari environment)
        import os
        self.mqtt_broker = os.getenv("MQTT_BROKER", "ef6ff411.ala.asia-southeast1.emqxsl.com")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "8883"))
        self.mqtt_username = os.getenv("MQTT_USERNAME", "user1")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "public1")
        self.mqtt_topic = os.getenv("MQTT_TOPIC", "uav/telemetry/crepes387")
        self.publish_interval = float(os.getenv("PUBLISH_INTERVAL", "1.0"))
        
        # Output file
        default_output = Path(__file__).resolve().parent.parent / "data" / "latest.json"
        self.output_file = Path(os.getenv("TELEMETRY_OUTPUT_FILE", str(default_output)))
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create components
        self.mavlink = MAVLinkListener(self.mavlink_listen_port)
        self.mqtt = MQTTPublisher(
            self.mqtt_broker,
            self.mqtt_port,
            self.mqtt_username,
            self.mqtt_password,
            self.mqtt_topic
        )
    
    async def run(self):
        """Main bridge loop"""
        try:
            if not self.mqtt.setup_client():
                logger.error("Failed to setup MQTT client")
                return
            
            if not self.mqtt.connect():
                logger.error("Failed to connect to MQTT")
                return
            
            logger.info("🌉 Starting MAVLink↔MQTT bridge...")
            
            # Start MAVLink listener in background
            mavlink_task = asyncio.create_task(self.mavlink.start_listening())
            
            # Give it time to start
            await asyncio.sleep(1)
            
            try:
                while True:
                    try:
                        telemetry = self.mavlink.get_telemetry()
                        self.mqtt.publish_telemetry(telemetry)
                        self.mqtt.save_to_file(telemetry, self.output_file)
                        await asyncio.sleep(self.publish_interval)
                    except Exception as e:
                        logger.error(f"Publish loop error: {e}")
                        await asyncio.sleep(1)
                        
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping bridge...")
                self.mavlink.stop()
                mavlink_task.cancel()
                self.mqtt.disconnect()
                
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.mqtt.disconnect()


# ============================================================================
# ENTRY POINT
# ============================================================================

async def main():
    """Entry point"""
    import os
    app = MAVLinkMQTTBridge()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
