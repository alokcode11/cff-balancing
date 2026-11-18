"""
CFF LAN Discovery Script
Finds the CFF MCGS controller IP on the network, then probes known ports.
Saves results to: CFF_LAN_Investigation/reports/12_cff_lan_discovery_live.md
"""
import subprocess, socket, concurrent.futures, time, json, os, sys

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
os.makedirs(REPORT_DIR, exist_ok=True)
REPORT_FILE = os.path.join(REPORT_DIR, "12_cff_lan_discovery_live.md")

# MCGS Kunlun Tongtai factory default IPs and machine confirmed IPs
KNOWN_TARGETS = [
    "192.168.0.2",       # CFF Machine LAN1/LAN2 confirmed IP
    "200.200.200.190",   # CFF Machine LAN3 confirmed IP
    "192.168.0.1",
    "192.168.0.100",
    "200.200.200.1",
    "200.200.200.100",
    "192.168.1.1",
    "192.168.1.100",
    "192.168.137.1",
]

# Subnet sweeps
SUBNETS = [
    ("192.168.0",   range(1, 50)),
    ("200.200.200", range(1, 255)),
    ("192.168.1",   range(1, 100)),
]

# Ports to check on discovered hosts
PORTS_TO_CHECK = [
    (502,  "Modbus TCP"),
    (80,   "HTTP WebUI"),
    (8080, "HTTP Alt"),
    (9100, "Raw Print / Jetdirect"),
    (23,   "Telnet"),
    (21,   "FTP"),
    (5000, "MCGS Custom"),
    (5001, "MCGS Custom Alt"),
    (8888, "MCGS Web"),
    (4001, "Serial-over-LAN"),
    (4000, "Serial-over-LAN Alt"),
    (12000,"JP Balancer Custom"),
]


def ping(ip, timeout_ms=400):
    r = subprocess.run(
        ["ping", "-n", "1", "-w", str(timeout_ms), ip],
        capture_output=True, text=True
    )
    return r.returncode == 0


def check_port(ip, port, timeout=1.5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((ip, port))
        s.close()
        return result == 0
    except Exception:
        return False


def try_http(ip, port=80, timeout=2):
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((ip, port))
        req = f"GET / HTTP/1.0\r\nHost: {ip}\r\n\r\n"
        s.send(req.encode())
        resp = s.recv(2048).decode(errors='ignore')
        s.close()
        return resp[:500]
    except Exception as e:
        return f"Error: {e}"


def try_modbus(ip, port=502, timeout=2):
    """Send Modbus TCP Read Holding Registers request (FC=3, addr=0, count=10)"""
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((ip, port))
        # Modbus ADU: Transaction=1, Protocol=0, Length=6, Unit=1, FC=3, Start=0, Count=10
        pdu = bytes([0x00, 0x01, 0x00, 0x00, 0x00, 0x06,
                     0x01, 0x03, 0x00, 0x00, 0x00, 0x0A])
        s.send(pdu)
        resp = s.recv(256)
        s.close()
        return resp.hex()
    except Exception as e:
        return f"Error: {e}"


def main():
    print("=" * 60)
    print("  CFF MCGS LAN DISCOVERY - STARTING")
    print("=" * 60)
    
    results = {
        "scan_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "alive_hosts": [],
        "open_ports": {},
        "cff_candidate": None,
    }
    
    # Phase 1: Try known MCGS IPs first (fast)
    print("\n[Phase 1] Testing known MCGS factory default IPs...")
    alive = []
    for ip in KNOWN_TARGETS:
        ok = ping(ip, 500)
        status = "✅ ALIVE" if ok else "❌ No response"
        print(f"  {ip:20s}  {status}")
        if ok:
            alive.append(ip)
    
    # Phase 2: Subnet sweep (if no known IP found)
    if not alive:
        print("\n[Phase 2] No known IP responded. Running subnet sweep...")
        all_targets = []
        for subnet, r in SUBNETS:
            for i in r:
                all_targets.append(f"{subnet}.{i}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
            future_map = {ex.submit(ping, ip, 300): ip for ip in all_targets}
            for fut in concurrent.futures.as_completed(future_map):
                ip = future_map[fut]
                try:
                    if fut.result():
                        alive.append(ip)
                        print(f"  🔍 ALIVE: {ip}")
                except Exception:
                    pass
    
    if not alive:
        print("\n❌ No hosts found on any subnet.")
        print("   Possible causes:")
        print("   1. PC IP not on same subnet as CFF")
        print("   2. CFF Ethernet port is for different purpose")
        print("   3. CFF uses a non-standard IP")
        print("   4. Run STEP1_Setup_And_Find_CFF.bat as Administrator first!")
        results["alive_hosts"] = []
    else:
        print(f"\n✅ Found {len(alive)} host(s):", alive)
        results["alive_hosts"] = alive
    
    # Phase 3: Port probe all alive hosts
    if alive:
        print("\n[Phase 3] Port scanning alive hosts...")
        for ip in alive:
            print(f"\n  Scanning {ip}:")
            open_ports = {}
            for port, name in PORTS_TO_CHECK:
                is_open = check_port(ip, port, timeout=1.5)
                if is_open:
                    print(f"    ✅  PORT {port:5d}  {name}  OPEN")
                    open_ports[port] = name
                    
                    # Extra probes on open ports
                    if port in [80, 8080, 8888]:
                        resp = try_http(ip, port)
                        print(f"         HTTP Response: {resp[:200]}")
                        open_ports[f"{port}_http_resp"] = resp[:500]
                    
                    if port == 502:
                        resp = try_modbus(ip)
                        print(f"         Modbus Response: {resp}")
                        open_ports["502_modbus_resp"] = resp
                else:
                    print(f"    ⬜  PORT {port:5d}  {name}  closed")
            
            results["open_ports"][ip] = open_ports
            
            if open_ports:
                results["cff_candidate"] = ip
                print(f"\n  ★ CFF CANDIDATE: {ip} has {len(open_ports)} open port(s)")
    
    # Save results to JSON
    json_path = os.path.join(REPORT_DIR, "cff_discovery_result.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Save markdown report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# CFF LAN Discovery Report\n\n")
        f.write(f"**Scan Time:** {results['scan_time']}\n\n")
        f.write("## Alive Hosts\n\n")
        if results["alive_hosts"]:
            for h in results["alive_hosts"]:
                f.write(f"- `{h}`\n")
        else:
            f.write("- None found\n")
        f.write("\n## Open Ports\n\n")
        for ip, ports in results["open_ports"].items():
            f.write(f"### {ip}\n\n")
            for p, n in ports.items():
                f.write(f"- Port `{p}`: {n}\n")
            f.write("\n")
        f.write(f"\n## CFF Candidate IP: `{results.get('cff_candidate', 'Not found')}`\n")
    
    print(f"\n📄 Report saved: {REPORT_FILE}")
    print(f"📄 JSON saved:   {json_path}")
    
    return results


if __name__ == "__main__":
    r = main()
    sys.exit(0 if r["cff_candidate"] else 1)
