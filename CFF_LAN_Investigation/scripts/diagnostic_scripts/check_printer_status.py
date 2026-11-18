import ctypes
import ctypes.wintypes as wt

winspool = ctypes.WinDLL("winspool.drv")

class PRINTER_INFO_2(ctypes.Structure):
    _fields_ = [
        ("pServerName", wt.LPWSTR),
        ("pPrinterName", wt.LPWSTR),
        ("pShareName", wt.LPWSTR),
        ("pPortName", wt.LPWSTR),
        ("pDriverName", wt.LPWSTR),
        ("pComment", wt.LPWSTR),
        ("pLocation", wt.LPWSTR),
        ("pDevMode", ctypes.c_void_p),
        ("pSepFile", wt.LPWSTR),
        ("pPrintProcessor", wt.LPWSTR),
        ("pDatatype", wt.LPWSTR),
        ("pParameters", wt.LPWSTR),
        ("pSecurityDescriptor", ctypes.c_void_p),
        ("Attributes", wt.DWORD),
        ("Priority", wt.DWORD),
        ("DefaultPriority", wt.DWORD),
        ("StartTime", wt.DWORD),
        ("UntilTime", wt.DWORD),
        ("Status", wt.DWORD),
        ("cJobs", wt.DWORD),
        ("AveragePPM", wt.DWORD)
    ]

printer_name = "ZDesigner ZD421-300dpi ZPL"
hPrinter = wt.HANDLE()

if winspool.OpenPrinterW(printer_name, ctypes.byref(hPrinter), None):
    cbNeeded = wt.DWORD()
    winspool.GetPrinterW(hPrinter, 2, None, 0, ctypes.byref(cbNeeded))
    buf = (ctypes.c_byte * cbNeeded.value)()
    if winspool.GetPrinterW(hPrinter, 2, buf, cbNeeded.value, ctypes.byref(cbNeeded)):
        pInfo = ctypes.cast(buf, ctypes.POINTER(PRINTER_INFO_2)).contents
        print("Port Name:", pInfo.pPortName)
        print("Driver Name:", pInfo.pDriverName)
        print("Print Processor:", pInfo.pPrintProcessor)
        print("Datatype:", pInfo.pDatatype)
        print("Status Flags:", hex(pInfo.Status))
        print("Attributes:", hex(pInfo.Attributes))
        print("Current Jobs Count:", pInfo.cJobs)
    winspool.ClosePrinter(hPrinter)
else:
    print("Could not open printer")
