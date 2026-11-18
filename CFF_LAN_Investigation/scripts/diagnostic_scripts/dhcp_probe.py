import socket
import select
import time
import struct

print("=== STARTING LOW-LEVEL PACKET & PROTOCOL PROBE ON INTERFACE 21 ===", flush=True)

# 1. Listen on DHCP Server port (67)
s_dhcp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s_dhcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s_dhcp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
try:
    s_dhcp.bind(('0.0.0.0', 67))
    print("[UDP 67] Bound successfully (Listening for DHCP Discover / Requests)", flush=True)
except Exception as e:
    print(f"[UDP 67] Bind failed: {e}", flush=True)

# 2. Listen on NetBIOS / LLMNR / mDNS / SSDP
sockets = [s_dhcp]
for port in [137, 5353, 5355, 1900, 502, 8000]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('0.0.0.0', port))
        sockets.append(s)
        print(f"[UDP {port}] Bound successfully", flush=True)
    except Exception as e:
        pass

print("Monitoring for 15 seconds...", flush=True)
start_time = time.time()
pkts = 0

while time.time() - start_time < 15:
    r, _, _ = select.select(sockets, [], [], 1.0)
    for s in r:
        try:
            data, addr = s.recvfrom(4096)
            port = s.getsockname()[1]
            sender_ip, sender_port = addr
            # Ignore our own PC IP and Wi-Fi IP
            if sender_ip not in ['192.168.137.1', '10.254.254.234', '127.0.0.1']:
                print(f"[PACKET DETECTED] Port {port} from {sender_ip}:{sender_port} (Len: {len(data)})", flush=True)
                print(f"  Raw Hex: {data[:40].hex()}", flush=True)
                pkts += 1
        except Exception as e:
            pass

for s in sockets:
    s.close()

print(f"Probe finished. Non-host packets captured: {pkts}", flush=True)
