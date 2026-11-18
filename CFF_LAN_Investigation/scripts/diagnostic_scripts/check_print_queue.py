import subprocess

r = subprocess.run([
    'powershell', '-Command',
    '''
    try {
        Get-PrintJob -PrinterName "ZDesigner ZD421-300dpi ZPL" -ErrorAction Stop | 
        Select-Object Id, DocumentName, JobStatus, SubmittedTime, TotalPages | Format-Table -AutoSize
    } catch {
        Write-Host "Error checking print jobs:" $_
    }
    '''
], capture_output=True, text=True)

print("STDOUT:")
print(r.stdout)
print("STDERR:")
print(r.stderr)
