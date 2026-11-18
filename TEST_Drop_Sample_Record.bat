@echo off
title Quick Test - CFF Auto Engine
color 0B
echo.
echo  QUICK TEST: Dropping a sample CSV into the drop folder
echo  to verify the full pipeline works (parse, QR, print)
echo.
cd /d "C:\Users\alokp\Desktop\CFF"

REM Create a test CSV in the drop folder
echo No,Time,Name,SerialNo,Speed,P1Amount,P1Angle,P2Amount,P2Angle > "CFF_LAN_Investigation\data\drop_folder\test_record.csv"
echo 11580,2026-11-14 16:30:00,122x992mm,CFF-TEST-001,1100,0.045,112.0,0.031,95.0 >> "CFF_LAN_Investigation\data\drop_folder\test_record.csv"

echo  Test CSV created: CFF_LAN_Investigation\data\drop_folder\test_record.csv
echo.
echo  Now run Launch_CFF_AUTO_ENGINE.bat - it will auto-detect and print!
echo.
pause
