import ctypes
from ctypes import wintypes
import socket
import struct
from concurrent.futures import ThreadPoolExecutor

SendARP = ctypes.windll.iphlpapi.SendARP

def ip_to_int(ip_str):
    return struct.unpack("<I", socket.inet_aton(ip_str))[0]

def check_ip(ip_str, src_ip):
    dest_ip = ip_to_int(ip_str)
    mac = (ctypes.c_byte * 6)()
    mac_len = wintypes.ULONG(6)
    res = SendARP(dest_ip, src_ip, ctypes.byref(mac), ctypes.byref(mac_len))
    if res == 0:
        mac_str = ':'.join(f'{b & 0xFF:02X}' for b in mac[:mac_len.value])
        return (ip_str, mac_str)
    return None

if __name__ == '__main__':
    src_ip = ip_to_int("192.168.137.1")
    ips = [f"192.168.137.{i}" for i in range(1, 255)]
    print(f"Scanning {len(ips)} IPs on 192.168.137.0/24 with 50 threads...", flush=True)
    
    found = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(lambda ip: check_ip(ip, src_ip), ips)
        for r in results:
            if r:
                print(f"[FOUND] {r[0]} -> MAC: {r[1]}", flush=True)
                found.append(r)
                
    print(f"Sweep complete. Total found on 192.168.137.0/24: {len(found)}", flush=True)
