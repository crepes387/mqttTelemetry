# 🏗️ SYSTEM ARCHITECTURE DIAGRAM

## Overview Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    MQTT TELEMETRY SYSTEM                          │
└──────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │    PIXHAWK      │
                    │  (Drone/UAV)    │
                    │   or SITL       │
                    └────────┬────────┘
                             │
                        MAVLink Stream
                             │
                ┌────────────┴────────────┐
                │   (UDP/Serial 14540)   │
                ▼                        ▼
         ┌──────────────────┐    ┌──────────────────┐
         │   MAVProxy       │    │   publisher.py   │
         │   (HUB)          │    │   (Direct MAVSDK)│
         ├──────────────────┤    └──────────────────┘
         │ Input:  14540    │            │
         │ Out1:   14550 →→→→→→→ Mission Planner
         │ Out2:   14551 ⬇
         │ Out3:   14552    │
         └──────────┬───────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  mavlink_bridge.py   │
         │  Parse MAVLink       │
         │  Convert → JSON      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   MQTT Broker        │
         │   (Cloud)            │
         │   - EMQX             │
         │   - HiveMQ           │
         │   - Mosquitto        │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────────────┐
         │   GCS / Remote Location      │
         │                              │
         │  ┌────────────────────────┐  │
         │  │  mqtt_to_mavlink_gcs   │  │
         │  │  Subscribe MQTT        │  │
         │  │  → Create MAVLink Srv  │  │
         │  └───────────┬────────────┘  │
         │              │               │
         │              ▼               │
         │  ┌────────────────────────┐  │
         │  │  MAVLink Server 14550  │  │
         │  └────────────┬───────────┘  │
         │               │              │
         │               ▼              │
         │  ┌────────────────────────┐  │
         │  │  Mission Planner       │  │
         │  │  (GUI)                 │  │
         │  └────────────────────────┘  │
         └──────────────────────────────┘

                    │
                    ▼
         ┌──────────────────────────────┐
         │  Dashboard (Browser)         │
         │  http://localhost:8000       │
         │                              │
         │  - Live Map                  │
         │  - Telemetry Graphs          │
         │  - Battery Status            │
         │  - Attitude Indicator        │
         └──────────────────────────────┘
```

---

## Data Flow - Sender Side (Pixhawk → MQTT)

```
     PIXHAWK                MAVProxy                    MQTT Broker
     ════════                ════════                    ═══════════
        │
        │ MAVLink packets
        │ (UDP:14540)
        ▼
    ┌─────────┐
    │ Listen  │
    │ UDP14540│
    └────┬────┘
         │
         │ MAVLink message stream
         │
    ┌────▼─────────────────────────────┐
    │ Parse MAVLink Message             │
    │ - GLOBAL_POSITION_INT (GPS)      │
    │ - ATTITUDE (Roll, Pitch, Yaw)    │
    │ - VELOCITY_VFR (Speed)           │
    │ - BATTERY_STATUS (Power)         │
    │ - HEARTBEAT (Status)             │
    └────┬──────────────────────────────┘
         │
         │ Extract telemetry
         │
    ┌────▼──────────────────────────────┐
    │ Convert to JSON                    │
    │ {                                  │
    │   "ts": "2024-05-25T12:00:00Z",   │
    │   "gps": { "lat": ..., "lon": ... │
    │   "attitude": { "roll": ... },     │
    │   "battery": { "v": 12.6, "%" ... │
    │   ...                              │
    │ }                                  │
    └────┬──────────────────────────────┘
         │
         │ MQTT Publish
         │ Topic: uav/telemetry/crepes387
         │
         ▼
    ┌──────────────────┐
    │ MQTT Broker      │
    │ (Cloud)          │
    └──────────────────┘
```

---

## Data Flow - Receiver Side (MQTT → Mission Planner)

```
    MQTT Broker              GCS Converter             Mission Planner
    ═══════════              ═════════════             ══════════════
        │
        │ MQTT Subscribe
        │ Topic: uav/telemetry/crepes387
        │
    ┌───▼────────────────────────────┐
    │ Receive JSON Message            │
    │ {                               │
    │   "ts": ..., "gps": {...},      │
    │   "attitude": {...}, ...        │
    │ }                               │
    └───┬────────────────────────────┘
        │
        │ Parse JSON telemetry
        │
    ┌───▼──────────────────────────────┐
    │ Create MAVLink Messages           │
    │ - HEARTBEAT                       │
    │ - GLOBAL_POSITION_INT             │
    │ - ATTITUDE                        │
    │ - VFR_HUD                         │
    │ - BATTERY_STATUS                  │
    └───┬──────────────────────────────┘
        │
        │ MAVLink packets
        │ TCP Server :14550
        │
    ┌───▼──────────────────────────────┐
    │ MAVLink Server                    │
    │ Broadcast to clients              │
    │ :14550 (TCP)                      │
    └───┬──────────────────────────────┘
        │
        │ MAVLink Stream (TCP)
        │
        ▼
    ┌─────────────────────────┐
    │ Mission Planner         │
    │ Receive packets         │
    ├─────────────────────────┤
    │ ✅ Drone icon on map    │
    │ ✅ Telemetry display    │
    │ ✅ Battery % & Voltage  │
    │ ✅ GPS coordinates      │
    │ ✅ Attitude gauge       │
    │ ✅ Flight mode          │
    └─────────────────────────┘
```

---

## Local Setup (Single PC)

```
        TERMINAL 1              TERMINAL 2              TERMINAL 3
        ══════════              ══════════              ══════════

    ┌──────────────────┐
    │  MAVProxy        │
    │ (HUB)            │
    ├──────────────────┤
    │ Listen: 14540    │
    │ Out: 14550       │
    │ Out: 14551       │
    │ Out: 14552       │
    └────────┬─────────┘
             │
    ┌────────┴──────────┬────────────────────┐
    │                   │                    │
    ▼                   ▼                    ▼
┌─────────┐         ┌──────────────────┐ ┌──────────────────┐
│   MP    │         │ mavlink_bridge   │ │  publisher.py    │
│ :14550  │         │     :14551       │ │  (MAVSDK direct) │
│         │         │                  │ │                  │
└─────────┘         └────────┬─────────┘ └──────────────────┘
                             │
                             ▼
                        ┌──────────┐
                        │ MQTT     │
                        │ :8883    │
                        └──────────┘
                             │
                    TERMINAL 4 (optional)
                    ══════════════════════
                             │
                             ▼
                        ┌──────────────┐
                        │  Dashboard   │
                        │  :8000       │
                        └──────────────┘
```

---

## Network Setup (2 PCs)

```
        COMPUTER A (Pixhawk Site)          COMPUTER B (GCS Office)
        ════════════════════════════════════════════════════════════

        TERMINAL 1          TERMINAL 2      TERMINAL 1          TERMINAL 2
        ══════════          ══════════      ══════════          ══════════

    ┌──────────────┐   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   MAVProxy   │   │  mavlink_    │  │ mqtt_to_     │  │  Mission     │
    │   14540 ←─   │   │  bridge.py   │  │ mavlink_gcs  │  │  Planner     │
    │   14550 →    │   │   14551 ←─   │  │  :14550      │  │  TCP :14550  │
    │   14551 →→   │   │              │  │              │  │              │
    └──────────────┘   └────────┬─────┘  └────────┬─────┘  └──────────────┘
                                │                 │
                                ▼                 │
                           ┌──────────┐           │
                           │   MQTT   │◄──────────┘
                           │  Broker  │
                           │ (Cloud)  │
                           └──────────┘
```

---

## Port Mapping Reference

```
┌────────────────────────────────────────────────────────┐
│                   PORT ALLOCATION                       │
├────────────────────────────────────────────────────────┤
│                                                         │
│  14540  ◄─────── Pixhawk/SITL Input to MAVProxy      │
│         UDP                                             │
│                                                         │
│  14550  ────────► Mission Planner Output from MAVProxy │
│         TCP       (localhost or network)                │
│                                                         │
│  14551  ────────► MAVLink Bridge Input from MAVProxy   │
│         UDP       (localhost only)                      │
│                                                         │
│  14552  ────────► (Optional) Extra output port         │
│         UDP                                             │
│                                                         │
│  8883   ◄────────► MQTT Broker (TLS Encrypted)         │
│         TCP       (Cloud)                               │
│                                                         │
│  8000   ────────► Dashboard (Browser)                  │
│         TCP       (http://localhost:8000)               │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## Component Interactions

```
      SENDER SIDE              TRANSPORT               RECEIVER SIDE
      ═══════════              ═════════               ══════════════

    ┌─────────────┐
    │   PIXHAWK   │
    └──────┬──────┘
           │ MAVLink (UDP:14540)
           │
    ┌──────▼───────────────┐
    │   MAVProxy (HUB)      │
    │  ├─ Parse MAVLink     │
    │  ├─ Buffer data       │
    │  └─ Multiplex output  │
    └──────┬────────────────┘
           │
       ┌───┴────┬─────────┐
       │        │         │
       │        │         │
  14550│  14551 │   14552  │
  (TCP)│  (UDP) │   (UDP)  │
       │        │         │
    ┌──▼─┐  ┌──▼──┐     │
    │ MP │  │Bridge   │     │
    └────┘  └───┬──┘     │
               │         │
               │ JSON    │
               │ over    │
               │ MQTT    │
               │         │
          ┌────▼────────────┐
          │  MQTT Broker    │
          │  (Centralized   │
          │   Message Bus)  │
          └────┬────────────┘
               │ JSON from MQTT
               │
          ┌────▼──────────────┐
          │  GCS Converter    │
          │  ├─ Subscribe MQTT│
          │  ├─ Parse JSON    │
          │  └─ Emit MAVLink  │
          └────┬───────────────┘
               │ MAVLink (TCP:14550)
               │
          ┌────▼───────────────┐
          │  Mission Planner   │
          │  ├─ Parse MAVLink  │
          │  ├─ Update Map     │
          │  └─ Show Telemetry │
          └────────────────────┘
```

---

## State Transitions - Mission Planner Connection

```
START
  │
  ├─ All terminals launched
  │
  ▼
[INITIALIZING]
  │
  ├─ MAVProxy connecting to Pixhawk
  │
  ▼
[WAITING FOR HEARTBEAT]
  │
  ├─ Bridge listening on :14551
  │ └─ MAVProxy sending MAVLink stream
  │
  ▼
[STREAMING MAVLink]
  │
  ├─ Bridge parsing messages
  │ ├─ GLOBAL_POSITION_INT ✓
  │ ├─ ATTITUDE ✓
  │ ├─ VELOCITY ✓
  │ ├─ BATTERY_STATUS ✓
  │ └─ HEARTBEAT ✓
  │
  ▼
[PUBLISHING TO MQTT]
  │
  ├─ JSON messages to broker
  │ └─ Topic: uav/telemetry/crepes387
  │
  ▼
[MISSION PLANNER CONNECTS]
  │
  ├─ MP sends TCP connect to :14550
  │ └─ (if remote GCS, connects to :14550 from converter)
  │
  ▼
[CONNECTED]
  ├─ ✅ Drone icon on map
  ├─ ✅ Real-time telemetry
  ├─ ✅ Battery display
  ├─ ✅ Flight status
  └─ ✅ Ready for operations

RUNNING
  │
  ├─ Continuous telemetry update
  │ ├─ 2Hz default rate
  │ └─ Configurable via PUBLISH_INTERVAL
  │
  └─ Press Ctrl+C to stop any process
```

---

## Protocol Stack

```
┌─────────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                       │
│  ├─ Mission Planner GUI                                 │
│  ├─ Dashboard (Web)                                     │
│  └─ Custom apps                                         │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  PROTOCOL LAYER                                          │
│  ├─ MAVLink (MAVProxy, Bridge, Converter)               │
│  ├─ JSON (MQTT transport)                               │
│  └─ HTTP (Dashboard)                                    │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  TRANSPORT LAYER                                         │
│  ├─ TCP :14550 (MP connection)                          │
│  ├─ UDP :14540-14552 (MAVProxy streams)                │
│  ├─ TCP/TLS :8883 (MQTT broker)                         │
│  └─ TCP :8000 (HTTP dashboard)                          │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  PHYSICAL LAYER                                          │
│  ├─ Serial (Pixhawk↔computer)                           │
│  ├─ UDP/TCP (Localhost)                                 │
│  ├─ Ethernet/WiFi (Network)                             │
│  └─ Internet (Cloud MQTT)                               │
└─────────────────────────────────────────────────────────┘
```

