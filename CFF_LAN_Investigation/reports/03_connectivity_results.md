# Phase 3: Connectivity & Ethernet Services Status Report

**Date:** 2026-11-07  
**Machine:** Shanghai Jianping PHGS-5D (S/N 26010050)  

---

## 1. Summary of Connectivity Matrix

| OSI Layer | Status | Classification | Evidence |
| :--- | :--- | :--- | :--- |
| **Layer 1 (Physical)** | **Connected** | **CONFIRMED** | Link speed negotiated at 100 Mbps; Realtek GbE PHY indicates link Up. |
| **Layer 2 (Data Link)** | **Unestablished** | **OBSERVED** | No ARP replies received from target on current subnet (`192.168.137.0/24`). |
| **Layer 3 (Network)** | **Blocked / Misconfigured Subnet** | **OBSERVED** | Target IP address is outside `192.168.137.0/24` subnet. |
| **Layer 4 (Transport)** | **Pending IP Discovery** | **UNKNOWN** | TCP/UDP ports cannot be probed until matching IP subnet is reached. |
| **Layer 7 (Application)**| **Pending IP Discovery** | **UNKNOWN** | Protocol availability (HTTP, Modbus TCP, FTP, JP proprietary) pending Layer 3 link. |

---

## 2. Service Evaluation (Preliminary)

According to official technical documentation from Shanghai Jianping on the JP-800 series embedded measuring system:
1. **Network Printing / Server Backup:** Supported natively when equipment IP is configured to match the corporate server segment.
2. **Remote Maintenance:** Supported via TCP/IP connection to JP technical support server.
3. **Automated Live Balancing Stream:** Not enabled by default on embedded units without specific software configuration or server target setting.
