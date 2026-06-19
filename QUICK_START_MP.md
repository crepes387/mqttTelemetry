# 🚀 Quick Start: Mission Planner Connection

## ✅ Sistem Status Saat Ini

**Terminal 1 - MAVLink Bridge (Aircraft Side):**
```
cd publisher
python mavlink_bridge.py
```
✅ Running - Publishing seq 10, 11, 12... to MQTT

**Terminal 2 - GCS MQTT↔MAVLink Converter (GCS Side):**
```
cd gcs
python mqtt_to_mavlink_gcs.py
```
✅ Running - Listening on 0.0.0.0:14550

---

## 🎯 Step 1: Buka Mission Planner

Jika belum installed, download dari: https://ardupilot.org/planner/

---

## 🔗 Step 2: Connect ke GCS

**Klik dropdown di pojok kanan atas:**

![Connection Dropdown]

Pilih: **UDP** atau **TCP**

### Option A: TCP (Recommended)
- **Connection Type:** TCP
- **IP Address:** `127.0.0.1`
- **Port:** `14550`
- **Baud Rate:** Tidak digunakan untuk TCP

### Option B: UDP (Alternative)
- **Connection Type:** UDP
- **IP Address:** `127.0.0.1`
- **Port:** `14551`

---

## ✨ Step 3: Klik CONNECT

Setelah klik "CONNECT", seharusnya:

1. ✅ Connection status berubah dari `DISCONNECTED` menjadi `CONNECTED`
2. ✅ Map tab menampilkan drone icon
3. ✅ Telemetry data terlihat:
   - Altitude
   - Speed
   - Heading
   - Battery status
   - GPS coordinates

**Terminal GCS harus menampilkan:**
```
📱 Client connected: ('127.0.0.1', 58950) (Total: 1)
📡 Broadcasting seq 285 to 1 client(s)
📡 Broadcasting seq 286 to 1 client(s)
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection Refused" | GCS server tidak running - jalankan `python mqtt_to_mavlink_gcs.py` |
| "Connection Timeout" | Port 14550 blocked - cek firewall |
| Connected tapi no data | Cek apakah mavlink_bridge.py running di terminal 1 |
| GCS terminal showing "0 client(s)" | Mission Planner belum connect atau connection dropped |

---

## 📊 Data Flow

```
Pixhawk COM12 (Real Hardware atau SITL)
    ↓
MAVProxy (Port 14550/14551)
    ↓
mavlink_bridge.py (UDP listener, MQTT publisher)
    ↓
MQTT Broker Cloud ☁️
    ↓
mqtt_to_mavlink_gcs.py (MQTT subscriber, TCP server)
    ↓
Mission Planner GUI (TCP client)
```

---

## 💡 Pro Tips

1. **Single PC Setup:** Gunakan `127.0.0.1` (localhost)
2. **Two PC Setup:** Ganti `127.0.0.1` dengan IP address GCS PC (contoh: `192.168.1.100`)
3. **Test Connection:** Di terminal, cek port listening:
   ```bash
   netstat -ano | findstr :14550
   # Harus ada: TCP 0.0.0.0:14550 LISTENING
   ```

---

## ✅ Success Indicators

- Map menampilkan drone di koordinat (meskipun 0,0 normal untuk simulator)
- Altitude gauge menunjilkan nilai  
- Battery indicator berwarna hijau (>50%)
- Speed indicator menunjuk non-zero jika drone bergerak
- Heading/compass menunjuk arah

---

**Jika ada masalah, check TROUBLESHOOTING_MP_CONNECTION.md!** 🚀
