import glob
import struct
import os

folder = r"c:\Users\alokp\Desktop\CFF\CFF_LAN_Investigation\samples\raw_balancing_records"
files = sorted(glob.glob(os.path.join(folder, "udp_dump_*_67.bin")))
print(f"Total DHCP dump files: {len(files)}")

def parse_dhcp(data):
    if len(data) < 240:
        return {'Error': 'Too short'}
    op, htype, hlen, hops, xid, secs, flags, ciaddr, yiaddr, siaddr, giaddr = struct.unpack('!BBBBIHH4s4s4s4s', data[:28])
    chaddr = data[28:28+hlen]
    mac = ':'.join(f'{b:02x}' for b in chaddr)
    
    options = {}
    i = 240
    while i < len(data):
        opt = data[i]
        if opt == 255:
            break
        if opt == 0:
            i += 1
            continue
        if i + 1 >= len(data):
            break
        opt_len = data[i+1]
        opt_val = data[i+2:i+2+opt_len]
        options[opt] = opt_val
        i += 2 + opt_len
        
    res = {'MAC': mac.upper(), 'xid': hex(xid)}
    msg_types = {1: 'DISCOVER', 2: 'OFFER', 3: 'REQUEST', 4: 'DECLINE', 5: 'ACK', 6: 'NAK', 7: 'RELEASE', 8: 'INFORM'}
    if 53 in options:
        res['MsgType'] = msg_types.get(options[53][0], str(options[53][0]))
    if 50 in options and len(options[50]) == 4:
        res['RequestedIP'] = '.'.join(str(b) for b in options[50])
    if 12 in options:
        res['Hostname'] = options[12].decode('latin-1', errors='ignore')
    if 60 in options:
        res['VendorClass'] = options[60].decode('latin-1', errors='ignore')
    return res

seen_macs = set()
for f in files:
    with open(f, 'rb') as fp:
        d = fp.read()
    info = parse_dhcp(d)
    mac = info.get('MAC')
    fname = os.path.basename(f)
    print(f"{fname} -> {info}")
