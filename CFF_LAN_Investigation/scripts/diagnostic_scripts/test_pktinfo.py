import socket
import struct

# Check if IP_PKTINFO is available
IP_PKTINFO = 19 # Windows IP_PKTINFO = 19

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
try:
    s.setsockopt(socket.IPPROTO_IP, IP_PKTINFO, 1)
    s.bind(('0.0.0.0', 67))
    print("Bound with IP_PKTINFO!")
    s.settimeout(3.0)
    data, ancdata, flags, addr = s.recvmsg(4096, 512)
    for cmsg_level, cmsg_type, cmsg_data in ancdata:
        if cmsg_level == socket.IPPROTO_IP and cmsg_type == IP_PKTINFO:
            # struct in_pktinfo { unsigned int ipi_ifindex; struct in_addr ipi_addr; }
            ifindex, addr_b = struct.unpack("=I4s", cmsg_data[:8])
            print(f"Packet received on ifIndex: {ifindex} (Interface 21=Ethernet, 11=Wi-Fi)")
except Exception as e:
    print("Error:", e)
finally:
    s.close()
