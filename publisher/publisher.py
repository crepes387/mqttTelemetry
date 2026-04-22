import asyncio
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from mavsdk import System
import json
import os
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
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
    timestamp: float
    gps: GPSData
    attitude: AttitudeData
    velocity: VelocityData
    battery: BatteryData
    status: StatusData
    sequence: int


# ============================================================================
# PIXHAWK DATA READER (MAVSDK)
# ============================================================================

class PixhawkReader:
    """Membaca telemetry real-time dari Pixhawk via MAVSDK"""
    
    def __init__(self, connection_url: str = "udpin://:14540"):
        self.drone = System()
        self.connection_url = connection_url
        self.is_connected = False
        self.sequence = 0
        
        # Cache latest telemetry
        self.latest_gps: Optional[GPSData] = None
        self.latest_attitude: Optional[AttitudeData] = None
        self.latest_velocity: Optional[VelocityData] = None
        self.latest_battery: Optional[BatteryData] = None
        self.latest_status: Optional[StatusData] = None
    
    async def connect(self) -> bool:
        """Connect ke Pixhawk"""
        try:
            logger.info(f"🔗 Connecting ke Pixhawk: {self.connection_url}")
            await self.drone.connect(system_address=self.connection_url)
            
            async for state in self.drone.core.connection_state():
                if state.is_connected:
                    logger.info("✅ Connected to Pixhawk!")
                    self.is_connected = True
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect dari Pixhawk"""
        logger.info("🛑 Disconnecting from Pixhawk...")
    
    async def read_telemetry(self) -> PixhawkTelemetry:
        """Baca semua telemetry data dari Pixhawk"""
        
        if not self.is_connected:
            raise RuntimeError("Not connected to Pixhawk!")
        
        telemetry = PixhawkTelemetry(
            timestamp=time.time(),
            gps=self.latest_gps or GPSData(0, 0, 0, 0, 0),
            attitude=self.latest_attitude or AttitudeData(0, 0, 0),
            velocity=self.latest_velocity or VelocityData(0, 0, 0, 0),
            battery=self.latest_battery or BatteryData(0, None, 0, None),
            status=self.latest_status or StatusData(False, "UNKNOWN", False, False),
            sequence=self.sequence
        )
        
        self.sequence += 1
        return telemetry
    
    async def start_telemetry_streams(self):
        """Start background telemetry streams"""
        
        tasks = [
            asyncio.create_task(self._stream_position()),
            asyncio.create_task(self._stream_attitude()),
            asyncio.create_task(self._stream_velocity()),
            asyncio.create_task(self._stream_battery()),
            asyncio.create_task(self._stream_status()),
        ]
        
        await asyncio.gather(*tasks)
    
    async def _stream_position(self):
        """Subscribe ke position stream"""
        try:
            async for position in self.drone.telemetry.position():
                self.latest_gps = GPSData(
                    latitude=position.latitude_deg,
                    longitude=position.longitude_deg,
                    altitude_msl=position.absolute_altitude_m,
                    altitude_relative=position.relative_altitude_m,
                    satellite_count=0
                )
        except Exception as e:
            logger.error(f"Position stream error: {e}")
    
    async def _stream_attitude(self):
        """Subscribe ke attitude stream"""
        try:
            async for attitude in self.drone.telemetry.attitude_euler():
                self.latest_attitude = AttitudeData(
                    roll=attitude.roll_deg,
                    pitch=attitude.pitch_deg,
                    yaw=attitude.yaw_deg
                )
        except Exception as e:
            logger.error(f"Attitude stream error: {e}")
    
    async def _stream_velocity(self):
        """Subscribe ke velocity stream"""
        try:
            async for velocity in self.drone.telemetry.velocity_ned():
                ground_speed = (velocity.north_m_s**2 + velocity.east_m_s**2)**0.5
                self.latest_velocity = VelocityData(
                    x=velocity.north_m_s,
                    y=velocity.east_m_s,
                    z=velocity.down_m_s,
                    ground_speed=ground_speed
                )
        except Exception as e:
            logger.error(f"Velocity stream error: {e}")
    
    async def _stream_battery(self):
        """Subscribe ke battery stream"""
        try:
            async for battery in self.drone.telemetry.battery():
                self.latest_battery = BatteryData(
                    voltage_v=battery.voltage_v,
                    current_a=battery.current_a,
                    remaining_percent=battery.remaining_percent,
                    health=battery.health_percent
                )
        except Exception as e:
            logger.error(f"Battery stream error: {e}")
    
    async def _stream_status(self):
        """Subscribe ke status stream"""
        try:
            armed_task = asyncio.create_task(self._watch_armed())
            flight_mode_task = asyncio.create_task(self._watch_flight_mode())
            in_air_task = asyncio.create_task(self._watch_in_air())
            
            await asyncio.gather(armed_task, flight_mode_task, in_air_task)
        except Exception as e:
            logger.error(f"Status stream error: {e}")
    
    async def _watch_armed(self):
        """Monitor armed status"""
        try:
            async for armed in self.drone.telemetry.armed():
                if self.latest_status:
                    self.latest_status.armed = armed
        except Exception as e:
            logger.error(f"Armed status error: {e}")
    
    async def _watch_flight_mode(self):
        """Monitor flight mode"""
        try:
            async for flight_mode in self.drone.telemetry.flight_mode():
                if self.latest_status:
                    self.latest_status.flight_mode = str(flight_mode)
        except Exception as e:
            logger.error(f"Flight mode error: {e}")
    
    async def _watch_in_air(self):
        """Monitor in-air status"""
        try:
            async for in_air in self.drone.telemetry.in_air():
                if self.latest_status:
                    self.latest_status.in_air = in_air
                else:
                    self.latest_status = StatusData(
                        armed=False,
                        flight_mode="UNKNOWN",
                        in_air=in_air,
                        is_connected=self.is_connected
                    )
        except Exception as e:
            logger.error(f"In-air status error: {e}")


# ============================================================================
# MQTT PUBLISHER
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
                client_id="crepes387_pixhawk",
                callback_api_version=CallbackAPIVersion.VERSION2
            )
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            
            cert_path = Path(__file__).resolve().parent / "emqxsl-ca.crt"
            if cert_path.exists():
                try:
                    self.client.tls_set(ca_certs=str(cert_path))
                    logger.info("✅ TLS certificate loaded")
                except Exception as e:
                    logger.warning(f"⚠️ TLS error, using insecure: {e}")
                    self.client.tls_set()
                    self.client.tls_insecure_set(True)
            else:
                self.client.tls_set()
                self.client.tls_insecure_set(True)
            
            self.client.username_pw_set(self.username, self.password)
            self.client.max_inflight_messages_set(5)
            
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
                logger.info(f"🚀 [{telemetry.sequence}] Published (sz:{len(json_string)} bytes)")
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
            logger.warning("⚠️ MQTT disconnected, will reconnect...")
        self.is_connected = False
    
    def _on_publish(self, client, userdata, mid, rc, prop):
        pass


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class TelemPublisher:
    """Main application - koordinate Pixhawk reader + MQTT publisher"""
    
    def __init__(self):
        self.pixhawk_connection = os.getenv("PIXHAWK_CONNECTION", "udpin://:14540")
        self.mqtt_broker = os.getenv("MQTT_BROKER", "ef6ff411.ala.asia-southeast1.emqxsl.com")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "8883"))
        self.mqtt_username = os.getenv("MQTT_USERNAME", "user1")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "public1")
        self.mqtt_topic = os.getenv("MQTT_TOPIC", "uav/telemetry/crepes387")
        self.publish_interval = float(os.getenv("PUBLISH_INTERVAL", "0.5"))
        
        default_output = Path(__file__).resolve().parent.parent / "data" / "latest.json"
        self.output_file = Path(os.getenv("TELEMETRY_OUTPUT_FILE", str(default_output)))
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.pixhawk = PixhawkReader(self.pixhawk_connection)
        self.mqtt = MQTTPublisher(
            self.mqtt_broker,
            self.mqtt_port,
            self.mqtt_username,
            self.mqtt_password,
            self.mqtt_topic
        )
    
    async def run(self):
        """Main application loop"""
        try:
            if not self.mqtt.setup_client():
                logger.error("Failed to setup MQTT client")
                return
            
            if not self.mqtt.connect():
                logger.error("Failed to connect to MQTT")
                return
            
            if not await self.pixhawk.connect():
                logger.error("Failed to connect to Pixhawk")
                self.mqtt.disconnect()
                return
            
            logger.info("🚀 Starting telemetry collection...")
            
            telemetry_task = asyncio.create_task(self.pixhawk.start_telemetry_streams())
            
            try:
                while True:
                    try:
                        telemetry = await self.pixhawk.read_telemetry()
                        self.mqtt.publish_telemetry(telemetry)
                        self.mqtt.save_to_file(telemetry, self.output_file)
                        await asyncio.sleep(self.publish_interval)
                        
                    except Exception as e:
                        logger.error(f"Publish loop error: {e}")
                        await asyncio.sleep(1)
                        
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping...")
                telemetry_task.cancel()
                await self.pixhawk.disconnect()
                self.mqtt.disconnect()
                
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.mqtt.disconnect()


# ============================================================================
# ENTRY POINT
# ============================================================================

async def main():
    """Entry point"""
    app = TelemPublisher()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())