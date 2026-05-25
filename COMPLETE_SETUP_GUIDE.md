# 📚 PANDUAN LENGKAP - MQTT Telemetry System
## Setup Sender (Drone/Aircraft) ke Receiver (GCS) + Mission Planner

---

## 📌 RINGKASAN SISTEM

Sistem ini terdiri dari **3 komponen utama**:

```
┌─────────────────┐
│    PIXHAWK      │
│   (Drone/UAV)   │
└────────┬────────┘
         │ MAVLink (UDP/Serial)
         ▼
┌──────────────────────────────┐
│      MAVProxy (HUB)          │
│  - Listen ke Pixhawk         │
│  - Forward ke multiple out   │
└────┬─────────────────────────┘
     │
  ┌──┴────┬──────────────┐
  │       │              │
  ▼       ▼              ▼
┌──────┐ ┌──────────┐  ┌──────────────┐
│  MP  │ │ Bridge   │  │  Publisher   │
│      │ │ (UDP)    │  │  (MAVSDK)    │
└──────┘ └────┬─────┘  └──────────────┘
              │
              ▼
        ┌──────────────┐
        │ MQTT Broker  │
        │  (Cloud)     │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │ GCS PC/Laptop│
        │ - Dashboard  │
        │ - Converter  │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │   Mission    │
        │   Planner    │
        └──────────────┘
```

**3 Skenario Penggunaan:**

1. **Lokal (1 PC)**: Pixhawk + MAVProxy + MP + Dashboard semua di 1 komputer
2. **Network Lokal**: Pixhawk di 1 PC, Mission Planner di PC lain (Network)
3. **Cloud (Distributed)**: Pixhawk di lapangan, GCS di kantor via MQTT Broker

---

# 🎯 SKENARIO 1: SETUP LOKAL (Semua di 1 Komputer)

## Step 1: Install Dependencies

```bash
# Buka terminal di folder mqttTelemetry
cd d:\AgumAgum\coding\mqttTelemetry

# Install MAVProxy + dependencies
pip install -r requirements_mavproxy.txt

# Install publisher dependencies (optional, jika pakai original publisher.py)
cd publisher
pip install -r requirements.txt
cd ..
```

**Verifikasi instalasi:**
```bash
mavproxy.py --version
python -c "from pymavlink.dialects.v10 import ardupilotmega; print('✅ pymavlink installed')"
```

---

## Step 2: Setup Pixhawk Connection

### Option A: SITL Simulator (No Hardware)

**Terminal 1 - Jalankan DroneKit SITL:**
```bash
# Dari folder mqttTelemetry
cd publisher
python -c "from dronekit_sitl import SITL; sitl = SITL(); sitl.launch(['--home=0,0,0,0'], await_ready=True)"
```

Atau gunakan MAVProxy bawaan:
```bash
python -m pymavlink.tools.simulator --home=0,0,0
```

### Option B: Real Hardware (Serial Connection)

**Cek port COM:**
- Windows: Device Manager → Ports (COM & LPT)
- Linux: `ls /dev/tty*`

**Example untuk COM3, 57600 baud:**
```bash
mavproxy.py --master=com3,57600 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551
```

---

## Step 3: Jalankan MAVProxy (Terminal 1)

**Untuk SITL/Simulator:**
```bash
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551 \
    --default-modules=compass,streamrate
```

**Output yang diharapkan:**
```
Loaded module mavsys
Loaded module compass
Loaded module streamrate
Loaded module cutdownrate
Loaded module missitemrate
Ready to fly
```

---

## Step 4: Jalankan MAVLink Bridge (Terminal 2)

```bash
cd d:\AgumAgum\coding\mqttTelemetry\publisher
python mavlink_bridge.py
```

**Output yang diharapkan:**
```
✅ Connected to MQTT broker
📡 Listening on UDP port 14551
🚀 Publishing telemetry to MQTT...
📍 GPS: 0.000000, 0.000000
🔋 Battery: 12.60V, 100%
```

---

## Step 5: Connect Mission Planner (Terminal 3)

1. **Download Mission Planner** (jika belum ada)
   - Windows: Download dari https://ardupilot.org/planner/index.html
   - Ubuntu: `sudo apt install mono-mcs mission-planner`

2. **Buka Mission Planner**

3. **Connect:**
   - Klik dropdown di kanan atas (default "COM3" atau sejenisnya)
   - Pilih **TCP**
   - IP: `127.0.0.1`
   - Port: `14550`
   - Klik **CONNECT**

**Jika berhasil, akan terlihat:**
- ✅ "Connected" di status bar
- 🗺️ Map dengan drone icon
- 📊 Telemetry data (altitude, speed, battery, dll)

---

## Step 6: Lihat Dashboard (Terminal 4 - Optional)

```bash
# Dari folder mqttTelemetry
cd dashboard

# Jalankan simple server
python -m http.server 8000
```

**Buka browser:**
```
http://localhost:8000
```

Akan melihat:
- Real-time GPS position
- Battery status
- Attitude gauge (roll, pitch, yaw)
- Velocity graph

---

# 🌐 SKENARIO 2: NETWORK LOKAL (Pixhawk & GCS berbeda PC)

## Arsitektur

```
COMPUTER A (Drone Site)         COMPUTER B (GCS)
════════════════════════════════════════════════

[Pixhawk/SITL]
    ↓
[MAVProxy]
    ↓
[MAVLink Bridge] → [MQTT Broker (Cloud)]
    ↓                    ↑
    └────────────────────┘
                         ↓
                    [MQTT Subscriber]
                         ↓
                    [GCS Converter]
                         ↓
                    [MAVLink Server :14550]
                         ↓
                    [Mission Planner]
```

---

## Computer A Setup (Pixhawk Site)

### Terminal 1: Jalankan MAVProxy
```bash
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551
```

### Terminal 2: Jalankan Bridge
```bash
cd publisher
python mavlink_bridge.py
```

**Catatan:** MQTT Broker harus accessible dari kedua PC
- Gunakan broker online seperti **EMQX, HiveMQ, Mosquitto**
- Atau set up Mosquitto lokal di router

---

## Computer B Setup (GCS Site)

### Prerequisites

```bash
# Install dependencies
cd gcs
pip install -r requirements.txt
```

### Terminal 1: Jalankan GCS Converter

```bash
cd gcs
python mqtt_to_mavlink_gcs.py
```

**Output yang diharapkan:**
```
✅ Connected to MQTT broker
📡 Subscribed to: uav/telemetry/crepes387
✅ MAVLink server listening on 0.0.0.0:14550
📨 Received seq 1
```

### Terminal 2: Buka Mission Planner

1. Klik dropdown → **TCP**
2. IP: `127.0.0.1` (localhost)
3. Port: `14550`
4. Klik **CONNECT**

✅ **Connected!** Data mengalir dari Pixhawk A → MQTT Broker → GCS B → Mission Planner

---

# ☁️ SKENARIO 3: DISTRIBUTED GCS (Cloud-based)

## Setup Broker MQTT

### Option A: Pakai Broker Online (Recommended)

**EMQX (Free tier):**
1. Daftar di https://www.emqx.com/
2. Buat deployment (free tier available)
3. Dapatkan: `Broker Address`, `Port`, `Username`, `Password`

**Contoh:**
```
Broker: ef6ff411.ala.asia-southeast1.emqxsl.com
Port: 8883 (TLS)
Username: user1
Password: public1
Topic: uav/telemetry/crepes387
```

### Option B: Setup Mosquitto Lokal

```bash
# Install Mosquitto
sudo apt install mosquitto mosquitto-clients  # Linux
# Atau download dari https://mosquitto.org (Windows)

# Start service
sudo systemctl start mosquitto
```

---

## Computer A: Drone Site

```bash
# Terminal 1: MAVProxy
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551

# Terminal 2: MAVLink Bridge
cd publisher
python mavlink_bridge.py
```

---

## Computer B: Remote GCS (Kantor)

### Set Environment Variables (Edit before running)

**Linux/Mac:**
```bash
# Edit .bashrc atau .zshrc
export MQTT_BROKER="your-broker.emqxsl.com"
export MQTT_PORT="8883"
export MQTT_USERNAME="user1"
export MQTT_PASSWORD="public1"
export MQTT_TOPIC="uav/telemetry/crepes387"

# Reload
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
$env:MQTT_BROKER="your-broker.emqxsl.com"
$env:MQTT_PORT="8883"
$env:MQTT_USERNAME="user1"
$env:MQTT_PASSWORD="public1"
$env:MQTT_TOPIC="uav/telemetry/crepes387"
```

### Run GCS Converter

```bash
cd gcs
python mqtt_to_mavlink_gcs.py
```

### Connect Mission Planner

```
TCP → 127.0.0.1 : 14550 → CONNECT
```

---

# 🔧 KONFIGURASI ENVIRONMENT VARIABLES

## Untuk `publisher/mavlink_bridge.py`

| Variable | Default | Keterangan |
|----------|---------|-----------|
| `PIXHAWK_CONNECTION` | `udpin://127.0.0.1:14540` | Koneksi ke MAVProxy |
| `MAVLINK_LISTEN_PORT` | `14551` | Port listen UDP |
| `MQTT_BROKER` | `ef6ff411.ala.asia-southeast1.emqxsl.com` | MQTT broker |
| `MQTT_PORT` | `8883` | MQTT port (TLS) |
| `MQTT_USERNAME` | `user1` | Username MQTT |
| `MQTT_PASSWORD` | `public1` | Password MQTT |
| `MQTT_TOPIC` | `uav/telemetry/crepes387` | MQTT topic publish |
| `PUBLISH_INTERVAL` | `0.5` | Interval publish (detik) |

## Untuk `gcs/mqtt_to_mavlink_gcs.py`

| Variable | Default | Keterangan |
|----------|---------|-----------|
| `MQTT_BROKER` | (sama) | MQTT broker |
| `MQTT_PORT` | (sama) | MQTT port |
| `MQTT_USERNAME` | (sama) | Username |
| `MQTT_PASSWORD` | (sama) | Password |
| `MQTT_TOPIC` | (sama) | Topic subscribe |
| `MAVLINK_SERVER_PORT` | `14550` | Port untuk MP connect |

---

# 📊 PUBLISHER vs BRIDGE vs ORIGINAL CODE

## Publisher.py (Original)

- **Gunakan untuk:** Direct connect ke Pixhawk via MAVSDK
- **Kelebihan:** Full MAVSDK features, control commands
- **Kekurangan:** Hanya publish ke MQTT, tidak bikin MAVLink server
- **Output:** JSON ke MQTT topic

```bash
cd publisher
python publisher.py
```

---

## MAVLink Bridge

- **Gunakan untuk:** Konversi MAVProxy UDP ↔ MQTT
- **Kelebihan:** MAVProxy-agnostic, reliable
- **Kekurangan:** Perlu MAVProxy running
- **Input:** UDP dari MAVProxy
- **Output:** MQTT publish + Dashboard

```bash
cd publisher
python mavlink_bridge.py
```

---

## GCS Converter

- **Gunakan untuk:** Remote GCS dengan MQTT
- **Kelebihan:** Mission Planner compatible, real-time sync
- **Kekurangan:** Perlu GCS Converter + MQTT connection
- **Input:** MQTT subscribe
- **Output:** MAVLink server (localhost:14550)

```bash
cd gcs
python mqtt_to_mavlink_gcs.py
```

---

# ✅ CHECKLIST SETUP

## Lokal (Skenario 1)

- [ ] Install `requirements_mavproxy.txt`
- [ ] Install `publisher/requirements.txt`
- [ ] Terminal 1: Jalankan MAVProxy
- [ ] Terminal 2: Jalankan `mavlink_bridge.py`
- [ ] Terminal 3: Open Mission Planner → Connect TCP 127.0.0.1:14550
- [ ] Lihat drone icon di map
- [ ] Terminal 4 (optional): Dashboard di localhost:8000

## Network Lokal (Skenario 2)

### Computer A:
- [ ] MAVProxy running (Terminal 1)
- [ ] `mavlink_bridge.py` running (Terminal 2)
- [ ] MQTT connection OK

### Computer B:
- [ ] Install `gcs/requirements.txt`
- [ ] Set MQTT_BROKER ke broker yang accessible
- [ ] `mqtt_to_mavlink_gcs.py` running (Terminal 1)
- [ ] Mission Planner TCP connect ke 127.0.0.1:14550 (Terminal 2)

## Cloud (Skenario 3)

### Computer A (Drone):
- [ ] MAVProxy running
- [ ] `mavlink_bridge.py` running
- [ ] Publish ke MQTT broker berhasil

### Computer B (GCS):
- [ ] Environment variables set (MQTT credentials)
- [ ] `mqtt_to_mavlink_gcs.py` running
- [ ] Subscribe dari MQTT broker berhasil
- [ ] Mission Planner TCP connect berhasil

---

# 🐛 TROUBLESHOOTING

## Problem 1: "mavproxy.py not found"

**Solusi:**
```bash
pip install MAVProxy
# Atau
pip install MAVProxy==1.8.60
```

---

## Problem 2: "Port already in use (14550)"

**Solusi (Windows):**
```powershell
netstat -ano | findstr :14550
taskkill /PID <PID> /F
```

**Solusi (Linux):**
```bash
lsof -i :14550
kill -9 <PID>
```

---

## Problem 3: "Connection refused (MQTT broker)"

**Cek:**
1. Broker online? `ping ef6ff411.ala.asia-southeast1.emqxsl.com`
2. Username/Password benar?
3. Port benar? (8883 untuk TLS, 1883 for non-TLS)
4. Firewall allow?

**Test MQTT:**
```bash
# Publish
mosquitto_pub -h <broker> -u <user> -P <pass> -p 8883 --cafile <cert> -t test -m "hello"

# Subscribe
mosquitto_sub -h <broker> -u <user> -P <pass> -p 8883 --cafile <cert> -t test
```

---

## Problem 4: "Mission Planner won't connect"

**Cek:**
1. MAVProxy running? `mavproxy.py --version`
2. Bridge running? `cd publisher && python mavlink_bridge.py`
3. Port 14550 listening? `netstat -an | grep 14550`
4. Firewall allow TCP 14550?

**Test koneksi:**
```bash
# Dari PC GCS
telnet 127.0.0.1 14550
# Jika connected, tekan Ctrl+]
```

---

## Problem 5: "No telemetry data in Mission Planner"

**Cek:**
1. Pixhawk connected ke MAVProxy?
   - MAVProxy console harus show "Ready to fly"
2. Bridge getting data?
   - Lihat logs: `python mavlink_bridge.py` harus show "📍 GPS: ..."
3. MQTT publishing?
   - Check broker di web console (EMQX)

---

## Problem 6: "FileNotFoundError: emqxsl-ca.crt"

**Solusi:**
```bash
# Download certificate
curl -o emqxsl-ca.crt https://assets.emqx.com/api/emqxsl-ca.crt

# Letakkan di:
# - publisher/emqxsl-ca.crt
# - gcs/emqxsl-ca.crt
```

---

# 🎓 UNDERSTANDING PORT NUMBERS

```
14540: Input dari Pixhawk → MAVProxy
14550: Output dari MAVProxy → Mission Planner (TCP)
14551: Output dari MAVProxy → MAVLink Bridge (UDP)
14552: (optional) Output dari MAVProxy untuk aplikasi lain
8883: MQTT Broker (TLS)
8000: Dashboard (Web)
```

---

# 📱 QUICK COMMAND REFERENCE

### Terminal 1: Start MAVProxy
```bash
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551
```

### Terminal 2: Start Bridge
```bash
cd publisher && python mavlink_bridge.py
```

### Terminal 3: Start GCS Converter (remote)
```bash
cd gcs && python mqtt_to_mavlink_gcs.py
```

### Terminal 4: Mission Planner
```
Connect → TCP → 127.0.0.1:14550
```

### Terminal 5: Dashboard (optional)
```bash
cd dashboard && python -m http.server 8000
# Buka http://localhost:8000
```

---

# 📖 FILE STRUCTURE

```
mqttTelemetry/
├── publisher/
│   ├── publisher.py              ← Original (MAVSDK direct)
│   ├── mavlink_bridge.py         ← MAVProxy → MQTT
│   ├── sitl.py                   ← SITL simulator
│   └── requirements.txt
├── gcs/
│   ├── mqtt_to_mavlink_gcs.py   ← MQTT → MAVLink server
│   └── requirements.txt
├── dashboard/
│   └── index.html                ← Web dashboard
├── data/
│   └── latest.json               ← Latest telemetry
├── REQUIREMENTS.md               ← Dependencies guide
├── QUICKSTART.md                 ← Quick start
├── SETUP_MAVPROXY.md            ← MAVProxy setup
├── DISTRIBUTED_GCS.md           ← Cloud setup
└── COMPLETE_SETUP_GUIDE.md      ← Dokumentasi ini
```

---

# 🚀 NEXT STEPS

1. **Pilih skenario** (Lokal/Network/Cloud)
2. **Install dependencies** sesuai skenario
3. **Set environment variables** (jika network/cloud)
4. **Run components** di terminal terpisah
5. **Connect Mission Planner** ke TCP 127.0.0.1:14550
6. **Monitor dashboard** (optional) di localhost:8000

---

**Pertanyaan atau masalah? Cek troubleshooting section atau lihat terminal logs untuk detail error.**
