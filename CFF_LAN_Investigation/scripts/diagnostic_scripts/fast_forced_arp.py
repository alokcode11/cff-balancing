import ctypes
from ctypes import wintypes
import socket
import concurrent.futures

IPHLPAPI = ctypes.windll.iphlpapi

src_ip_str = "192.168.137.1"
src_ip_bytes = socket.inet_aton(src_ip_str)
src_ip_int = ctypes.c_ulong.from_buffer_copy(src_ip_bytes).value

def send_arp_forced(dest_ip_str):
    dest_ip_bytes = socket.inet_aton(dest_ip_str)
    dest_ip_int = ctypes.c_ulong.from_buffer_copy(dest_ip_bytes).value
    mac_addr = (ctypes.c_byte * 6)()
    phys_addr_len = wintypes.ULONG(6)
    ret = IPHLPAPI.SendARP(dest_ip_int, src_ip_int, mac_addr, ctypes.byref(phys_addr_len))
    if ret == 0:
        return dest_ip_str, ':'.join(f'{b & 0xff:02X}' for b in mac_addr)
    return None

targets = [f"192.168.137.{i}" for i in range(2, 255)]
print(f"Scanning 192.168.137.0/24 (forced via src {src_ip_str}) with 50 threads...")

hits = []
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
    for res in ex.map(send_arp_forced, targets):
        if res:
            print("  HIT:", res)
            hits.append(res)

print("Scan complete. Hits:", hits)
