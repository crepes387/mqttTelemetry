# 🚨 TROUBLESHOOTING: Mission Planner Tidak Terhubung

## 📋 CHECKLIST

### ✅ Step 1: Verify mqtt_to_mavlink_gcs.py Running

**Terminal Output Should Show:**
```
================================================================================
🌍 GCS MQTT ↔ MAVLink Converter Configuration
================================================================================
📡 MQTT Broker: ef6ff411.ala.asia-southeast1.emqxsl.com:8883
📝 MQTT Topic: uav/telemetry/crepes387
🔗 MAVLink Server: 0.0.0.0:14550
⏱️ Broadcast Interval: 100ms (10Hz)
================================================================================
✅ Connected to MQTT broker
📡 Subscribed to: uav/telemetry/crepes387
✅ MAVLink server listening on 0.0.0.0:14550
💡 Mission Planner should connect to: 127.0.0.1:14550 (TCP)
```

**Jika ada error:**
- ❌ `MQTT connection failed` → Cek MQTT_BROKER, MQTT_PORT, credentials
- ❌ `Failed to setup MQTT client` → Cek paho-mqtt installed

---

### ✅ Step 2: Verify Telemetry Data Diterima dari MQTT

**Terminal Should Show:**
```
📨 Received MQTT seq 123: GPS=−35.3633,149.1652 | Battery=95%
📨 Received MQTT seq 124: GPS=−35.3633,149.1652 | Battery=95%
```

**Jika tidak ada:**
- ❌ MAVLink Bridge tidak sending ke MQTT → Cek [mavlink_bridge.py running]
- ❌ Credentials MQTT salah → Data tidak diterima
- ⏳ Tunggu 10 detik, data akan mulai masuk

---

### ✅ Step 3: Verify MAVLink Server Menerima Client

**Terminal Should Show Saat Mission Planner Connect:**
```
📱 Client connected: ('127.0.0.1', 58950) (Total: 1)
📡 Broadcasting seq 123 to 1 client(s)
📡 Broadcasting seq 124 to 1 client(s)
```

**Jika tidak ada client:**
- ❌ Mission Planner tidak connect → Cek connection settings
- ❌ Port 14550 blocked → Cek firewall
- ⏳ Tunggu 5 detik setelah MP connect

---

### ✅ Step 4: Open Mission Planner & Connect

**Mission Planner:**
1. Klik **Dropdown** (kanan atas)
2. Pilih **TCP**
3. IP: `127.0.0.1`
4. Port: `14550`
5. Klik **CONNECT**

**Jika berhasil:**
- ✅ Status bar shows "Connected"
- ✅ Map appears dengan drone icon
- ✅ Telemetry data visible

**Jika gagal:**
- ❌ "Connection timeout" → MAVLink server tidak running
- ❌ "Connection refused" → Server tidak listening on 14550
- ❌ Connected tapi no telemetry → Data format issue

---

## 🔧 DEBUGGING STEPS

### Problem: "Connection Refused" atau "Timeout"

**Check 1: Port 14550 Listening?**
```powershell
netstat -ano | findstr :14550
# Output: TCP    0.0.0.0:14550    0.0.0.0:0    LISTENING    12345
```

Jika tidak ada → mqtt_to_mavlink_gcs.py tidak running dengan benar!

**Check 2: Firewall**
```powershell
# Allow port 14550 in firewall
netsh advfirewall firewall add rule name="MAVLink" dir=in action=allow protocol=tcp localport=14550
```

---

### Problem: Connected tapi No Telemetry Data

**Check di Terminal:**
```
📨 Received MQTT seq 123: ...  ← Data diterima dari MQTT?
📡 Broadcasting seq 123 to 1 client(s)  ← Data dikirim ke MP?
```

**Jika tidak ada:**
- ❌ MQTT data tidak masuk → Cek MAVLink Bridge
- ❌ Broadcasting tapi no "to 1 client" → MP disconnected

**Jika ada tapi MP tetap kosong:**
- ❌ MAVLink message format invalid → Check logs untuk errors
- ❌ Drone not armed → MP shows map tapi grey (normal)

---

### Problem: Lots of Errors di Terminal

**Common Errors:**

| Error | Solusi |
|-------|--------|
| `'list' object has no attribute 'get_type'` | Already fixed in mavlink_bridge.py |
| `getaddrinfo failed` | MQTT broker address salah atau network down |
| `connection refused` | Port 14550 already in use atau firewall |
| `Failed to create HEARTBEAT` | MAVLink encoding error - check pymavlink version |

---

## ✅ COMPLETE SETUP (GCS Side)

### Terminal 1: mqtt_to_mavlink_gcs.py

```bash
cd d:\AgumAgum\coding\mqttTelemetry\gcs

# Set MQTT credentials (same as aircraft side)
$env:MQTT_BROKER="ef6ff411.ala.asia-southeast1.emqxsl.com"
$env:MQTT_PORT="8883"
$env:MQTT_USERNAME="user1"
$env:MQTT_PASSWORD="public1"
$env:MQTT_TOPIC="uav/telemetry/crepes387"

# Run
python mqtt_to_mavlink_gcs.py
```

**Wait for:**
```
✅ MAVLink server listening on 0.0.0.0:14550
```

### Terminal 2: Mission Planner (GUI)

1. **Open Mission Planner**
2. **Connect**: TCP → 127.0.0.1:14550
3. **Wait 5 seconds**
4. **Should see map + telemetry data**

---

## 📊 FLOW DIAGRAM

```
Pixhawk (COM12)
    ↓
MAVProxy (Terminal 1 aircraft side)
    ↓
mavlink_bridge.py (Terminal 2 aircraft side)
    ↓
MQTT Broker (Cloud)
    ↓
mqtt_to_mavlink_gcs.py (Terminal 1 GCS side) ← YOU ARE HERE
    ↓
Mission Planner (GUI, connects to 127.0.0.1:14550)
```

---

## 🎯 EXPECTED OUTPUT

### Aircraft Side (mavlink_bridge.py)
```
📍 GPS: -35.3633, 149.1652, Alt: 50.2m
🔋 Battery: 12.60V, 95%, Current: 5.2A
🔄 Attitude: R=0.05°, P=-0.02°, Y=45.20°
⚡ Speed: 1.54 m/s, Climb: 0.00 m/s
📡 Status: Armed=True, Mode=LOITER
🎯 Published seq 1 to MQTT (GPS: -35.3633, 149.1652)
```

### GCS Side (mqtt_to_mavlink_gcs.py)
```
📡 MQTT Broker: ef6ff411.ala.asia-southeast1.emqxsl.com:8883
🔗 MAVLink Server: 0.0.0.0:14550
✅ Connected to MQTT broker
📡 Subscribed to: uav/telemetry/crepes387
✅ MAVLink server listening on 0.0.0.0:14550
📨 Received MQTT seq 1: GPS=-35.3633,149.1652 | Battery=95%
📱 Client connected: ('127.0.0.1', 58950) (Total: 1)
📡 Broadcasting seq 1 to 1 client(s)
```

### Mission Planner
```
✅ Connected
🗺️ Map visible
✅ Telemetry data (altitude, speed, heading, battery)
✅ Can add/edit waypoints
```

---

## 🆘 LAST RESORT: Full System Check

1. **Cek MQTT:** 
   ```bash
   mosquitto_pub -h ef6ff411... -u user1 -P public1 -t test -m "hello"
   ```

2. **Cek Port 14551 (MAVProxy):**
   ```powershell
   netstat -ano | findstr :14551
   ```

3. **Cek Port 14550 (GCS):**
   ```powershell
   netstat -ano | findstr :14550
   ```

4. **Restart Everything:**
   - Kill MAVProxy
   - Kill mavlink_bridge.py
   - Kill mqtt_to_mavlink_gcs.py
   - Start from beginning

---

**Jika masih error, copy-paste terminal output dan tunjukkan ke saya!** 🚀
