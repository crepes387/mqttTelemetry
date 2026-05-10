# 🗺️ Waypoint Management Guide

Dengan MAVProxy + Mission Planner integration, Anda bisa fully manage waypoints sambil monitoring real-time telemetry.

---

## Mission Planner Waypoint Workflow

### 1. Create/Edit Waypoints

**In Mission Planner:**

1. **Switch to FLIGHT PLAN tab**
   - Left panel: "Flight Data" view
   - Top menu: "FLIGHT PLAN" tab
   - (or press Ctrl+Alt+W)

2. **Add Waypoint**
   - Right-click on map
   - Select "Add Waypoint"
   - Edit parameters in list below:
     - **Alt (m)**: Altitude above ground
     - **Cmd**: Command type (Waypoint, Loiter, RTH, etc.)
     - **Lat/Lon**: Auto-populated from click location

3. **Example Mission:**
   ```
   Waypoint 1 (Home): 0,0,0m
   Waypoint 2: 100m north, 50m alt
   Waypoint 3: 200m east, 50m alt
   Waypoint 4: Return to Launch (RTL)
   ```

### 2. Upload Waypoints to Drone

1. **Click "Write WPs" button** (in toolbar)
   - MAVProxy will send to Pixhawk
   - Wait for confirmation

2. **View in telemetry:**
   ```
   [MAVProxy Console]
   wp list   # List all waypoints
   wp status # Current waypoint progress
   ```

### 3. Monitor Execution

**Real-time Display:**
- Current waypoint highlighted on map
- Drone icon follows GPS position
- Breadcrumb trail shows flight path
- Telemetry data updates in real-time:
  - Altitude
  - Speed (groundspeed, vertical speed)
  - Battery %
  - Flight mode
  - Yaw angle

---

## Advanced Waypoint Features

### Loiter Waypoint (circle at location)

1. Add waypoint (right-click)
2. Change **Cmd** to "Loiter" or "Loiter Unlim"
3. Set:
   - **Alt**: Loiter altitude
   - **Param1**: Radius (meters)
   - **Param2**: Direction (1=clockwise, -1=ccw)
   - **Param3**: Turns (number of circles, 0=infinite)

### Conditional Waypoints

- **Do-Pause-Continue**: Stop and wait
- **Do-Set-Servo**: Trigger external device
- **Do-Set-Relay**: Turn on/off relay

These sync through MAVProxy→Bridge→MQTT for logging.

### Geofence

1. Plan tab → Geofence sub-tab
2. Set polygon/circle boundary
3. Write to drone
4. Drone auto-RTL if exceeds fence

---

## Telemetry During Mission

### What gets logged to MQTT:

Every time bridge publishes (interval=1.0s by default):

```json
{
  "ts": "2026-05-10T14:30:45.123Z",
  "seq": 42,
  "gps": {
    "latitude": -35.363261,
    "longitude": 149.165230,
    "altitude_msl": 100.5,
    "altitude_relative": 50.2,
    "satellite_count": 10
  },
  "attitude": {
    "roll": 5.2,
    "pitch": -2.1,
    "yaw": 45.8
  },
  "velocity": {
    "x": 3.5,
    "y": 2.1,
    "z": -0.5,
    "ground_speed": 4.2
  },
  "battery": {
    "voltage_v": 11.8,
    "current_a": 2.5,
    "remaining_percent": 85,
    "health": null
  },
  "status": {
    "armed": true,
    "flight_mode": "AUTO",
    "in_air": true,
    "is_connected": true
  }
}
```

### Subscribe to telemetry:

```bash
mosquitto_sub -h ef6ff411.ala.asia-southeast1.emqxsl.com \
    -u user1 -P public1 \
    -t "uav/telemetry/crepes387" \
    | jq '.' # Pretty print JSON
```

---

## Dashboard Integration

### HTML Dashboard auto-reads from `/data/latest.json`

The bridge writes telemetry to:
```
../data/latest.json
```

Your dashboard can:
1. Read this file every 100ms (fast updates)
2. Parse JSON
3. Display on map/gauge

**Example dashboard update loop:**
```javascript
// Fetch telemetry
fetch('/data/latest.json')
    .then(r => r.json())
    .then(data => {
        // Update map marker
        marker.setLatLng([data.gps.latitude, data.gps.longitude]);
        
        // Update gauges
        document.querySelector('.altitude').textContent = 
            data.gps.altitude_relative.toFixed(1) + ' m';
        
        document.querySelector('.battery').textContent = 
            data.battery.remaining_percent + ' %';
        
        // Update waypoint marker
        showCurrentWaypoint(data.seq);
    });

// Repeat every 100ms
setInterval(updateTelemetry, 100);
```

---

## Mission Planner + Custom Dashboard Sync

### Option 1: Mission Planner for control, Dashboard for monitoring

```
┌──────────────┐
│  Drone       │
└──────┬───────┘
       │
       ▼
    MAVProxy
    ↙      ↘
   MP      Bridge
(control) (telemetry)
    ↓        ↓
  User   Dashboard
  (web)
```

- Mission Planner: Upload waypoints, control drone
- Dashboard: Monitor in real-time from any device
- Telemetry: Logged to MQTT for analysis

### Option 2: Programmatic Waypoint Upload

Modify `mavlink_bridge.py` to support programmatic waypoint management:

```python
class WAypointManager:
    """Upload waypoints via MAVLink without Mission Planner GUI"""
    
    async def upload_mission(self, waypoints: List[Dict]):
        """
        waypoints = [
            {'lat': -35.363, 'lon': 149.165, 'alt': 50},
            {'lat': -35.364, 'lon': 149.166, 'alt': 50},
            {'lat': -35.365, 'lon': 149.165, 'alt': 50},
        ]
        """
        # Send SET_MISSION_COUNT message
        # For each waypoint, send MISSION_ITEM message
        # Drone acknowledges with MISSION_ACK
        pass
```

This lets you create missions programmatically from web dashboard!

---

## Troubleshooting

### Waypoints won't upload
- ❌ Mission Planner not connected
  - Solution: Check "CONNECT" button is green
  
- ❌ Drone not armed
  - Solution: Arm drone first (Ctrl+A in MP)
  
- ❌ Message: "Bad command"
  - Solution: Set correct **Cmd** type in mission

### Waypoints uploaded but drone doesn't execute
- ❌ Flight mode not set to AUTO
  - Solution: Change to AUTO mode first
  
- ❌ Mission item limit reached
  - Solution: Reduce number of waypoints (max ~255)

### Telemetry not syncing with waypoints
- ❌ Bridge receiving old data
  - Solution: Check `--master` and `--out` ports in MAVProxy
  
- ❌ MQTT not connected
  - Solution: Check broker credentials in `.env`

---

## Example: Create Mission from Dashboard

Here's sample code to create/upload missions from web dashboard:

```html
<!-- Dashboard HTML -->
<button onclick="createMission()">Create Test Mission</button>
<button onclick="uploadMission()">Upload to Drone</button>

<script>
async function createMission() {
    const mission = [
        {lat: -35.363, lon: 149.165, alt: 0, type: 'TAKEOFF'},
        {lat: -35.364, lon: 149.166, alt: 50, type: 'WAYPOINT'},
        {lat: -35.365, lon: 149.165, alt: 50, type: 'WAYPOINT'},
        {lat: -35.363, lon: 149.165, alt: 0, type: 'LAND'},
    ];
    
    // Send to server which forwards to Mission Planner
    const response = await fetch('/api/mission/upload', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({waypoints: mission})
    });
    
    alert('Mission uploaded!');
}
</script>
```

To implement this, add to `mavlink_bridge.py`:

```python
from aiohttp import web

class MissionAPI:
    async def upload_mission(self, request):
        data = await request.json()
        waypoints = data.get('waypoints', [])
        
        # Send each waypoint to Pixhawk
        for idx, wp in enumerate(waypoints):
            msg = self.mavlink.mission_item_int(
                target_system=1,
                target_component=1,
                seq=idx,
                frame=3,  # FRAME_GLOBAL_RELATIVE_ALT
                command=16,  # MAV_CMD_NAV_WAYPOINT
                current=0,
                autocontinue=1,
                param1=0, param2=0, param3=0, param4=0,
                x=int(wp['lat'] * 1e7),
                y=int(wp['lon'] * 1e7),
                z=wp['alt']
            )
            await self.send_message(msg)
        
        return web.json_response({'status': 'ok'})
```

---

## Key Takeaway

✨ **MAVProxy acts as the hub:**
- Mission Planner connects for interactive control
- Bridge connects for programmatic access
- Dashboard connects for visualization
- All synchronized through single Pixhawk connection

This is more robust and efficient than multiple apps connecting directly! 🚀
