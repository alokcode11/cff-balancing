import subprocess, os

img_path = r'c:\Users\alokp\Desktop\CFF\CFF_LAN_Investigation\samples\raw_balancing_records\latest_cff_qr_sticker.png'
printer_name = 'ZDesigner ZD421-300dpi ZPL'

ps_cmd = f'''
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("{img_path}")
$pd = New-Object System.Drawing.Printing.PrintDocument
$pd.PrinterSettings.PrinterName = "{printer_name}"
Write-Host "Printer Valid:" $pd.PrinterSettings.IsValid
$img.Dispose()
'''

r = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True)
print("STDOUT:", r.stdout.strip())
print("STDERR:", r.stderr.strip())
