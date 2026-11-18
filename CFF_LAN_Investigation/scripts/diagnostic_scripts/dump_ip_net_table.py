import ctypes
from ctypes import wintypes
import socket
import struct

IPHLPAPI = ctypes.windll.iphlpapi

class MIB_IPNETROW(ctypes.Structure):
    _fields_ = [
        ('dwIndex', wintypes.DWORD),
        ('dwPhysAddrLen', wintypes.DWORD),
        ('bPhysAddr', ctypes.c_byte * 8),
        ('dwAddr', wintypes.DWORD),
        ('dwType', wintypes.DWORD) # 1=other, 2=invalid, 3=dynamic, 4=static
    ]

dwSize = wintypes.DWORD(0)
IPHLPAPI.GetIpNetTable(None, ctypes.byref(dwSize), False)
buf = ctypes.create_string_buffer(dwSize.value)
ret = IPHLPAPI.GetIpNetTable(buf, ctypes.byref(dwSize), False)
num = struct.unpack('<I', buf[:4])[0]
print(f"Total IPNet entries: {num}")

row_size = ctypes.sizeof(MIB_IPNETROW)
offset = 4
type_map = {1: 'Other', 2: 'Invalid', 3: 'Dynamic', 4: 'Static'}

for i in range(num):
    raw_row = buf.raw[offset : offset + row_size]
    row = MIB_IPNETROW.from_buffer_copy(raw_row)
    offset += row_size
    ip = socket.inet_ntoa(struct.pack('<I', row.dwAddr))
    mac = ':'.join(f'{b & 0xff:02X}' for b in row.bPhysAddr[:row.dwPhysAddrLen])
    type_str = type_map.get(row.dwType, str(row.dwType))
    if not ip.startswith('224.') and not ip.startswith('239.') and ip != '255.255.255.255':
        print(f"Interface {row.dwIndex}: IP={ip:<16} MAC={mac:<18} Type={type_str}")
