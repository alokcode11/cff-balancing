import ctypes
import ctypes.wintypes as wt

winspool = ctypes.WinDLL("winspool.drv")

class DOC_INFO_1(ctypes.Structure):
    _fields_ = [
        ("pDocName", wt.LPWSTR),
        ("pOutputFile", wt.LPWSTR),
        ("pDatatype", wt.LPWSTR)
    ]

def send_zpl_raw(printer_name, zpl_string):
    hPrinter = wt.HANDLE()
    if not winspool.OpenPrinterW(printer_name, ctypes.byref(hPrinter), None):
        print("Failed to open printer")
        return False
    
    docInfo = DOC_INFO_1("CFF_Direct_ZPL", None, "RAW")
    dwJob = winspool.StartDocPrinterW(hPrinter, 1, ctypes.byref(docInfo))
    if dwJob <= 0:
        print("Failed StartDocPrinter")
        winspool.ClosePrinter(hPrinter)
        return False
    
    winspool.StartPagePrinter(hPrinter)
    raw_data = zpl_string.encode('utf-8')
    dwWritten = wt.DWORD()
    ok = winspool.WritePrinter(hPrinter, raw_data, len(raw_data), ctypes.byref(dwWritten))
    winspool.EndPagePrinter(hPrinter)
    winspool.EndDocPrinter(hPrinter)
    winspool.ClosePrinter(hPrinter)
    print(f"WritePrinter result: {ok}, Bytes written: {dwWritten.value} / {len(raw_data)}")
    return dwWritten.value == len(raw_data)

# Physical 22.4mm x 15mm sticker (265 x 177 dots @ 300 DPI)
zpl_test = """^XA
~SD30
^PW265
^LL177
^MD30
^PR4,4,4
^MTT
^MNY
^FO82,12^BQN,2,4,Q^FDQA,7020001384261102045643^FS
^FO22,126^A0N,24,10^FD7020001384261102045643^FS
^XZ
"""

printer = "ZDesigner ZD421-300dpi ZPL"
print("Sending test ZPL to:", printer)
success = send_zpl_raw(printer, zpl_test)
print("Success:", success)
