@echo off
title CFF LAN Setup + Auto Discovery (DUAL SUBNET: 192.168.0.x + 200.200.200.x)
echo ============================================================
echo  CFF BALANCING MACHINE - LAN AUTO SETUP
echo  Configuring for CFF Controller: 192.168.0.2 / 200.200.200.190
echo  Run this as Administrator!
echo ============================================================
echo.

REM --- Reset onboard Ethernet to DHCP to prevent IP conflict ---
echo [1/4] Configuring Ethernet adapters...
netsh interface ipv4 set address name="Ethernet" source=dhcp >nul 2>&1

REM --- Assign Primary IP on Ethernet 2 for LAN1/LAN2 (192.168.0.100) ---
echo       Setting Primary IP: 192.168.0.100 on Ethernet 2 (for LAN1/LAN2)...
netsh interface ipv4 set address name="Ethernet 2" static 192.168.0.100 255.255.255.0 >nul 2>&1

REM --- Add Secondary IP on Ethernet 2 for LAN3 (200.200.200.100) ---
echo       Adding Secondary IP: 200.200.200.100 on Ethernet 2 (for LAN3)...
netsh interface ipv4 add address name="Ethernet 2" 200.200.200.100 255.255.255.0 >nul 2>&1

REM Wait for adapter to apply
echo [2/4] Waiting 3 seconds for adapter to apply IPs...
timeout /t 3 /nobreak >nul

echo.
echo Active IPs on Ethernet 2:
netsh interface ipv4 show addresses name="Ethernet 2" | findstr /I "IP Address"

echo.
echo [3/4] Running CFF Discovery on 192.168.0.2 and 200.200.200.190...
python "c:\Users\alokp\Desktop\CFF\CFF_LAN_Investigation\scripts\diagnostic_scripts\cff_lan_discovery.py"

echo.
echo [4/4] Done.
pause
