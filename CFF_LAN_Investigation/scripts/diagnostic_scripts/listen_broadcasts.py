import socket
import select
import time
import struct

ports = [67, 137, 1900, 5353, 5355]
sockets = []

for port in ports:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('0.0.0.0', port))
        s.setblocking(False)
        sockets.append((port, s))
        print(f"Listening on UDP port {port}")
    except Exception as e:
        print(f"Failed to bind UDP port {port}: {e}")

print("Listening for 10 seconds...")
start_time = time.time()
received_packets = 0

while time.time() - start_time < 10:
    r_list = [s for _, s in sockets]
    readable, _, _ = select.select(r_list, [], [], 0.5)
    for s in readable:
        for port, sock in sockets:
            if s == sock:
                try:
                    data, addr = s.recvfrom(4096)
                    # Filter out loopback or our own local IPs
                    sender_ip, sender_port = addr
                    print(f"[RECV] Port {port}: Received {len(data)} bytes from {sender_ip}:{sender_port}")
                    # If DHCP (port 67), extract client MAC if possible
                    if port == 67 and len(data) >= 44:
                        chaddr = data[28:44]
                        mac = ':'.join(f'{b:02x}' for b in chaddr[:6])
                        print(f"  DHCP Client MAC: {mac}")
                    received_packets += 1
                except Exception as ex:
                    print(f"Error receiving: {ex}")

for _, s in sockets:
    s.close()

print(f"Done. Total packets received: {received_packets}")
