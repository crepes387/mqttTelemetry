import socket
import time

def test_udp_port(port=14551):
    """Test apakah UDP port 14551 bisa menerima data"""
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind(("0.0.0.0", port))
        sock.settimeout(2)
        
        print(f"✅ UDP port {port} terbuka dan siap listen")
        print(f"⏱️ Waiting for data for 5 seconds...")
        
        received = False
        start_time = time.time()
        
        while time.time() - start_time < 5:
            try:
                data, addr = sock.recvfrom(1024)
                print(f"✅ DATA RECEIVED: {len(data)} bytes from {addr}")
                print(f"   First 50 bytes: {data[:50]}")
                received = True
                break
            except socket.timeout:
                continue
        
        if not received:
            print(f"❌ NO DATA RECEIVED after 5 seconds!")
            print(f"   This means MAVProxy is NOT sending to port {port}")
            print(f"   Check your MAVProxy --out parameter")
        
    except OSError as e:
        print(f"❌ Cannot bind to port {port}: {e}")
        print(f"   This usually means port is already in use")
    finally:
        sock.close()

if __name__ == "__main__":
    print("🧪 UDP Port 14551 Diagnostic Test")
    print("=" * 60)
    test_udp_port(14551)
