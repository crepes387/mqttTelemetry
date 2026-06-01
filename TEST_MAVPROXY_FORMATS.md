# 🧪 TEST BERBAGAI FORMAT MAVPROXY OUTPUT

Jika `--out=udpout:0.0.0.0:14551` tidak bekerja, coba format lain:

## Format 1: UDP Output dengan IP Address (PALING MUNGKIN BEKERJA)
```bash
python mavproxy.py --master COM12 --baudrate 57600 ^
    --out=tcpin:0.0.0.0:14550 ^
    --out=127.0.0.1:14551
```

## Format 2: UDP dengan prefix `udp:`
```bash
python mavproxy.py --master COM12 --baudrate 57600 ^
    --out=tcpin:0.0.0.0:14550 ^
    --out=udp:127.0.0.1:14551
```

## Format 3: UDP dengan prefix `udpout:` dan IP
```bash
python mavproxy.py --master COM12 --baudrate 57600 ^
    --out=tcpin:0.0.0.0:14550 ^
    --out=udpout:127.0.0.1:14551
```

## Format 4: UDP dengan prefix `udpout:` dan 0.0.0.0
```bash
python mavproxy.py --master COM12 --baudrate 57600 ^
    --out=tcpin:0.0.0.0:14550 ^
    --out=udpout:0.0.0.0:14551
```

---

## 🎯 REKOMENDASI

Coba **Format 1** terlebih dahulu (paling umum):
```bash
python mavproxy.py --master COM12 --baudrate 57600 --out=tcpin:0.0.0.0:14550 --out=127.0.0.1:14551
```

Jika tidak bekerja, coba Format 2-4 secara berurutan.
