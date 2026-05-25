# ⚡ QUICK REFERENCE - Setup Commands

## 🔥 FASTEST SETUP (Local - 5 Minutes)

### Prerequisites (1 kali)
```bash
cd d:\AgumAgum\coding\mqttTelemetry
pip install -r requirements_mavproxy.txt
cd publisher && pip install -r requirements.txt && cd ..
```

### Terminal 1: Start Simulator + MAVProxy
```bash
# Jika pakai SITL
cd publisher
python -c "from dronekit_sitl import SITL; s=SITL(); s.launch(['--home=0,0,0'])" &
sleep 2

# Jalankan MAVProxy
mavproxy.py --master=udpin://0.0.0.0:14540 --out=127.0.0.1:14550 --out=udpserver:0.0.0.0:14551
```

### Terminal 2: Start Bridge
```bash
cd d:\AgumAgum\coding\mqttTelemetry\publisher
python mavlink_bridge.py
```

### Terminal 3: Mission Planner
```
1. Open Mission Planner
2. Click: CONNECT dropdown → TCP
3. IP: 127.0.0.1
4. Port: 14550
5. Click CONNECT
```

### Terminal 4: Dashboard (Optional)
```bash
cd d:\AgumAgum\coding\mqttTelemetry\dashboard
python -m http.server 8000

# Open browser: http://localhost:8000
```

---

## 🌐 DISTRIBUTED SETUP (2 Computers)

### Computer A (Drone Site) - 2 Terminals

**Terminal 1:**
```bash
mavproxy.py --master=udpin://0.0.0.0:14540 --out=127.0.0.1:14550 --out=udpserver:0.0.0.0:14551
```

**Terminal 2:**
```bash
cd d:\AgumAgum\coding\mqttTelemetry\publisher
python mavlink_bridge.py
```

### Computer B (GCS) - 2 Terminals

**Terminal 1: Set MQTT Variables (PowerShell)**
```powershell
$env:MQTT_BROKER = "your-broker.com"
$env:MQTT_PORT = "8883"
$env:MQTT_USERNAME = "user1"
$env:MQTT_PASSWORD = "public1"
$env:MQTT_TOPIC = "uav/telemetry/crepes387"

# Then run converter
cd d:\AgumAgum\coding\mqttTelemetry\gcs
python mqtt_to_mavlink_gcs.py
```

**Terminal 2: Mission Planner**
```
1. CONNECT → TCP
2. IP: 127.0.0.1
3. Port: 14550
4. CONNECT
```

---

## 📊 EXPECTED OUTPUT

### Terminal 1 (MAVProxy)
```
Loaded module mavsys
Ready to fly
Received MAVLink messages
```

### Terminal 2 (Bridge)
```
✅ Connected to MQTT broker
📡 Listening on UDP port 14551
🚀 Publishing telemetry...
📍 GPS: 0.000000, 0.000000
🔋 Battery: 12.60V, 100%
🔄 Attitude: R=0.05, P=-0.02, Y=45.20
```

### Terminal 3 (Mission Planner)
```
Status: Connected
Drone icon visible on map
Real-time telemetry displayed
```

---

## ✅ VERIFICATION CHECKLIST

- [ ] MAVProxy running and show "Ready to fly"
- [ ] Bridge show "🚀 Publishing telemetry..."
- [ ] MQTT broker connected
- [ ] Mission Planner show "Connected"
- [ ] Drone icon visible on map
- [ ] Battery % displayed
- [ ] GPS coordinates visible

---

## 🔧 ENVIRONMENT VARIABLES (Full List)

### For `publisher/mavlink_bridge.py`
```powershell
$env:PIXHAWK_CONNECTION = "udpin://127.0.0.1:14540"
$env:MAVLINK_LISTEN_PORT = "14551"
$env:MQTT_BROKER = "ef6ff411.ala.asia-southeast1.emqxsl.com"
$env:MQTT_PORT = "8883"
$env:MQTT_USERNAME = "user1"
$env:MQTT_PASSWORD = "public1"
$env:MQTT_TOPIC = "uav/telemetry/crepes387"
$env:PUBLISH_INTERVAL = "0.5"
```

### For `gcs/mqtt_to_mavlink_gcs.py`
```powershell
$env:MQTT_BROKER = "ef6ff411.ala.asia-southeast1.emqxsl.com"
$env:MQTT_PORT = "8883"
$env:MQTT_USERNAME = "user1"
$env:MQTT_PASSWORD = "public1"
$env:MQTT_TOPIC = "uav/telemetry/crepes387"
$env:MAVLINK_SERVER_PORT = "14550"
```

---

## 🆘 QUICK FIXES

### "Port already in use"
```powershell
netstat -ano | findstr :14550
taskkill /PID <PID> /F
```

### "Module not found"
```bash
pip install -r requirements_mavproxy.txt
cd publisher && pip install -r requirements.txt
```

### "Can't connect to MQTT"
```bash
# Test MQTT connection
mosquitto_pub -h your-broker.com -u user1 -P public1 -p 8883 -t test -m "hello"
```

### "Mission Planner won't connect"
```bash
# Test if port 14550 is listening
telnet 127.0.0.1 14550
# Should connect. Press Ctrl+]
```

---

## 📝 REFERENCE - Port Numbers

| Port | Service | From | To |
|------|---------|------|-----|
| 14540 | Pixhawk↔MAVProxy | Pixhawk | MAVProxy |
| 14550 | MAVProxy↔Mission Planner | MAVProxy | MP (TCP) |
| 14551 | MAVProxy↔Bridge | MAVProxy | Bridge (UDP) |
| 8883 | MQTT (TLS) | Any | Broker |
| 8000 | Dashboard | Browser | Dashboard |

---

## 💡 TIPS

1. **Always start MAVProxy first** - it's the central hub
2. **Check logs carefully** - they show exactly what's happening
3. **Use environment variables** - makes config management easier
4. **Test MQTT connection separately** - helps isolate issues
5. **Verify ports are accessible** - firewall might block them

---

## 📞 COMMON ISSUES & SOLUTIONS

| Issue | Solution |
|-------|----------|
| "MQTT connection refused" | Check broker URL, port, username, password |
| "No drone icon on map" | Check MAVProxy showing "Ready to fly" |
| "Telemetry not updating" | Check Bridge logs for MQTT publish messages |
| "Can't connect to broker" | Try different broker or ping to test network |
| "Python module not found" | Run `pip install -r requirements.txt` again |
| "Port already in use" | Find and kill process using that port |
| "Certificate error" | Download emqxsl-ca.crt to publisher/ and gcs/ folders |

