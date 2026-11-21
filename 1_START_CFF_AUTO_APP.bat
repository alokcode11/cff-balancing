@echo off
title CFF BALANCING - QR AUTOMATION APP (100% AUTO MODE)
color 0A
cls
echo ============================================================
echo   CFF BALANCING MACHINE - QR AUTOMATION SYSTEM
echo ============================================================
echo.
echo   [1] USB Drive / Pendrive Monitoring : ACTIVE (D: to Z:)
echo   [2] Drop Folder Monitoring          : ACTIVE
echo   [3] Zebra ZD421 Auto-Print          : ACTIVE (22.4mm x 15mm)
echo   [4] Latest Record Chronology        : ALWAYS TOP (Row 1)
echo.
echo ============================================================
echo  Starting Application...
echo ============================================================
cd /d "C:\Users\alokp\Desktop\CFF"
python "CFF_LAN_Investigation\scripts\CFF_QR_Automation_App.py"
pause
