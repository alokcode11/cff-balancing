#!/bin/bash
# Setup Raspberry Pi Zero 2W as a USB Mass Storage Gadget for CFF Machine
# This makes the Pi Zero appear as a standard FAT32 U-disk to the balancing machine.

set -e

echo "=== CONFIGURING RASPBERRY PI ZERO USB-OTG MASS STORAGE GADGET ==="

# 1. Enable dwc2 USB driver in boot config
if ! grep -q "dtoverlay=dwc2" /boot/config.txt; then
    echo "dtoverlay=dwc2" | sudo tee -a /boot/config.txt
fi

# 2. Enable dwc2 kernel module
if ! grep -q "dwc2" /etc/modules; then
    echo "dwc2" | sudo tee -a /etc/modules
fi

# 3. Create a 512MB FAT32 virtual flash drive container
DISK_IMG="/var/cff_virtual_udisk.bin"
if [ ! -f "$DISK_IMG" ]; then
    echo "Creating 512MB virtual disk image..."
    sudo dd if=/dev/zero of=$DISK_IMG bs=1M count=512
    sudo mkfs.vfat -F 32 -n "CFF_DATA" $DISK_IMG
fi

# 4. Load the mass storage gadget module
echo "Loading g_mass_storage module..."
sudo modprobe g_mass_storage file=$DISK_IMG stall=0 ro=0 removable=1

echo "=== USB GADGET READY! PLUG PI ZERO USB-OTG PORT INTO CFF MACHINE ==="
