import ctypes
import ctypes.wintypes as wt

winspool = ctypes.WinDLL("winspool.drv")

class PRINTER_DEFAULTS(ctypes.Structure):
    _fields_ = [
        ("pDataType", wt.LPWSTR),
        ("pDevMode", ctypes.c_void_p),
        ("DesiredAccess", wt.DWORD)
    ]

class JOB_INFO_1(ctypes.Structure):
    _fields_ = [
        ("JobId", wt.DWORD),
        ("pPrinterName", wt.LPWSTR),
        ("pMachineName", wt.LPWSTR),
        ("pUserName", wt.LPWSTR),
        ("pDocument", wt.LPWSTR),
        ("pDatatype", wt.LPWSTR),
        ("pStatus", wt.LPWSTR),
        ("Status", wt.DWORD),
        ("Priority", wt.DWORD),
        ("Position", wt.DWORD),
        ("TotalPages", wt.DWORD),
        ("PagesPrinted", wt.DWORD),
        ("Submitted", wt.BYTE * 16) # SYSTEMTIME
    ]

printer_name = "ZDesigner ZD421-300dpi ZPL"
hPrinter = wt.HANDLE()

res = winspool.OpenPrinterW(printer_name, ctypes.byref(hPrinter), None)
print("OpenPrinter result:", res, "Handle:", hPrinter.value)

if res and hPrinter.value:
    cbNeeded = wt.DWORD()
    cReturned = wt.DWORD()
    winspool.EnumJobsW(hPrinter, 0, 100, 1, None, 0, ctypes.byref(cbNeeded), ctypes.byref(cReturned))
    print("Jobs buffer needed:", cbNeeded.value)
    if cbNeeded.value > 0:
        buf = (ctypes.c_byte * cbNeeded.value)()
        res2 = winspool.EnumJobsW(hPrinter, 0, 100, 1, buf, cbNeeded.value, ctypes.byref(cbNeeded), ctypes.byref(cReturned))
        print("Jobs returned:", cReturned.value)
        jobs = ctypes.cast(buf, ctypes.POINTER(JOB_INFO_1))
        for i in range(cReturned.value):
            job = jobs[i]
            print(f"Job ID: {job.JobId}, Doc: {job.pDocument}, Status: {job.pStatus}, Status Flags: {hex(job.Status)}")
    else:
        print("No jobs currently in spooler (spooler is empty)")
    winspool.ClosePrinter(hPrinter)
