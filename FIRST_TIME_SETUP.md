# 🎯 STEP-BY-STEP FIRST-TIME SETUP

## Total Time: ~15 minutes

---

## PART 1: INSTALLATION (5 minutes)

### Step 1.1: Open Terminal

Windows:
1. Press `Win + R`
2. Type `powershell`
3. Press Enter

Or:
1. Search "Command Prompt" or "PowerShell"
2. Click "Run as Administrator" (recommended)

### Step 1.2: Navigate to Project

```bash
cd d:\AgumAgum\coding\mqttTelemetry
```

**Verify you see files:**
```bash
ls
# Should show:
# - publisher/
# - gcs/
# - dashboard/
# - REQUIREMENTS.md
# - QUICKSTART.md
# etc.
```

### Step 1.3: Install Dependencies

```bash
pip install -r requirements_mavproxy.txt
```

**Wait for completion (~3-5 minutes)**

Expected output:
```
Successfully installed MAVProxy paho-mqtt pymavlink ...
```

### Step 1.4: Verify Installation

```bash
mavproxy.py --version
```

Should output something like:
```
MAVProxy 1.8.60
```

If error: Go to [Troubleshooting - Issue 1](#issue-1)

---

## PART 2: STARTING THE SYSTEM (10 minutes)

Choose ONE of the following scenarios:

---

## 🟢 SCENARIO A: SIMPLE LOCAL (Recommended for First-Time)

**Perfect for:** Testing locally, learning, simulator mode

### Terminal 1: Start MAVProxy Hub

```bash
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551
```

**Wait for:**
```
Loaded module mavsys
Ready to fly
```

Leave this running.

### Terminal 2: Start Bridge

1. Open **new terminal window** (Ctrl+Shift+N or File → New Window)
2. Navigate to project:
   ```bash
   cd d:\AgumAgum\coding\mqttTelemetry\publisher
   ```
3. Run bridge:
   ```bash
   python mavlink_bridge.py
   ```

**Wait for:**
```
✅ Listening on UDP port 14551
✅ Connected to MQTT broker
```

**You should see:**
```
📍 GPS: 0.000000, 0.000000
🔋 Battery: 12.60V, 100%
🔄 Attitude: R=0.05, P=-0.02, Y=45.20
🚀 Published seq 1 (245 bytes)
```

### Terminal 3: Connect Mission Planner

1. **Download Mission Planner** (if not have):
   - Go to: https://ardupilot.org/planner/
   - Click "Download" for your OS
   - Install

2. **Open Mission Planner**

3. **Connect:**
   - Find the dropdown at top-right (shows "COM3" or similar)
   - Click dropdown
   - Select **TCP** from the list
   - IP field: `127.0.0.1`
   - Port field: `14550`
   - Click **CONNECT**

4. **Wait 5-10 seconds**
   - Should show "Connected" at top
   - Map appears with drone icon
   - Telemetry data visible (battery %, altitude, etc.)

### Terminal 4: View Dashboard (Optional)

1. Open **new terminal** in dashboard folder:
   ```bash
   cd d:\AgumAgum\coding\mqttTelemetry\dashboard
   python -m http.server 8000
   ```

2. Open browser:
   ```
   http://localhost:8000
   ```

3. Should see live telemetry data

---

## 🔵 SCENARIO B: NETWORK SETUP (2 Computers)

**Perfect for:** Real drone operation, field + office setup

### Computer A (Drone Site) - Terminal 1

```bash
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551
```

### Computer A (Drone Site) - Terminal 2

```bash
cd d:\AgumAgum\coding\mqttTelemetry\publisher
python mavlink_bridge.py
```

Wait for:
```
✅ Publishing telemetry...
📍 GPS data showing
```

### Computer B (GCS Office) - Terminal 1

Install GCS requirements:
```bash
cd d:\AgumAgum\coding\mqttTelemetry\gcs
pip install -r requirements.txt
```

Then run converter:
```bash
python mqtt_to_mavlink_gcs.py
```

Should show:
```
✅ Connected to MQTT broker
📡 Subscribed to: uav/telemetry/crepes387
✅ MAVLink server listening on 0.0.0.0:14550
```

### Computer B (GCS Office) - Terminal 2

Mission Planner:
1. Click dropdown → **TCP**
2. IP: `127.0.0.1`
3. Port: `14550`
4. Click **CONNECT**

Should connect successfully!

---

## ✅ VERIFICATION CHECKLIST

**After everything started, check these:**

- [ ] **Terminal 1 (MAVProxy)** - Shows "Ready to fly"
- [ ] **Terminal 2 (Bridge)** - Shows "🚀 Published seq N"
- [ ] **Mission Planner** - Shows "Connected" in top-right
- [ ] **Mission Planner Map** - Drone icon visible
- [ ] **Mission Planner HUD** - Shows battery %, altitude, speed
- [ ] **Terminal 2** - Shows "📍 GPS:" and "🔋 Battery:" data

If any are missing → See [Troubleshooting](#troubleshooting)

---

## 🎮 TESTING MISSION PLANNER

Once connected, try:

### View Telemetry

1. In Mission Planner, find the tabs: **Flight Plan**, **Flight Data**, **Simulation**, **Config/Tuning**
2. Click **Flight Data**
3. You should see:
   - Map with your location
   - Drone icon
   - Attitude gauge (roll, pitch, yaw)
   - Battery status
   - Current mode
   - Altitude, speed, etc.

### Zoom Map

1. Use scroll wheel to zoom in/out
2. Right-click drag to pan

### See Full Telemetry

1. Right-side has tabs
2. Click each to see different data:
   - GPS coordinates
   - Battery details
   - Flight time
   - Message log

---

## 🛑 STOPPING THE SYSTEM

When done testing:

1. **Terminal 3 (Mission Planner)**: Close the window
2. **Terminal 2 (Bridge)**: Press `Ctrl+C`
3. **Terminal 1 (MAVProxy)**: Press `Ctrl+C`

All should stop cleanly.

---

## 🔧 NEXT STEPS

Now that basic setup works:

1. **Read COMPLETE_SETUP_GUIDE.md** for all 3 scenarios explained
2. **Read QUICK_REFERENCE.md** for command reference
3. **Read ARCHITECTURE.md** to understand the system
4. **Set environment variables** for your specific broker
5. **Test with real hardware** (Pixhawk/drone)

---

## 📊 WHAT EACH TERMINAL IS DOING

### Terminal 1 (MAVProxy)
- **Role:** Central hub/router
- **Input:** Pixhawk MAVLink stream (UDP 14540)
- **Output:** Sends to multiple places (14550, 14551, etc.)
- **Status:** "Ready to fly" = working

### Terminal 2 (MAVLink Bridge)
- **Role:** Converter and publisher
- **Input:** UDP stream from MAVProxy (14551)
- **Process:** Parse MAVLink messages → Convert to JSON
- **Output:** Publish to MQTT broker
- **Status:** "🚀 Published seq N" = working

### Terminal 3 (Mission Planner)
- **Role:** Ground station GUI
- **Input:** MAVLink stream from MAVProxy (TCP 14550)
- **Display:** Map, telemetry, graphs
- **Status:** "Connected" = working

### Terminal 4 (Dashboard - Optional)
- **Role:** Web-based telemetry view
- **Input:** MQTT from broker (via WebSocket)
- **Display:** Live charts and gauges
- **Access:** http://localhost:8000

---

## ❓ QUICK TROUBLESHOOTING

| Problem | Quick Fix |
|---------|-----------|
| "Command not found: mavproxy.py" | Run: `pip install MAVProxy` |
| "Port already in use" | Kill process: `taskkill /F /IM python.exe` |
| "Mission Planner won't connect" | Check "Connected" shows in top-right MP window |
| "No drone icon on map" | Check Terminal 1 shows "Ready to fly" |
| "No telemetry data" | Check Terminal 2 shows "🚀 Published..." |
| "MQTT connection error" | Check internet connection to broker |

---

## 💡 TIPS FOR SUCCESS

1. **Keep terminals in view** - easier to see if something stops
2. **Read the logs** - they tell you what's happening
3. **Test one terminal at a time** - make sure each starts successfully
4. **Don't close Mission Planner while troubleshooting** - it might interfere
5. **Restart in order** - Terminal 1 → Terminal 2 → Terminal 3
6. **Check ports** - if stuck, ports might be blocked/in-use
7. **Test without real hardware first** - use simulator to learn

---

## 🎓 UNDERSTANDING THE FLOW

```
PIXHAWK DATA FLOW:
Pixhawk → MAVProxy → Split to 3 outputs:
                    ├─→ Mission Planner (TCP)
                    ├─→ Bridge (UDP)
                    │     └─→ MQTT Broker
                    │
                    └─→ Dashboard (Browser)
```

---

## 📝 NOTES FOR NEXT SESSION

Once working, save these details for next time:

```
✅ Command that worked:
   mavproxy.py --master=udpin://0.0.0.0:14540 \
       --out=127.0.0.1:14550 \
       --out=udpserver:0.0.0.0:14551

✅ MQTT Broker used:
   ef6ff411.ala.asia-southeast1.emqxsl.com:8883

✅ Mission Planner connection:
   TCP - 127.0.0.1:14550

✅ Time to setup: ~15 minutes
```

---

## 🚀 WHEN READY FOR REAL HARDWARE

1. Instead of simulator, connect real Pixhawk
2. Change: `--master=/dev/ttyUSB0,57600` (Linux)
3. Or: `--master=com3,57600` (Windows)
4. Everything else stays the same!
5. Check SETUP_MAVPROXY.md for details

---

## 📞 IF STUCK

1. Check **TROUBLESHOOTING.md** - has solutions for common issues
2. Check **QUICK_REFERENCE.md** - has all commands
3. Read terminal error messages carefully - they tell you what's wrong
4. Restart everything and try again
5. Make sure all terminals are in correct folder
6. Make sure dependencies are installed correctly

---

**Congratulations! You have a working MQTT telemetry system! 🎉**

Next, explore the advanced features in COMPLETE_SETUP_GUIDE.md
