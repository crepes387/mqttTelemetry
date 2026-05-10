# 🚀 Quick Start - MAVProxy + Mission Planner Integration

## TL;DR Setup (3 terminals)

### Terminal 1: Install & Run MAVProxy
```bash
# Install dependencies
pip install -r requirements_mavproxy.txt

# Start MAVProxy (hub)
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551
```

### Terminal 2: Start MAVLink→MQTT Bridge
```bash
cd publisher
python mavlink_bridge.py
```

### Terminal 3: Mission Planner (Windows/Linux GUI)
1. Open **Mission Planner**
2. Click **CONNECT** dropdown → Select **TCP**
3. Enter: `127.0.0.1` : `14550`
4. Click **CONNECT**

✅ **Mission Planner terhubung!**

---

## Apa yang akan Anda lihat?

### Mission Planner:
- ✅ Drone icon di map (shows GPS position)
- ✅ Real-time attitude (pitch, roll, yaw)
- ✅ Battery voltage & %
- ✅ Flight mode
- ✅ Altitude & speed
- ✅ Can add/manage waypoints

### Dashboard (http://localhost:8000):
- ✅ Auto-update dari MQTT
- ✅ Same telemetry data
- ✅ Browser-based (no software needed)

### Terminal 2 (Bridge):
```
📍 GPS: -35.363261, 149.165230
🔄 Attitude: R=0.05, P=-0.02, Y=45.20
🔋 Battery: 11.80V, 95%
🚀 Published seq 42 (245 bytes)
```

---

## Port Reference

| Port | Service | Input/Output |
|------|---------|---|
| **14540** | Pixhawk→MAVProxy | Input (from drone) |
| **14550** | MAVProxy→Mission Planner | Output (to MP) |
| **14551** | MAVProxy→Bridge | Output (to app) |
| **8883** | MQTT Broker | (cloud) |
| **8000** | Dashboard | (your browser) |

---

## Possible Issues & Quick Fixes

| Issue | Fix |
|-------|-----|
| "mavproxy.py not found" | `pip install MAVProxy` |
| "Port 14550 already in use" | `lsof -i :14550` then `kill -9 <PID>` |
| "Mission Planner won't connect" | Check MAVProxy is running, port open: `netstat -an \| grep 14550` |
| "No telemetry in bridge" | Check Pixhawk connected to MAVProxy: look for "Ready to fly" message |
| "MQTT not publishing" | Verify broker online: `mosquitto_pub -h <broker> -u <user> -P <pass> -t test -m hi` |

---

## Environment Variables (optional)

```bash
export MQTT_BROKER="your-broker.com"
export MQTT_PORT="8883"
export MQTT_USERNAME="user1"
export MQTT_PASSWORD="pass1"
export MQTT_TOPIC="uav/telemetry/crepes387"
export PUBLISH_INTERVAL="1.0"
export MAVLINK_LISTEN_PORT="14551"

# Then run bridge
python mavlink_bridge.py
```

---

## Next: Waypoint Management

Once connected to Mission Planner:

1. **Create Waypoint**: Right-click map → Add Waypoint
2. **Set Altitude & Speed**: Edit waypoint properties
3. **Upload**: Click **Write WPs** button
4. **Monitor**: Watch drone fly waypoints in real-time
5. **Download**: Click **Read WPs** to get waypoints from drone

All synchronized through MAVProxy bridge! ✨

---

## Full Documentation

See [SETUP_MAVPROXY.md](./SETUP_MAVPROXY.md) for detailed setup, troubleshooting, and remote setup.

---

## Architecture Diagram

```
Pixhawk (UDP 14540)
       ↓
    MAVProxy (central hub)
    ↙      ↘      ↙
MP     Bridge   Apps
(visual) (MQTT) (other)
```

**Key Idea:** MAVProxy receives MAVLink data once from Pixhawk, then distributes to multiple consumers (Mission Planner, your app, etc.)

This avoids multiple connections to Pixhawk which can cause conflicts!

---

## One More Thing...

**Already have original publisher.py running?**

Don't run it alongside the bridge! Choose one:

- **Option A (Recommended):** Use `mavlink_bridge.py` (connects via MAVProxy)
- **Option B:** Keep `publisher.py` (direct MAVSDK connection)

You can't have both connecting to Pixhawk at the same time (they'll fight over the same data stream).

👉 For Mission Planner integration → use MAVProxy + Bridge ✨
