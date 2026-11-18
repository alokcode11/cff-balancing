import sys
sys.path.insert(0, r'c:\Users\alokp\Desktop\CFF\CFF_LAN_Investigation\scripts')
import importlib.util, os

spec = importlib.util.spec_from_file_location(
    "app",
    r'c:\Users\alokp\Desktop\CFF\CFF_LAN_Investigation\scripts\CFF_QR_Automation_App.py'
)
mod = importlib.util.module_from_spec(spec)

# Patch tkinter out for headless test
import unittest.mock as mock
sys.modules['tkinter'] = mock.MagicMock()
sys.modules['tkinter.ttk'] = mock.MagicMock()
sys.modules['tkinter.messagebox'] = mock.MagicMock()
sys.modules['tkinter.filedialog'] = mock.MagicMock()

spec.loader.exec_module(mod)

# Write a test CSV with 3 rows — we expect the LAST row to be used
csv_content = """No,Time,Name,SerialNo,Speed,P1Amount,P1Angle,P2Amount,P2Angle
11577,2026-11-14 16:33:00,122x992mm,,1100,0.036,55.0,0.019,180.0
11578,2026-11-14 16:39:42,122x992mm,,1100,0.122,91.0,0.077,214.0
11579,2026-11-14 16:39:55,122x992mm,,1100,0.103,88.0,0.065,210.0
"""
test_csv = r'c:\Users\alokp\Desktop\CFF\CFF_LAN_Investigation\data\drop_folder\real_test.csv'
with open(test_csv, 'w') as f:
    f.write(csv_content)

rec = mod.parse_last_record(test_csv)
print("LAST record parsed:")
for k, v in rec.items():
    print(f"  {k}: {v}")

print()
sticker = mod.build_sticker(rec)
print(f"Sticker saved: {sticker}")
print(f"File exists:   {os.path.exists(sticker)}")
print(f"File size:     {os.path.getsize(sticker)} bytes")
print()
print("SUCCESS - Full pipeline OK")
