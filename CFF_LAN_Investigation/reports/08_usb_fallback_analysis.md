# Phase 7: USB Export Fallback & Alternative Automation Analysis

**Date:** 2026-11-07  
**Project:** CFF Balancing Machine QR Automation (PHGS-5D)  

---

## 1. Confirmed Existing USB Export Workflow

The user has confirmed the following operational procedure on the PHGS-5D machine:
1. Operator mounts CFF rotor on balancing cradle.
2. Machine spins and measures unbalance.
3. Machine automatically writes balancing record to internal memory.
4. Operator opens the **U-disk Export** function on the touch screen.
5. Operator selects record(s).
6. Machine writes the file to the connected USB flash drive.

---

## 2. Technical Evaluation of Fallback Architectures

If direct Ethernet extraction is not natively supported or requires proprietary vendor software, three practical fallback architectures exist to eliminate manual USB flash drive swapping:

### Option 1: Hardware-Assisted USB Drive Emulator (Wireless/LAN USB Mass Storage)
- **Concept:** A micro-device (such as a Raspberry Pi Zero 2W / CM4 configured with `gadget_fs` / USB OTG Mass Storage emulation, or an industrial SanDisk / Toshiba FlashAir SD-to-USB bridge) acts as a virtual USB flash drive to the CFF machine.
- **Workflow:**
  1. The balancing machine writes exported files to the virtual USB drive over the existing USB port.
  2. The emulator detects file write events in real-time.
  3. The emulator automatically reads the file and transmits it via Wi-Fi/Ethernet to the PC collection script or MQTT broker.
  4. The PC parses the record and triggers the QR printer immediately.
- **Feasibility:** High. Does not require any modification to the CFF controller firmware or hardware.
- **Cost:** < $50 (compared to the $7,000 processor replacement quote).

### Option 2: Machine Touch-Screen Screen Scraping / OCR Fallback
- **Concept:** As detailed in the vendor proposal document (`CFF_OCR_QR_Integration_Vendor_Proposal.pdf`):
  - A fixed industrial camera / USB web camera or video capture feed observes the machine's display.
  - Optical Character Recognition (OCR) reads final unbalance values, angle, RPM, and OK/NG status.
  - A barcode / 2D scanner captures the physical CFF serial number before loading.
- **Pros:** Completely non-invasive, no software changes needed on CFF machine.
- **Cons:** Dependent on ambient lighting, cycle completion detection timing, and potential OCR misreads of decimal points.

### Option 3: USB Protocol Sniffing / Direct USB-A PC Connection
- **Concept:** Testing whether the CFF machine's USB-A port or internal USB hub supports USB-CDC (Serial Com Port) or USB HID/Printer mode when connected to a PC via an active USB host-to-host or data-transfer bridge.
- **Note:** Standard USB-A to USB-A cables should NOT be plugged between two host controllers directly as it can cause electrical damage to 5V power rails.

---

## 3. Next Steps for USB Fallback Validation

1. Request a sample exported file from the user's USB drive (from any recent test run on the PHGS-5D).
2. Determine:
   - File extension (`.csv`, `.txt`, `.dat`, `.xls`, `.xml`).
   - Encoding (UTF-8, GB2312, GBK, ASCII, binary).
   - Exact header format and columns.
   - Whether individual records include timestamps and unique sequential IDs.
