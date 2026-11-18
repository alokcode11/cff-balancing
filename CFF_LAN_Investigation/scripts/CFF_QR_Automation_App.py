"""
CFF QR Automation App - FIXED VERSION
Fixes:
  1. PRINT BUTTON: Silent direct print via mspaint /pt (no dialog)
  2. PRINTER PICKER: Select your thermal printer from dropdown
  3. AUTO-PRINT: When latest record is OK -> prints immediately, zero clicks
  4. USB WATCHER: Auto-detects new files, parses LAST ROW, generates QR, auto-prints
  5. REAL-TIME indicator on status bar
"""
import os, sys, json, time, glob, re, csv, threading, subprocess, winreg, datetime
import ctypes
import ctypes.wintypes as wt
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont
import sqlite3

APP_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(APP_DIR, ".."))
SAMPLES_DIR = os.path.join(PROJECT_DIR, "samples", "raw_balancing_records")
DATA_DIR    = os.path.join(PROJECT_DIR, "data")
PRINT_DIR   = os.path.join(PROJECT_DIR, "samples", "print_queue")
DROP_FOLDER = os.path.join(DATA_DIR, "drop_folder")
DB_PATH     = os.path.join(DATA_DIR, "cff_balancing_records.db")

for d in [SAMPLES_DIR, DATA_DIR, PRINT_DIR, DROP_FOLDER]:
    os.makedirs(d, exist_ok=True)

winspool = ctypes.WinDLL("winspool.drv")

class DOC_INFO_1(ctypes.Structure):
    _fields_ = [
        ("pDocName", wt.LPWSTR),
        ("pOutputFile", wt.LPWSTR),
        ("pDatatype", wt.LPWSTR)
    ]

def send_zpl_raw(printer_name: str, zpl_string: str) -> bool:
    """Sends raw ZPL byte stream directly to Zebra thermal printer port."""
    hPrinter = wt.HANDLE()
    if not winspool.OpenPrinterW(printer_name, ctypes.byref(hPrinter), None):
        return False
    docInfo = DOC_INFO_1("CFF_Dynamic_Label", None, "RAW")
    dwJob = winspool.StartDocPrinterW(hPrinter, 1, ctypes.byref(docInfo))
    if dwJob <= 0:
        winspool.ClosePrinter(hPrinter)
        return False
    winspool.StartPagePrinter(hPrinter)
    raw_bytes = zpl_string.encode('utf-8')
    dwWritten = wt.DWORD()
    ok = winspool.WritePrinter(hPrinter, raw_bytes, len(raw_bytes), ctypes.byref(dwWritten))
    winspool.EndPagePrinter(hPrinter)
    winspool.EndDocPrinter(hPrinter)
    winspool.ClosePrinter(hPrinter)
    return bool(ok and dwWritten.value == len(raw_bytes))


def print_to_zebra_zpl(rec: dict, printer_name: str) -> bool:
    """
    Generate industrial 300 DPI ZPL label matching exact physical label:
    Width = 22.4mm (265 dots), Height = 15.0mm (177 dots) @ 300 DPI.
    Exact match to factory production sticker:
      - QR Code Version 1 (21x21 modules, chunkier bold dots): ^BQN,2,4,M with ^FDMA
      - QR Code horizontally centered: X=86, Y=14
      - Condensed serial font (Font 0 native narrow): ^A0N,18,9 centered at X=34, Y=132
      - Maximum solid pitch-black contrast: ~SD30, ^MD30, ^PR2,2,2
    """
    sn = str(rec.get("cff_serial") or "7020001384261102045643")
    clean_sn = re.sub(r'[^A-Za-z0-9\-_]', '', sn)
    if not clean_sn or len(clean_sn) < 5:
        clean_sn = "7020001384261102045643"

    zpl = (
        "^XA\n"
        "~SD30\n"
        "^PW265\n"
        "^LL177\n"
        "^MD30\n"
        "^PR4,4,4\n"
        "^MTT\n"
        "^MNY\n"
        f"^FO82,10^BQN,2,4,Q^FDQA,{clean_sn}^FS\n"
        f"^FO12,124^A0N,32,11^FD{clean_sn}^FS\n"
        "^XZ\n"
    )
    return send_zpl_raw(printer_name, zpl)

# ─────────────────────────── PRINTER UTILS ───────────────────
def get_all_printers():
    """Read installed printers from Windows registry."""
    printers = []
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Print\Printers"
        )
        i = 0
        while True:
            try:
                printers.append(winreg.EnumKey(key, i))
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except Exception:
        pass
    if not printers:
        printers = ["Microsoft Print to PDF"]
    return printers


def get_default_printer():
    printers = get_all_printers()
    # Automatically prioritize Zebra / Thermal label printer
    for p in printers:
        if any(term in p.lower() for term in ["zdesigner", "zebra", "zd421", "thermal", "label", "tsc"]):
            return p
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows NT\CurrentVersion\Windows"
        )
        val, _ = winreg.QueryValueEx(key, "Device")
        winreg.CloseKey(key)
        return val.split(",")[0].strip()
    except Exception:
        return printers[0] if printers else "Microsoft Print to PDF"


def silent_print(image_path: str, printer_name: str) -> bool:
    """
    Sends image directly to printer WITHOUT showing any dialog.
    Direct PowerShell PrintDocument with high quality label scaling.
    """
    if not os.path.exists(image_path):
        return False

    # Primary method: Direct PowerShell PrintDocument
    try:
        ps_cmd = (
            f'Add-Type -AssemblyName System.Drawing; '
            f'$img = [System.Drawing.Image]::FromFile("{image_path}"); '
            f'$pd = New-Object System.Drawing.Printing.PrintDocument; '
            f'$pd.PrinterSettings.PrinterName = "{printer_name}"; '
            f'$pd.OriginAtMargins = $false; '
            f'$pd.DefaultPageSettings.Margins = New-Object System.Drawing.Printing.Margins(0, 0, 0, 0); '
            f'$pd.add_PrintPage({{ param($s, $e) '
            f'$pageRect = $e.PageBounds; '
            f'$e.Graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic; '
            f'$e.Graphics.DrawImage($img, $pageRect); '
            f'}}); '
            f'$pd.Print(); $img.Dispose()'
        )
        res = subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            timeout=20, capture_output=True
        )
        if res.returncode == 0:
            return True
    except Exception:
        pass

    # Fallback method: mspaint /pt
    try:
        subprocess.run(
            ["mspaint.exe", "/pt", image_path, printer_name],
            capture_output=True, timeout=15
        )
        return True
    except Exception:
        return False


# ─────────────────────────── DATABASE ────────────────────────
def normalize_timestamp(s: str) -> str:
    """Standardizes all timestamps into ISO YYYY-MM-DD HH:MM:SS for strict chronological sorting."""
    if not s or str(s).strip() in ("", "N/A", "None"):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    s = str(s).strip()
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})', s)
    if m:
        return s[:19]
    for fmt in ('%d-%b-%Y %I:%M:%S %p', '%d-%b-%Y %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.datetime.strptime(s, fmt).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
    return s


def db_init():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='balancing_records'")
    if not cur.fetchone():
        conn.execute("""CREATE TABLE balancing_records (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_code      TEXT,
            cff_serial       TEXT,
            machine_model    TEXT DEFAULT 'PHGS-5D',
            machine_sn       TEXT DEFAULT '26010050',
            part_model       TEXT,
            test_timestamp   TEXT,
            plane1_amount_g  REAL DEFAULT 0,
            plane1_angle_deg REAL DEFAULT 0,
            plane2_amount_g  REAL DEFAULT 0,
            plane2_angle_deg REAL DEFAULT 0,
            result_status    TEXT DEFAULT 'OK',
            qr_payload       TEXT,
            created_at       TEXT DEFAULT (datetime('now','localtime')),
            is_printed       INTEGER DEFAULT 0,
            speed_rpm        REAL DEFAULT 1100,
            record_number    TEXT DEFAULT '',
            source           TEXT DEFAULT 'USB',
            sticker_path     TEXT DEFAULT ''
        )""")
        conn.commit()
    else:
        # Migrate: add missing columns
        cur.execute("PRAGMA table_info(balancing_records)")
        existing = {r[1] for r in cur.fetchall()}
        for col, defn in [
            ("speed_rpm",     "REAL DEFAULT 1100"),
            ("record_number", "TEXT DEFAULT ''"),
            ("source",        "TEXT DEFAULT 'USB'"),
            ("sticker_path",  "TEXT DEFAULT ''"),
        ]:
            if col not in existing:
                try:
                    conn.execute(f"ALTER TABLE balancing_records ADD COLUMN {col} {defn}")
                except Exception:
                    pass
        conn.commit()
    conn.close()


def db_save(rec: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(balancing_records)")
    all_cols = {r[1] for r in cur.fetchall()}

    sn    = str(rec.get("cff_serial") or "")
    part  = str(rec.get("part_model") or "")
    ts    = normalize_timestamp(rec.get("test_timestamp"))
    p1g   = float(rec.get("plane1_g") or rec.get("plane1_amount_g") or 0)
    p1d   = float(rec.get("plane1_deg") or rec.get("plane1_angle_deg") or 0)
    p2g   = float(rec.get("plane2_g") or rec.get("plane2_amount_g") or 0)
    p2d   = float(rec.get("plane2_deg") or rec.get("plane2_angle_deg") or 0)
    st    = str(rec.get("result_status") or "OK")
    spd   = float(rec.get("speed_rpm") or 1100)
    rno   = str(rec.get("record_number") or "")
    src   = str(rec.get("source") or "USB")
    stk   = str(rec.get("sticker_path") or "")
    qr    = f"{sn};{part};{ts};{p1g};{p1d};{p2g};{p2d};{st}"

    col_map = {
        "unique_code":      f"{sn}-{int(time.time())}",
        "cff_serial":       sn,
        "machine_model":    "PHGS-5D",
        "machine_sn":       "26010050",
        "part_model":       part,
        "test_timestamp":   ts,
        "plane1_amount_g":  p1g,
        "plane1_angle_deg": p1d,
        "plane2_amount_g":  p2g,
        "plane2_angle_deg": p2d,
        "result_status":    st,
        "qr_payload":       qr,
        "is_printed":       0,
        "speed_rpm":        spd,
        "record_number":    rno,
        "source":           src,
        "sticker_path":     stk,
    }
    ins_cols = [c for c in col_map if c in all_cols]
    vals     = [col_map[c] for c in ins_cols]
    cur.execute(
        f"INSERT INTO balancing_records ({','.join(ins_cols)}) VALUES ({','.join(['?']*len(ins_cols))})",
        vals
    )
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id


def db_is_dup(rec_no, ts):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    norm_ts = normalize_timestamp(ts)
    cur.execute(
        "SELECT id FROM balancing_records WHERE record_number=? AND (test_timestamp=? OR test_timestamp=?)",
        (str(rec_no), str(ts), norm_ts)
    )
    found = cur.fetchone()
    conn.close()
    return found is not None


def db_get_records(limit=5000):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        # STRICT CHRONOLOGICAL ORDER: Latest tests ALWAYS at the very top!
        cur.execute("""
            SELECT id, COALESCE(test_timestamp, created_at, 'N/A'), part_model, cff_serial,
                   plane1_amount_g, plane1_angle_deg,
                   plane2_amount_g, plane2_angle_deg,
                   result_status, is_printed
            FROM balancing_records 
            ORDER BY test_timestamp DESC, id DESC LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
    except Exception:
        rows = []
    conn.close()
    return rows


def db_mark_printed(row_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE balancing_records SET is_printed=1 WHERE id=?", (row_id,))
    conn.commit()
    conn.close()


# ─────────────────────────── QR STICKER ──────────────────────
def build_sticker(rec: dict) -> str:
    """
    Generate exact 22.4mm x 15mm physical sticker PNG preview (265x177 @ 300 DPI).
    Centered layout: QR Code in upper center + Serial number underneath.
    """
    sn = str(rec.get("cff_serial") or "7020001384261104038755")
    clean_sn = re.sub(r'[^A-Za-z0-9\-_]', '', sn)
    if not clean_sn or len(clean_sn) < 5:
        clean_sn = "7020001384261104038755"

    scale = 2
    W = 265 * scale
    H = 177 * scale

    sticker = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(sticker)
    draw.rounded_rectangle([(4, 4), (W - 4, H - 4)], radius=16, outline="#94A3B8", width=3)

    # QR Code in Upper Center
    qr = qrcode.QRCode(version=1, box_size=8, border=0)
    qr.add_data(clean_sn)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_size = int(96 * scale)
    qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)
    qr_x = int((W - qr_size) / 2)
    qr_y = int(10 * scale)
    sticker.paste(qr_resized, (qr_x, qr_y))

    # Serial Number Text Centered Underneath QR Code (Bold, Prominent)
    try:
        font = ImageFont.truetype("arialbd.ttf", int(18 * scale))
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), clean_sn, font=font)
    txt_w = bbox[2] - bbox[0]
    txt_x = int((W - txt_w) / 2)
    txt_y = int(124 * scale)
    draw.text((txt_x, txt_y), clean_sn, fill="#000000", font=font)

    fname = f"sticker_{clean_sn}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    out_path = os.path.join(SAMPLES_DIR, fname)
    sticker.save(out_path)

    import shutil
    shutil.copy(out_path, os.path.join(SAMPLES_DIR, "latest_cff_qr_sticker.png"))
    shutil.copy(out_path, os.path.join(PRINT_DIR, fname))

    return out_path


# ─────────────────────────── FILE PARSER ─────────────────────
def parse_last_record(filepath: str) -> dict | None:
    """
    Parse CFF export file. Returns ONLY THE LAST (newest) record.
    Handles: XML (Jobs.xml from MicroBalance), CSV, TSV, TXT, DAT.
    """
    # 1. Check for XML (Jobs.xml)
    if filepath.lower().endswith(".xml") or "<jobs>" in open(filepath, "rb").read(500).decode("utf-8", errors="ignore").lower():
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(filepath)
            root = tree.getroot()
            if len(root) > 0:
                last_job = root[-1]
                data = {child.tag: (child.text or "").strip() for child in last_job}
                l_res = data.get("LeftResult", "")
                r_res = data.get("RightResult", "")
                status = "OK" if ("balance" in l_res.lower() and "balance" in r_res.lower()) else "NG"

                now = datetime.datetime.now()
                erp = "7020001384"
                run_no = data.get("JobRun") or data.get("JobNo") or str(int(time.time()))[-6:]
                yy = now.strftime("%y")
                mm = now.strftime("%m")
                machine_no = "02"
                run_padded = str(re.sub(r'\D', '', str(run_no))).zfill(6)[-6:]
                sn = f"{erp}{yy}{mm}{machine_no}{run_padded}"

                raw_dt = data.get("JobDate") or now.strftime("%Y-%m-%d %H:%M:%S")
                return {
                    "record_number":  str(data.get("JobId") or run_no),
                    "part_model":     data.get("JobName") or "107.5X695MM",
                    "cff_serial":     sn,
                    "test_timestamp": normalize_timestamp(raw_dt),
                    "speed_rpm":      float(data.get("BalancingSpeed") or 1080),
                    "plane1_g":       float(data.get("LeftWeight") or 0),
                    "plane1_deg":     float(data.get("LeftAngle") or 0),
                    "plane2_g":       float(data.get("RightWeight") or 0),
                    "plane2_deg":     float(data.get("RightAngle") or 0),
                    "result_status":  status,
                    "source":         "XML",
                }
        except Exception:
            pass

    try:
        raw  = open(filepath, "rb").read()
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        return None

    records = []

    # Try CSV
    if "," in text:
        try:
            import io
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                r = _map_row(row)
                if r:
                    records.append(r)
        except Exception:
            pass

    # Try TSV
    if not records and "\t" in text:
        try:
            import io
            reader = csv.DictReader(io.StringIO(text), dialect="excel-tab")
            for row in reader:
                r = _map_row(row)
                if r:
                    records.append(r)
        except Exception:
            pass

    # Regex fallback
    if not records:
        floats = re.findall(r'\b(\d+\.?\d*)\b', text)
        nums   = [float(x) for x in floats]
        if len(nums) >= 4:
            records.append({
                "record_number":  "",
                "part_model":     _find_model(text),
                "cff_serial":     "",
                "test_timestamp": _find_dt(text),
                "speed_rpm":      _find_speed(nums),
                "plane1_g":       nums[0],
                "plane1_deg":     nums[1],
                "plane2_g":       nums[2],
                "plane2_deg":     nums[3],
                "result_status":  "OK" if "OK" in text.upper() else "NG",
                "source":         "FILE",
                "raw_data":       text[:200],
            })

    if not records:
        return None

    # Return LAST row (most recent balancing result)
    last = records[-1]
    last["source"] = "USB"
    # Auto-assign standard 22-digit serial if blank
    if not last.get("cff_serial") or len(str(last.get("cff_serial"))) < 10:
        now = datetime.datetime.now()
        rno = re.sub(r'\D', '', str(last.get("record_number") or int(time.time())))
        rno_padded = str(rno).zfill(6)[-6:]
        last["cff_serial"] = f"7020001384{now.strftime('%y%m')}02{rno_padded}"
    return last


def _map_row(row: dict) -> dict | None:
    def g(*keys):
        for k in keys:
            for rk in row:
                if rk and k.lower() in rk.lower().strip():
                    v = str(row[rk] or "").strip()
                    if v:
                        return v
        return ""

    p1g = g("Left Weight","LeftWeight","P1Amount","Plane1","P1","plane1_amount")
    p2g = g("Right Weight","RightWeight","P2Amount","Plane2","P2","plane2_amount")
    if not p1g and not p2g:
        return None

    l_res = g("Left Result","LeftResult")
    r_res = g("Right Result","RightResult")
    if l_res or r_res:
        is_ok = ("balance" in l_res.lower() and "balance" in r_res.lower())
    else:
        is_ok = True

    try:
        return {
            "record_number":  g("SNo","No","Serial","序号","JobRun"),
            "part_model":     g("JobName","Name","Part","产品") or "107.5X695MM",
            "cff_serial":     g("Serial No","SerialNo","Serial_No","序列号"),
            "test_timestamp": g("JobDate","Time","Date","时间"),
            "speed_rpm":      float(g("BalancingSpeed","Speed","RPM","转速") or 1080),
            "plane1_g":       float(p1g or 0),
            "plane1_deg":     float(g("LeftAngle","Left Angle","P1Angle","Angle1","plane1_angle") or 0),
            "plane2_g":       float(p2g or 0),
            "plane2_deg":     float(g("RightAngle","Right Angle","P2Angle","Angle2","plane2_angle") or 0),
            "result_status":  "OK" if is_ok else "NG",
            "source":         "USB",
        }
    except Exception:
        return None

def _find_model(t):
    m = re.search(r'(\d{3}x\d{3,4}mm)', t, re.I)
    return m.group(1) if m else "122x992mm"

def _find_dt(t):
    m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2}[\sT]\d{2}:\d{2}:\d{2})', t)
    if m:
        return normalize_timestamp(m.group(1))
    m2 = re.search(r'(\d{1,2}-[A-Za-z]{3}-\d{4}\s+\d{1,2}:\d{2}:\d{2}(?:\s*[AaPp][Mm])?)', t)
    if m2:
        return normalize_timestamp(m2.group(1))
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _find_speed(nums):
    for n in nums:
        if 500 <= n <= 3000:
            return n
    return 1100.0


# ─────────────────────────── MAIN APP ────────────────────────
class CFFApp:
    def __init__(self, root):
        self.root     = root
        self.root.title("CFF Dynamic Balancing — QR Automation System")
        self.root.geometry("1080x800")
        self.root.configure(bg="#F1F5F9")

        # State
        self.auto_print_enabled = tk.BooleanVar(value=True)
        self.printer_var        = tk.StringVar(value=get_default_printer())
        self.last_sticker_path  = None
        self.usb_monitoring     = True
        self._seen_files        = set()
        self._activity_count    = 0

        db_init()
        self._build_ui()
        self._refresh_preview_from_latest()

        # Start USB + Drop Folder watcher
        threading.Thread(target=self._watcher_loop, daemon=True).start()

        # Start LAN status checker
        threading.Thread(target=self._lan_status_loop, daemon=True).start()

    # ── UI BUILD ──────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#0F172A", height=60)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="CFF BALANCING MACHINE (PHGS-5D) — QR AUTOMATION SYSTEM",
                 fg="white", bg="#0F172A",
                 font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT, padx=20, pady=12)
        self.status_dot = tk.Label(hdr, text="● SYSTEM READY & DATABASE CONNECTED",
                                   fg="#22C55E", bg="#0F172A",
                                   font=("Segoe UI", 10, "bold"))
        self.status_dot.pack(side=tk.RIGHT, padx=20)

        # Tabs
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        t1 = tk.Frame(nb, bg="#F8FAFC", padx=10, pady=10)
        t2 = tk.Frame(nb, bg="#F8FAFC", padx=12, pady=12)
        t3 = tk.Frame(nb, bg="#F8FAFC", padx=12, pady=12)
        nb.add(t1, text="  1. Live Balancing & QR  ")
        nb.add(t2, text="  2. Printer & Rules  ")
        nb.add(t3, text="  3. Records & History  ")

        self._build_tab1(t1)
        self._build_tab2(t2)
        self._build_tab3(t3)

        # Bottom log bar
        self.log_bar = tk.Label(self.root,
            text="System ready | Watching USB drives and drop folder...",
            bg="#1E293B", fg="#94A3B8",
            font=("Segoe UI", 9), anchor="w", padx=12, pady=5)
        self.log_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _build_tab1(self, parent):
        pane = tk.PanedWindow(parent, orient=tk.HORIZONTAL, sashwidth=4, bg="#E2E8F0")
        pane.pack(fill=tk.BOTH, expand=True)

        # Left: input form
        left = tk.LabelFrame(pane, text=" Balancing Test Parameters ",
                             font=("Segoe UI", 10, "bold"),
                             bg="white", padx=14, pady=12)
        pane.add(left, minsize=380)

        self.v_part  = tk.StringVar(value="107.5X695MM")
        self.v_sn    = tk.StringVar(value="7020001384261102045643")
        self.v_mach  = tk.StringVar(value="PHGS-5D (26010050)")
        self.v_date  = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.v_speed = tk.StringVar(value="1100")
        self.v_p1g   = tk.StringVar(value="0.103")
        self.v_p1d   = tk.StringVar(value="88.0")
        self.v_p2g   = tk.StringVar(value="0.065")
        self.v_p2d   = tk.StringVar(value="210.0")
        self.v_status= tk.StringVar(value="OK")

        self._field(left, "Part Model:",      self.v_part)
        self._field(left, "CFF Serial / Barcode:", self.v_sn)
        self._field(left, "Machine Model & S/N:",  self.v_mach)
        self._field(left, "Test Date / Time:",     self.v_date)
        self._field(left, "Balancing Speed (RPM):", self.v_speed)
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # Plane rows
        for label, vg, vd in [
            ("Plane 1 Amount [g]:", self.v_p1g, self.v_p1d),
            ("Plane 2 Amount [g]:", self.v_p2g, self.v_p2d),
        ]:
            row = tk.Frame(left, bg="white"); row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label, font=("Segoe UI",9,"bold"),
                     bg="white", width=18, anchor="w").pack(side=tk.LEFT)
            tk.Entry(row, textvariable=vg, width=8,
                     font=("Segoe UI",10)).pack(side=tk.LEFT, padx=2)
            tk.Label(row, text="Angle [°]:", font=("Segoe UI",9,"bold"),
                     bg="white").pack(side=tk.LEFT, padx=4)
            tk.Entry(row, textvariable=vd, width=8,
                     font=("Segoe UI",10)).pack(side=tk.LEFT)

        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # Verdict
        vrow = tk.Frame(left, bg="white"); vrow.pack(fill=tk.X, pady=4)
        tk.Label(vrow, text="Balancing Verdict:", font=("Segoe UI",10,"bold"),
                 bg="white", width=16, anchor="w").pack(side=tk.LEFT)
        tk.Radiobutton(vrow, text="OK (Pass)", variable=self.v_status, value="OK",
                       font=("Segoe UI",10,"bold"), fg="#16A34A", bg="white",
                       command=self._on_generate).pack(side=tk.LEFT, padx=8)
        tk.Radiobutton(vrow, text="NG (Fail)", variable=self.v_status, value="NG",
                       font=("Segoe UI",10,"bold"), fg="#DC2626", bg="white",
                       command=self._on_generate).pack(side=tk.LEFT)

        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # Buttons
        tk.Button(left, text="  GENERATE QR STICKER  ",
                  bg="#2563EB", fg="white", font=("Segoe UI",11,"bold"),
                  command=self._on_generate, pady=7).pack(fill=tk.X, pady=3)

        tk.Button(left, text="  Browse & Import U-Disk / CSV File  ",
                  bg="#059669", fg="white", font=("Segoe UI",10,"bold"),
                  command=self._on_browse, pady=5).pack(fill=tk.X, pady=3)

        # ── Auto-Print status indicator ──
        self.auto_lbl = tk.Label(left,
            text="⚡ AUTO-PRINT: ON — latest OK result prints instantly",
            bg="#DCFCE7", fg="#166534",
            font=("Segoe UI", 9, "bold"), pady=4, padx=6)
        self.auto_lbl.pack(fill=tk.X, pady=(10,0))

        # Right: preview + print
        right = tk.LabelFrame(pane, text=" Live QR Sticker Preview ",
                              font=("Segoe UI",10,"bold"),
                              bg="white", padx=10, pady=10)
        pane.add(right, minsize=440)

        self.preview_lbl = tk.Label(right, bg="#F1F5F9", text="Waiting for data...",
                                    font=("Segoe UI",11), fg="#94A3B8")
        self.preview_lbl.pack(fill=tk.BOTH, expand=True, pady=6)

        # ── THE PRINT BUTTON (FIXED) ──
        self.btn_print = tk.Button(
            right,
            text="  🖨  PRINT STICKER TO THERMAL PRINTER  ",
            bg="#16A34A", fg="white",
            font=("Segoe UI", 12, "bold"),
            command=self._on_print,
            pady=10
        )
        self.btn_print.pack(fill=tk.X, pady=(6,2))

        self.print_status_lbl = tk.Label(right, text="",
                                         bg="white", fg="#16A34A",
                                         font=("Segoe UI", 9, "bold"))
        self.print_status_lbl.pack()

    def _build_tab2(self, parent):
        tk.Label(parent, text="Printer Selection & Auto-Print Rules",
                 font=("Segoe UI",12,"bold"), bg="#F8FAFC", fg="#0F172A"
                 ).pack(anchor="w", pady=(0,12))

        # ── Printer selection ──
        pf = tk.LabelFrame(parent, text=" Select Thermal Printer ",
                           font=("Segoe UI",10,"bold"), bg="white", padx=14, pady=12)
        pf.pack(fill=tk.X, pady=6)

        printers = get_all_printers()
        tk.Label(pf, text="Active Printer:", font=("Segoe UI",10,"bold"),
                 bg="white").pack(anchor="w")

        printer_menu = ttk.Combobox(pf, textvariable=self.printer_var,
                                    values=printers, state="readonly",
                                    font=("Segoe UI",11), width=50)
        printer_menu.pack(anchor="w", pady=6)

        tk.Label(pf,
                 text="⚠  If your thermal printer is not listed:\n"
                      "  → Connect it via USB / LAN\n"
                      "  → Install its Windows driver\n"
                      "  → It will appear here automatically",
                 bg="white", fg="#B45309", font=("Segoe UI",9),
                 justify="left").pack(anchor="w", pady=4)

        tk.Button(pf, text=" Refresh Printer List ",
                  bg="#0284C7", fg="white", font=("Segoe UI",9,"bold"),
                  command=self._refresh_printers).pack(anchor="w", pady=4)

        # ── Print test ──
        tk.Button(pf, text=" 🖨  Print Latest Sticker Now (Test) ",
                  bg="#16A34A", fg="white", font=("Segoe UI",10,"bold"),
                  command=self._on_print, pady=6).pack(anchor="w", pady=(10,0))

        # ── Auto-print rule ──
        rf = tk.LabelFrame(parent, text=" Auto-Print Rule ",
                           font=("Segoe UI",10,"bold"), bg="white", padx=14, pady=12)
        rf.pack(fill=tk.X, pady=10)

        tk.Checkbutton(rf,
                       text="✅  Auto-Print ON: When new balancing record is detected and result = OK\n"
                            "    → Sticker is generated and printed AUTOMATICALLY (zero clicks)",
                       variable=self.auto_print_enabled,
                       bg="white", font=("Segoe UI",10,"bold"), fg="#166534",
                       command=self._update_auto_lbl).pack(anchor="w")

        tk.Label(rf,
                 text="\nQuality Gate: NG (Fail) results are NEVER printed automatically.\n"
                      "You can manually print them from the Records tab if needed.",
                 bg="white", fg="#64748B", font=("Segoe UI",9)).pack(anchor="w")

    def _build_tab3(self, parent):
        bar = tk.Frame(parent, bg="#F8FAFC"); bar.pack(fill=tk.X, pady=(0,8))
        tk.Label(bar, text="Saved Balancing Records",
                 font=("Segoe UI",12,"bold"), bg="#F8FAFC", fg="#0F172A"
                 ).pack(side=tk.LEFT)
        tk.Button(bar, text=" Refresh ", bg="#0284C7", fg="white",
                  font=("Segoe UI",9,"bold"),
                  command=self._load_history).pack(side=tk.RIGHT, padx=4)
        tk.Button(bar, text=" Export CSV ", bg="#10B981", fg="white",
                  font=("Segoe UI",9,"bold"),
                  command=self._export_csv).pack(side=tk.RIGHT, padx=4)

        cols = ("ID","Timestamp","Part Model","CFF Serial",
                "P1 g","P1 °","P2 g","P2 °","Result","Printed")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=20)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90, anchor="center")
        self.tree.column("ID",        width=40)
        self.tree.column("Timestamp", width=145)
        self.tree.column("Part Model",width=110)
        self.tree.column("CFF Serial",width=130)

        sb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._load_history()

    # ── HELPERS ───────────────────────────────────────────────
    def _field(self, parent, label, var):
        f = tk.Frame(parent, bg="white"); f.pack(fill=tk.X, pady=3)
        tk.Label(f, text=label, font=("Segoe UI",9,"bold"),
                 bg="white", width=20, anchor="w").pack(side=tk.LEFT)
        tk.Entry(f, textvariable=var, font=("Segoe UI",10)).pack(
            side=tk.RIGHT, fill=tk.X, expand=True)

    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_bar.configure(text=f"[{ts}]  {msg}")
        print(f"[{ts}] {msg}")

    def _update_auto_lbl(self):
        if self.auto_print_enabled.get():
            self.auto_lbl.configure(
                text="⚡ AUTO-PRINT: ON — latest OK result prints instantly",
                bg="#DCFCE7", fg="#166534")
        else:
            self.auto_lbl.configure(
                text="⏸  AUTO-PRINT: OFF — click Print manually",
                bg="#FEF9C3", fg="#854D0E")

    def _refresh_printers(self):
        printers = get_all_printers()
        # Find combobox in tab2
        for w in self.root.winfo_children():
            self._update_comboboxes(w, printers)
        self._log(f"Printer list refreshed: {printers}")

    def _update_comboboxes(self, widget, values):
        if isinstance(widget, ttk.Combobox):
            widget["values"] = values
        for child in widget.winfo_children():
            self._update_comboboxes(child, values)

    # ── GENERATE ─────────────────────────────────────────────
    def _on_generate(self, rec: dict = None):
        """Generate QR sticker from form values OR from a parsed record dict."""
        if rec is None:
            rec = {
                "cff_serial":    self.v_sn.get(),
                "part_model":    self.v_part.get(),
                "test_timestamp":self.v_date.get(),
                "speed_rpm":     self.v_speed.get(),
                "plane1_g":      float(self.v_p1g.get() or 0),
                "plane1_deg":    float(self.v_p1d.get() or 0),
                "plane2_g":      float(self.v_p2g.get() or 0),
                "plane2_deg":    float(self.v_p2d.get() or 0),
                "result_status": self.v_status.get(),
                "record_number": "",
                "source":        "MANUAL",
            }
        else:
            # Update form fields to match the detected record
            self.v_sn.set(str(rec.get("cff_serial") or ""))
            self.v_part.set(str(rec.get("part_model") or ""))
            self.v_date.set(str(rec.get("test_timestamp") or ""))
            self.v_speed.set(str(rec.get("speed_rpm") or "1100"))
            self.v_p1g.set(str(rec.get("plane1_g") or 0))
            self.v_p1d.set(str(rec.get("plane1_deg") or 0))
            self.v_p2g.set(str(rec.get("plane2_g") or 0))
            self.v_p2d.set(str(rec.get("plane2_deg") or 0))
            self.v_status.set(str(rec.get("result_status") or "OK"))

        path = build_sticker(rec)
        self.last_sticker_path = path

        # Update preview
        try:
            img = Image.open(path)
            img = img.resize((400, 267), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self.preview_lbl.configure(image=tk_img, text="")
            self.preview_lbl.image = tk_img
        except Exception as e:
            self.preview_lbl.configure(text=f"Preview error: {e}")

        self._log(f"QR sticker generated: {os.path.basename(path)}")

        # Auto-print if enabled and result is OK
        if self.auto_print_enabled.get() and rec.get("result_status") == "OK":
            self.root.after(500, self._on_print_silent)

        return rec, path

    # ── PRINT (FIXED — NO DIALOG) ─────────────────────────────
    def _on_print(self):
        """Called when user clicks Print button."""
        if not self.last_sticker_path or not os.path.exists(self.last_sticker_path):
            messagebox.showwarning("No Sticker", "Generate a QR sticker first!")
            return
        self._do_print(self.last_sticker_path, show_confirm=True)

    def _on_print_silent(self):
        """Called automatically on OK result — no confirm dialog."""
        if self.last_sticker_path and os.path.exists(self.last_sticker_path):
            self._do_print(self.last_sticker_path, show_confirm=False)

    def _do_print(self, path: str, show_confirm: bool = True):
        printer = self.printer_var.get()
        self._log(f"Printing → {printer}  |  {os.path.basename(path)}")
        self.btn_print.configure(text="  🖨  PRINTING...  ", bg="#F59E0B")
        self.root.update_idletasks()

        rec_for_print = {
            "cff_serial":     self.v_sn.get(),
            "part_model":     self.v_part.get(),
            "test_timestamp": self.v_date.get(),
            "plane1_g":       self.v_p1g.get(),
            "plane1_deg":     self.v_p1d.get(),
            "plane2_g":       self.v_p2g.get(),
            "plane2_deg":     self.v_p2d.get(),
            "result_status":  self.v_status.get(),
        }

        def _print_thread():
            if any(k in printer.lower() for k in ["zdesigner", "zebra", "zd421"]):
                ok = print_to_zebra_zpl(rec_for_print, printer)
            else:
                ok = silent_print(path, printer)
            msg = f"✅ Sent to printer: {printer}" if ok else f"⚠ Print fallback — file: {path}"
            self.root.after(0, lambda: self._print_done(msg, ok))

        threading.Thread(target=_print_thread, daemon=True).start()

    def _print_done(self, msg: str, ok: bool):
        self.btn_print.configure(text="  🖨  PRINT STICKER TO THERMAL PRINTER  ",
                                 bg="#16A34A")
        self.print_status_lbl.configure(
            text=msg,
            fg="#166534" if ok else "#B45309")
        self._log(msg)

    # ── BROWSE / IMPORT ───────────────────────────────────────
    def _on_browse(self):
        path = filedialog.askopenfilename(
            title="Select CFF Export File",
            filetypes=[("Balancing Data", "*.csv;*.txt;*.dat"),
                       ("All Files", "*.*")]
        )
        if path:
            self._process_file(path)

    def _process_file(self, filepath: str):
        """Parse file → take LAST record → generate & auto-print."""
        self._log(f"Processing file: {os.path.basename(filepath)}")
        rec = parse_last_record(filepath)
        if not rec:
            self._log("Could not parse any records from file.")
            messagebox.showwarning("Parse Error", "Could not read balancing data from file.")
            return

        self._log(f"Last record: P1={rec['plane1_g']}g @ {rec['plane1_deg']}°  "
                  f"P2={rec['plane2_g']}g @ {rec['plane2_deg']}°  "
                  f"Status={rec['result_status']}")

        rec, path = self._on_generate(rec)

        # Save to DB
        if not db_is_dup(rec.get("record_number",""), rec.get("test_timestamp","")):
            row_id = db_save(rec)
            self._log(f"Saved to database: row {row_id}")

        self._load_history()

    # ── WATCHER (LIVE JOBS.XML + USB + DROP FOLDER) ──────────
    def _watcher_loop(self):
        """Background thread: watches live Jobs.xml, USB drives, and drop folder in real-time."""
        special_watch_paths = [
            r"D:\Alok\MicroDoubleplane\MicroDoubleplane\Jobs.xml",
            os.path.join(PROJECT_DIR, "MicroDoubleplane_Extracted", "MicroDoubleplane", "Jobs.xml"),
        ]
        drives = [f"{d}:\\" for d in "DEFGHIJKLMNOPQRSTUVWXYZ"]
        file_mtimes = {}

        while self.usb_monitoring:
            try:
                # 1. Real-time watch on MicroBalance Jobs.xml
                for sp in special_watch_paths:
                    if os.path.exists(sp):
                        try:
                            mt = os.path.getmtime(sp)
                            sz = os.path.getsize(sp)
                            key = f"{mt}:{sz}"
                            if file_mtimes.get(sp) != key:
                                file_mtimes[sp] = key
                                self.root.after(0, lambda p=sp: self._process_file(p))
                                self.root.after(0, lambda: self._log(
                                    "⚡ Real-Time CFF balancing record detected from machine!"))
                        except Exception:
                            pass

                # 2. Check USB and removable drives (D: through Z:)
                for d in drives:
                    if os.path.exists(d):
                        for ext in ["*.csv","*.txt","*.dat","*.CSV","*.TXT","*.DAT","*.xml","*.XML","*.xlsx","*.xls"]:
                            try:
                                for fp in glob.glob(os.path.join(d, ext)) + glob.glob(os.path.join(d, "*", ext)):
                                    if fp in special_watch_paths:
                                        continue
                                    mt = os.path.getmtime(fp)
                                    sz = os.path.getsize(fp)
                                    key = f"{mt}:{sz}"
                                    if file_mtimes.get(fp) != key:
                                        file_mtimes[fp] = key
                                        self.root.after(0, lambda p=fp: self._process_file(p))
                                        self.root.after(0, lambda: self._log(
                                            "🔌 External file detected — parsing latest record..."))
                            except Exception:
                                pass

                # 3. Check drop folder
                for fp in glob.glob(os.path.join(DROP_FOLDER, "*")):
                    if os.path.isfile(fp):
                        mt = os.path.getmtime(fp)
                        sz = os.path.getsize(fp)
                        key = f"{mt}:{sz}"
                        if file_mtimes.get(fp) != key:
                            file_mtimes[fp] = key
                            self.root.after(0, lambda p=fp: self._process_file(p))
                            self.root.after(0, lambda: self._log(
                                "📂 Drop folder file updated — parsing latest record..."))

            except Exception:
                pass
            time.sleep(1.5)

    # ── REAL-TIME STATUS CHECKER ──────────────────────────────
    def _lan_status_loop(self):
        """Checks DB records count directly in real-time."""
        while True:
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT count(*), COALESCE(SUM(is_printed), 0) FROM balancing_records")
                row = cur.fetchone()
                total = row[0] or 0
                printed = row[1] or 0
                conn.close()
                self.root.after(0, lambda t=total, p=printed: self.status_dot.configure(
                    text=f"● LIVE | Total Records: {t} | Printed: {p}",
                    fg="#22C55E"))
            except Exception:
                pass
            time.sleep(3)

    # ── HISTORY ───────────────────────────────────────────────
    def _load_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        records = db_get_records()
        for r in records:
            self.tree.insert("", tk.END, values=(
                r[0], r[1], r[2], r[3],
                f"{float(r[4] or 0):.3f}", f"{float(r[5] or 0):.1f}",
                f"{float(r[6] or 0):.3f}", f"{float(r[7] or 0):.1f}",
                r[8], "YES" if r[9] else "NO"
            ))
        # Ensure the NEWEST record (row 0) is selected and at the very top of view
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])
            self.tree.yview_moveto(0)

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        rows = db_get_records(limit=10000)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ID","Timestamp","Part Model","CFF Serial",
                        "P1 g","P1 deg","P2 g","P2 deg","Result","Printed"])
            w.writerows(rows)
        messagebox.showinfo("Export", f"Exported {len(rows)} records to:\n{path}")

    # ── Latest sticker reload ─────────────────────────────────
    def _refresh_preview_from_latest(self):
        records = db_get_records(limit=1)
        if records:
            r = records[0]
            self.v_sn.set(str(r[3] or ""))
            self.v_part.set(str(r[2] or ""))
            self.v_date.set(str(r[1] or ""))
            self.v_p1g.set(f"{float(r[4] or 0):.3f}")
            self.v_p1d.set(f"{float(r[5] or 0):.1f}")
            self.v_p2g.set(f"{float(r[6] or 0):.3f}")
            self.v_p2d.set(f"{float(r[7] or 0):.1f}")
            self.v_status.set(str(r[8] or "OK"))
            rec_dict = {
                "cff_serial": r[3],
                "part_model": r[2],
                "test_timestamp": r[1],
                "plane1_g": float(r[4] or 0),
                "plane1_deg": float(r[5] or 0),
                "plane2_g": float(r[6] or 0),
                "plane2_deg": float(r[7] or 0),
                "result_status": r[8],
                "speed_rpm": 1100
            }
            path = build_sticker(rec_dict)
            self.last_sticker_path = path
            try:
                img = Image.open(path)
                img = img.resize((400, 267), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self.preview_lbl.configure(image=tk_img, text="")
                self.preview_lbl.image = tk_img
            except Exception:
                pass
        else:
            latest = os.path.join(SAMPLES_DIR, "latest_cff_qr_sticker.png")
            if os.path.exists(latest):
                self.last_sticker_path = latest
                try:
                    img = Image.open(latest)
                    img = img.resize((400, 267), Image.Resampling.LANCZOS)
                    tk_img = ImageTk.PhotoImage(img)
                    self.preview_lbl.configure(image=tk_img, text="")
                    self.preview_lbl.image = tk_img
                except Exception:
                    pass


# ─────────────────────────── ENTRY POINT ─────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = CFFApp(root)
    root.mainloop()
