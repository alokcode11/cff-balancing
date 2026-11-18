# Phase 6: Protocol Investigation & Communication Methods

**Date:** 2026-11-07  
**Machine:** Shanghai Jianping PHGS-5D (S/N 26010050)  

---

## 1. Candidate Communication Channels

1. **Jianping Network Printer / Server Protocol:**
   - JP-800 HMI documentation indicates native capability to send reports to a network printer or backup server.
   - Mechanism: Machine acts as a client pushing data to a configured server IP:Port upon test completion.
2. **Modbus TCP (Slave Mode):**
   - If enabled on the internal PLC/measuring board, holding registers (40001+) typically contain RPM, angle, unbalance magnitude, and OK/NG flags.
3. **HTTP REST / Web API:**
   - Some modern embedded HMIs serve a lightweight web interface with live/history export endpoints (`/export`, `/records.csv`).
4. **Direct Raw Socket:**
   - Proprietary ASCII or binary packet broadcast upon cycle completion.

---

## 2. Experimental Verification Prerequisites

Empirical socket probing will begin immediately upon acquiring the machine's static IP address.
