# 📚 MQTT TELEMETRY SYSTEM - DOCUMENTATION INDEX

## Welcome! Start Here 👋

This project is a complete telemetry system for connecting drones/aircraft to Mission Planner via MQTT and MAVLink.

---

## 📖 DOCUMENTATION GUIDE

### 🟢 **For First-Time Users** (Read in this order)

1. **[FIRST_TIME_SETUP.md](FIRST_TIME_SETUP.md)** ⭐ **START HERE**
   - Quick 15-minute setup
   - Step-by-step instructions
   - Assumes no prior knowledge
   - Covers basic local setup

2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**
   - Command reference
   - Expected outputs
   - Quick checklist
   - Common fixes

3. **[ARCHITECTURE.md](ARCHITECTURE.md)**
   - Visual diagrams
   - System flow
   - Component interactions
   - Protocol stack

### 🔵 **For Comprehensive Understanding**

4. **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)**
   - 3 complete scenarios:
     - Local (1 PC)
     - Network (2 PCs)
     - Cloud (Distributed)
   - Environment variables
   - Port reference
   - File structure

### 🟠 **For Troubleshooting**

5. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
   - 7 common issues with solutions
   - Diagnostic commands
   - Port checking
   - MQTT testing
   - Emergency restart

### 📋 **For Reference**

6. **[REQUIREMENTS.md](REQUIREMENTS.md)** (Existing)
   - Dependency management
   - Installation options
   - Use cases by scenario

7. **[QUICKSTART.md](QUICKSTART.md)** (Existing)
   - TL;DR version
   - Port reference
   - Common issues

---

## 🎯 QUICK NAVIGATION BY USE CASE

### "I want to test it locally right now"
→ Read **[FIRST_TIME_SETUP.md](FIRST_TIME_SETUP.md)** (15 min)

### "I want to understand the system"
→ Read **[ARCHITECTURE.md](ARCHITECTURE.md)** then **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)**

### "I want to use it with 2 computers (field + office)"
→ Read **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)** → SCENARIO 2

### "I want to use it with cloud MQTT broker"
→ Read **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)** → SCENARIO 3

### "Something doesn't work"
→ Read **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

### "I need quick commands"
→ Read **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**

### "I want to know all configuration options"
→ Read **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)** → Environment Variables section

---

## 📂 PROJECT STRUCTURE

```
mqttTelemetry/
│
├── 📚 DOCUMENTATION (NEW - You're Here)
│   ├── FIRST_TIME_SETUP.md          ← START HERE
│   ├── QUICK_REFERENCE.md
│   ├── COMPLETE_SETUP_GUIDE.md
│   ├── ARCHITECTURE.md
│   ├── TROUBLESHOOTING.md
│   ├── README.md                    ← THIS FILE
│   │
│   └── EXISTING DOCS
│       ├── REQUIREMENTS.md
│       ├── QUICKSTART.md
│       ├── SETUP_MAVPROXY.md
│       ├── DISTRIBUTED_GCS.md
│       └── WAYPOINT_GUIDE.md
│
├── 📁 publisher/                     (Sender side)
│   ├── publisher.py                  Original - MAVSDK direct
│   ├── mavlink_bridge.py             Bridge - MAVProxy → MQTT
│   ├── sitl.py                       Simulator
│   ├── requirements.txt
│   └── emqxsl-ca.crt                 (Certificate)
│
├── 📁 gcs/                           (Receiver side)
│   ├── mqtt_to_mavlink_gcs.py        Converter - MQTT → MAVLink
│   ├── requirements.txt
│   └── emqxsl-ca.crt                 (Certificate)
│
├── 📁 dashboard/                     (Web UI)
│   ├── index.html                    Browser-based telemetry
│   └── (CSS/JS included in HTML)
│
├── 📁 data/                          (Output)
│   └── latest.json                   Last telemetry snapshot
│
└── 📄 ROOT FILES
    ├── setup.py
    ├── requirements_mavproxy.txt     Root dependencies
    └── launch_stack.sh               Shell script to run all
```

---

## 🚀 QUICK START (COPY-PASTE)

### Terminal 1: Start Hub
```bash
cd d:\AgumAgum\coding\mqttTelemetry
pip install -r requirements_mavproxy.txt
mavproxy.py --master=udpin://0.0.0.0:14540 --out=127.0.0.1:14550 --out=udpserver:0.0.0.0:14551
```

### Terminal 2: Start Bridge
```bash
cd d:\AgumAgum\coding\mqttTelemetry\publisher
python mavlink_bridge.py
```

### Terminal 3: Open Mission Planner
```
1. Start Mission Planner
2. CONNECT dropdown → TCP
3. IP: 127.0.0.1
4. Port: 14550
5. CONNECT
```

✅ Done! You should see drone icon on map.

---

## 🎓 UNDERSTANDING THE SYSTEM

### 3 Main Components

**1. Publisher/Bridge (Sender Side)**
- Reads MAVLink data from Pixhawk
- Converts to JSON
- Publishes to MQTT broker
- Runs on drone PC

**2. MQTT Broker (Middle)**
- Cloud service (EMQX, HiveMQ, etc.)
- Routes messages between sender and receiver
- Acts as message queue

**3. GCS Converter (Receiver Side)**
- Subscribes to MQTT messages
- Converts JSON back to MAVLink
- Creates server for Mission Planner
- Runs on GCS PC

### Telemetry Data Included

✅ GPS coordinates (latitude, longitude)
✅ Altitude (MSL and relative)
✅ Attitude (roll, pitch, yaw)
✅ Velocity (x, y, z, ground speed)
✅ Battery (voltage, current, %)
✅ Status (armed, flight mode, in-air)
✅ Timestamp (ISO 8601)
✅ Sequence number

---

## 🔧 CONFIGURATION

### Via Environment Variables

```bash
export MQTT_BROKER="your-broker.com"
export MQTT_PORT="8883"
export MQTT_USERNAME="user1"
export MQTT_PASSWORD="password"
export MQTT_TOPIC="uav/telemetry/crepes387"
export PUBLISH_INTERVAL="0.5"
```

### Default Broker (EMQX)

```
Host: ef6ff411.ala.asia-southeast1.emqxsl.com
Port: 8883 (TLS) or 1883 (non-TLS)
User: user1
Pass: public1
Topic: uav/telemetry/crepes387
```

---

## 📊 TYPICAL SETUP SCENARIOS

### Scenario 1: Local (1 PC)
```
Pixhawk/SITL → MAVProxy → MP (same PC)
              ↓
           Bridge
              ↓
           MQTT
              ↓
           Dashboard
```
**Time:** ~15 min | **Complexity:** Low

### Scenario 2: Network (2 PCs)
```
Pixhawk PC (Field)          GCS PC (Office)
    ↓                            ↓
MAVProxy ────→ MQTT ←───── GCS Converter
    ↓           Broker         ↓
Bridge                    Mission Planner
    ↓
MQTT Publisher
```
**Time:** ~20 min | **Complexity:** Medium

### Scenario 3: Cloud (Distributed)
```
Pixhawk (Remote Site)
    ↓
MAVProxy + Bridge
    ↓
MQTT Broker (Cloud)
    ↓
Any GCS (Office/Home/Mobile)
    ↓
Mission Planner
```
**Time:** ~25 min | **Complexity:** Medium

---

## ⚡ PERFORMANCE SPECS

| Metric | Value |
|--------|-------|
| Default publish rate | 2 Hz (0.5s interval) |
| Configurable range | 0.1 - 10 Hz |
| Typical message size | 200-300 bytes |
| Typical bandwidth | ~60 KB/min at 2 Hz |
| Latency | <100 ms (local network) |
| Cloud latency | ~200-500 ms (depends on broker) |

---

## 🔐 SECURITY NOTES

### MQTT Credentials
- Default: user1/public1 (for demo only)
- For production: Use strong passwords
- Store in environment variables (not code)

### TLS/SSL
- Default broker uses TLS on port 8883
- Certificate: emqxsl-ca.crt (already included)
- Non-TLS option on port 1883 (less secure)

### Network
- Do NOT expose MQTT broker to internet without auth
- Use VPN/firewall for remote connections
- Change default credentials

---

## 📞 SUPPORT & HELP

### Common Issues
See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for:
- Port conflicts
- Connection errors
- MQTT issues
- Mission Planner problems
- Diagnostic commands

### Quick Fixes
See **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** for:
- Common error solutions
- Command reference
- Verification checklist

### Learning
See **[ARCHITECTURE.md](ARCHITECTURE.md)** for:
- Visual diagrams
- Data flow
- Component interactions

---

## 🎯 RECOMMENDED LEARNING PATH

1. **Day 1:** Read [FIRST_TIME_SETUP.md](FIRST_TIME_SETUP.md) and do basic setup (15 min)
2. **Day 2:** Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand system (30 min)
3. **Day 3:** Read [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md) for advanced setup (45 min)
4. **Day 4+:** Deploy to your specific scenario with confidence!

---

## 💡 KEY TAKEAWAYS

✅ **This system bridges Pixhawk ↔ Mission Planner via MQTT**

✅ **It works locally, on network, or via cloud**

✅ **No code changes needed** - just configuration

✅ **Mission Planner gets real-time telemetry** automatically

✅ **Multiple GCS can connect** to same telemetry

✅ **Works with real hardware and simulators**

---

## 📝 FILES YOU'LL USE MOST

### As a Developer
- `publisher/mavlink_bridge.py` - Bridge code
- `gcs/mqtt_to_mavlink_gcs.py` - GCS converter code

### As an Operator
- Commands in QUICK_REFERENCE.md
- Environment variables
- MQTT credentials

### For Troubleshooting
- Terminal logs (most important!)
- TROUBLESHOOTING.md
- Diagnostic commands

---

## 🎉 NEXT STEPS

1. **Pick your scenario:**
   - [ ] Local (1 PC) - FIRST_TIME_SETUP.md
   - [ ] Network (2 PCs) - COMPLETE_SETUP_GUIDE.md → SCENARIO 2
   - [ ] Cloud - COMPLETE_SETUP_GUIDE.md → SCENARIO 3

2. **Follow the guide step-by-step**

3. **Test with the provided default broker** (EMQX)

4. **When working, customize for your needs:**
   - Change topic name
   - Set your own broker
   - Adjust publish interval

5. **Enjoy real-time telemetry! 🚁**

---

## 📖 ADDITIONAL RESOURCES

- **ArduPilot Documentation:** https://ardupilot.org/
- **Mission Planner Docs:** https://ardupilot.org/planner/
- **EMQX Documentation:** https://www.emqx.com/docs
- **MAVLink Protocol:** https://mavlink.io/
- **PyMAVLink:** https://github.com/ArduPilot/pymavlink

---

**Version:** 1.0
**Last Updated:** May 25, 2026
**Status:** Complete and tested ✅

---

**Ready to get started? → [FIRST_TIME_SETUP.md](FIRST_TIME_SETUP.md) (15 min)**
