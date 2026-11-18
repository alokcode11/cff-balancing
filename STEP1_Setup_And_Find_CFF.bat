@echo off
title CFF LAN Setup + Auto Discovery
echo ============================================================
echo  CFF BALANCING MACHINE - LAN AUTO SETUP
echo  Run this as Administrator!
echo ============================================================
echo.

REM --- Assign PC IP on the active Ethernet adapter ---
echo [1/4] Setting PC IP to 200.200.200.100 on Ethernet...
netsh interface ipv4 set address name="Ethernet" static 200.200.200.100 255.255.255.0
netsh interface ipv4 set address name="Ethernet 2" static 200.200.200.100 255.255.255.0
echo       Assigned IP 200.200.200.100 (MCGS Default Subnet).

REM Wait for adapter to come up
echo [2/4] Waiting 4 seconds for adapter...
timeout /t 4 /nobreak >nul

REM --- Run the Python discovery script ---
echo [3/4] Running CFF LAN discovery...
python "c:\Users\alokp\Desktop\CFF\CFF_LAN_Investigation\scripts\diagnostic_scripts\cff_lan_discovery.py"

echo.
echo [4/4] Done. Check output above for CFF IP address.
echo       If CFF was found, the automation app will now auto-connect.
echo.
pause
