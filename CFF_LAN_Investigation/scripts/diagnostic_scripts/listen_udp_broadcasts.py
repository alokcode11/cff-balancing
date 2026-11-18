import socket
import select
import time

ports = [67, 137, 138, 1900, 5353, 502, 5000, 8000, 10001, 20000]
sockets = []

for port in ports:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('0.0.0.0', port))
        s.setblocking(False)
        sockets.append((port, s))
    except Exception as e:
        # Some ports may be in use by Windows
        pass

print(f"Listening on {len(sockets)} broadcast/discovery UDP ports for 4 seconds...")
start = time.time()
found = []

while time.time() - start < 4.0:
    r_list = [s for _, s in sockets]
    readable, _, _ = select.select(r_list, [], [], 0.5)
    for s in readable:
        port = next(p for p, sock in sockets if sock == s)
        try:
            data, addr = s.recvfrom(2048)
            print(f"INCOMING UDP on port {port}: From {addr} | Length: {len(data)} bytes | Hex: {data[:32].hex()}")
            found.append((port, addr, data))
        except:
            pass

for _, s in sockets:
    s.close()

if not found:
    print("No UDP broadcast packets captured.")
else:
    print(f"Total packets captured: {len(found)}")
