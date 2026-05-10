# 🌐 Distributed GCS Setup (Remote Mission Planner)

Untuk setup di mana **Pixhawk di satu komputer** dan **GCS (Mission Planner) di komputer lain**.

---

## 🏗️ Arsitektur 

```
COMPUTER A (Pixhawk Site)          COMPUTER B (Remote GCS)
═════════════════════════════════════════════════════════

[Pixhawk]
    ↓ (MAVLink via UDP/Serial)
[MAVProxy]
    ↙        ↘
  Port 14550  Port 14551
    ↓          ↓
   (Network)  [Bridge]
    ↓          ↓
    │       [MQTT Publish]
    │          ↓
    │       [MQTT Broker]
    │       (Cloud/Network)
    │          ↓
    └──────→[MQTT Sub]
            ↓
        [GCS Converter]
        (mqtt_to_mavlink)
            ↓
        MAVLink Server :14550
            ↓
        [Mission Planner]
```

---

## 📋 Ada 2 Solusi

### **Solusi A: Direct TCP Connection (Simple)**
✅ Kelebihan: Langsung, low latency
❌ Kekurangan: Network harus stabil, perlu firewall rules

### **Solusi B: MQTT-based (Robust - Recommended)**
✅ Kelebihan: Async, cache data, bisa offline, flexible
❌ Kekurangan: Sedikit lebih kompleks, extra hop

---

## 🔌 Solusi A: Direct TCP

### Computer A Setup (Pixhawk side)

**Change MAVProxy output dari `127.0.0.1` ke `0.0.0.0`:**

```bash
# SEBELUM (localhost only):
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551

# SESUDAH (network accessible):
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=0.0.0.0:14550 \
    --out=udpserver:0.0.0.0:14551
```

**Also run bridge (Terminal 2):**
```bash
cd publisher
python mavlink_bridge.py
```

### Computer B Setup (GCS side)

**Mission Planner:**
1. CONNECT → TCP
2. IP: `[COMPUTER_A_IP]` (e.g., `192.168.1.100`)
3. Port: `14550`
4. Click CONNECT

✅ Done! Mission Planner connected ke remote Pixhawk

---

## 🟢 Solusi B: MQTT-based (Recommended)

Lebih robust karena tidak perlu direct network connectivity antar computers.

### Computer A Setup (Pixhawk side)

```bash
# Terminal 1: MAVProxy (output ke localhost OK, MQTT akan distribute)
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551

# Terminal 2: Bridge (converts MAVLink → MQTT)
cd publisher
python mavlink_bridge.py
```

**Verify:**
```bash
# Check if MQTT publishing
mosquitto_sub -h ef6ff411.ala.asia-southeast1.emqxsl.com \
    -u user1 -P public1 \
    -t "uav/telemetry/crepes387"

# You should see JSON telemetry flowing
```

### Computer B Setup (GCS side)

**Installation (one-time):**
```bash
pip install paho-mqtt pymavlink

# Or install from requirements:
pip install -r requirements_mavproxy.txt
```

**Run GCS Converter (Terminal 1):**
```bash
cd gcs
python mqtt_to_mavlink_gcs.py
```

**Expected output:**
```
✅ Connected to MQTT broker
📡 Subscribed to: uav/telemetry/crepes387
✅ MAVLink server listening on 0.0.0.0:14550
📨 Received seq 1
📡 Broadcast seq 1
```

**Mission Planner (Terminal 2):**
1. CONNECT → TCP
2. IP: `127.0.0.1` (atau `localhost`)
3. Port: `14550`
4. Click CONNECT

✅ Mission Planner connected! Data from remote Pixhawk via MQTT!

---

## 🔧 Configuration

### Environment Variables (Computer A - Pixhawk side):
```bash
export MQTT_BROKER="ef6ff411.ala.asia-southeast1.emqxsl.com"
export MQTT_PORT="8883"
export MQTT_USERNAME="user1"
export MQTT_PASSWORD="public1"
export MQTT_TOPIC="uav/telemetry/crepes387"
export PUBLISH_INTERVAL="1.0"
```

### Environment Variables (Computer B - GCS side):
```bash
# Same MQTT config so it subscribes to same topic
export MQTT_BROKER="ef6ff411.ala.asia-southeast1.emqxsl.com"
export MQTT_PORT="8883"
export MQTT_USERNAME="user1"
export MQTT_PASSWORD="public1"
export MQTT_TOPIC="uav/telemetry/crepes387"
export MAVLINK_SERVER_PORT="14550"
export BROADCAST_INTERVAL="0.1"  # 10Hz
```

---

## 📊 Architecture Comparison

| Aspek | Solusi A (Direct TCP) | Solusi B (MQTT) |
|-------|----------------------|-----------------|
| **Setup** | 1 line change | 2 files + converter |
| **Latency** | Rendah (~50ms) | Medium (~200ms) |
| **Robustness** | Depends on network | Cache friendly |
| **Firewall** | Perlu allow port 14550 | Perlu broker access |
| **Offline mode** | Tidak | Yes (cached) |
| **Multiple GCS** | Harus buat connection lain | All subscribe same topic |
| **Rekomendasi** | Local network, stable | Internet/unstable, multi-client |

---

## 🗺️ Multi-GCS Setup (MQTT-based)

**Solusi B allows multiple GCS computers!**

```
Computer A (Pixhawk):
  → Bridge → MQTT Broker

Computer B (GCS 1):
  → MQTT Sub → MP1 → :14550

Computer C (GCS 2):
  → MQTT Sub → MP2 → :14551

Computer D (GCS 3):
  → MQTT Sub → MP3 → :14552

All share same telemetry!
```

**Setiap GCS di port berbeda:**
```bash
# Computer B
export MAVLINK_SERVER_PORT="14550"
python mqtt_to_mavlink_gcs.py

# Computer C
export MAVLINK_SERVER_PORT="14551"
python mqtt_to_mavlink_gcs.py

# Computer D
export MAVLINK_SERVER_PORT="14552"
python mqtt_to_mavlink_gcs.py
```

---

## 🔍 Troubleshooting

### "Mission Planner can't connect" (Solusi A)

```bash
# Check if port 14550 open
netstat -an | grep 14550

# Check firewall
sudo ufw allow 14550  # Linux

# Check from other computer
telnet 192.168.1.100 14550
```

### "No telemetry received" (Solusi B)

```bash
# Check MQTT connection
python -c "
import paho.mqtt.client as mqtt
c = mqtt.Client()
c.connect('ef6ff411.ala.asia-southeast1.emqxsl.com', 8883)
print('✅ MQTT OK')
"

# Check topic
mosquitto_sub -h ef6ff411.ala.asia-southeast1.emqxsl.com \
    -u user1 -P public1 \
    -t "uav/telemetry/crepes387"
```

### "GCS converter won't start" (Solusi B)

```bash
# Check Python version
python --version  # Need 3.8+

# Check packages
python -c "import pymavlink; print('OK')"
python -c "import paho.mqtt; print('OK')"

# Run with verbose
python mqtt_to_mavlink_gcs.py 2>&1 | head -20
```

---

## 🚀 Quick Decision Tree

```
Choose your setup:

1. Pixhawk & GCS on SAME LOCAL NETWORK?
   → Use Solusi A (Direct TCP) - simpler

2. Pixhawk & GCS on DIFFERENT NETWORKS (Internet)?
   → Use Solusi B (MQTT) - more reliable

3. Need MULTIPLE GCS computers?
   → Use Solusi B (MQTT) - all subscribe same topic

4. Pixhawk in field, GCS back at office?
   → Use Solusi B (MQTT) - robustness++
```

---

## 📝 Example: Full Remote Setup

**Scenario:** 
- Pixhawk in field (IP 192.168.1.100, offline SITL)
- GCS in office (IP 10.0.0.50, on internet)
- MQTT broker in cloud

### Computer A (Pixhawk in field):
```bash
# Terminal 1
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551

# Terminal 2
export MQTT_BROKER="broker.emqx.io"
export MQTT_USERNAME="field_user"
export MQTT_PASSWORD="secure_pass"
export MQTT_TOPIC="drone/telemetry/field_site"
cd publisher && python mavlink_bridge.py
```

### Computer B (GCS in office):
```bash
# Terminal 1
export MQTT_BROKER="broker.emqx.io"
export MQTT_USERNAME="field_user"
export MQTT_PASSWORD="secure_pass"
export MQTT_TOPIC="drone/telemetry/field_site"
cd gcs && python mqtt_to_mavlink_gcs.py

# Terminal 2
# Open Mission Planner
# CONNECT → TCP → localhost:14550
```

✅ **Done!** Office can monitor field drone real-time!

---

## 💡 Pro Tips

1. **Latency tuning:**
   ```bash
   # Increase broadcast frequency (Computer B)
   export BROADCAST_INTERVAL="0.05"  # 20Hz instead of 10Hz
   ```

2. **Data persistence:**
   ```bash
   # Auto-save telemetry
   export TELEMETRY_OUTPUT_FILE="/var/log/drone_telemetry.json"
   ```

3. **Network optimization:**
   ```bash
   # Computer A: reduce publish interval if needed
   export PUBLISH_INTERVAL="2.0"  # 0.5Hz instead of 1Hz (save bandwidth)
   ```

4. **SSL/TLS cert issues:**
   ```bash
   # If TLS fails, can work without cert but less secure
   # In code: client.tls_insecure_set(True)
   ```

---

## ✅ Verification Checklist

- [ ] Computer A: MAVProxy running
- [ ] Computer A: Bridge running (check MQTT publish)
- [ ] Computer B: GCS Converter running (check MQTT subscribe)
- [ ] Computer B: Mission Planner connected (green light)
- [ ] See drone position on map
- [ ] Telemetry values updating in real-time

**All good?** You have a working remote GCS! 🎉
