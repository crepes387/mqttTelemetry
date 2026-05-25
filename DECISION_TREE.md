# 🎯 SETUP DECISION TREE

Use this guide to quickly determine which setup is right for you.

---

## STEP 1: Do you have a Pixhawk/drone?

```
┌─────────────────────────────────────────────────┐
│  Do you have actual Pixhawk hardware?           │
├─────────────────────────────────────────────────┤
│                                                 │
│  YES ──────────────────→ Go to STEP 2          │
│                                                 │
│  NO ──────────────────→ Use SITL Simulator    │
│      (for testing)      → Go to STEP 2          │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## STEP 2: How many computers?

```
                         ┌─────────────────┐
                         │ How many PCs?   │
                         └────────┬────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
            ONE (1)          TWO (2)          THREE+ (3)
                 │                │                │
                 ▼                ▼                ▼
            ┌─────────┐     ┌──────────┐     ┌─────────┐
            │SCENARIO │     │SCENARIO │     │SCENARIO │
            │    A    │     │    B    │     │    C    │
            │ LOCAL   │     │ NETWORK │     │ CLOUD   │
            └─────────┘     └──────────┘     └─────────┘
```

---

## SCENARIO A: LOCAL (1 Computer)

```
┌──────────────────────────────────────────────────────┐
│ SCENARIO A: LOCAL SETUP (Single PC)                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Setup: Everything on ONE computer                   │
│                                                      │
│ ┌─────────────┐                                     │
│ │   Pixhawk/  │                                     │
│ │   SITL      │                                     │
│ └──────┬──────┘                                     │
│        │ (USB/Simulator)                            │
│        ▼                                             │
│ ┌──────────────────────────────────────────┐       │
│ │ Terminal 1: MAVProxy (HUB)               │       │
│ │ Terminal 2: MAVLink Bridge               │       │
│ │ Terminal 3: Mission Planner              │       │
│ │ Terminal 4: Dashboard (Optional)        │       │
│ └──────────────────────────────────────────┘       │
│                                                      │
│ WHEN TO USE:                                        │
│ ✅ Testing the system locally                      │
│ ✅ Learning how it works                           │
│ ✅ Developing/debugging                            │
│ ✅ Single operator with one computer               │
│                                                      │
│ TIME TO SETUP: ~15 minutes                         │
│ DIFFICULTY: Easy ⭐                                 │
│                                                      │
│ 📚 GUIDE: FIRST_TIME_SETUP.md (or)                 │
│           COMPLETE_SETUP_GUIDE.md → SCENARIO 1     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## SCENARIO B: NETWORK (2 Computers)

```
┌──────────────────────────────────────────────────────┐
│ SCENARIO B: NETWORK SETUP (2 PCs)                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Setup: Pixhawk site + Remote GCS                    │
│                                                      │
│ COMPUTER A (Drone Site)                            │
│ ┌──────────────────────────────────────────┐       │
│ │ Terminal 1: MAVProxy                     │       │
│ │ Terminal 2: MAVLink Bridge               │       │
│ │ (via MQTT Broker)                        │       │
│ └──────────────────────────────────────────┘       │
│              ↓ MQTT                                 │
│        [MQTT Broker] ← NETWORK                     │
│              ↑                                      │
│ COMPUTER B (Remote GCS)                            │
│ ┌──────────────────────────────────────────┐       │
│ │ Terminal 1: GCS Converter                │       │
│ │ Terminal 2: Mission Planner              │       │
│ └──────────────────────────────────────────┘       │
│                                                      │
│ WHEN TO USE:                                        │
│ ✅ Field operations (drone site)                   │
│ ✅ Remote monitoring (office/home)                 │
│ ✅ Multiple operators                              │
│ ✅ Persistent data logging                         │
│                                                      │
│ REQUIREMENTS:                                       │
│ - Both PCs on same network OR accessible network   │
│ - MQTT broker (can be local or cloud)             │
│ - Firewall rules allowing MQTT port (8883)        │
│                                                      │
│ TIME TO SETUP: ~20 minutes                         │
│ DIFFICULTY: Medium ⭐⭐                             │
│                                                      │
│ 📚 GUIDE: COMPLETE_SETUP_GUIDE.md                  │
│           → SCENARIO 2: NETWORK LOKAL              │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## SCENARIO C: CLOUD (Distributed)

```
┌──────────────────────────────────────────────────────┐
│ SCENARIO C: CLOUD SETUP (Distributed)               │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Setup: Drone (anywhere) + GCS (anywhere) via Cloud │
│                                                      │
│ COMPUTER A (Remote Drone Site)                     │
│ ┌──────────────────────────────────────────┐       │
│ │ Terminal 1: MAVProxy                     │       │
│ │ Terminal 2: MAVLink Bridge               │       │
│ └──────────────────────────────────────────┘       │
│              ↓ MQTT (Internet)                     │
│      [CLOUD MQTT BROKER]                          │
│      (EMQX, HiveMQ, Mosquitto)                    │
│              ↑                                      │
│ COMPUTER B (Remote GCS - Any Location)            │
│ ┌──────────────────────────────────────────┐       │
│ │ Terminal 1: GCS Converter                │       │
│ │ Terminal 2: Mission Planner              │       │
│ └──────────────────────────────────────────┘       │
│                                                      │
│ MULTIPLE OBSERVERS POSSIBLE:                        │
│ └─ Smartphone, Tablet, Another PC...              │
│                                                      │
│ WHEN TO USE:                                        │
│ ✅ Multiple locations geographically distributed  │
│ ✅ Need remote monitoring over internet            │
│ ✅ Multiple operators watching same drone         │
│ ✅ Long-range operations                           │
│ ✅ Backup monitoring system                        │
│                                                      │
│ REQUIREMENTS:                                       │
│ - Internet connection (both sides)                 │
│ - Cloud MQTT broker account                        │
│ - Broker credentials (username/password)           │
│ - Firewall/port forwarding if needed              │
│                                                      │
│ POPULAR BROKERS:                                    │
│ - EMQX (emqx.com) - Free tier available          │
│ - HiveMQ (hivemq.com) - Cloud service             │
│ - Self-hosted Mosquitto - Maximum control         │
│                                                      │
│ TIME TO SETUP: ~25 minutes                         │
│ DIFFICULTY: Medium-Hard ⭐⭐⭐                      │
│                                                      │
│ 📚 GUIDE: COMPLETE_SETUP_GUIDE.md                  │
│           → SCENARIO 3: DISTRIBUTED GCS           │
│           → ☁️ SKENARIO 3: SETUP BROKER MQTT      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## WHICH GUIDE TO READ?

```
┌─────────────────────────────────────────────┐
│ SCENARIO A: LOCAL                           │
├─────────────────────────────────────────────┤
│ 📚 Read: FIRST_TIME_SETUP.md (15 min)      │
│          Then: QUICK_REFERENCE.md           │
│          Later: ARCHITECTURE.md             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ SCENARIO B: NETWORK                         │
├─────────────────────────────────────────────┤
│ 📚 Read: COMPLETE_SETUP_GUIDE.md            │
│          → SCENARIO 2: NETWORK LOKAL        │
│          Then: QUICK_REFERENCE.md           │
│          Then: TROUBLESHOOTING.md (if need) │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ SCENARIO C: CLOUD                           │
├─────────────────────────────────────────────┤
│ 📚 Read: COMPLETE_SETUP_GUIDE.md            │
│          → SCENARIO 3: DISTRIBUTED GCS      │
│          Then: QUICK_REFERENCE.md           │
│          Then: TROUBLESHOOTING.md (if need) │
└─────────────────────────────────────────────┘
```

---

## QUICK COMPARISON TABLE

```
╔═════════════╦═════════════╦═════════════╦═════════════╗
║  Feature    ║ SCENARIO A  ║ SCENARIO B  ║ SCENARIO C  ║
║             ║   LOCAL     ║  NETWORK    ║   CLOUD     ║
╠═════════════╬═════════════╬═════════════╬═════════════╣
║ Computers   ║     1       ║      2      ║   Many      ║
║ Setup Time  ║   15 min    ║   20 min    ║   25 min    ║
║ Difficulty  ║    Easy     ║   Medium    ║  Medium-Hd  ║
║ Cost        ║    Free     ║    Free     ║    Free+    ║
║ Range       ║   Local     ║   Network   ║   Global    ║
║ Latency     ║   <50ms     ║   50-200ms  ║  200-500ms  ║
║ Reliability ║   Very High ║    High     ║   Medium    ║
║ Best For    ║  Testing    ║  Ops Teams  ║ Monitoring  ║
╚═════════════╩═════════════╩═════════════╩═════════════╝
```

---

## DECISION FLOWCHART (VISUAL)

```
                            START HERE
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Do you have a PC     │
                    │  with Python?         │
                    └───┬───────────────┬───┘
                        │ NO            │ YES
                        ▼               ▼
                    ┌────────┐      ┌──────────┐
                    │Install │      │Continue  │
                    │Python  │      └────┬─────┘
                    └────┬───┘           │
                         │              ▼
                         └─────→ ┌──────────────────┐
                                │ Do you have a    │
                                │ Pixhawk/drone?   │
                                └───┬────────┬──────┘
                                    │ NO     │ YES
                                    ▼        ▼
                                 ┌───┐   ┌───┐
                                 │USE│   │USE│
                                 │SITL   │HW │
                                 │ SIM   └─┬─┘
                                 └───┬───┘ │
                                     └─┬───┘
                                       ▼
                          ┌──────────────────────┐
                          │ How many computers   │
                          │ will you use?        │
                          └──┬─────────┬────┬────┘
                             │         │    │
                          ONE│       TWO   3+
                             ▼         │    │
                          ┌────┐      │    ▼
                          │SCEN│      │  ┌────┐
                          │A:  │      │  │SCEN│
                          │LOCAL     │  │C:  │
                          │15 min    │  │CLOUD
                          │Easy      │  │25 min
                          └──┬─┘      │  │Hard
                             │        ▼  └────┘
                             │     ┌────┐
                             │     │SCEN│
                             │     │B:  │
                             │     │NET │
                             │     │20 min
                             │     │Med │
                             │     └────┘
                             │      │
                    FIRST_TIME│      │
                    _SETUP.md │      │
                             ▼      ▼
                          COMPLETE_SETUP_GUIDE.md
```

---

## READY? LET'S GO!

### If Scenario A (LOCAL):
```bash
👉 Open: FIRST_TIME_SETUP.md
   Follow step by step (15 minutes)
```

### If Scenario B (NETWORK):
```bash
👉 Open: COMPLETE_SETUP_GUIDE.md
   Jump to: SKENARIO 2: NETWORK LOKAL
   Follow instructions for both computers
```

### If Scenario C (CLOUD):
```bash
👉 Open: COMPLETE_SETUP_GUIDE.md
   Jump to: SKENARIO 3: DISTRIBUTED GCS
   Follow instructions for all components
```

### If Something Goes Wrong:
```bash
👉 Open: TROUBLESHOOTING.md
   Find your issue number
   Follow solution steps
```

### If You Need Quick Commands:
```bash
👉 Open: QUICK_REFERENCE.md
   Copy-paste commands
   Expected outputs shown
```

### If You Want to Understand the System:
```bash
👉 Open: ARCHITECTURE.md
   Study the diagrams
   Understand data flow
```

---

## BONUS: RECOMMENDED PROGRESSION

**Week 1:** Get comfortable with Scenario A
- Install dependencies
- Run all 3 terminals locally
- Connect Mission Planner
- View telemetry data
- Play with dashboard

**Week 2:** Try Scenario B
- Set up 2 computers
- Test network connectivity
- Run bridge on one PC
- Run GCS converter on other PC
- Confirm remote connection works

**Week 3:** Deploy to Real Hardware
- Replace simulator with real Pixhawk
- Verify all data streams
- Test failure recovery
- Document your setup

**Week 4+:** Explore Advanced Features
- Custom MQTT topics
- Data logging
- Multiple GCS connections
- Integration with other systems

---

## 🎯 FINAL CHECKLIST

Before you start, make sure you have:

- [ ] **Computer(s)** with Windows/Linux/Mac
- [ ] **Python 3.8+** installed
- [ ] **Internet connection** (for pip install)
- [ ] **Pixhawk or SITL simulator** (if testing real hardware)
- [ ] **Mission Planner** downloaded (if using MP)
- [ ] **~15-25 minutes** of free time
- [ ] **Patience** to read the documentation
- [ ] **Terminal/command-line** familiarity

---

## ✨ YOU'RE READY!

Choose your scenario and start reading the appropriate guide.

**Most people start with:** [FIRST_TIME_SETUP.md](FIRST_TIME_SETUP.md)

**Good luck! 🚀**

---

*Version: 1.0 | Last Updated: May 25, 2026*
