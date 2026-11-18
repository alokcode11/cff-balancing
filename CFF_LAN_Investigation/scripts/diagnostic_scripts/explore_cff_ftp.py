import ftplib, socket

TARGET_IP = "192.168.0.2"

print("=" * 60)
print(f"  EXPLORING CFF MACHINE FILES VIA FTP: {TARGET_IP}")
print("=" * 60)

# Test both anonymous and privileged logins
USERS_TO_TEST = [
    ("root", ""),
    ("root", "root"),
    ("root", "123456"),
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "mcgs"),
    ("mcgs", "mcgs"),
    ("mcgs", "123456"),
    ("anonymous", ""),
]

for u, p in USERS_TO_TEST:
    try:
        ftp = ftplib.FTP()
        ftp.connect(TARGET_IP, 21, timeout=3.0)
        ftp.login(u, p)
        print(f"\n[+] Logged in as: '{u}' (pwd='{p}')")
        print(f"    Current dir: {ftp.pwd()}")
        
        # Test Passive Mode first, then Active mode
        for pasv in [True, False]:
            mode = "PASV" if pasv else "PORT (Active)"
            ftp.set_pasv(pasv)
            try:
                items = []
                ftp.retrlines("LIST", items.append)
                print(f"    [{mode}] LIST count: {len(items)}")
                if items:
                    for item in items[:15]:
                        print(f"      {item}")
                    if len(items) > 15:
                        print(f"      ... and {len(items)-15} more items")
                    break
            except Exception as e:
                print(f"    [{mode}] LIST failed: {e}")

        # Try to change directory to common MCGS directories
        for d in ["/mcgs", "/flash", "/opt", "/home", "/root", "/mnt", "/udisk", "/var", "/tmp"]:
            try:
                ftp.cwd(d)
                items = []
                ftp.set_pasv(True)
                try:
                    ftp.retrlines("LIST", items.append)
                except Exception:
                    ftp.set_pasv(False)
                    ftp.retrlines("LIST", items.append)
                if items:
                    print(f"    Directory '{d}' exists with {len(items)} items:")
                    for it in items[:10]:
                        print(f"      {it}")
            except Exception:
                pass
        ftp.quit()
        if u in ("root", "admin", "mcgs"):
            break
    except ftplib.error_perm as ep:
        pass
    except Exception as e:
        print(f"[-] Login '{u}' error: {e}")

print("\n" + "=" * 60)
print("  FTP Exploration Complete.")
print("=" * 60)
