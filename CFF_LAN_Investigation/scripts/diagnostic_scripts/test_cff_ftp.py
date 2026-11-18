import ftplib, socket

TARGET_IP = "192.168.0.2"

print("=" * 60)
print(f"  CONNECTING TO CFF MACHINE FTP SERVER: {TARGET_IP}:21")
print("=" * 60)

# 1. Grab FTP Banner
try:
    s = socket.socket()
    s.settimeout(2.0)
    s.connect((TARGET_IP, 21))
    banner = s.recv(1024).decode('utf-8', errors='ignore')
    s.close()
    print(f"FTP SERVER BANNER:\n{banner.strip()}\n")
except Exception as e:
    print("Could not get banner:", e)

# 2. Try common factory credentials
CREDENTIALS = [
    ("anonymous", ""),
    ("anonymous", "guest"),
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "mcgs"),
    ("admin", "888888"),
    ("admin", "000000"),
    ("admin", ""),
    ("root", "root"),
    ("root", ""),
    ("root", "123456"),
    ("mcgs", "mcgs"),
    ("mcgs", "123456"),
    ("user", "user"),
    ("guest", "guest"),
]

success_ftp = None
working_user = None
working_pass = None

for u, p in CREDENTIALS:
    try:
        ftp = ftplib.FTP()
        ftp.connect(TARGET_IP, 21, timeout=2.0)
        ftp.login(u, p)
        print(f"  >>> SUCCESSFUL LOGIN! User='{u}', Pass='{p}' <<<")
        success_ftp = ftp
        working_user = u
        working_pass = p
        break
    except ftplib.error_perm as ep:
        pass
    except Exception as e:
        print(f"Error testing ({u}): {e}")
        break

if success_ftp:
    print("\n" + "=" * 60)
    print(f"  FTP AUTHENTICATION GRANTED! (User: {working_user})")
    print("=" * 60)
    try:
        print("Current Directory:", success_ftp.pwd())
        print("\nFiles in Root Directory:")
        lines = []
        success_ftp.retrlines("LIST", lines.append)
        for line in lines:
            print("  ", line)
    except Exception as e:
        print("LIST error:", e)
        try:
            print("NLST fallback:", success_ftp.nlst())
        except Exception as e2:
            print("NLST error:", e2)
    success_ftp.quit()
else:
    print("\nNone of the common credentials logged in automatically.")
    print("Please check if the machine touch screen shows an FTP username/password in Network Settings.")
