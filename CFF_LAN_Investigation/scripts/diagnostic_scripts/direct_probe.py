import socket, ctypes, struct
from ctypes import wintypes

iphlpapi = ctypes.windll.iphlpapi

def send_arp(ip_str):
    dst_ip = struct.unpack('<I', socket.inet_aton(ip_str))[0]
    mac = (ctypes.c_byte * 6)()
    mac_len = wintypes.ULONG(6)
    res = iphlpapi.SendARP(dst_ip, 0, ctypes.byref(mac), ctypes.byref(mac_len))
    if res == 0:
        return ':'.join(f'{b & 0xff:02X}' for b in bytes(mac))
    return None

targets = ['192.168.0.2', '200.200.200.190', '192.168.0.1', '200.200.200.1']
print("=== TESTING DIRECT HARDWARE ARP (LAYER 2) ===")
for t in targets:
    mac = send_arp(t)
    status = f"FOUND MAC: {mac}" if mac else "NO MAC (Unreachable on this port)"
    print(f"Target {t:16} -> {status}")

print("\n=== TESTING DIRECT TCP PORTS ON 192.168.0.2 ===")
ports = [80, 502, 21, 23, 8080, 5000, 8888, 4001, 12000, 9100]
for p in ports:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.4)
    code = s.connect_ex(('192.168.0.2', p))
    s.close()
    if code == 0:
        print(f"  >>> PORT {p} on 192.168.0.2 is OPEN!")

print("\n=== TESTING DIRECT TCP PORTS ON 200.200.200.190 ===")
for p in ports:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.4)
    code = s.connect_ex(('200.200.200.190', p))
    s.close()
    if code == 0:
        print(f"  >>> PORT {p} on 200.200.200.190 is OPEN!")

print("\nScan completed.")
