import subprocess

r = subprocess.run([
    'powershell', '-Command',
    'Get-NetAdapter | Select-Object Name,Status,LinkSpeed,MediaConnectionState | Format-Table -AutoSize'
], capture_output=True, text=True)
print(r.stdout)
print(r.stderr[:300])
