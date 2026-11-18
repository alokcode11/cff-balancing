import ctypes
from ctypes import wintypes
import socket
import struct

SendARP = ctypes.windll.iphlpapi.SendARP

def ip_to_int(ip_str):
    return struct.unpack("<I", socket.inet_aton(ip_str))[0]

print("Scanning 192.168.137.1 to 192.168.137.254 using SendARP...")
found = []
src_ip = ip_to_int("192.168.137.1")

for last_octet in range(1, 255):
    ip_str = f"192.168.137.{last_octet}"
    dest_ip = ip_to_int(ip_str)
    mac = (ctypes.c_byte * 6)()
    mac_len = wintypes.ULONG(6)
    
    res = SendARP(dest_ip, src_ip, ctypes.byref(mac), ctypes.byref(mac_len))
    if res == 0:
        mac_str = ':'.join(f'{b & 0xFF:02X}' for b in mac[:mac_len.value])
        print(f"[FOUND] {ip_str} -> MAC: {mac_str}")
        found.append((ip_str, mac_str))

print(f"Sweep complete. Found {len(found)} devices.")
