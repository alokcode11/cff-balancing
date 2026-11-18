#!/usr/bin/env python3
"""
CFF Virtual USB Watcher & Real-Time Sync Daemon
Monitors the virtual USB drive for new export files from the CFF balancing machine
and instantly streams them to the PC QR Automation application over Wi-Fi / LAN.
"""

import time
import os
import requests
import glob
import subprocess

MOUNT_DIR = "/mnt/cff_virtual_udisk"
DISK_IMG = "/var/cff_virtual_udisk.bin"
PC_ENDPOINT = "http://192.168.1.100:5000/api/ingest_record" # Configurable PC IP

def ensure_mounted():
    os.makedirs(MOUNT_DIR, exist_ok=True)
    subprocess.run(["sudo", "mount", "-o", "ro", DISK_IMG, MOUNT_DIR], capture_output=True)

def sync_new_records():
    ensure_mounted()
    files = glob.glob(os.path.join(MOUNT_DIR, "**", "*.csv"), recursive=True) + \
            glob.glob(os.path.join(MOUNT_DIR, "**", "*.txt"), recursive=True)
    
    for f in files:
        mtime = os.path.getmtime(f)
        if time.time() - mtime < 10: # Modified in the last 10 seconds
            print(f"[NEW TEST DETECTED] Syncing {f} to PC...")
            with open(f, "rb") as fp:
                try:
                    res = requests.post(PC_ENDPOINT, files={"file": fp}, timeout=2.0)
                    print(f"Sync Result: {res.status_code}")
                except Exception as e:
                    print(f"Sync error: {e}")

if __name__ == "__main__":
    print("Starting CFF Real-Time USB Sync Daemon...")
    while True:
        try:
            sync_new_records()
        except Exception as ex:
            pass
        time.sleep(0.5)
