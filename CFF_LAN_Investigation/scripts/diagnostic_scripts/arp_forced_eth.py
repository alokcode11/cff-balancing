import ctypes
from ctypes import wintypes
import socket
import struct

IPHLPAPI = ctypes.windll.iphlpapi

src_ip_str = "192.168.137.1"
src_ip_bytes = socket.inet_aton(src_ip_str)
src_ip_int = ctypes.c_ulong.from_buffer_copy(src_ip_bytes).value

def send_arp_forced(dest_ip_str):
    dest_ip_bytes = socket.inet_aton(dest_ip_str)
    dest_ip_int = ctypes.c_ulong.from_buffer_copy(dest_ip_bytes).value
    mac_addr = (ctypes.c_byte * 6)()
    phys_addr_len = wintypes.ULONG(6)
    
    # Pass src_ip_int to FORCE transmission through Realtek GbE interface!
    ret = IPHLPAPI.SendARP(dest_ip_int, src_ip_int, mac_addr, ctypes.byref(phys_addr_len))
    if ret == 0:
        return ':'.join(f'{b & 0xff:02X}' for b in mac_addr)
    return None

print(f"Scanning 192.168.137.2 to 192.168.137.254 FORCED through Ethernet (src={src_ip_str})...")
found = []
for i in range(2, 255):
    ip = f"192.168.137.{i}"
    mac = send_arp_forced(ip)
    if mac:
        print(f"!!! HIT FOUND !!! IP={ip} MAC={mac}")
        found.append((ip, mac))

if not found:
    print("No device responded on 192.168.137.x subnet directly on the CFF cable.")
else:
    print("Discovered devices on CFF cable:", found)
