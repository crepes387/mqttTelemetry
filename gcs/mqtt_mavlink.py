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
from pymavlink.dialects.v20 import ardupilotmega as mavlink_module  # MAVLink v2

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # ✅ UBAH KE DEBUG UNTUK DEBUGGING
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
            
            # Log setiap 5 messages
            if self.latest_telemetry.sequence % 5 == 0:
                logger.info(f"📨 Received MQTT seq {self.latest_telemetry.sequence}: GPS={self.latest_telemetry.gps.latitude:.4f},{self.latest_telemetry.gps.longitude:.4f} | Battery={self.latest_telemetry.battery.remaining_percent}%")
            else:
                logger.debug(f"📨 Received MQTT seq {self.latest_telemetry.sequence}")
            
        except Exception as e:
            logger.error(f"❌ Failed to parse MQTT message: {e}", exc_info=True)


# ============================================================================
# MAVLink SERVER
# ============================================================================

class MAVLinkServer:
    """
    Broadcast MAVLink messages ke clients (Mission Planner, dll)
    Converts telemetry data ke MAVLink messages
    """
    
    def __init__(self, listen_port: int = 14550):
        import io
        self.listen_port = listen_port
        self.server = None
        self.clients = set()
        # ✅ FIX: Gunakan io.BytesIO agar pack() increment sequence dengan benar (MAVLink v2)
        self._mav_buf = io.BytesIO()
        self.mavlink = mavlink_module.MAVLink(self._mav_buf)
        self.mavlink.srcSystem = 1
        self.mavlink.srcComponent = 1
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
        logger.info(f"💡 Mission Planner should connect to: 127.0.0.1:{self.listen_port} (TCP)")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def handle_client(self, reader, writer):
        """Handle client connection (Mission Planner)"""
        addr = writer.get_extra_info('peername')
        logger.info(f"📱 Client connected: {addr} (Total: {len(self.clients) + 1})")
        self.clients.add((reader, writer))

        # Kirim heartbeat segera + param list supaya MP tidak stuck
        await self._send_initial_heartbeat(writer, addr)
        await self._send_param_list(writer, addr)

        try:
            while True:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=5.0)
                    if not data:
                        logger.info(f"📱 Client {addr} closed connection (EOF)")
                        break
                    logger.debug(f"📥 Received {len(data)} bytes from {addr}")
                    await self._handle_incoming_mavlink(data, writer, addr)
                except asyncio.TimeoutError:
                    pass
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.warning(f"⚠️ Read error from {addr}: {e}")
                    break
        except asyncio.CancelledError:
            logger.debug("Client handler cancelled")
        except Exception as e:
            logger.error(f"❌ Client handler error: {e}")
        finally:
            self.clients.discard((reader, writer))
            writer.close()
            try:
                await writer.wait_closed()
            except:
                pass
            logger.info(f"📱 Client disconnected: {addr} (Remaining: {len(self.clients)})")
    

    async def _send_initial_heartbeat(self, writer, addr):
        """Kirim heartbeat segera saat client connect."""
        try:
            msg = self.mavlink.heartbeat_encode(
                type=2, autopilot=4, base_mode=0x01, custom_mode=4, system_status=3
            )
            writer.write(msg.pack(self.mavlink))
            await writer.drain()
            logger.info(f"💓 Sent initial HEARTBEAT to {addr}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to send initial heartbeat: {e}")

    # Minimal params agar Mission Planner tidak stuck di "Getting params"
    FAKE_PARAMS = [
        ("SYSID_THISMAV",   1.0,  mavlink_module.MAV_PARAM_TYPE_INT32),
        ("SYSID_MYGCS",   255.0,  mavlink_module.MAV_PARAM_TYPE_INT32),
        ("ARMING_CHECK",    1.0,  mavlink_module.MAV_PARAM_TYPE_INT32),
        ("BRD_TYPE",        0.0,  mavlink_module.MAV_PARAM_TYPE_INT32),
        ("FRAME_CLASS",     1.0,  mavlink_module.MAV_PARAM_TYPE_INT32),
        ("FRAME_TYPE",      1.0,  mavlink_module.MAV_PARAM_TYPE_INT32),
        ("FS_THR_ENABLE",   1.0,  mavlink_module.MAV_PARAM_TYPE_INT32),
        ("BATT_MONITOR",    4.0,  mavlink_module.MAV_PARAM_TYPE_INT32),
        ("GPS_TYPE",        1.0,  mavlink_module.MAV_PARAM_TYPE_INT32),
        ("INS_ENABLE_MASK", 1.0,  mavlink_module.MAV_PARAM_TYPE_INT32),
    ]

    async def _send_param_list(self, writer, addr):
        """Balas PARAM_REQUEST_LIST — inilah yang bikin MP stuck kalau tidak dibalas."""
        logger.info(f"📋 Sending {len(self.FAKE_PARAMS)} params to {addr}")
        total = len(self.FAKE_PARAMS)
        for idx, (name, value, ptype) in enumerate(self.FAKE_PARAMS):
            try:
                msg = self.mavlink.param_value_encode(
                    param_id=name.encode().ljust(16, b"\x00")[:16],
                    param_value=value,
                    param_type=ptype,
                    param_count=total,
                    param_index=idx
                )
                writer.write(msg.pack(self.mavlink))
            except Exception as e:
                logger.warning(f"⚠️ param encode error ({name}): {e}")
        try:
            await writer.drain()
            logger.info(f"✅ Param list sent ({total} params) to {addr}")
        except Exception as e:
            logger.warning(f"⚠️ drain error after param list: {e}")

    async def _handle_incoming_mavlink(self, data: bytes, writer, addr):
        """Parse MAVLink frames dari Mission Planner dan balas request yang perlu."""
        try:
            parser = mavlink_module.MAVLink(None)
            parser.robust_parsing = True
            msgs = parser.parse_buffer(data)
            if not msgs:
                return
            for msg in msgs:
                mtype = msg.get_type()
                logger.debug(f"📨 MP→GCS: {mtype}")

                if mtype == "PARAM_REQUEST_LIST":
                    logger.info("📋 MP sent PARAM_REQUEST_LIST → replying")
                    await self._send_param_list(writer, addr)

                elif mtype == "PARAM_REQUEST_READ":
                    raw_id = msg.param_id
                    if isinstance(raw_id, bytes):
                        name = raw_id.rstrip(b"\x00").decode("utf-8", errors="ignore")
                    else:
                        name = str(raw_id).strip("\x00")
                    val = next((v for n, v, t in self.FAKE_PARAMS if n == name), 0.0)
                    ptype = next((t for n, v, t in self.FAKE_PARAMS if n == name),
                                 mavlink_module.MAV_PARAM_TYPE_REAL32)
                    try:
                        reply = self.mavlink.param_value_encode(
                            param_id=name.encode().ljust(16, b"\x00")[:16],
                            param_value=val, param_type=ptype,
                            param_count=len(self.FAKE_PARAMS), param_index=0
                        )
                        writer.write(reply.pack(self.mavlink))
                        await writer.drain()
                        logger.debug(f"📤 Replied param {name}={val}")
                    except Exception as e:
                        logger.warning(f"param_request_read reply error: {e}")

                elif mtype == "REQUEST_DATA_STREAM":
                    try:
                        ack = self.mavlink.data_stream_encode(
                            stream_id=msg.req_stream_id,
                            message_rate=msg.req_message_rate,
                            on_off=msg.start_stop
                        )
                        writer.write(ack.pack(self.mavlink))
                        await writer.drain()
                        logger.debug(f"📤 ACK data_stream {msg.req_stream_id}")
                    except Exception as e:
                        logger.debug(f"data_stream ack skipped: {e}")

                elif mtype == "HEARTBEAT":
                    logger.debug(f"💓 HB from MP sysid={msg.get_srcSystem()}")

        except Exception as e:
            logger.debug(f"MAVLink parse warning (non-fatal): {e}")

    def _build_packets(self, telemetry: PixhawkTelemetry) -> bytes:
        """
        Build semua MAVLink packets ke dalam satu buffer bytes.
        Menggunakan io.BytesIO agar sequence number auto-increment dengan benar.
        """
        import io, math
        buf = io.BytesIO()
        mav = mavlink_module.MAVLink(buf)
        mav.srcSystem = self.system_id
        mav.srcComponent = self.component_id

        # --- HEARTBEAT ---
        base_mode = (0x80 | 0x01) if telemetry.status.armed else 0x01
        mode_map = {
            "STABILIZE":0,"ACRO":1,"ALT_HOLD":2,"AUTO":3,"GUIDED":4,
            "LOITER":5,"RTL":6,"CIRCLE":7,"POSITION":8,"LAND":9
        }
        custom_mode = mode_map.get(telemetry.status.flight_mode, 4)
        mav.heartbeat_send(
            type=1, autopilot=3,
            base_mode=base_mode,
            custom_mode=custom_mode,
            system_status=4 if telemetry.status.in_air else 3,
            mavlink_version=3
        )

        # --- ATTITUDE (radian!) ---
        mav.attitude_send(
            time_boot_ms=self.sequence * 100,
            roll=telemetry.attitude.roll,
            pitch=telemetry.attitude.pitch,
            yaw=telemetry.attitude.yaw,
            rollspeed=0.0, pitchspeed=0.0, yawspeed=0.0
        )

        # --- GLOBAL_POSITION_INT ---

        yaw_deg = math.degrees(telemetry.attitude.yaw)
        hdg_cd = yaw_deg % 360
        if hdg_cd < 0: hdg_cd += 360
        hdg_cd = int(hdg_cd * 100)  # centidegrees

        mav.global_position_int_send(
            time_boot_ms=self.sequence * 100,
            lat=int(telemetry.gps.latitude * 1e7),
            lon=int(telemetry.gps.longitude * 1e7),
            alt=int(telemetry.gps.altitude_msl * 1000),
            relative_alt=int(telemetry.gps.altitude_relative * 1000),
            vx=int(telemetry.velocity.x * 100),
            vy=int(telemetry.velocity.y * 100),
            vz=int(telemetry.velocity.z * 100),
            hdg=hdg_cd
        )

        # --- GPS_RAW_INT (wajib untuk GPS status bar di MP) ---
        gps_fix = 3 if telemetry.gps.satellite_count >= 6 else (1 if telemetry.gps.satellite_count > 0 else 0)
        mav.gps_raw_int_send(
            time_usec=0,
            fix_type=gps_fix,
            lat=int(telemetry.gps.latitude * 1e7),
            lon=int(telemetry.gps.longitude * 1e7),
            alt=int(telemetry.gps.altitude_msl * 1000),
            eph=65535, epv=65535,
            vel=int(telemetry.velocity.ground_speed * 100),
            cog=hdg_cd,
            satellites_visible=telemetry.gps.satellite_count
        )

        # --- SYS_STATUS (battery untuk HUD) ---
        sensors = 0x1 | 0x2 | 0x4 | 0x20 | 0x40000
        current_ca = int(telemetry.battery.current_a * 100) if telemetry.battery.current_a is not None else -1
        mav.sys_status_send(
            onboard_control_sensors_present=sensors,
            onboard_control_sensors_enabled=sensors,
            onboard_control_sensors_health=sensors,
            load=0,
            voltage_battery=int(telemetry.battery.voltage_v * 1000),
            current_battery=current_ca,
            battery_remaining=int(telemetry.battery.remaining_percent),
            drop_rate_comm=0, errors_comm=0,
            errors_count1=0, errors_count2=0, errors_count3=0, errors_count4=0
        )

        # --- BATTERY_STATUS ---
        mav.battery_status_send(
            id=0, battery_function=0, type=4,
            temperature=32767,
            voltages=[int(telemetry.battery.voltage_v * 1000)] + [65535]*9,
            current_battery=current_ca,
            current_consumed=-1, energy_consumed=-1,
            battery_remaining=int(telemetry.battery.remaining_percent)
        )

        # --- VFR_HUD ---
        heading_deg = int(telemetry.attitude.yaw % 360)
        if heading_deg < 0: heading_deg += 360
        mav.vfr_hud_send(
            airspeed=float(telemetry.velocity.ground_speed),
            groundspeed=float(telemetry.velocity.ground_speed),
            heading=heading_deg,
            throttle=0,
            alt=float(telemetry.gps.altitude_relative),
            climb=float(-telemetry.velocity.z)
        )

        buf.seek(0)
        return buf.read()

    async def broadcast_telemetry(self, telemetry: PixhawkTelemetry):
        """Convert telemetry to MAVLink packets dan broadcast ke semua clients"""
        try:
            self.sequence = (self.sequence + 1) % 256
            packet_data = self._build_packets(telemetry)
            logger.debug(f"📦 Built {len(packet_data)} bytes MAVLink data (7 messages)")

            dead_clients = []
            current_clients = set(self.clients)
            if current_clients:
                for reader, writer in current_clients:
                    try:
                        writer.write(packet_data)
                        await writer.drain()
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to send to client: {e}")
                        dead_clients.append((reader, writer))
            else:
                logger.debug("⏸️ No clients connected, messages not sent")

            for client in dead_clients:
                self.clients.discard(client)
                logger.warning("⚠️ Removed dead client")

        except Exception as e:
            logger.error(f"❌ Unexpected error in broadcast_telemetry: {e}", exc_info=True)
    
    def _create_heartbeat(self, telemetry: PixhawkTelemetry):
        """HEARTBEAT message"""
        self.heartbeat_count += 1
        
        # For MAVProxy/Mission Planner: armed requires bit 7 (0x80) in base_mode
        base_mode = 0x81 if telemetry.status.armed else 0x01  # 0x01 = GUIDED mode, 0x80 = ARMED
        
        # Map flight mode to custom_mode
        mode_map = {
            "STABILIZE": 0, "ACRO": 1, "ALT_HOLD": 2, "AUTO": 3,
            "GUIDED": 4, "LOITER": 5, "RTL": 6, "CIRCLE": 7,
            "POSITION": 8, "LAND": 9, "OF_LOITER": 10
        }
        custom_mode = mode_map.get(telemetry.status.flight_mode, 4)  # Default to GUIDED
        
        msg = self.mavlink.heartbeat_encode(
            type=2,  # QUADROTOR (ArduCopter)
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
            hdg=int((telemetry.attitude.yaw % 360) * 100) if telemetry.attitude.yaw >= 0 else int(((telemetry.attitude.yaw % 360) + 360) * 100)  # centidegrees 0-35999
        )
        return msg
    
    def _create_attitude(self, telemetry: PixhawkTelemetry):
        """ATTITUDE message — roll/pitch/yaw dalam RADIAN (MAVLink spec)"""
        import math
        # MAVSDK/Pixhawk mengirim derajat, MAVLink ATTITUDE butuh radian
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
        # Heading harus 0-359 (yaw bisa -180~180 → normalize ke 0~360)
        heading = int(telemetry.attitude.yaw % 360)
        if heading < 0:
            heading += 360
        # NED convention: vz positif = turun, climb di MP = positif naik → invert
        climb = -telemetry.velocity.z
        msg = self.mavlink.vfr_hud_encode(
            airspeed=float(telemetry.velocity.ground_speed),
            groundspeed=float(telemetry.velocity.ground_speed),
            heading=heading,
            throttle=0,
            alt=float(telemetry.gps.altitude_relative),
            climb=float(climb)
        )
        return msg
    
    def _create_battery_status(self, telemetry: PixhawkTelemetry):
        """BATTERY_STATUS message"""
        # current_battery: centiamps, -1 = unknown (jangan 0 karena 0 = valid)
        if telemetry.battery.current_a is not None:
            current_ca = int(telemetry.battery.current_a * 100)
        else:
            current_ca = -1
        # voltages: per-cell mV, cell tidak dipakai diisi 65535 (UINT16_MAX = invalid)
        voltage_mv = int(telemetry.battery.voltage_v * 1000)
        msg = self.mavlink.battery_status_encode(
            id=0,
            battery_function=0,       # BATTERY_FUNCTION_UNKNOWN
            type=4,                    # BATTERY_TYPE_LIPO
            temperature=32767,         # INT16_MAX = tidak tersedia (bukan 0°C)
            voltages=[voltage_mv] + [65535] * 9,
            current_battery=current_ca,
            current_consumed=-1,       # -1 = unknown
            energy_consumed=-1,        # -1 = unknown
            battery_remaining=int(telemetry.battery.remaining_percent)
        )
        return msg
    
    def _create_sys_status(self, telemetry: PixhawkTelemetry):
        """SYS_STATUS message"""
        # Sensor bitmask realistis untuk ArduCopter dengan GPS
        # MAV_SYS_STATUS_SENSOR: 3DGYRO|3DACCEL|3DMAG|GPS|AHRS
        sensors = (0x1 | 0x2 | 0x4 | 0x20 | 0x40000)
        # current_battery: centiamps (cA), -1 jika tidak tersedia
        if telemetry.battery.current_a is not None:
            current_ca = int(telemetry.battery.current_a * 100)
        else:
            current_ca = -1
        msg = self.mavlink.sys_status_encode(
            onboard_control_sensors_present=sensors,
            onboard_control_sensors_enabled=sensors,
            onboard_control_sensors_health=sensors,
            load=0,
            voltage_battery=int(telemetry.battery.voltage_v * 1000),  # mV
            current_battery=current_ca,                                # cA
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
            # Log configuration
            logger.info("=" * 80)
            logger.info("🌍 GCS MQTT ↔ MAVLink Converter Configuration")
            logger.info("=" * 80)
            logger.info(f"📡 MQTT Broker: {self.subscriber.broker_address}:{self.subscriber.port}")
            logger.info(f"📝 MQTT Topic: {self.subscriber.topic}")
            logger.info(f"🔗 MAVLink Server: 0.0.0.0:{self.server.listen_port}")
            logger.info(f"⏱️ Broadcast Interval: {self.broadcast_interval * 1000:.0f}ms ({1/self.broadcast_interval:.1f}Hz)")
            logger.info("=" * 80)
            
            # Setup MQTT
            if not self.subscriber.setup_client():
                logger.error("❌ Failed to setup MQTT client")
                return
            
            if not self.subscriber.connect():
                logger.error("❌ Failed to connect to MQTT")
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
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
            self.subscriber.disconnect()
    
    async def _broadcast_loop(self):
        """Broadcast telemetry ke connected clients"""
        broadcast_count = 0
        
        while True:
            try:
                if self.subscriber.latest_telemetry:
                    await self.server.broadcast_telemetry(self.subscriber.latest_telemetry)
                    broadcast_count += 1
                    
                    # Log setiap 10 broadcasts
                    if broadcast_count % 10 == 0:
                        logger.info(f"📡 Broadcasting seq {self.subscriber.latest_telemetry.sequence} to {len(self.server.clients)} client(s)")
                else:
                    logger.debug("⏳ Waiting for MQTT telemetry data...")
                
                await asyncio.sleep(self.broadcast_interval)
            except Exception as e:
                logger.error(f"❌ Broadcast error: {e}", exc_info=True)
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