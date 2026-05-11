# 📦 Requirements Structure

This project uses multiple `requirements.txt` files organized by component.

## File Organization

```
mqttTelemetry/
├── requirements_mavproxy.txt     ← Root: MAVProxy stack only
├── publisher/
│   ├── requirements.txt          ← Publisher: Full deps (MAVSDK + MQTT)
│   └── publishenv/               ← Virtual environment (gitignored)
├── gcs/
│   ├── requirements.txt          ← GCS: MQTT subscriber only
│   └── gcsenv/                   ← Virtual environment (gitignored)
└── dashboard/
    └── (no Python deps needed)
```

---

## Installation Guide

### Option 1: MAVProxy Stack (Minimal - Recommended)

**For both Pixhawk & GCS computers:**

```bash
pip install -r requirements_mavproxy.txt
```

**Includes:**
- `MAVProxy>=1.8.60` - Central hub for MAVLink routing
- `pymavlink>=2.4.40` - Parse MAVLink messages
- `paho-mqtt>=1.7.1` - MQTT publish/subscribe

---

### Option 2: Full Publisher (Original publisher.py)

**Only on Pixhawk computer if using original publisher.py:**

```bash
cd publisher
pip install -r requirements.txt
```

**Includes:**
- All of `requirements_mavproxy.txt` PLUS:
- `dronekit>=2.9.2` - MAVSDK alternative
- `dronekit-sitl>=3.3.0` - Simulator support
- `matplotlib` - Plotting (optional)
- etc.

---

### Option 3: GCS Converter (Remote Mission Planner)

**On GCS computer only:**

```bash
cd gcs
pip install -r requirements.txt
```

**Includes:**
- `paho-mqtt>=2.1.0` - MQTT subscribe
- `pymavlink>=2.4.49` - Generate MAVLink messages

---

## Use Cases

### Scenario A: Local Setup (Everything on one machine)
```bash
# Install complete stack
pip install -r requirements_mavproxy.txt
cd publisher && pip install -r requirements.txt
cd ../gcs && pip install -r requirements.txt
```

### Scenario B: Field + Remote GCS (2 machines)

**Machine A (Pixhawk in field):**
```bash
pip install -r requirements_mavproxy.txt
# Run MAVProxy + Bridge
```

**Machine B (GCS office):**
```bash
cd gcs
pip install -r requirements.txt
# Run GCS converter
```

### Scenario C: Minimal MAVProxy Setup
```bash
# Both machines
pip install -r requirements_mavproxy.txt
```

---

## Virtual Environment Setup (Optional)

### Create per-folder venvs:

**Publisher folder:**
```bash
cd publisher
python -m venv publishenv
source publishenv/bin/activate  # macOS/Linux
publishenv\Scripts\activate     # Windows

pip install -r requirements.txt
```

**GCS folder:**
```bash
cd gcs
python -m venv gcsenv
source gcsenv/bin/activate     # macOS/Linux
gcsenv\Scripts\activate        # Windows

pip install -r requirements.txt
```

---

## What's in Each File?

### `requirements_mavproxy.txt` (51 bytes, 3 packages)
Minimal, only what you need for MAVProxy stack:
- MAVProxy (the hub)
- pymavlink (MAVLink parsing)
- paho-mqtt (MQTT support)

**Best for:** Cloud deployment, container images, minimal footprint

### `publisher/requirements.txt` (1359 bytes, 45+ packages)
Everything for the publisher application:
- Full DroneKit suite
- All dependencies for SITL simulator
- Extra tools (matplotlib, etc.)

**Best for:** Development, testing, simulator

### `gcs/requirements.txt` (52 bytes, 2 packages)
Minimal for GCS conversion only:
- paho-mqtt (receive telemetry)
- pymavlink (generate MAVLink)

**Best for:** Remote GCS computers

---

## Troubleshooting

### "Module not found: pymavlink"
```bash
# Reinstall from correct requirements file
pip install -r requirements_mavproxy.txt
```

### "MAVProxy command not found"
```bash
# Check if installed in virtual environment
which mavproxy.py  # should show path

# If not, install:
pip install MAVProxy
```

### Different Python versions across machines?
```bash
# Generate requirements.txt with specific versions:
pip freeze > requirements_pinned.txt

# Use pinned version for exact reproduction:
pip install -r requirements_pinned.txt
```

---

## .gitignore Configuration

The `.gitignore` at root level ignores:
- `publishenv/` - Publisher virtual environment
- `gcsenv/` - GCS virtual environment
- `venv/`, `env/`, `.venv/` - Generic venv folders
- `__pycache__/`, `*.pyc` - Python caches
- `.DS_Store` - macOS files
- `.env` - Environment variable files

This keeps your git repo clean! ✨

---

## Updating Dependencies

When you add new packages:

```bash
# Update requirements.txt
cd publisher
pip install new-package
pip freeze | grep new-package >> requirements.txt

# Or more carefully:
pip install new-package==version
# Edit requirements.txt manually to add the line
```

---

## Docker Support (Future)

If you want to containerize:

```dockerfile
FROM python:3.9
RUN pip install -r requirements_mavproxy.txt
# Smaller image!
```

Or:

```dockerfile
FROM python:3.9
RUN pip install -r publisher/requirements.txt
# Full image
```

---

## Summary

✅ **Do:**
- Use `requirements_mavproxy.txt` for minimal deployments
- Use folder-specific `requirements.txt` for each component
- Add new dependencies to the appropriate requirements file
- Commit requirements files (not the venv folders!)

❌ **Don't:**
- Commit virtual environments (they're in .gitignore)
- Mix different requirement files without understanding
- Manually track package versions (use pip freeze)

---

All set! Your requirements structure is now organized and production-ready. 🚀
