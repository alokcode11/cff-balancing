# Phase 4 & 5: Manufacturer Documentation & Controller Identification Report

**Date:** 2026-11-07  
**Manufacturer:** Shanghai Jianping Dynamic Balancing Machine Manufacturing Co., Ltd.  
**Website:** https://www.jp-balancer.com/  
**Machine Model:** PHGS-5D (Cross Flow Fan Balancing Machine)  
**Machine S/N:** 26010050  
**Manufacturing Date:** 2026-01  

---

## 1. Manufacturer & Model Analysis

Shanghai Jianping Dynamic Balancing Machine Manufacturing Co., Ltd. is one of the primary manufacturers of dynamic balancing systems in China. 

- **Model Hierarchy:**
  - `PHG` / `PHGS`: Dedicated horizontal balancing machines specifically configured for cylindrical fans, cross flow fans (CFF), blower wheels, and tubular rotors.
  - `-5` / `-5D`: Maximum rotor weight capacity of 5 kg, 220V single phase, 50 Hz, 1.5 kVA power rating.
  - `D`: Hard-bearing / digital measuring configuration.

---

## 2. Controller Architecture Identification

Across Shanghai Jianping's product catalog and production deployments, two primary measuring unit architectures exist:

### Architecture A: Industrial PC-Based Measuring System (e.g., JP-580 series)
- **Deployed in:** The 8 existing factory machines that already support automated QR sticker printing.
- **Hardware:** Built on an Advantech or similar industrial PC motherboard, 17" LCD monitor, running Windows XP / Windows 7 / Windows 10 embedded.
- **Storage & Interface:** Local relational database (Access / SQL Server / SQLite), standard Windows print spooler, native TCP/IP networking, USB/Ethernet integration.
- **Cost to upgrade:** The manufacturer quoted approximately **USD 7,000 per machine** to swap the embedded controller for this PC-based system. Management has declined this replacement unless technically unavoidable.

### Architecture B: Embedded Touch-Screen Measuring Unit (e.g., JP-800 / JP-680 series)
- **Deployed in:** The 2 machines under investigation (including S/N 26010050).
- **Hardware:** An integrated human-machine interface (HMI) / PLC measuring unit (typically 10" to 12" touch panel) running Windows CE or embedded real-time Linux.
- **User Interface:** Touch-screen driven interface with 3 account tiers:
  1. *Operator* (Routine balancing cycles, run/stop, result view).
  2. *Inspector* (Tolerance threshold setup, calibration records).
  3. *Administrator* (System configuration, communication settings, network IP setup, password management).
- **Data Export Feature:** Confirmed native "U-disk Export" function which dumps selected balancing records to a FAT32 USB flash drive.
- **Ethernet (RJ45) Port Role:**
  - Designed for **Data Printing & Server Backup** and **Remote Assistance**.
  - According to manufacturer technical specifications, the unit supports static IP configuration for connecting to a local area network or backup server, but the network segment must match the local network.

---

## 3. Key Findings on Network Communication

1. **IP Assignment Mode:**
   - The embedded JP-800 series controllers **do not use DHCP by default**. They are assigned a static IPv4 address at the factory or during machine commissioning.
   - If the machine is powered on without a matching subnet on the PC, no Layer 3 IP communication occurs, even though Layer 1/2 physical link negotiation succeeds at 100 Mbps.
2. **Accessing Network Settings on the Machine:**
   - Network parameters (IP address, Subnet Mask, Gateway, and Port) are stored in the controller's internal non-volatile memory and can be viewed or configured directly on the machine's touch screen under `Administrator` / `System Settings` / `Communication` or `Network`.
   - Default factory passwords commonly used by JP on these HMIs include `0000`, `1234`, `8888`, or blank (none), unless set by commissioning technicians.

---

## 4. Balancing Data Fields & Structure

Based on standard JP balancing records and the confirmed U-disk export capability, balancing records typically contain:

1. **Timestamp:** Date and time of measurement (`YYYY-MM-DD HH:MM:SS`).
2. **Rotor / Part Type:** Selected CFF model configuration.
3. **Balancing Speed:** Rotational speed in RPM.
4. **Plane 1 (Left Plane):**
   - Unbalance amount (g or mg).
   - Angle (degrees, 0–360°).
   - Correction weight.
5. **Plane 2 (Right Plane):**
   - Unbalance amount (g or mg).
   - Angle (degrees, 0–360°).
   - Correction weight.
6. **Tolerance & Status:** Allowable unbalance limit, OK / NG qualification verdict.
7. **Record Sequence ID:** Sequential test index.

*Critical Requirement:* A physical CFF serial number or barcode association is essential to ensure QR stickers are printed and attached to the correct physical workpiece.
