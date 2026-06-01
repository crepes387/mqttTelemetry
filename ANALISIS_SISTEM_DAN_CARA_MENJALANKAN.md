# 🎯 ANALISIS SISTEM MQTT TELEMETRY + CARA MENJALANKAN

## ✅ STATUS SISTEM

- **Syntax Errors**: ❌ TIDAK ADA
- **Dependencies**: ✅ LENGKAP (sudah dikonfigurasi di requirements.txt)
- **Structure**: ✅ LENGKAP
- **Dokumentasi**: ✅ LENGKAP

---

## 🏗️ ARSITEKTUR SISTEM

### Komponen Utama

```
┌──────────────────────────────────────────────────────────────┐
│                    MQTT TELEMETRY SYSTEM                      │
└──────────────────────────────────────────────────────────────┘

┌─ SENDER SIDE (Aircraft/Drone) ─────────────────────────────┐
│                                                              │
│  ┌─────────────┐                                             │
│  │  PIXHAWK    │ (Drone Flight Controller)                   │
│  │  atau SITL  │ (Simulator)                                 │
│  └──────┬──────┘                                             │
│         │ MAVLink (UDP Port 14540)                           │
│         ▼                                                    │
│  ┌──────────────────┐                                        │
│  │   MAVProxy       │ Hub untuk multiple outputs              │
│  │   (Server)       │                                        │
│  ├──────────────────┤                                        │
│  │ Input:  14540    │                                        │
│  │ Output: 14550    │ → Mission Planner                      │
│  │ Output: 14551    │ → MAVLink Bridge (UDP Listener)        │
│  └────────┬─────────┘                                        │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────┐                                 │
│  │  mavlink_bridge.py      │                                 │
│  │  - Listen UDP 14551     │                                 │
│  │  - Parse MAVLink        │                                 │
│  │  - Convert to JSON      │                                 │
│  │  - Publish to MQTT      │                                 │
│  └────────┬────────────────┘                                 │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────┐                                    │
│  │  MQTT Broker         │                                    │
│  │  - EMQX / HiveMQ     │                                    │
│  │  - Mosquitto         │                                    │
│  │  Topic:              │                                    │
│  │ uav/telemetry/crepes387                                   │
│  └────────┬─────────────┘                                    │
└───────────┼──────────────────────────────────────────────────┘
            │
            │ MQTT Network
            │ (WiFi / Internet)
            │
┌───────────┼──────────────────────────────────────────────────┐
│ ┌─────────▼─────────────────────────────────────────────────┤
│ │                                                             │
│ │ ┌─ RECEIVER SIDE (GCS/Ground Control Station) ─────────┐  │
│ │ │                                                        │  │
│ │ │  ┌─────────────────────────────┐                     │  │
│ │ │  │  MQTT Subscriber            │                     │  │
│ │ │  │  - Subscribe MQTT Topic     │                     │  │
│ │ │  │  - Receive JSON Telemetry   │                     │  │
│ │ │  └──────────┬──────────────────┘                     │  │
│ │ │             │                                         │  │
│ │ │             ▼                                         │  │
│ │ │  ┌─────────────────────────────┐                     │  │
│ │ │  │  mqtt_to_mavlink_gcs.py     │                     │  │
│ │ │  │  - Convert JSON → MAVLink   │                     │  │
│ │ │  │  - Create UDP Server        │                     │  │
│ │ │  │  - Listen on 14550          │                     │  │
│ │ │  └──────────┬──────────────────┘                     │  │
│ │ │             │                                         │  │
│ │ │             ▼                                         │  │
│ │ │  ┌─────────────────────────────┐                     │  │
│ │ │  │  Mission Planner            │                     │  │
│ │ │  │  - Visualize telemetry      │                     │  │
│ │ │  │  - Control missions         │                     │  │
│ │ │  │  - Manage waypoints         │                     │  │
│ │ │  └─────────────────────────────┘                     │  │
│ │ │                                                        │  │
│ │ └────────────────────────────────────────────────────────┘  │
│ │                                                             │
│ │ ┌─ DASHBOARD (Optional) ──────────────────────────────────┐  │
│ │ │  Browser: http://localhost:8000                         │  │
│ │ │  - Real-time map                                        │  │
│ │ │  - Battery status                                       │  │
│ │ │  - Attitude gauge                                       │  │
│ │ └─────────────────────────────────────────────────────────┘  │
│ │                                                             │
│ └─────────────────────────────────────────────────────────────┘
│
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ ISSUES YANG DITEMUKAN

| # | Issue | Severity | Solusi |
|---|-------|----------|--------|
| 1 | MQTT credentials tidak dikonfigurasi | 🔴 HIGH | Set environment variables sebelum run |
| 2 | Port 14540, 14550, 14551 mungkin conflict | 🔴 HIGH | Kill process jika ada yang pakai port |
| 3 | TLS certificate `emqxsl-ca.crt` tidak ada | 🟡 MEDIUM | Script sudah handle fallback ke insecure |
| 4 | `.env` file tidak ada | 🟡 MEDIUM | Manual set environment variables atau hardcode |
| 5 | Dua file yang berbeda (publisher.py vs mavlink_bridge.py) | 🟢 LOW | Tidak ada masalah, pilih salah satu yang cocok |
| 6 | Dashboard service tidak auto-start | 🟢 LOW | Manual run jika ingin dashboard |

---

## 🚀 CARA MENJALANKAN

### OPSI 1: SIMPLE LOCAL (Recommended untuk Testing)
**Setup**: Pixhawk (atau SITL) + MAVProxy + Mission Planner + Bridge = 1 PC

#### Terminal 1: Jalankan MAVProxy (Hub)

**UNTUK PIXHAWK VIA SERIAL COM12 (RECOMMENDED):**
```bash
cd d:\AgumAgum\coding\mqttTelemetry

# Jalankan MAVProxy dengan serial connection ke COM12
mavproxy.py --master COM12 --baudrate 57600 ^
    --out=tcpin:0.0.0.0:14550 ^
    --out=udpout:0.0.0.0:14551
```

**Output yang diharapkan:**
```
Connect COM12 source_system=255
Detected vehicle 1:1 on link 0
Received 995 parameters (ftp)
MANUAL>
```

**Penjelasan:**
- `--master COM12` → Serial connection ke Pixhawk di COM12
- `--baudrate 57600` → Kecepatan komunikasi (default Pixhawk)
- `--out=tcpin:0.0.0.0:14550` → TCP Server untuk Mission Planner
- `--out=udpout:0.0.0.0:14551` → UDP Output ke Bridge

**⚠️ PENTING - Kecepatan Baud Rate:**
- Pixhawk default: **57600**
- Jika tidak bekerja, coba: 115200
- Untuk mengecek di Mission Planner: COM Port Settings → Baud Rate

**Jika ingin test dengan SITL (tanpa hardware):**
```bash
mavproxy.py --master=udpin://0.0.0.0:14540 ^
    --out=tcpin:0.0.0.0:14550 ^
    --out=udpout:0.0.0.0:14551
```

---

#### Terminal 2: Jalankan MAVLink Bridge
```bash
cd d:\AgumAgum\coding\mqttTelemetry\publisher

# Set MQTT Credentials (Windows PowerShell)
$env:MQTT_BROKER="broker.emqxsl.com"  # atau "localhost" untuk Mosquitto lokal
$env:MQTT_PORT="8883"
$env:MQTT_USERNAME="user1"
$env:MQTT_PASSWORD="public1"
$env:MQTT_TOPIC="uav/telemetry/crepes387"

# Atau (Linux/Mac):
# export MQTT_BROKER="broker.emqxsl.com"
# export MQTT_PORT="8883"
# export MQTT_USERNAME="user1"
# export MQTT_PASSWORD="public1"

# Jalankan bridge
python mavlink_bridge.py
```

**Output yang diharapkan:**
```
✅ Connected to MQTT broker (broker.emqxsl.com:8883)
✅ Listening on UDP port 14551
🚀 Publishing telemetry to uav/telemetry/crepes387
📍 GPS: 0.000000, 0.000000, Alt: 0m
🔋 Battery: 12.60V, 100%, 0.0A
🔄 Attitude: R=0.05°, P=-0.02°, Y=45.20°
⚡ Velocity: 0.00 m/s
📡 Armed: False, Flight Mode: UNKNOWN
🎯 Published seq 1 (245 bytes)
```

---

#### Terminal 3: Buka Mission Planner
```bash
# Download dari: https://ardupilot.org/planner/

# Atau jika sudah install:
# Windows: Cari aplikasi "Mission Planner" di Start Menu
# Linux: mission-planner (jika sudah install via apt)
```

**Connection Steps:**
1. Buka Mission Planner
2. Klik dropdown di kanan atas (shows "COM3" atau similar)
3. Pilih **TCP** dari dropdown
4. IP: `127.0.0.1`
5. Port: `14550`
6. Klik **CONNECT**

**Jika berhasil:**
- ✅ "Connected" di top bar
- 🗺️ Map muncul dengan drone icon
- 📊 Telemetry data visible (battery %, altitude, speed, dll)
- 🎮 Bisa add/edit waypoints

---

#### Terminal 4 (Optional): Dashboard
```bash
cd d:\AgumAgum\coding\mqttTelemetry\dashboard

# Jalankan web server
python -m http.server 8000
```

**Buka browser:**
```
http://localhost:8000
```

**Yang akan dilihat:**
- Real-time GPS map
- Battery voltage & percentage
- Attitude indicator (roll, pitch, yaw)
- Speed graph
- Altitude graph

---

### OPSI 2: TESTING DENGAN SITL SIMULATOR (Tanpa Hardware)

**Terminal 0: Start SITL**
```bash
cd d:\AgumAgum\coding\mqttTelemetry\publisher

# Jalankan simulator (opsional, jika tidak ada hardware)
python -c "from dronekit_sitl import SITL; sitl = SITL(); sitl.launch(['--home=-35.363261,149.165230,584,353'], await_ready=True)"
```

**Output:**
```
Starting SITL [sim_vehicle.py -f CopterSITL ...]
Ready to fly
```

Kemudian di Terminal 1, gunakan:
```bash
mavproxy.py --master=udpin://0.0.0.0:14540 ^
    --out=tcpin:0.0.0.0:14550 ^
    --out=udpout:0.0.0.0:14551
```

Lanjut dengan Terminal 2, 3, 4 seperti biasa.

---

### OPSI 3: NETWORK SETUP (Pixhawk di PC 1, GCS di PC 2)

#### Di PC 1 (Aircraft Side - Pixhawk via COM12):

**Terminal 1:**
```bash
# Untuk Pixhawk via serial COM12 (baud rate 57600)
mavproxy.py --master COM12 --baudrate 57600 ^
    --out=tcpin:0.0.0.0:14550 ^
    --out=udpout:0.0.0.0:14551

# Jika menggunakan kecepatan baud lain:
# mavproxy.py --master COM12 --baudrate 115200 --out=tcpin:0.0.0.0:14550 --out=udpout:0.0.0.0:14551
```

**Terminal 2:**
```bash
$env:MQTT_BROKER="PC2-IP"  # atau MQTT broker yang accessible
$env:MQTT_PORT="1883"

cd publisher
python mavlink_bridge.py
```

---

#### Di PC 2 (GCS Side - Ground Control Station):

**Terminal 1:**
```bash
$env:MQTT_BROKER="PC1-IP"  # IP dimana aircraft menjalankan MQTT
$env:MQTT_PORT="1883"
$env:MQTT_USERNAME="user1"
$env:MQTT_PASSWORD="public1"

cd gcs
python mqtt_to_mavlink_gcs.py
```

**Output:**
```
✅ Connected to MQTT broker
📡 Subscribed to uav/telemetry/crepes387
✅ MAVLink server listening on 127.0.0.1:14550
```

**Terminal 2:**
```bash
# Buka Mission Planner
# Connect ke: 127.0.0.1:14550 (TCP)
```

---

## 🔧 TROUBLESHOOTING

### Issue: "Port already in use"

**Diagnosis:**
```powershell
# Cek port mana yang dipakai
netstat -ano | findstr :14550

# Output: TCP  0.0.0.0:14550  0.0.0.0:0  LISTENING  12345
```

**Solution:**
```powershell
# Kill process by PID
taskkill /PID 12345 /F

# Atau kill semua Python
taskkill /F /IM python.exe
```

---

### Issue: "MQTT Connection Failed"

**Diagnosis:**
```bash
# Test MQTT broker connectivity
mosquitto_pub -h broker.emqxsl.com -p 8883 -u user1 -P public1 -t test -m "hello"
```

**Solution:**
- ✅ Verify credentials (MQTT_USERNAME, MQTT_PASSWORD)
- ✅ Verify broker is accessible
- ✅ Verify firewall tidak block port 8883
- ✅ Jika lokal, gunakan `127.0.0.1` atau `localhost` sebagai MQTT_BROKER

---

### Issue: "MAVProxy not found"

**Solution:**
```bash
# Install MAVProxy
pip install -r requirements_mavproxy.txt

# Verify
mavproxy.py --version
```

---

### Issue: "Mission Planner won't connect"

**Checklist:**
- ✅ MAVProxy running dan shows "Ready to fly"
- ✅ Port 14550 terbuka (`netstat -ano | findstr :14550`)
- ✅ Mission Planner set ke TCP, IP 127.0.0.1, Port 14550
- ✅ Tidak ada firewall yang block

---

## 📊 DATA FLOW

### Sender Side (Pixhawk → MQTT)

```
Pixhawk (MAVLink)
    ↓ (UDP:14540)
MAVProxy (Hub)
    ↓ (UDP:14551)
mavlink_bridge.py (MAVLink Parser)
    ↓ (JSON Payload)
MQTT Broker
    ↓ (Topic: uav/telemetry/crepes387)
{
  "timestamp": "2024-01-15T12:30:45Z",
  "gps": {
    "latitude": -35.363261,
    "longitude": 149.165230,
    "altitude_msl": 584.5,
    "altitude_relative": 50.2,
    "satellite_count": 12
  },
  "attitude": {
    "roll": 0.05,
    "pitch": -0.02,
    "yaw": 45.20
  },
  "velocity": {
    "x": 1.5,
    "y": 0.3,
    "z": -0.1,
    "ground_speed": 1.54
  },
  "battery": {
    "voltage_v": 12.60,
    "current_a": 5.2,
    "remaining_percent": 95,
    "health": 100.0
  },
  "status": {
    "armed": true,
    "flight_mode": "LOITER",
    "in_air": true,
    "is_connected": true
  },
  "sequence": 1234
}
```

### Receiver Side (MQTT → Mission Planner)

```
MQTT Broker
    ↓ (Subscribe)
mqtt_to_mavlink_gcs.py (JSON Parser)
    ↓ (MAVLink Messages)
MAVLink UDP Server (127.0.0.1:14550)
    ↓
Mission Planner (TCP Client)
    ↓ (Display)
Map + Telemetry
```

---

## 🎯 QUICK START COMMANDS

### Windows PowerShell (Pixhawk via COM12)

```powershell
# 1. Setup MQTT Variables
$env:MQTT_BROKER="ef6ff411.ala.asia-southeast1.emqxsl.com"
$env:MQTT_PORT="8883"
$env:MQTT_USERNAME="user1"
$env:MQTT_PASSWORD="public1"

# 2. Terminal 1 - MAVProxy (dengan serial COM12)
cd d:\AgumAgum\coding\mqttTelemetry
mavproxy.py --master COM12 --baudrate 57600 --out=tcpin:0.0.0.0:14550 --out=udpout:0.0.0.0:14551

# 3. Terminal 2 - Bridge
cd publisher
python mavlink_bridge.py

# 4. Terminal 3 - Mission Planner
# Buka Mission Planner GUI
# Connect ke 127.0.0.1:14550 (TCP)

# 5. Terminal 4 - Dashboard (optional)
cd ../dashboard
python -m http.server 8000
# Buka: http://localhost:8000
```

### Windows PowerShell (SITL Simulator)

```powershell
# 1. Setup MQTT Variables
$env:MQTT_BROKER="ef6ff411.ala.asia-southeast1.emqxsl.com"
$env:MQTT_PORT="8883"
$env:MQTT_USERNAME="user1"
$env:MQTT_PASSWORD="public1"

# 2. Terminal 1 - MAVProxy (dengan SITL simulator)
cd d:\AgumAgum\coding\mqttTelemetry
mavproxy.py --master=udpin://0.0.0.0:14540 --out=tcpin:0.0.0.0:14550 --out=udpout:0.0.0.0:14551

# 3. Terminal 2 - Bridge
cd publisher
python mavlink_bridge.py

# 4. Terminal 3 - Mission Planner
# Buka Mission Planner GUI
# Connect ke 127.0.0.1:14550 (TCP)

# 5. Terminal 4 - Dashboard (optional)
cd ../dashboard
python -m http.server 8000
# Buka: http://localhost:8000
```

### Linux/Mac

```bash
# 1. Setup MQTT Variables
export MQTT_BROKER="ef6ff411.ala.asia-southeast1.emqxsl.com"
export MQTT_PORT="8883"
export MQTT_USERNAME="user1"
export MQTT_PASSWORD="public1"

# 2. Terminal 1 - MAVProxy
cd /path/to/mqttTelemetry
mavproxy.py --master=udpin://0.0.0.0:14540 --out=127.0.0.1:14550 --out=udpserver:0.0.0.0:14551

# 3. Terminal 2 - Bridge
cd publisher
python mavlink_bridge.py

# 4. Terminal 3 - Mission Planner
# Buka Mission Planner GUI
# Connect ke 127.0.0.1:14550 (TCP)

# 5. Terminal 4 - Dashboard (optional)
cd ../dashboard
python -m http.server 8000
# Buka: http://localhost:8000
```

---

## 📝 ENVIRONMENT VARIABLES REFERENCE

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_BROKER` | ef6ff411.ala.asia-southeast1.emqxsl.com | MQTT Broker address |
| `MQTT_PORT` | 8883 | MQTT Port (8883=TLS, 1883=no TLS) |
| `MQTT_USERNAME` | user1 | MQTT Username |
| `MQTT_PASSWORD` | public1 | MQTT Password |
| `MQTT_TOPIC` | uav/telemetry/crepes387 | MQTT Topic untuk publish/subscribe |
| `PUBLISH_INTERVAL` | 1.0 | Publish interval (seconds) |
| `MAVLINK_LISTEN_PORT` | 14551 | Port untuk listen MAVLink UDP |

---

## 🎮 PORTS REFERENCE

| Port | Service | Direction | Description |
|------|---------|-----------|-------------|
| **14540** | Pixhawk → MAVProxy | Input | MAVLink dari Pixhawk/SITL |
| **14550** | MAVProxy → Mission Planner | Output | TCP untuk Mission Planner |
| **14551** | MAVProxy → Bridge | Output | UDP untuk mavlink_bridge.py |
| **8883** | MQTT Broker | Network | MQTT dengan TLS |
| **1883** | MQTT Broker | Network | MQTT tanpa TLS |
| **8000** | Dashboard | Local | Web browser |

---

## ✨ NEXT STEPS

1. **Test Local Setup** (Opsi 1)
   - Jalankan MAVProxy → Bridge → Mission Planner
   - Verifikasi telemetry flow

2. **Setup MQTT Broker**
   - Pilih broker: EMQX, HiveMQ, atau Mosquitto lokal
   - Configure credentials

3. **Test with SITL** (Opsi 2)
   - Jalankan simulator untuk testing tanpa hardware

4. **Deploy to Network** (Opsi 3)
   - Setup 2 PC: aircraft + GCS
   - Configure remote MQTT broker

5. **Integrate Dashboard**
   - Jalankan web server
   - Monitor telemetry real-time

---

## 📚 FILE REFERENCE

| File | Purpose |
|------|---------|
| [mavlink_bridge.py](publisher/mavlink_bridge.py) | Converts MAVLink → JSON → MQTT (Sender) |
| [mqtt_to_mavlink_gcs.py](gcs/mqtt_to_mavlink_gcs.py) | Converts JSON → MAVLink (Receiver) |
| [publisher.py](publisher/publisher.py) | Alternative: Direct MAVSDK approach |
| [dashboard/index.html](dashboard/index.html) | Web dashboard untuk monitoring |
| [launch_stack.sh](launch_stack.sh) | Automation script untuk launch semua |

---

## 🆘 NEED HELP?

1. Baca [TROUBLESHOOTING.md](TROUBLESHOOTING.md) untuk common issues
2. Cek [QUICK_REFERENCE.md](QUICK_REFERENCE.md) untuk command reference
3. Lihat [ARCHITECTURE.md](ARCHITECTURE.md) untuk system design
4. Baca [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md) untuk advanced setup

**Good luck! 🚀**
