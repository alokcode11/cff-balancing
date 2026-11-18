import subprocess, concurrent.futures, socket, time

PRINTER = "ZDesigner ZD421-300dpi ZPL"
LAN_IP = "192.168.137.1"

# 1. Ping sweep — CFF machine must be on 192.168.137.x subnet
print("=" * 55)
print("  CFF MACHINE DISCOVERY — 192.168.137.0/24")
print("=" * 55)

def ping(ip):
    r = subprocess.run(['ping','-n','1','-w','400', ip], capture_output=True)
    return ip if r.returncode == 0 else None

targets = [f"192.168.137.{i}" for i in range(1, 255)]
found = []
with concurrent.futures.ThreadPoolExecutor(max_workers=60) as ex:
    for result in ex.map(ping, targets):
        if result and result != LAN_IP:
            found.append(result)
            print(f"  ALIVE: {result}")

if not found:
    print("  No hosts found on 192.168.137.0/24")
    # Also try MCGS default subnet
    print("\n  Trying MCGS default 200.200.200.0/24...")
    targets2 = [f"200.200.200.{i}" for i in range(1, 255)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as ex:
        for result in ex.map(ping, targets2):
            if result:
                found.append(result)
                print(f"  ALIVE: {result}")
else:
    print(f"\n  Found {len(found)} device(s): {found}")

# 2. Port scan on found hosts
if found:
    print("\n--- Port Scan ---")
    for ip in found:
        for port in [502, 80, 8080, 23, 5000, 4001]:
            try:
                s = socket.socket()
                s.settimeout(1)
                res = s.connect_ex((ip, port))
                s.close()
                if res == 0:
                    print(f"  {ip}:{port} OPEN")
            except:
                pass

# 3. Printer check
print("\n--- Printer Check ---")
import ctypes, ctypes.wintypes as wt
winspool = ctypes.WinDLL("winspool.drv")
hPrinter = wt.HANDLE()
if winspool.OpenPrinterW(PRINTER, ctypes.byref(hPrinter), None):
    print(f"  {PRINTER}: CONNECTED OK")
    winspool.ClosePrinter(hPrinter)
else:
    print(f"  {PRINTER}: NOT ACCESSIBLE")

print("\n=== DIAGNOSTIC COMPLETE ===")
