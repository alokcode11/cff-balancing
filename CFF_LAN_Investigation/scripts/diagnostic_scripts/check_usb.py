import subprocess
import json

cmd = "powershell -NoProfile -Command \"Get-WmiObject Win32_DiskDrive | Select-Object Model, InterfaceType, MediaType, Size | ConvertTo-Json\""
try:
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    print("Disks:")
    print(res.stdout)
except Exception as e:
    print(e)
