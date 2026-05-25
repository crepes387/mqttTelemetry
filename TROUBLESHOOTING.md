# 🔍 TROUBLESHOOTING & DIAGNOSTIC GUIDE

---

## Issue 1: "mavproxy.py: command not found" or "ModuleNotFoundError"

### Symptoms
```
❌ 'mavproxy.py' is not recognized
❌ ModuleNotFoundError: No module named 'pymavlink'
```

### Root Cause
- MAVProxy not installed
- Python not in PATH
- Wrong Python environment

### Solution

**Step 1: Verify Python**
```bash
python --version
# Output should be Python 3.8+
```

**Step 2: Install MAVProxy**
```bash
pip install MAVProxy pymavlink
# Or specific version
pip install MAVProxy==1.8.60 pymavlink==2.4.40
```

**Step 3: Verify Installation**
```bash
mavproxy.py --version
python -c "from pymavlink.dialects.v10 import ardupilotmega; print('✅ OK')"
```

**Step 4: If Still Not Working**
```bash
# Check if pip is using correct Python
where pip
which pip

# Try direct path
python -m pip install MAVProxy
```

---

## Issue 2: "Port already in use" (14550, 14540, etc.)

### Symptoms
```
❌ OSError: [Errno 48] Address already in use
❌ Address already in use: 0.0.0.0:14550
```

### Root Cause
- Another process using port
- Previous process not fully closed
- UAV software running

### Solution

**Windows (PowerShell):**
```powershell
# Find process using port 14550
netstat -ano | findstr :14550
# Output: TCP  0.0.0.0:14550  0.0.0.0:0  LISTENING  12345

# Kill process by PID
taskkill /PID 12345 /F

# Or kill all Python processes (careful!)
taskkill /F /IM python.exe
```

**Linux/Mac:**
```bash
# Find process
lsof -i :14550
# Output: COMMAND  PID  USER   FD  TYPE DEVICE SIZE/OFF NODE NAME

# Kill process
kill -9 PID

# Or using fuser
fuser -k 14550/tcp
```

**Alternative: Use Different Port**
```bash
# MAVProxy
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14560 \
    --out=udpserver:0.0.0.0:14561

# Bridge (edit environment)
export MAVLINK_LISTEN_PORT=14561
python mavlink_bridge.py

# Mission Planner: Connect to 127.0.0.1:14560
```

---

## Issue 3: "Connection refused" - MAVProxy not responding

### Symptoms
```
❌ telnet: Unable to connect to remote host: Connection refused
❌ Error: Cannot connect to 127.0.0.1:14550
```

### Root Cause
- MAVProxy not running
- Wrong IP or port
- Firewall blocking

### Solution

**Step 1: Check MAVProxy Running**
```powershell
# Windows
netstat -ano | findstr :14540
# Should show LISTENING

# Linux
netstat -an | grep 14540
```

**Step 2: Check Process**
```powershell
# Windows
Get-Process | findstr python

# Linux
ps aux | grep mavproxy
```

**Step 3: Test Connection**
```bash
# Test if port 14550 is open
telnet 127.0.0.1 14550

# If connected, you'll see blank screen
# Press Ctrl+] then type "quit"

# Or use nc/ncat
nc -zv 127.0.0.1 14550
```

**Step 4: Check Firewall**
```powershell
# Windows - Check if blocked
netsh advfirewall show allprofiles

# Ubuntu - Check UFW
sudo ufw status
sudo ufw allow 14550
```

---

## Issue 4: "Bridge not receiving MAVLink packets"

### Symptoms
```
❌ No GPS data
❌ No battery data
❌ Bridge not showing: "📍 GPS: ..."
```

### Root Cause
- Pixhawk not connected to MAVProxy
- MAVProxy UDP output misconfigured
- Bridge listening on wrong port

### Solution

**Step 1: Verify MAVProxy Output**
```bash
# Start MAVProxy with verbose output
mavproxy.py --master=udpin://0.0.0.0:14540 \
    --out=127.0.0.1:14550 \
    --out=udpserver:0.0.0.0:14551 \
    -v
```

**Step 2: Check Pixhawk Connection to MAVProxy**
```bash
# MAVProxy console should show:
#   "Loaded module mavsys"
#   "Ready to fly"
#   "Heartbeat from..." (indicates connected)

# If not showing, Pixhawk not connected
# Check: USB driver, COM port, baud rate
```

**Step 3: Verify Bridge Listening**
```powershell
# Check if bridge port is listening
netstat -ano | findstr :14551

# Should show LISTENING on UDP
```

**Step 4: Sniff UDP Packets**
```bash
# Install Wireshark if not have
# Or use tcpdump

# Linux
tcpdump -i lo -n 'udp port 14551'

# Windows - need Wireshark or npcap
```

**Step 5: Bridge Diagnostic**
```bash
# Run bridge with verbose output
cd publisher
python mavlink_bridge.py

# Should show within 5 seconds:
# ✅ Listening on UDP port 14551
# 📍 GPS: ...
# 🔋 Battery: ...

# If not, MAVProxy not sending to 14551
```

---

## Issue 5: "MQTT connection failed"

### Symptoms
```
❌ Failed to connect to MQTT broker
❌ Authentication failed
❌ Certificate error (SSL: CERTIFICATE_VERIFY_FAILED)
```

### Root Cause
- Wrong broker address/port
- Invalid credentials
- Missing TLS certificate
- Network unreachable

### Solution

**Step 1: Verify Broker Credentials**
```bash
# Check MQTT_BROKER environment variable
echo $MQTT_BROKER
echo $MQTT_USERNAME
echo $MQTT_PASSWORD
echo $MQTT_PORT

# Example: EMQX
# MQTT_BROKER: ef6ff411.ala.asia-southeast1.emqxsl.com
# MQTT_PORT: 8883 (TLS) or 1883 (non-TLS)
# MQTT_USERNAME: user1
# MQTT_PASSWORD: public1
```

**Step 2: Test MQTT Connection Directly**
```bash
# Install mosquitto-clients
pip install paho-mqtt

# Python test
python -c "
import paho.mqtt.client as mqtt
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect('your-broker.com', 8883)
print('✅ Connected!')
"

# Or use mosquitto tools
mosquitto_pub -h ef6ff411.ala.asia-southeast1.emqxsl.com \
    -u user1 \
    -P public1 \
    -p 8883 \
    -t test \
    -m "hello"
```

**Step 3: Download Certificate**
```bash
# If TLS error, download certificate
# For EMQX
curl -o emqxsl-ca.crt https://assets.emqx.com/api/emqxsl-ca.crt

# Place in both folders
cp emqxsl-ca.crt publisher/
cp emqxsl-ca.crt gcs/
```

**Step 4: Test with Non-TLS**
```bash
# Set MQTT_PORT to 1883 (non-TLS)
# Temporarily disable TLS for testing

export MQTT_PORT=1883
python mavlink_bridge.py
```

**Step 5: Check Network**
```bash
# Ping broker
ping ef6ff411.ala.asia-southeast1.emqxsl.com

# Check DNS
nslookup ef6ff411.ala.asia-southeast1.emqxsl.com

# Check firewall
# Broker port might be blocked
```

---

## Issue 6: "Mission Planner won't connect"

### Symptoms
```
❌ "Connect" button does nothing
❌ "Failed to connect to telemetry"
❌ Mission Planner shows "Waiting for heartbeat"
```

### Root Cause
- TCP port 14550 not listening
- Bridge or MAVProxy crashed
- Firewall blocking
- Mission Planner connecting to wrong IP/port

### Solution

**Step 1: Verify Port Listening**
```powershell
# Check if 14550 is listening
netstat -ano | findstr :14550

# Should show something like:
# TCP  127.0.0.1:14550  0.0.0.0:0  LISTENING  4567
```

**Step 2: Test Connection Manually**
```bash
# Try telnet
telnet 127.0.0.1 14550

# If connected (blank screen), good
# If "Connection refused", port not listening

# Ctrl+] to quit telnet
```

**Step 3: Check MAVProxy Output**
```bash
# Mission Planner connects to MAVProxy output
# Make sure MAVProxy has:
# --out=127.0.0.1:14550

# NOT:
# --out=0.0.0.0:14550  (this is wrong for local)
```

**Step 4: Verify Mission Planner Settings**
```
1. Click dropdown → Select TCP
2. Host: 127.0.0.1
3. Port: 14550
4. Baud: (N/A for TCP, ignored)
5. Click CONNECT

Wait 5-10 seconds, should connect
```

**Step 5: Check Firewall**
```powershell
# Windows - Allow Python through firewall
netsh advfirewall firewall add rule name="Python MAVProxy" `
    dir=in action=allow program="C:\path\to\python.exe" enable=yes

# Or disable temporarily for testing
netsh advfirewall set allprofiles state off
```

**Step 6: Mission Planner Logs**
```
# Windows
C:\Users\<user>\AppData\Local\Temp\MAVProxy.log

# Check for connection errors
```

---

## Issue 7: "Dashboard not updating" (http://localhost:8000)

### Symptoms
```
❌ Dashboard page blank
❌ No telemetry data displayed
❌ Browser console shows errors
```

### Root Cause
- Web server not running
- MQTT not publishing
- Browser can't connect

### Solution

**Step 1: Start Web Server**
```bash
cd dashboard
python -m http.server 8000

# Should show:
# Serving HTTP on 0.0.0.0 port 8000
```

**Step 2: Access Dashboard**
```
http://localhost:8000
# Or
http://127.0.0.1:8000
```

**Step 3: Check Browser Console**
```
F12 → Console tab

Look for errors like:
❌ Failed to connect to ws://broker:8883
❌ Cannot read property 'x' of undefined
```

**Step 4: Verify MQTT Publish**
```bash
# Check if bridge is publishing to MQTT
# Look for lines like:
# 🚀 Published seq 42 (245 bytes)

# If not publishing, bridge not receiving MAVLink
```

**Step 5: Dashboard Connectivity**
```
# Dashboard connects via MQTT (WebSocket)
# Broker must support WebSocket on port 8883 or 8884

# Some brokers don't support WebSocket
# Use different broker or MQTT bridge
```

---

## Diagnostic Commands - Quick Checklist

```bash
# 1. Check Python version
python --version

# 2. Check MAVProxy installed
mavproxy.py --version

# 3. Check ports listening
netstat -ano | findstr :14540  # Pixhawk input
netstat -ano | findstr :14550  # Mission Planner output
netstat -ano | findstr :14551  # Bridge input
netstat -ano | findstr :8883   # MQTT

# 4. Check process running
tasklist | findstr python

# 5. Test port connection
telnet 127.0.0.1 14550
telnet 127.0.0.1 14551

# 6. Check MQTT broker
mosquitto_pub -h broker.com -u user1 -P pass1 -p 8883 -t test -m hi

# 7. Check environment variables
echo %MQTT_BROKER%
echo %MQTT_PORT%
echo %MQTT_USERNAME%

# 8. Check file exists
dir d:\AgumAgum\coding\mqttTelemetry\publisher\
dir d:\AgumAgum\coding\mqttTelemetry\gcs\

# 9. Check Python imports
python -c "import paho.mqtt.client; print('✅ MQTT OK')"
python -c "from pymavlink.dialects.v10 import ardupilotmega; print('✅ MAVLink OK')"

# 10. Test MQTT via Python
python -c "
import paho.mqtt.client as mqtt
c = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
c.connect('your-broker.com', 8883)
print('✅ MQTT Connected')
"
```

---

## Emergency Restart

If everything is broken, complete restart:

```bash
# 1. Kill all Python processes
taskkill /F /IM python.exe

# 2. Wait 2 seconds
timeout /t 2

# 3. Kill MAVProxy specifically
taskkill /F /IM mavproxy.py

# 4. Clear ports (Windows)
netsh int ipv4 set dynamicport tcp start=49152 num=16384
netsh int ipv4 set dynamicport udp start=49152 num=16384

# 5. Check no process on ports
netstat -ano | findstr :14540
netstat -ano | findstr :14550
netstat -ano | findstr :14551

# 6. Start fresh
cd d:\AgumAgum\coding\mqttTelemetry
mavproxy.py --master=udpin://0.0.0.0:14540 --out=127.0.0.1:14550 --out=udpserver:0.0.0.0:14551
```

---

## Getting Help

If still stuck:

1. **Check terminal logs** - they contain the actual error
2. **Read error messages carefully** - they usually tell you exactly what's wrong
3. **Verify each component separately**:
   - Is MAVProxy running? (`mavproxy.py --version`)
   - Can Bridge connect to MAVProxy? (run and check logs)
   - Can Bridge connect to MQTT? (check logs)
   - Can Mission Planner connect to port? (`telnet 127.0.0.1 14550`)
4. **Test MQTT independently** - use `mosquitto_pub` and `mosquitto_sub`
5. **Test Mission Planner** - try connecting to simulator first
6. **Check firewall** - disable temporarily for testing
7. **Try simpler setup first** - start with local, not network
8. **Check file permissions** - can Python read/write required files?

---

## Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: pymavlink` | Not installed | `pip install pymavlink` |
| `Address already in use` | Port taken | Kill process or use different port |
| `Connection refused` | Service not running | Start MAVProxy/Bridge |
| `Authentication failed` | Wrong MQTT password | Check credentials |
| `CERTIFICATE_VERIFY_FAILED` | Missing cert | Download `emqxsl-ca.crt` |
| `No module named 'paho'` | MQTT not installed | `pip install paho-mqtt` |
| `Timeout` | Service not responding | Check service is running |
| `Cannot find host` | Wrong IP/hostname | Verify IP and hostname |
| `Permission denied` | Firewall/security | Allow in firewall |
| `Broken pipe` | Connection lost | Check network, restart |

