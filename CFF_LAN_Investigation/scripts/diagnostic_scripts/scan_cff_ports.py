import socket, sys, time
from concurrent.futures import ThreadPoolExecutor

TARGET_IP = "192.168.0.2"

# Industrial, MCGS, embedded and common ports
PRIORITY_PORTS = [
    21, 22, 23, 80, 102, 135, 139, 445, 502, 1080, 1433, 1502, 1883,
    2000, 2001, 2020, 3000, 3001, 3306, 3389, 4000, 4001, 4002, 4003,
    5000, 5001, 5002, 5003, 5004, 5005, 5020, 6000, 6001, 7000, 7001, 7002, 7003, 7004, 7005,
    8000, 8001, 8080, 8081, 8088, 8888, 9000, 9100, 9101, 9999,
    10000, 10001, 10002, 12000, 12001, 12002, 161, 514, 5353
]
ALL_PORTS = list(dict.fromkeys(PRIORITY_PORTS + list(range(1, 1025))))

print("=" * 60)
print(f"  SCANNING CFF CONTROLLER PORTS: {TARGET_IP}")
print(f"  Total ports to test: {len(ALL_PORTS)}")
print("=" * 60)

open_ports = []

def probe(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.6)
        res = s.connect_ex((TARGET_IP, port))
        s.close()
        if res == 0:
            return port
    except Exception:
        pass
    return None

start = time.time()
with ThreadPoolExecutor(max_workers=60) as ex:
    for p in ex.map(probe, ALL_PORTS):
        if p is not None:
            open_ports.append(p)
            print(f"  >>> FOUND OPEN PORT: {p} !!!")

elapsed = time.time() - start
print("\n" + "=" * 60)
if open_ports:
    print(f"  SUCCESS! Open ports found on {TARGET_IP}: {open_ports}")
else:
    print(f"  No standard TCP ports open on {TARGET_IP} (Scanned in {elapsed:.1f}s)")
print("=" * 60)
