import ctypes
from ctypes import wintypes
import socket
import select
import time
import os
import sys

print("=== STARTING CFF LIVE LAN LISTENER & DATA CAPTURE ===", flush=True)

class MIB_IFROW(ctypes.Structure):
    _fields_ = [
        ('wszName', ctypes.c_wchar * 256),
        ('dwIndex', wintypes.DWORD),
        ('dwType', wintypes.DWORD),
        ('dwMtu', wintypes.DWORD),
        ('dwSpeed', wintypes.DWORD),
        ('dwPhysAddrLen', wintypes.DWORD),
        ('bPhysAddr', ctypes.c_byte * 8),
        ('dwAdminStatus', wintypes.DWORD),
        ('dwOperStatus', wintypes.DWORD),
        ('dwLastChange', wintypes.DWORD),
        ('dwInOctets', wintypes.DWORD),
        ('dwInUcastPkts', wintypes.DWORD),
        ('dwInNUcastPkts', wintypes.DWORD),
        ('dwInDiscards', wintypes.DWORD),
        ('dwInErrors', wintypes.DWORD),
        ('dwInUnknownProtos', wintypes.DWORD),
        ('dwOutOctets', wintypes.DWORD),
        ('dwOutUcastPkts', wintypes.DWORD),
        ('dwOutNUcastPkts', wintypes.DWORD),
        ('dwOutDiscards', wintypes.DWORD),
        ('dwOutErrors', wintypes.DWORD),
        ('dwOutQLen', wintypes.DWORD),
        ('dwDescrLen', wintypes.DWORD),
        ('bDescr', ctypes.c_byte * 256)
    ]

def get_stats():
    row = MIB_IFROW()
    row.dwIndex = 21 # Interface 21 = Ethernet
    res = ctypes.windll.iphlpapi.GetIfEntry(ctypes.byref(row))
    if res == 0:
        return row.dwInOctets, row.dwInUcastPkts, row.dwInNUcastPkts
    return 0, 0, 0

# Baseline stats
base_in_octets, base_in_ucast, base_in_nucast = get_stats()
print(f"Hardware Baseline: InOctets={base_in_octets}, InUcastPkts={base_in_ucast}, InNUcastPkts={base_in_nucast}", flush=True)

# Common TCP listening ports (acting as Print / Data server)
tcp_ports = [9100, 8000, 8080, 5000, 502, 6000, 3000]
tcp_sockets = []

for port in tcp_ports:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        s.listen(5)
        s.setblocking(False)
        tcp_sockets.append((port, s))
        print(f"[TCP SERVER] Listening on port {port}...", flush=True)
    except Exception as e:
        print(f"[TCP SERVER] Could not bind port {port}: {e}", flush=True)

# Common UDP listening ports
udp_ports = [67, 137, 502, 514, 1900, 2000, 5000, 6000, 8000, 8080, 9100]
udp_sockets = []

for port in udp_ports:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('0.0.0.0', port))
        s.setblocking(False)
        udp_sockets.append((port, s))
        print(f"[UDP LISTENER] Bound port {port}...", flush=True)
    except Exception as e:
        pass

print("\n*** READY FOR BALANCING TEST! ***", flush=True)
print("Listening on all channels for 180 seconds. Run the balancing cycle now...", flush=True)

start_time = time.time()
active_clients = []
output_dir = r"c:\Users\alokp\Desktop\CFF\CFF_LAN_Investigation\samples\raw_balancing_records"
os.makedirs(output_dir, exist_ok=True)

last_check_time = start_time
last_octets = base_in_octets

while time.time() - start_time < 180:
    # 1. Check physical hardware packet counters every 2 seconds
    now = time.time()
    if now - last_check_time >= 2.0:
        curr_octets, curr_ucast, curr_nucast = get_stats()
        delta_octets = curr_octets - last_octets
        total_delta = curr_octets - base_in_octets
        if delta_octets > 0:
            print(f"[{time.strftime('%H:%M:%S')}] *** HARDWARE TRAFFIC DETECTED! *** +{delta_octets} bytes on wire! (Total received: {total_delta} bytes, Ucast={curr_ucast}, NonUcast={curr_nucast})", flush=True)
        last_octets = curr_octets
        last_check_time = now

    # 2. Select on TCP and UDP sockets
    r_list = [s for _, s in tcp_sockets] + [s for _, s in udp_sockets] + [c for c, _ in active_clients]
    readable, _, _ = select.select(r_list, [], [], 0.2)

    for s in readable:
        # Check if new TCP connection
        for port, sock in tcp_sockets:
            if s == sock:
                try:
                    conn, addr = sock.accept()
                    conn.setblocking(False)
                    active_clients.append((conn, addr))
                    print(f"[{time.strftime('%H:%M:%S')}] *** INCOMING TCP CONNECTION *** from {addr[0]}:{addr[1]} on port {port}!", flush=True)
                except Exception as ex:
                    print(f"Accept error: {ex}", flush=True)

        # Check if UDP packet
        for port, sock in udp_sockets:
            if s == sock:
                try:
                    data, addr = sock.recvfrom(65535)
                    ts = time.strftime('%Y%m%d_%H%M%S')
                    print(f"[{time.strftime('%H:%M:%S')}] *** UDP PACKET RECEIVED *** from {addr[0]}:{addr[1]} on port {port}! Length={len(data)} bytes", flush=True)
                    fname = os.path.join(output_dir, f"udp_dump_{ts}_{port}.bin")
                    with open(fname, "wb") as f:
                        f.write(data)
                    print(f"Saved payload to {fname}: {data[:100]}", flush=True)
                except Exception as ex:
                    print(f"UDP recv error: {ex}", flush=True)

        # Check existing TCP client data
        for c, addr in list(active_clients):
            if s == c:
                try:
                    data = c.recv(65535)
                    if data:
                        ts = time.strftime('%Y%m%d_%H%M%S')
                        print(f"[{time.strftime('%H:%M:%S')}] *** TCP DATA RECEIVED *** from {addr[0]}:{addr[1]}! Length={len(data)} bytes", flush=True)
                        fname = os.path.join(output_dir, f"tcp_dump_{ts}.bin")
                        with open(fname, "wb") as f:
                            f.write(data)
                        print(f"Saved payload to {fname}: {data[:100]}", flush=True)
                    else:
                        print(f"Client {addr} disconnected.", flush=True)
                        active_clients.remove((c, addr))
                        c.close()
                except Exception as ex:
                    print(f"Client read error: {ex}", flush=True)
                    active_clients.remove((c, addr))
                    c.close()

# Cleanup
for _, s in tcp_sockets:
    s.close()
for _, s in udp_sockets:
    s.close()
for c, _ in active_clients:
    c.close()

final_octets, final_ucast, final_nucast = get_stats()
print(f"Listener stopped. Total bytes received on wire during test: {final_octets - base_in_octets}", flush=True)
