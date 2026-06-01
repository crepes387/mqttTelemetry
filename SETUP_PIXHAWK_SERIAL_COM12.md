# 🔌 PANDUAN KONEKSI PIXHAWK via SERIAL COM12

## ✅ PERUBAHAN YANG DIPERLUKAN

Karena Anda menghubungkan Pixhawk via **kabel serial COM12**, berikut adalah perubahan yang diperlukan:

---

## 1️⃣ PERUBAHAN DI MAVPROXY (PALING PENTING!)

### ❌ SEBELUMNYA (SIMULASI/UDP):
```bash
mavproxy.py --master=udpin://0.0.0.0:14540 ^
    --out=127.0.0.1:14550 ^
    --out=udpserver:0.0.0.0:14551
```

### ✅ SESUDAHNYA (SERIAL COM12):
```bash
mavproxy.py --master=com12,57600 ^
    --out=127.0.0.1:14550 ^
    --out=udpserver:0.0.0.0:14551
```

**Penjelasan:**
- `com12` = Port serial tempat Pixhawk terhubung
- `57600` = Kecepatan baud rate (default Pixhawk)

---

## ⚙️ KECEPATAN BAUD RATE

### Default Pixhawk:
- **57600** ← Paling umum
- 115200 ← Jika setting di Mission Planner berbeda

### Cara mengecek di Mission Planner:
1. Buka **Mission Planner** (jika sudah pernah connect)
2. Pilih COM port dropdown
3. Lihat **Baud Rate** yang tertera
4. Gunakan kecepatan yang sama di MAVProxy

### Contoh dengan baud rate berbeda:
```bash
# Jika Pixhawk setting ke 115200:
mavproxy.py --master=com12,115200 ^
    --out=127.0.0.1:14550 ^
    --out=udpserver:0.0.0.0:14551
```

---

## 🔍 DIAGRAM PERUBAHAN

```
SEBELUMNYA (Simulator/UDP):
Pixhawk (SITL) → UDP:14540 → MAVProxy → 14550/14551

SESUDAHNYA (Serial COM12):
Pixhawk (Hardware) → Serial COM12 → MAVProxy → 14550/14551
```

---

## 📋 BAGIAN-BAGIAN YANG BERUBAH

### HANYA perubahan di:
1. **Terminal 1 - MAVProxy** ✅ (WAJIB UBAH)
2. Terminal 2 - Bridge ❌ (TIDAK BERUBAH)
3. Terminal 3 - Mission Planner ❌ (TIDAK BERUBAH)
4. Terminal 4 - Dashboard ❌ (TIDAK BERUBAH)

### TIDAK berubah:
- 🟢 `--out=127.0.0.1:14550` (tetap sama)
- 🟢 `--out=udpserver:0.0.0.0:14551` (tetap sama)
- 🟢 Semua port tetap sama
- 🟢 MQTT bridge script tetap sama
- 🟢 Mission Planner connection tetap sama

---

## 🚀 CARA MENJALANKAN (DENGAN COM12)

### Terminal 1: MAVProxy (dengan COM12)
```bash
cd d:\AgumAgum\coding\mqttTelemetry

mavproxy.py --master=com12,57600 ^
    --out=127.0.0.1:14550 ^
    --out=udpserver:0.0.0.0:14551 ^
    --default-modules=compass,streamrate
```

**Tunggu sampai output muncul:**
```
Loaded module compass
Loaded module streamrate
Ready to fly
```

**Jika error "Port not found":**
```powershell
# Cek port COM yang tersedia
Get-WmiObject Win32_SerialPort

# Output contoh:
# Name : COM12
# DeviceID : COM12

# Maka gunakan COM12 di MAVProxy
```

---

### Terminal 2: Bridge (sama seperti sebelumnya)
```bash
$env:MQTT_BROKER="broker.emqxsl.com"
$env:MQTT_PORT="8883"
$env:MQTT_USERNAME="user1"
$env:MQTT_PASSWORD="public1"

cd d:\AgumAgum\coding\mqttTelemetry\publisher
python mavlink_bridge.py
```

---

### Terminal 3: Mission Planner (sama seperti sebelumnya)
1. Buka **Mission Planner**
2. Dropdown → **TCP**
3. IP: `127.0.0.1`
4. Port: `14550`
5. Klik **CONNECT**

---

### Terminal 4: Dashboard (optional)
```bash
cd d:\AgumAgum\coding\mqttTelemetry\dashboard
python -m http.server 8000
```

---

## 🧪 TROUBLESHOOTING

### Error: "COM port does not exist"
```powershell
# Cek port yang tersedia
Get-WmiObject Win32_SerialPort

# Atau gunakan Device Manager:
# 1. Kanan-klik Start
# 2. Device Manager
# 3. Cari "Ports (COM & LPT)"
# 4. Lihat port Pixhawk (biasanya "USB Serial Device" atau "Silicon Labs")
```

### Error: "Port already in use"
```powershell
# Port COM tidak bisa dibuka karena dipakai aplikasi lain
# Solusi:
# 1. Tutup Mission Planner (jika already open)
# 2. Tutup aplikasi lain yang pakai serial
# 3. Restart MAVProxy

# Atau cek proses mana yang pakai COM12
wmic process get name | findstr python
```

### Error: "Read timeout" atau "Connection unstable"
- ✅ Cek kabel USB tidak longgar
- ✅ Coba ubah kecepatan baud (57600 → 115200)
- ✅ Pastikan Pixhawk powered on
- ✅ Coba port USB yang berbeda

### Error: "Ready to fly" tidak muncul
- ✅ Tunggu 5-10 detik lebih lama
- ✅ Cek Pixhawk LED status
- ✅ Cek apakah Pixhawk sudah calibrated
- ✅ Cek firmware Pixhawk

---

## 📝 RINGKASAN PERUBAHAN

| Aspek | Sebelum (UDP) | Sesudah (COM12) |
|-------|---------------|-----------------|
| MAVProxy --master | `udpin://0.0.0.0:14540` | `com12,57600` |
| Output 14550 | ✅ Sama | ✅ Sama |
| Output 14551 | ✅ Sama | ✅ Sama |
| Bridge script | ✅ Sama | ✅ Sama |
| Mission Planner | ✅ Sama | ✅ Sama |
| MQTT Flow | ✅ Sama | ✅ Sama |
| Port 14550 | ✅ Sama | ✅ Sama |
| Port 14551 | ✅ Sama | ✅ Sama |

---

## 🎯 LANGKAH CEPAT (SETUP COM12)

```powershell
# 1. Buka Terminal PowerShell

# 2. Set environment
$env:MQTT_BROKER="broker.emqxsl.com"
$env:MQTT_PORT="8883"
$env:MQTT_USERNAME="user1"
$env:MQTT_PASSWORD="public1"

# 3. Buka Terminal 1 - MAVProxy
cd d:\AgumAgum\coding\mqttTelemetry
mavproxy.py --master=com12,57600 --out=127.0.0.1:14550 --out=udpserver:0.0.0.0:14551

# 4. Buka Terminal 2 - Bridge
cd d:\AgumAgum\coding\mqttTelemetry\publisher
python mavlink_bridge.py

# 5. Buka Terminal 3 - Mission Planner
# (GUI application, buka dari Start Menu atau desktop icon)
# Connect ke 127.0.0.1:14550

# Done! 🎉
```

---

## ✨ TIPS

- ✅ Gunakan **com12,57600** untuk setting default Pixhawk
- ✅ Jika error, coba **com12,115200** (kecepatan alternatif)
- ✅ Cek COM port via `Get-WmiObject Win32_SerialPort` jika ragu
- ✅ Pastikan Pixhawk **powered on** sebelum start MAVProxy
- ✅ Tunggu "Ready to fly" muncul sebelum open Mission Planner
- ✅ Dashboard tetap bisa diakses dari `http://localhost:8000`

---

**INTINYA: HANYA UBAH `--master` di Terminal 1 MAVProxy!** ✨

Semua hal lain tetap sama. 🚀
