"""
GCS MQTT→MAVLink Converter
Runs on the remote GCS computer (tidak connect ke Pixhawk langsung)
Subscribe ke MQTT, convert ke MAVLink, create local server untuk Mission Planner
"""

import asyncio
import json
import socket
import struct
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

# Import pymavlink untuk create MAVLink messages
from pymavlink.dialects.v10 import ardupilotmega as mavlink_module

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# TELEMETRY DATA MODELS (same as bridge)
# ============================================================================

@dataclass
class GPSData:
    latitude: float
    longitude: float
    altitude_msl: float
    altitude_relative: float
    satellite_count: int

@dataclass
class AttitudeData:
    roll: float
    pitch: float
    yaw: float

@dataclass
class VelocityData:
    x: float
    y: float
    z: float
    ground_speed: float

@dataclass
class BatteryData:
    voltage_v: float
    current_a: Optional[float]
    remaining_percent: float
    health: Optional[float]

@dataclass
class StatusData:
    armed: bool
    flight_mode: str
    in_air: bool
    is_connected: bool

@dataclass
class PixhawkTelemetry:
    timestamp: str
    gps: GPSData
    attitude: AttitudeData
    velocity: VelocityData
    battery: BatteryData
    status: StatusData
    sequence: int


# ============================================================================
# MQTT SUBSCRIBER
# ============================================================================

class MQTTSubscriber:
    """Subscribe ke MQTT dan cache latest telemetry"""
    
    def __init__(self, broker_address: str, port: int, username: str, password: str, topic: str):
        self.broker_address = broker_address
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.client = None
        self.is_connected = False
        
        # Latest telemetry
        self.latest_telemetry = None
    
    def setup_client(self) -> bool:
        """Setup MQTT client"""
        try:
            self.client = mqtt.Client(
                client_id="gcs_mqtt_converter",
                callback_api_version=CallbackAPIVersion.VERSION2
            )
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # TLS setup
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
    
    def _on_connect(self, client, userdata, flags, rc, prop):
        if rc == 0:
            logger.info("✅ Connected to MQTT broker")
            self.is_connected = True
            # Subscribe ke topic
            client.subscribe(self.topic, qos=0)
            logger.info(f"📡 Subscribed to: {self.topic}")
        else:
            logger.error(f"❌ MQTT connection failed: {rc}")
    
    def _on_disconnect(self, client, userdata, flags, rc, prop):
        if rc != 0:
            logger.warning("⚠️ MQTT disconnected, will reconnect...")
        self.is_connected = False
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT message"""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Parse telemetry
            self.latest_telemetry = PixhawkTelemetry(
                timestamp=payload['ts'],
                gps=GPSData(**payload['gps']),
                attitude=AttitudeData(**payload['attitude']),
                velocity=VelocityData(**payload['velocity']),
                battery=BatteryData(**payload['battery']),
                status=StatusData(**payload['status']),
                sequence=payload['seq']
            )
            
            logger.debug(f"📨 Received seq {self.latest_telemetry.sequence}")
            
        except Exception as e:
            logger.error(f"Failed to parse MQTT message: {e}")


# ============================================================================
# MAVLink SERVER
# ============================================================================

class MAVLinkServer:
    """
    Broadcast MAVLink messages ke clients (Mission Planner, dll)
    Converts telemetry data ke MAVLink messages
    """
    
    def __init__(self, listen_port: int = 14550):
        self.listen_port = listen_port
        self.server = None
        self.clients = set()
        self.mavlink = mavlink_module.MAVLink(None, check_length=False)
        self.system_id = 1
        self.component_id = 1
        self.sequence = 0
        self.heartbeat_count = 0
    
    async def start(self):
        """Start MAVLink server"""
        self.server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            self.listen_port
        )
        
        logger.info(f"✅ MAVLink server listening on 0.0.0.0:{self.listen_port}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def handle_client(self, reader, writer):
        """Handle client connection (Mission Planner)"""
        addr = writer.get_extra_info('peername')
        logger.info(f"📱 Client connected: {addr}")
        self.clients.add((reader, writer))
        
        try:
            while True:
                # Keep connection open
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            self.clients.discard((reader, writer))
            writer.close()
            await writer.wait_closed()
            logger.info(f"📱 Client disconnected: {addr}")
    
    async def broadcast_telemetry(self, telemetry: PixhawkTelemetry):
        """Convert telemetry to MAVLink messages dan broadcast"""
        
        # Create MAVLink messages
        messages = [
            self._create_heartbeat(telemetry),
            self._create_global_position_int(telemetry),
            self._create_attitude(telemetry),
            self._create_vfr_hud(telemetry),
            self._create_battery_status(telemetry),
            self._create_sys_status(telemetry),
        ]
        
        # Send ke semua connected clients
        dead_clients = []
        for reader, writer in self.clients:
            for msg in messages:
                try:
                    packet = msg.get_msgbuf()
                    writer.write(packet)
                    await writer.drain()
                except Exception as e:
                    logger.debug(f"Failed to send to client: {e}")
                    dead_clients.append((reader, writer))
        
        # Remove dead clients
        for client in dead_clients:
            self.clients.discard(client)
    
    def _create_heartbeat(self, telemetry: PixhawkTelemetry):
        """HEARTBEAT message"""
        self.heartbeat_count += 1
        
        base_mode = 0x80 if telemetry.status.armed else 0x00  # Armed bit
        
        # Map flight mode to custom_mode
        mode_map = {
            "STABILIZE": 0, "ACRO": 1, "ALT_HOLD": 2, "AUTO": 3,
            "GUIDED": 4, "LOITER": 5, "RTL": 6, "CIRCLE": 7,
            "POSITION": 8, "LAND": 9, "OF_LOITER": 10
        }
        custom_mode = mode_map.get(telemetry.status.flight_mode, 0)
        
        msg = self.mavlink.heartbeat_encode(
            type=2,  # QUADROTOR
            autopilot=4,  # ARDUPILOT
            base_mode=base_mode,
            custom_mode=custom_mode,
            system_status=4 if telemetry.status.in_air else 3  # ACTIVE or STANDBY
        )
        return msg
    
    def _create_global_position_int(self, telemetry: PixhawkTelemetry):
        """GLOBAL_POSITION_INT message"""
        msg = self.mavlink.global_position_int_encode(
            time_boot_ms=int(self.sequence * 100),  # Approximate
            lat=int(telemetry.gps.latitude * 1e7),
            lon=int(telemetry.gps.longitude * 1e7),
            alt=int(telemetry.gps.altitude_msl * 1000),  # mm
            relative_alt=int(telemetry.gps.altitude_relative * 1000),  # mm
            vx=int(telemetry.velocity.x * 100),  # cm/s
            vy=int(telemetry.velocity.y * 100),
            vz=int(telemetry.velocity.z * 100),
            hdg=int(telemetry.attitude.yaw * 100)  # centidegrees
        )
        return msg
    
    def _create_attitude(self, telemetry: PixhawkTelemetry):
        """ATTITUDE message"""
        msg = self.mavlink.attitude_encode(
            time_boot_ms=int(self.sequence * 100),
            roll=telemetry.attitude.roll,
            pitch=telemetry.attitude.pitch,
            yaw=telemetry.attitude.yaw,
            rollspeed=0.0,
            pitchspeed=0.0,
            yawspeed=0.0
        )
        return msg
    
    def _create_vfr_hud(self, telemetry: PixhawkTelemetry):
        """VFR_HUD message"""
        msg = self.mavlink.vfr_hud_encode(
            airspeed=telemetry.velocity.ground_speed,
            groundspeed=telemetry.velocity.ground_speed,
            heading=int(telemetry.attitude.yaw),
            throttle=0,  # Unknown
            alt=telemetry.gps.altitude_relative,
            climb=telemetry.velocity.z
        )
        return msg
    
    def _create_battery_status(self, telemetry: PixhawkTelemetry):
        """BATTERY_STATUS message"""
        current_ma = int((telemetry.battery.current_a or 0) * 100)  # centiamps
        
        msg = self.mavlink.battery_status_encode(
            id=0,
            battery_function=0,  # BATTERY_FUNCTION_UNKNOWN
            type=4,  # BATTERY_TYPE_LIPO
            temperature=0,  # Unknown
            voltages=[int(telemetry.battery.voltage_v * 1000)] + [65535] * 9,  # mV
            current_battery=current_ma,
            current_consumed=0,
            energy_consumed=0,
            battery_remaining=int(telemetry.battery.remaining_percent),
            time_remaining=0,
            charge_state=0
        )
        return msg
    
    def _create_sys_status(self, telemetry: PixhawkTelemetry):
        """SYS_STATUS message"""
        msg = self.mavlink.sys_status_encode(
            onboard_control_sensors_present=65535,
            onboard_control_sensors_enabled=65535,
            onboard_control_sensors_health=65535,
            load=0,
            voltage_battery=int(telemetry.battery.voltage_v * 1000),  # mV
            current_battery=int((telemetry.battery.current_a or 0) * 100),  # cA
            battery_remaining=int(telemetry.battery.remaining_percent),
            drop_rate_comm=0,
            errors_comm=0,
            errors_count1=0,
            errors_count2=0,
            errors_count3=0,
            errors_count4=0
        )
        return msg


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class GCSMQTTConverter:
    """Main app: Subscribe MQTT → Broadcast as MAVLink"""
    
    def __init__(self):
        import os
        
        # MQTT config
        self.mqtt_broker = os.getenv("MQTT_BROKER", "ef6ff411.ala.asia-southeast1.emqxsl.com")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "8883"))
        self.mqtt_username = os.getenv("MQTT_USERNAME", "user1")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "public1")
        self.mqtt_topic = os.getenv("MQTT_TOPIC", "uav/telemetry/crepes387")
        
        # MAVLink server config
        self.mavlink_port = int(os.getenv("MAVLINK_SERVER_PORT", "14550"))
        self.broadcast_interval = float(os.getenv("BROADCAST_INTERVAL", "0.1"))  # 10Hz
        
        # Components
        self.subscriber = MQTTSubscriber(
            self.mqtt_broker,
            self.mqtt_port,
            self.mqtt_username,
            self.mqtt_password,
            self.mqtt_topic
        )
        self.server = MAVLinkServer(self.mavlink_port)
    
    async def run(self):
        """Main loop"""
        try:
            # Setup MQTT
            if not self.subscriber.setup_client():
                logger.error("Failed to setup MQTT client")
                return
            
            if not self.subscriber.connect():
                logger.error("Failed to connect to MQTT")
                return
            
            logger.info("🌍 Starting GCS MQTT↔MAVLink converter...")
            
            # Give MQTT time to connect
            await asyncio.sleep(2)
            
            # Start MAVLink server task
            server_task = asyncio.create_task(self.server.start())
            
            # Broadcast telemetry loop
            broadcast_task = asyncio.create_task(self._broadcast_loop())
            
            try:
                await asyncio.gather(server_task, broadcast_task)
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping...")
                broadcast_task.cancel()
                server_task.cancel()
                self.subscriber.disconnect()
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.subscriber.disconnect()
    
    async def _broadcast_loop(self):
        """Broadcast telemetry ke connected clients"""
        while True:
            try:
                if self.subscriber.latest_telemetry:
                    await self.server.broadcast_telemetry(self.subscriber.latest_telemetry)
                    logger.debug(f"📡 Broadcast seq {self.subscriber.latest_telemetry.sequence}")
                
                await asyncio.sleep(self.broadcast_interval)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                await asyncio.sleep(1)


# ============================================================================
# ENTRY POINT
# ============================================================================

async def main():
    """Entry point"""
    import os
    app = GCSMQTTConverter()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
