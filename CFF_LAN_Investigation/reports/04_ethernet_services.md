# Phase 3: Ethernet Services & Port Status

**Date:** 2026-11-07  
**Machine:** Shanghai Jianping PHGS-5D (S/N 26010050)  

---

## 1. Network Services Status

| Service / Protocol | Port | Status | Notes |
| :--- | :--- | :--- | :--- |
| **HTTP Web Server** | TCP 80 / 8080 | Pending IP Alignment | To be scanned once target IP is matched. |
| **Modbus TCP** | TCP 502 | Pending IP Alignment | Industrial telemetry protocol used by PLCs. |
| **FTP File Server** | TCP 21 | Pending IP Alignment | Often enabled on WinCE HMIs for remote log retrieval. |
| **SMB File Sharing** | TCP 445 | Pending IP Alignment | Used for Windows shared folders / network printers. |
| **Telnet / Raw Socket**| TCP 23 / 8000+ | Pending IP Alignment | Common for embedded diagnostic telemetry. |

---

## 2. Preliminary Evaluation

Physical connection is operational (100 Mbps). Service enumeration will be performed as soon as the target IP address is configured or identified.
