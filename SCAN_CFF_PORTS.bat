@echo off
title CFF Port Scanner (192.168.0.2)
color 0A
cd /d "C:\Users\alokp\Desktop\CFF"
python "CFF_LAN_Investigation\scripts\diagnostic_scripts\scan_cff_ports.py"
echo.
pause
