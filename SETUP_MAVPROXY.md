# 🛰️ Setup MAVProxy + Mission Planner + MQTT

## Arsitektur

```
┌──────────────┐
│   Pixhawk    │ (UDP 14540)
└──────┬───────┘
       │ MAVLink
       ▼
┌──────────────────────────┐
│   MAVProxy (hub)         │
├──────────────────────────┤
│ Inputs:  UDP 14540       │
│ Outputs: UDP 14550 (MP)  │
│          UDP 14551 (app) │
└──────┬───────────────────┘
       │
    ┌──┴──┬────────────────────┐
    │     │                    │
    ▼     ▼                    ▼
┌──────┐  ┌──────────────────┐  ┌─────────┐
│  MP  │  │ MAVLink Bridge   │  │ Original│
│      │  │ (mavlink_bridge.py)│ │Publisher│
└──────┘  └────────┬─────────┘  └─────────┘
                   │
                   ▼
            ┌──────────────┐
            │   MQTT       │
            │   Broker     │
            └──────────────┘
                   │
                   ▼
            ┌──────────────┐
            │  Dashboard   │
            │  (index.html)│
            └──────────────┘
```

---

## 📋 Prerequisites

### 1. Install Dependencies

```bash
# Go ke publisher directory
cd publisher

# Install MAVProxy & pymavlink
pip install MAVProxy pymavlink
```

### 2. Verify Installation

```bash
# Check MAVProxy
mavproxy.py --version

# Check pymavlink
python -c "from pymavlink.dialects.v10 import ardupilotmega; print('✅ pymavlink OK')"
```

---

## 🚀 Setup Steps

### Step 1: Start MAVProxy (Terminal 1)

MAVProxy akan connect ke Pixhawk dan forward data ke multiple outputs.

**Jika Pixhawk via UDP (simulator/SITL):**
```bash
mavproxy.py --master=udpin:0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551 \
    --default-modules=compass,streamrate
```

**Jika Pixhawk via Serial (real hardware):**
```bash
mavproxy.py --master=/dev/ttyUSB0,57600 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551 \
    --baudrate=57600 \
    --default-modules=compass,streamrate
```

**Penjelasan flag:**
- `--master=`: Source (Pixhawk connection)
- `--out=127.0.0.1:14550`: Output ke Mission Planner
- `--out=udpserver:0.0.0.0:14551`: Output UDP server untuk aplikasi lain
- `--default-modules=`: Load module (optional)

Tunggu sampai muncul pesan:
```
Loaded module mavsys
Ready to fly
Received 10 MAVLink messages
```

### Step 2: Start MAVLink→MQTT Bridge (Terminal 2)

```bash
cd publisher

# Set environment variables (optional, ada default)
export MAVLINK_LISTEN_PORT=14551
export MQTT_BROKER="ef6ff411.ala.asia-southeast1.emqxsl.com"
export MQTT_PORT=8883
export MQTT_USERNAME="user1"
export MQTT_PASSWORD="public1"
export MQTT_TOPIC="uav/telemetry/crepes387"
export PUBLISH_INTERVAL=1.0

# Run bridge
python mavlink_bridge.py
```

Tunggu log:
```
✅ Listening on UDP port 14551
✅ Connected to MQTT broker
🌉 Starting MAVLink↔MQTT bridge...
🚀 Published seq 1 (XXX bytes)
```

### Step 3: Connect Mission Planner (Terminal 3 - Windows/GUI)

**Via Network Connection:**
1. Buka Mission Planner
2. Klik **CONNECT**
3. Pilih **TCP** atau **UDP**
4. Setting:
   - **IP**: `127.0.0.1` (atau IP komputer Anda jika remote)
   - **Port**: `14550`
   - **Baud rate**: N/A (untuk TCP/UDP)
5. Click **CONNECT**

**Anda sekarang bisa:**
- ✅ Lihat real-time telemetry
- ✅ Lihat GPS position di map
- ✅ Lihat waypoints
- ✅ Monitor battery, speed, altitude
- ✅ Send commands (jika drone terhubung)

### Step 4: View Dashboard (Browser)

```bash
# Dari terminal terpisah, serve HTML
cd dashboard
python -m http.server 8000

# Buka di browser
http://localhost:8000
```

Dashboard akan auto-update dari `/data/latest.json` setiap detik.

---

## 📊 Expected Output

### Terminal 1 (MAVProxy):
```
Loaded module mavsys
Ready to fly (you can now run commands)
Received 45 MAVLink messages in 0.5s, dropped 0
```

### Terminal 2 (Bridge):
```
2026-05-10 14:30:45 - __main__ - INFO - ✅ Listening on UDP port 14551
2026-05-10 14:30:45 - __main__ - INFO - ✅ Connected to MQTT broker
2026-05-10 14:30:45 - __main__ - INFO - 🌉 Starting MAVLink↔MQTT bridge...
2026-05-10 14:30:46 - __main__ - INFO - 📍 GPS: -35.363261, 149.165230
2026-05-10 14:30:46 - __main__ - INFO - 🔄 Attitude: R=0.05, P=-0.02, Y=45.20
2026-05-10 14:30:46 - __main__ - INFO - 🚀 Published seq 1 (245 bytes)
```

### Terminal 3 (Mission Planner):
- ✅ Connected indicator will turn green
- ✅ Drone icon appears on map
- ✅ Telemetry values update in real-time

---

## 🔄 Waypoint Integration

Mission Planner punya built-in waypoint editor:

1. **Create Waypoints:**
   - Klik di map untuk add waypoint
   - Set altitude, speed, etc.
   
2. **Upload ke Drone:**
   - Klik **Write WPs**
   - MAVProxy akan forward ke Pixhawk

3. **Download dari Drone:**
   - Klik **Read WPs**
   - MAVProxy akan retrieve dari Pixhawk

4. **Monitor Execution:**
   - Lihat real-time progress di map
   - Mission Planner menampilkan current waypoint

---

## 🛠️ Troubleshooting

### MAVProxy tidak connect ke Pixhawk
```
# Check jika Pixhawk listening pada 14540
netstat -an | grep 14540

# Atau pake nmap
nmap -u -p 14540 127.0.0.1
```

### Mission Planner tidak connect
```
# Check jika port 14550 open
lsof -i :14550

# Check MAVProxy output stream
# Dalam MAVProxy console, ketik: "status" atau "log read"
```

### Bridge tidak terima data
```
# Check jika listening pada 14551
lsof -i :14551

# Di MAVProxy console, ketik:
# set target_system 1
# set target_component 1
# status
```

### MQTT tidak publish
```
# Check MQTT broker connection
mosquitto_pub -h ef6ff411.ala.asia-southeast1.emqxsl.com \
    -u user1 -P public1 -t test -m "hello" -p 8883

# Monitor MQTT messages
mosquitto_sub -h ef6ff411.ala.asia-southeast1.emqxsl.com \
    -u user1 -P public1 -t "uav/telemetry/crepes387" -p 8883
```

---

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAVLINK_LISTEN_PORT` | 14551 | Port untuk listen MAVLink stream |
| `MQTT_BROKER` | ef6ff411.ala.asia-southeast1.emqxsl.com | MQTT broker address |
| `MQTT_PORT` | 8883 | MQTT broker port |
| `MQTT_USERNAME` | user1 | MQTT username |
| `MQTT_PASSWORD` | public1 | MQTT password |
| `MQTT_TOPIC` | uav/telemetry/crepes387 | MQTT topic |
| `PUBLISH_INTERVAL` | 1.0 | Interval publish (seconds) |
| `TELEMETRY_OUTPUT_FILE` | ../data/latest.json | Output file path |

---

## 🌐 Remote Setup

Jika Mission Planner di komputer berbeda dari Pixhawk:

1. **Start MAVProxy di computer yang terhubung ke Pixhawk:**
```bash
mavproxy.py --master=udpin:0.0.0.0:14540 \
    --out=0.0.0.0:14550 \
    --out=udpserver:0.0.0.0:14551
```

2. **Di Mission Planner, gunakan IP address komputer tersebut:**
```
IP: 192.168.1.100 (contoh)
Port: 14550
```

3. **Bridge bisa di computer yang sama atau berbeda, asal bisa reach port 14551**

---

## ✅ Verification Checklist

- [ ] MAVProxy running dan menerima data dari Pixhawk
- [ ] Mission Planner connect ke MAVProxy (green indicator)
- [ ] Waypoints terlihat di Mission Planner map
- [ ] Bridge receiving MAVLink messages (cek log)
- [ ] MQTT publish berhasil
- [ ] Dashboard update dengan data terbaru
- [ ] All 3 terminals running tanpa error

---

## 📚 References

- MAVProxy docs: http://ardupilot.org/mavproxy/
- MAVLink protocol: https://mavlink.io/
- Mission Planner: http://ardupilot.org/planner/
- PyMAVLink: https://github.com/ArduPilot/pymavlink
