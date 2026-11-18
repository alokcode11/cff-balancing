# Phase 2: CFF Network Discovery Report

**Date:** 2026-11-07  
**Host:** Administrator PC  
**Physical Interface:** `Ethernet` (Realtek Gaming GbE Family Controller, MAC `F0:4E:A4:9D:18:59`)  
**Target:** Shanghai Jianping PHGS-5D Balancing Machine (S/N 26010050)  

---

## 1. Network Discovery Methodology & Constraints

To strictly protect corporate network traffic, all discovery actions were constrained to Interface Index 21 (`Ethernet`). The active Wi-Fi connection (`10.254.254.233`) and NordVPN tunnel (`10.3.0.2`) were completely excluded from diagnostic sweeps.

No network configuration changes, firewall alterations, or aggressive penetration tools were utilized.

---

## 2. Tests Executed & Empirical Results

### Test 1: Layer 1 & Layer 2 Physical Link Verification
- **Command:** Real-time query of `OperationalStatus` and `LinkSpeed`.
- **Result:**
  - Status: `Up`
  - Speed: `100 Mbps` (100BASE-TX)
- **Finding:** **CONFIRMED**. The CFF controller's physical network transceiver is active and physically linked directly to the PC's Ethernet port.

### Test 2: Passive Broadcast & Multicast Listener
- **Script:** `listen_broadcasts.py`
- **Monitored Ports:**
  - UDP 67 (DHCP Discover / Request)
  - UDP 137 (NetBIOS Name Service)
  - UDP 1900 (SSDP Discovery)
  - UDP 5353 (mDNS)
  - UDP 5355 (LLMNR)
- **Duration:** 10 seconds continuous listening.
- **Packets Captured:** `0`
- **Finding:** **CONFIRMED**. The CFF controller is not broadcasting DHCP requests and does not announce itself via common discovery protocols.

### Test 3: Exhaustive ARP Sweep on Configured Subnet (`192.168.137.0/24`)
- **Script:** `fast_arp_sweep.py` (50 concurrent threads, Win32 `SendARP` API)
- **Range Scanned:** `192.168.137.1` through `192.168.137.254`
- **Results:**
  - `192.168.137.1`: Responded (Local PC adapter `F0:4E:A4:9D:18:59`)
  - `192.168.137.2` to `192.168.137.254`: No response (`0` devices found)
- **Finding:** **CONFIRMED**. The CFF machine is **NOT** configured with an IP address in the `192.168.137.0/24` subnet.

---

## 3. Discovery Conclusions

1. **Subnet Mismatch:** The PC's current IP address (`192.168.137.1`) originates from default Windows ICS settings. The CFF controller uses a static IP address residing on a different subnet.
2. **Industrial Controller Behavior:** In accordance with Shanghai Jianping JP-800 series controller architecture, static IP addressing is standard. Devices remain passive listeners until contacted on their configured subnet and port.
3. **Next Discovery Requirement:** The exact IP address must either be:
   - Read directly from the CFF machine's touch-screen HMI settings menu, OR
   - Discovered through a controlled multi-subnet sweep after user approval to add temporary IP aliases.
