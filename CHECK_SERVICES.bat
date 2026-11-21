@echo off
title Check CFF Services (Ports 21, 22, 127)
color 0E
cd /d "C:\Users\alokp\Desktop\CFF"
python "CFF_LAN_Investigation\scripts\diagnostic_scripts\check_cff_services.py"
echo.
pause
