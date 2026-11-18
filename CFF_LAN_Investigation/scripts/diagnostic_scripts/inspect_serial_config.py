import re

path = r'D:\Alok\MicroDoubleplane\MicroDoubleplane\MicroBalance DoublePlane.exe'
with open(path, 'rb') as f:
    data = f.read()

# Look for baud rates (9600, 19200, 38400, 57600, 115200)
for baud in [9600, 19200, 38400, 57600, 115200]:
    b_bytes = str(baud).encode('ascii')
    if b_bytes in data:
        print(f"Found baud rate string: {baud}")

# Look for COM port references
coms = re.findall(rb'COM\d+', data)
if coms:
    print(f"Found COM ports: {set(coms)}")

# Look for any IP or port strings
ips = re.findall(rb'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', data)
if ips:
    print(f"Found IPs: {set(ips)}")
