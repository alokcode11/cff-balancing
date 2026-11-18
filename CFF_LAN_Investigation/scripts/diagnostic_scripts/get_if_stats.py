import ctypes
from ctypes import wintypes

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

# IfIndex 21 is our Realtek Ethernet adapter
row = MIB_IFROW()
row.dwIndex = 21
res = ctypes.windll.iphlpapi.GetIfEntry(ctypes.byref(row))
print(f"GetIfEntry res={res}")
print(f"InOctets (Bytes In): {row.dwInOctets}")
print(f"InUcastPkts: {row.dwInUcastPkts}")
print(f"InNUcastPkts (Broadcast/Multicast): {row.dwInNUcastPkts}")
print(f"InDiscards: {row.dwInDiscards}")
print(f"InErrors: {row.dwInErrors}")
print(f"InUnknownProtos: {row.dwInUnknownProtos}")
print(f"OutOctets (Bytes Out): {row.dwOutOctets}")
