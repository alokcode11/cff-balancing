import re

path = r'D:\Alok\MicroDoubleplane\MicroDoubleplane\MicroBalance DoublePlane.exe'
with open(path, 'rb') as f:
    data = f.read()

text = data.decode('latin-1', errors='ignore')

# Search for any communication references
patterns = [
    r'COM\d+',
    r'SerialPort',
    r'BaudRate',
    r'IPAddress',
    r'TcpClient',
    r'UdpClient',
    r'Socket',
    r'192\.168\.\d+\.\d+',
    r'Modbus',
    r'Ethernet',
    r'Correction\.xml',
    r'Jobs\.xml',
    r'Proteq',
    r'Jianping'
]

print("=== MICROBALANCE COMM SCAN ===")
for p in patterns:
    res = set(re.findall(p, text, re.IGNORECASE))
    if res:
        print(f"Matched {p}: {res}")

# Find any strings containing "Settings" or menu names
print("\n=== MENU / FORM NAMES ===")
forms = set(re.findall(r'frm[A-Za-z0-9_]+|Form[A-Za-z0-9_]+', text))
for form in sorted(forms):
    print(" ", form)

# Check for .NET metadata types
print("\n=== RELEVANT STRINGS ===")
words = re.findall(r'[A-Za-z0-9_]{4,30}', text)
comm_words = [w for w in words if any(k in w.lower() for k in ['port', 'baud', 'comm', 'net', 'ip', 'socket', 'channel', 'usb', 'ftdi', 'daq', 'card', 'device'])]
print(sorted(set(comm_words))[:40])
