import socket

TARGET_IP = "192.168.0.2"

def grab(port):
    try:
        s = socket.socket()
        s.settimeout(2.0)
        s.connect((TARGET_IP, port))
        # Wait for banner or send newline
        try:
            banner = s.recv(1024)
        except Exception:
            s.send(b"\r\n")
            banner = s.recv(1024)
        s.close()
        return repr(banner)
    except Exception as e:
        return f"Error: {e}"

print("=" * 60)
print(f"  PROBING OPEN PORTS ON {TARGET_IP}")
print("=" * 60)
print(f"Port 21 (FTP):  {grab(21)}")
print(f"Port 22 (SSH):  {grab(22)}")
print(f"Port 127:       {grab(127)}")
print("=" * 60)
