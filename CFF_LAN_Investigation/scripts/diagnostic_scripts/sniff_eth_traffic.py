import socket
import struct
import time

HOST = "192.168.137.1"

# Create raw socket to sniff all incoming IP packets on this interface
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
s.bind((HOST, 0))

# Include IP headers
s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# Enable promiscuous mode (SIO_RCVALL)
SIO_RCVALL = socket.SIO_RCVALL if hasattr(socket, 'SIO_RCVALL') else 0x98000001
s.ioctl(SIO_RCVALL, socket.RCVALL_ON)
s.settimeout(5.0)

print(f"Sniffing packets on {HOST} for 5 seconds...")

start_time = time.time()
seen_sources = set()

while time.time() - start_time < 5.0:
    try:
        data, addr = s.recvfrom(65535)
        # Parse IP header (first 20 bytes minimum)
        ip_header = data[:20]
        iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
        src_ip = socket.inet_ntoa(iph[8])
        dst_ip = socket.inet_ntoa(iph[9])
        proto = iph[6]
        
        if src_ip != HOST:
            key = (src_ip, dst_ip, proto)
            if key not in seen_sources:
                seen_sources.add(key)
                print(f"PACKET DETECTED: Src={src_ip} -> Dst={dst_ip} (Proto={proto}, Len={len(data)})")
    except socket.timeout:
        break
    except Exception as e:
        print("Sniff exception:", e)
        break

# Turn off promiscuous mode
try:
    s.ioctl(SIO_RCVALL, socket.RCVALL_OFF)
    s.close()
except:
    pass

if not seen_sources:
    print("No non-local IP packets captured in 5 seconds.")
else:
    print(f"Unique external traffic sources: {seen_sources}")
