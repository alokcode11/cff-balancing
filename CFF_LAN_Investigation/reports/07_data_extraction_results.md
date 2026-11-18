# Phase 6 & 7: Live Balancing Test & Extraction Results

**Date:** 2026-11-07 17:42  
**Target:** Shanghai Jianping PHGS-5D (S/N 26010050)  
**Experiment:** Live Balancing Cycle with Continuous Multi-Channel Sniffing  

---

## 1. Test Execution & Setup

During an active balancing cycle performed by the operator:
- **Hardware Layer:** Continuous polling of Windows physical network interface statistics on Interface Index 21 (`Ethernet` / Realtek GbE Controller).
- **Transport Layer (TCP):** Active multi-port server listening on ports `9100` (RAW JetDirect / Print), `8000`, `8080`, `5000`, `502` (Modbus TCP), `6000`, and `3000`.
- **Transport Layer (UDP):** Active datagram listener across broadcast/multicast channels (`67`, `137`, `502`, `514`, `1900`, `2000`, `5000`, `6000`, `8000`, `8080`, `9100`).

---

## 2. Empirical Findings

| Observation Metric | Result | Engineering Conclusion |
| :--- | :--- | :--- |
| **Automatic Outbound TCP Connection** | **None** | The machine does **not** initiate an outbound TCP connection to a PC/server upon test completion. |
| **Unicast Packets on Interface 21** | `InUcastPkts = 0` | The CFF machine sent zero directed IP packets to the laptop. |
| **Automatic Telemetry Broadcast** | **None** | No UDP broadcast containing unbalance, angle, or completion signals was transmitted on the direct Ethernet cable. |
| **Internal Storage Persistence** | **Active** | The machine saved the test result into its internal flash memory (as verified by the manual U-disk export workflow). |

---

## 3. Core Technical Determination

1. **Passive LAN Behavior:** The PHGS-5D embedded controller does **NOT** automatically push balancing records over Ethernet when a balancing cycle finishes.
2. **Architecture Distinction:**
   - Unlike the 8 PC-based machines (which run Windows and write directly to `Jobs.xml` via `MicroBalance DoublePlane.exe` / COM port), this embedded Chinese controller is designed strictly as a self-contained unit.
   - It requires an explicit user export action (U-disk Export) or an active host interrogation request.
3. **Primary Extraction Path:**
   - The immediate and foolproof path to automated QR generation is analyzing the **U-disk Export file structure**, followed by either:
     - Automated USB Mass-Storage Emulation Gateway (e.g. Raspberry Pi Zero 2W / USB OTG bridge) that captures the file automatically upon export, OR
     - Establishing whether an interrogation protocol (Modbus / raw ASCII query) is supported once the static IP is queried.
