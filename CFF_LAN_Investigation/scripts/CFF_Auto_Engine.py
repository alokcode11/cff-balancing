"""
CFF BALANCING MACHINE - FULL AUTO ENGINE
=========================================
Runs in the background. No user clicks required.

Trigger methods (in priority order):
  1. USB U-disk watcher   : Detects new CSV/DAT/TXT files when operator inserts U-disk
  2. LAN poller           : Polls CFF via Modbus/HTTP if CFF IP is found
  3. Folder drop watcher  : Watches a shared drop folder for manual drops

On new data detected:
  - Parses balancing record
  - Saves to SQLite database
  - Generates QR sticker PNG
  - Auto-prints to thermal printer (WIN32 print API)
  - Logs everything

Usage:
  python CFF_Auto_Engine.py                  # Headless daemon mode
  python CFF_Auto_Engine.py --with-gui       # Also launch the GUI app
"""

import os, sys, re, csv, json, glob, time, socket, threading, logging
import sqlite3, struct, subprocess, shutil, datetime, traceback

# ─────────────────────────── PATHS ───────────────────────────
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR    = os.path.join(BASE_DIR, "data")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples", "raw_balancing_records")
PRINT_DIR   = os.path.join(BASE_DIR, "samples", "print_queue")
LOG_DIR     = os.path.join(BASE_DIR, "logs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(PRINT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

DB_PATH     = os.path.join(DATA_DIR, "cff_balancing_records.db")
LOG_PATH    = os.path.join(LOG_DIR, "cff_auto_engine.log")

# ─────────────────────────── LOGGING ─────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("CFF_AutoEngine")

# ─────────────────────────── DATABASE ────────────────────────
def db_init():
    """
    Initialises DB. Handles BOTH the old schema (from cff_database.py)
    and creates the new unified schema if starting fresh.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if old schema exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='balancing_records'")
    table_exists = cur.fetchone()

    if table_exists:
        # Check which columns exist
        cur.execute("PRAGMA table_info(balancing_records)")
        existing_cols = {row[1] for row in cur.fetchall()}
        # Add new columns if missing (non-destructive migration)
        new_cols = {
            "source":        "TEXT DEFAULT 'USB'",
            "record_number": "TEXT DEFAULT ''",
            "machine_id":    "TEXT DEFAULT 'PHGS-5D-26010050'",
            "speed_rpm":     "REAL DEFAULT 1100",
            "plane1_g":      "REAL DEFAULT 0",
            "plane1_deg":    "REAL DEFAULT 0",
            "plane2_g":      "REAL DEFAULT 0",
            "plane2_deg":    "REAL DEFAULT 0",
            "sticker_path":  "TEXT DEFAULT ''",
            "raw_data":      "TEXT DEFAULT ''",
        }
        for col, col_def in new_cols.items():
            if col not in existing_cols:
                try:
                    conn.execute(f"ALTER TABLE balancing_records ADD COLUMN {col} {col_def}")
                    log.info(f"DB migration: added column '{col}'")
                except Exception as e:
                    log.debug(f"Column add skip ({col}): {e}")
    else:
        # Create fresh unified schema
        conn.execute("""CREATE TABLE balancing_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_code     TEXT,
            cff_serial      TEXT,
            machine_model   TEXT DEFAULT 'PHGS-5D',
            machine_sn      TEXT DEFAULT '26010050',
            part_model      TEXT,
            test_timestamp  TEXT,
            plane1_amount_g REAL DEFAULT 0,
            plane1_angle_deg REAL DEFAULT 0,
            plane2_amount_g REAL DEFAULT 0,
            plane2_angle_deg REAL DEFAULT 0,
            result_status   TEXT DEFAULT 'OK',
            qr_payload      TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            is_printed      INTEGER DEFAULT 0,
            source          TEXT DEFAULT 'USB',
            record_number   TEXT DEFAULT '',
            machine_id      TEXT DEFAULT 'PHGS-5D-26010050',
            speed_rpm       REAL DEFAULT 1100,
            plane1_g        REAL DEFAULT 0,
            plane1_deg      REAL DEFAULT 0,
            plane2_g        REAL DEFAULT 0,
            plane2_deg      REAL DEFAULT 0,
            sticker_path    TEXT DEFAULT '',
            raw_data        TEXT DEFAULT ''
        )""")
    conn.commit()
    conn.close()


def db_is_duplicate(record_number, test_timestamp):
    """Returns True if this exact record was already processed."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Check by record_number+timestamp OR by test_timestamp alone (old schema records)
    cur.execute(
        "SELECT id FROM balancing_records WHERE record_number=? AND test_timestamp=?",
        (str(record_number), str(test_timestamp))
    )
    row = cur.fetchone()
    conn.close()
    return row is not None


def db_save(record: dict) -> int:
    """Save record to DB. Works with both old and new schema."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Get current columns
    cur.execute("PRAGMA table_info(balancing_records)")
    all_cols = {row[1] for row in cur.fetchall()}

    sn        = record.get("cff_serial") or ""
    part      = record.get("part_model") or ""
    ts        = record.get("test_timestamp") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p1g       = float(record.get("plane1_g", 0) or 0)
    p1d       = float(record.get("plane1_deg", 0) or 0)
    p2g       = float(record.get("plane2_g", 0) or 0)
    p2d       = float(record.get("plane2_deg", 0) or 0)
    status    = record.get("result_status", "OK")
    qr_text   = record.get("qr_payload", f"{sn};{part};{ts};{p1g};{p1d};{p2g};{p2d};{status}")
    unique_cd = f"{sn}-{int(time.time())}"
    source    = record.get("source", "USB")
    rec_no    = record.get("record_number", "")
    machine   = record.get("machine_id", "PHGS-5D-26010050")
    speed     = float(record.get("speed_rpm", 1100) or 1100)
    sticker   = record.get("sticker_path", "")
    raw       = record.get("raw_data", "")[:1000]

    # Build insert dynamically based on what columns exist
    col_map = {
        "unique_code":      unique_cd,
        "cff_serial":       sn,
        "machine_model":    "PHGS-5D",
        "machine_sn":       "26010050",
        "part_model":       part,
        "test_timestamp":   ts,
        "plane1_amount_g":  p1g,
        "plane1_angle_deg": p1d,
        "plane2_amount_g":  p2g,
        "plane2_angle_deg": p2d,
        "result_status":    status,
        "qr_payload":       qr_text,
        "is_printed":       0,
        "source":           source,
        "record_number":    rec_no,
        "machine_id":       machine,
        "speed_rpm":        speed,
        "plane1_g":         p1g,
        "plane1_deg":       p1d,
        "plane2_g":         p2g,
        "plane2_deg":       p2d,
        "sticker_path":     sticker,
        "raw_data":         raw,
    }

    # Only insert columns that exist in this DB
    insert_cols = [c for c in col_map if c in all_cols]
    placeholders = ",".join(["?"] * len(insert_cols))
    values = [col_map[c] for c in insert_cols]

    cur.execute(
        f"INSERT INTO balancing_records ({','.join(insert_cols)}) VALUES ({placeholders})",
        values
    )
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id


# ─────────────────────────── QR STICKER GENERATOR ────────────
def generate_sticker(record: dict) -> str:
    """Generates QR sticker PNG. Returns saved file path."""
    try:
        import qrcode
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        log.error("qrcode / PIL not installed. Run: pip install qrcode pillow")
        return ""

    sn       = record.get("cff_serial") or "CFF-AUTO"
    part     = record.get("part_model") or "Unknown"
    dt       = record.get("test_timestamp") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    speed    = record.get("speed_rpm", "")
    p1g      = record.get("plane1_g", 0)
    p1d      = record.get("plane1_deg", 0)
    p2g      = record.get("plane2_g", 0)
    p2d      = record.get("plane2_deg", 0)
    status   = record.get("result_status", "OK")
    rec_num  = record.get("record_number", "")
    machine  = record.get("machine_id", "PHGS-5D-26010050")

    # QR payload (CSV format — compact for thermal label scanner)
    qr_text = f"{sn};{part};{dt};{p1g};{p1d};{p2g};{p2d};{status};{machine}"

    qr = qrcode.QRCode(version=2, box_size=4, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(qr_text)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    W = 265 * 2
    H = 177 * 2
    sticker = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(sticker)
    draw.rounded_rectangle([(4, 4), (W - 4, H - 4)], radius=16, outline="#CBD5E1", width=2)

    # QR Code Version 2 with Level Q error correction
    qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=8, border=0)
    qr.add_data(sn)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_size = int(100 * 2)
    qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)
    qr_x = int((W - qr_size) / 2)
    qr_y = int(12 * 2)
    sticker.paste(qr_resized, (qr_x, qr_y))

    # Serial Number Text Centered Underneath QR Code
    try:
        font = ImageFont.truetype("arialbd.ttf", int(14 * 2))
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), sn, font=font)
    txt_w = bbox[2] - bbox[0]
    txt_x = int((W - txt_w) / 2)
    txt_y = int(126 * 2)
    draw.text((txt_x, txt_y), sn, fill="#000000", font=font)

    # Save
    fname = f"sticker_{sn}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    out_path = os.path.join(SAMPLES_DIR, fname)
    sticker.save(out_path)

    # Also save as latest
    latest_path = os.path.join(SAMPLES_DIR, "latest_cff_qr_sticker.png")
    shutil.copy(out_path, latest_path)

    # Also copy to print queue
    print_path = os.path.join(PRINT_DIR, fname)
    shutil.copy(out_path, print_path)

    log.info(f"Sticker generated: {out_path}")
    return out_path


# ─────────────────────────── PRINTER (DIRECT ZPL) ───────────────
def send_zpl_raw(printer_name: str, zpl_string: str) -> bool:
    try:
        import ctypes
        import ctypes.wintypes as wt
        winspool = ctypes.WinDLL("winspool.drv")
        class DOC_INFO_1(ctypes.Structure):
            _fields_ = [("pDocName", wt.LPWSTR), ("pOutputFile", wt.LPWSTR), ("pDatatype", wt.LPWSTR)]
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
    except Exception as e:
        log.error(f"ZPL send error: {e}")
        return False


def auto_print(sticker_path: str, printer_name: str = None, sn: str = None):
    """
    Sends raw ZPL directly to Zebra printer.
    Width = 0.882" (265 dots), Height = 0.591" (177 dots) @ 300 DPI.
    Exact BarTender match: Darkness 30, Speed 4.0 ips, Thermal Transfer.
    """
    if printer_name is None:
        printer_name = "ZDesigner ZD421-300dpi ZPL"

    clean_sn = re.sub(r'[^A-Za-z0-9\-_]', '', str(sn or "7020001384261102045643"))
    if not clean_sn or len(clean_sn) < 5:
        # Extract SN from sticker filename if possible
        if sticker_path and "sticker_" in sticker_path:
            m = re.search(r'sticker_([A-Za-z0-9\-_]+)_', sticker_path)
            if m:
                clean_sn = m.group(1)
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
        f"^FO82,12^BQN,2,4,Q^FDQA,{clean_sn}^FS\n"
        f"^FO22,126^A0N,24,10^FD{clean_sn}^FS\n"
        "^XZ\n"
    )
    log.info(f"Streaming raw ZPL to {printer_name} (SN: {clean_sn})")
    ok = send_zpl_raw(printer_name, zpl)
    if ok:
        log.info(f"✅ ZPL sent successfully to {printer_name}")
    else:
        log.warning(f"ZPL stream failed")
    return ok


# ─────────────────────────── PARSER ──────────────────────────
def parse_cff_file(filepath: str, source: str = "USB") -> list:
    """
    Parse a CFF export file. Returns list of record dicts.
    Handles: CSV, TXT, DAT — tries multiple formats.
    """
    records = []
    try:
        raw = open(filepath, "rb").read()
        text = raw.decode("utf-8", errors="ignore")
    except Exception as e:
        log.error(f"Cannot read file {filepath}: {e}")
        return []

    log.info(f"Parsing file: {filepath} ({len(text)} bytes)")

    # ── FORMAT 1: Standard CSV with headers ──
    # Expected columns (from MCGS balancing software):
    # No, Time, Name, SerialNo, Speed, P1Amount, P1Angle, P2Amount, P2Angle
    if "," in text:
        try:
            import io
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                r = _extract_from_dict(row, source, filepath)
                if r:
                    records.append(r)
            if records:
                log.info(f"Parsed {len(records)} records (CSV format)")
                return records
        except Exception as e:
            log.debug(f"CSV parse attempt failed: {e}")

    # ── FORMAT 2: Tab-separated ──
    if "\t" in text:
        try:
            import io
            reader = csv.DictReader(io.StringIO(text), dialect="excel-tab")
            for row in reader:
                r = _extract_from_dict(row, source, filepath)
                if r:
                    records.append(r)
            if records:
                log.info(f"Parsed {len(records)} records (TSV format)")
                return records
        except Exception as e:
            log.debug(f"TSV parse attempt: {e}")

    # ── FORMAT 3: Free-text extraction (regex fallback) ──
    log.info("Using regex extraction on free-text file...")
    # Look for float pairs which are (Amount, Angle) repeated
    floats = re.findall(r'\b(\d+\.?\d*)\b', text)
    nums = [float(x) for x in floats]
    # Try to assemble one record from found numbers
    if len(nums) >= 4:
        # Heuristic: first plausible speed is 3-digit, then pairs of (amount<10, angle<360)
        rec = {
            "source": source,
            "record_number": "",
            "part_model": _extract_model(text),
            "cff_serial": _extract_serial(text),
            "test_timestamp": _extract_datetime(text),
            "speed_rpm": _find_speed(nums),
            "plane1_g": nums[0] if len(nums) > 0 else 0,
            "plane1_deg": nums[1] if len(nums) > 1 else 0,
            "plane2_g": nums[2] if len(nums) > 2 else 0,
            "plane2_deg": nums[3] if len(nums) > 3 else 0,
            "result_status": "OK" if "OK" in text.upper() else "NG",
            "raw_data": text[:500],
        }
        records.append(rec)
        log.info(f"Extracted 1 record via regex fallback")

    if not records:
        log.warning(f"Could not parse any records from: {filepath}")
    return records


def _extract_from_dict(row: dict, source: str, filepath: str) -> dict:
    """Map CSV row dict → standard record dict. Handles multiple column name variants."""
    def _get(row, *keys):
        for k in keys:
            for rk in row:
                if rk and k.lower() in rk.lower().strip():
                    v = row[rk]
                    if v is not None:
                        v = str(v).strip()
                        if v:
                            return v
        return ""

    try:
        rec_no   = _get(row, "No", "Serial", "序号", "编号")
        ts       = _get(row, "Time", "Date", "时间", "日期")
        name     = _get(row, "Name", "Part", "产品", "名称") or "122x992mm"
        sn       = _get(row, "SerialNo", "Serial No", "序列号", "产品序列")
        speed    = _get(row, "Speed", "RPM", "转速")
        p1g      = _get(row, "P1Amount", "Plane1", "P1", "左面不平衡量")
        p1d      = _get(row, "P1Angle",  "Angle1", "左面相位")
        p2g      = _get(row, "P2Amount", "Plane2", "P2", "右面不平衡量")
        p2d      = _get(row, "P2Angle",  "Angle2", "右面相位")

        if not any([p1g, p1d, p2g, p2d]):
            return None  # Empty row

        return {
            "source": source,
            "record_number": rec_no,
            "part_model": name,
            "cff_serial": sn or f"CFF-{datetime.date.today().strftime('%Y%m%d')}-{rec_no}",
            "test_timestamp": ts,
            "speed_rpm": float(speed or 0),
            "plane1_g": float(p1g or 0),
            "plane1_deg": float(p1d or 0),
            "plane2_g": float(p2g or 0),
            "plane2_deg": float(p2d or 0),
            "result_status": "OK",
            "raw_data": str(row)[:500],
        }
    except Exception as e:
        log.debug(f"Row extraction error: {e}")
        return None


def _extract_model(text):
    m = re.search(r'(\d{3}x\d{3,4}mm)', text, re.IGNORECASE)
    return m.group(1) if m else "CFF Model"

def _extract_serial(text):
    m = re.search(r'(CFF[-\s]?\d{4,})', text, re.IGNORECASE)
    return m.group(1) if m else ""

def _extract_datetime(text):
    m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2}[\s_T]\d{2}:\d{2}:\d{2})', text)
    if m: return m.group(1)
    m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', text)
    if m: return m.group(1)
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _find_speed(nums):
    for n in nums:
        if 500 <= n <= 3000:
            return n
    return 1100.0


# ─────────────────────────── PROCESS RECORD ──────────────────
def process_new_record(record: dict, auto_print_enabled: bool = True):
    """Full pipeline: dedupe → save DB → generate sticker → print."""
    rec_no = record.get("record_number", "")
    ts     = record.get("test_timestamp", "")

    if db_is_duplicate(rec_no, ts):
        log.info(f"Duplicate skipped: rec={rec_no} ts={ts}")
        return False

    log.info(f"Processing NEW record: rec={rec_no}  part={record.get('part_model')}  "
             f"p1={record.get('plane1_g')}g@{record.get('plane1_deg')}°  "
             f"p2={record.get('plane2_g')}g@{record.get('plane2_deg')}°  "
             f"status={record.get('result_status')}")

    # Generate sticker
    sticker_path = generate_sticker(record)
    record["sticker_path"] = sticker_path

    # Save to DB
    row_id = db_save(record)
    log.info(f"Saved to DB: row_id={row_id}")

    # Auto print (only OK results)
    if auto_print_enabled and record.get("result_status") == "OK":
        printed = auto_print(sticker_path)
        if printed:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("UPDATE balancing_records SET is_printed=1 WHERE id=?", (row_id,))
            conn.commit()
            conn.close()
    else:
        if record.get("result_status") != "OK":
            log.warning(f"Print BLOCKED: result is {record.get('result_status')} (NG)")

    return True


# ─────────────────────────── USB WATCHER ─────────────────────
class USBWatcher(threading.Thread):
    """
    Polls removable drives every 2 seconds.
    When a new .csv/.txt/.dat file appears on E:-Z:, parses and processes it.
    """
    def __init__(self, auto_print=True):
        super().__init__(daemon=True, name="USBWatcher")
        self.auto_print = auto_print
        self.seen = set()
        self.running = True

    def run(self):
        log.info("USB Watcher started (scanning E:-Z: every 2s)")
        drives = [f"{d}:\\" for d in "EFGHIJKLMNOPQRSTUVWXYZ"]
        while self.running:
            try:
                for d in drives:
                    if os.path.exists(d):
                        for ext in ["*.csv", "*.txt", "*.dat", "*.CSV", "*.TXT", "*.DAT"]:
                            for fpath in glob.glob(os.path.join(d, "**", ext), recursive=True):
                                if fpath not in self.seen:
                                    self.seen.add(fpath)
                                    log.info(f"USB: New file detected: {fpath}")
                                    time.sleep(0.5)  # Let file finish writing
                                    records = parse_cff_file(fpath, source="USB")
                                    for rec in records:
                                        process_new_record(rec, self.auto_print)
            except Exception as e:
                log.debug(f"USB watcher error: {e}")
            time.sleep(2)

    def stop(self):
        self.running = False


# ─────────────────────────── FOLDER WATCHER ──────────────────
class FolderWatcher(threading.Thread):
    """
    Watches a drop folder for manually copied files.
    Use this if operator manually copies files from USB to PC.
    """
    DROP_FOLDER = os.path.join(BASE_DIR, "data", "drop_folder")

    def __init__(self, auto_print=True):
        super().__init__(daemon=True, name="FolderWatcher")
        os.makedirs(self.DROP_FOLDER, exist_ok=True)
        self.auto_print = auto_print
        self.seen = set()
        self.running = True

    def run(self):
        log.info(f"Folder Watcher started on: {self.DROP_FOLDER}")
        while self.running:
            try:
                for fpath in glob.glob(os.path.join(self.DROP_FOLDER, "*")):
                    if fpath not in self.seen and os.path.isfile(fpath):
                        self.seen.add(fpath)
                        log.info(f"Drop Folder: New file: {fpath}")
                        time.sleep(0.3)
                        records = parse_cff_file(fpath, source="DROP_FOLDER")
                        for rec in records:
                            process_new_record(rec, self.auto_print)
            except Exception as e:
                log.debug(f"Folder watcher error: {e}")
            time.sleep(1)

    def stop(self):
        self.running = False


# ─────────────────────────── LAN POLLER ──────────────────────
class LANPoller(threading.Thread):
    """
    Polls the CFF controller over LAN.
    Tries Modbus TCP (port 502) to read holding registers.
    Falls back to HTTP if Modbus fails.
    """
    POLL_INTERVAL = 5  # seconds

    def __init__(self, cff_ip: str, auto_print=True):
        super().__init__(daemon=True, name="LANPoller")
        self.cff_ip     = cff_ip
        self.auto_print = auto_print
        self.running    = True
        self.last_rec_num = None

    def run(self):
        log.info(f"LAN Poller started → {self.cff_ip} (every {self.POLL_INTERVAL}s)")
        while self.running:
            try:
                record = self._poll_modbus() or self._poll_http()
                if record:
                    rec_num = record.get("record_number")
                    if rec_num and rec_num != self.last_rec_num:
                        self.last_rec_num = rec_num
                        process_new_record(record, self.auto_print)
            except Exception as e:
                log.debug(f"LAN poll error: {e}")
            time.sleep(self.POLL_INTERVAL)

    def _poll_modbus(self):
        """Read Modbus holding registers from CFF controller."""
        try:
            s = socket.socket()
            s.settimeout(2)
            s.connect((self.cff_ip, 502))

            # Read 20 holding registers starting at address 0
            # (Standard MCGS balancing data layout: depends on firmware)
            pdu = bytes([
                0x00, 0x01,              # Transaction ID
                0x00, 0x00,              # Protocol ID (Modbus)
                0x00, 0x06,              # Length
                0x01,                    # Unit ID
                0x03,                    # Function code: Read Holding Registers
                0x00, 0x00,              # Start address: 0
                0x00, 0x14,              # Quantity: 20 registers
            ])
            s.send(pdu)
            resp = s.recv(256)
            s.close()

            if len(resp) < 9:
                return None

            byte_count = resp[8]
            if byte_count < 1:
                return None

            regs = []
            for i in range(0, byte_count, 2):
                if 9 + i + 1 < len(resp):
                    val = struct.unpack(">H", resp[9+i:9+i+2])[0]
                    regs.append(val)

            log.info(f"Modbus response: {[hex(r) for r in regs]}")

            # Map registers — MCGS typical layout (may need calibration)
            # reg[0]  = Record number
            # reg[1]  = Speed (RPM)
            # reg[2]  = Plane1 amount * 1000 (milli-grams)
            # reg[3]  = Plane1 angle (degrees)
            # reg[4]  = Plane2 amount * 1000
            # reg[5]  = Plane2 angle
            # reg[6]  = Status (1=OK, 0=NG)
            if len(regs) < 6:
                return None

            rec_num = str(regs[0]) if regs[0] else None
            speed   = regs[1] if regs[1] > 0 else 1100
            p1g     = regs[2] / 1000.0 if regs[2] > 0 else 0
            p1d     = regs[3]
            p2g     = regs[4] / 1000.0 if regs[4] > 0 else 0
            p2d     = regs[5]
            st      = "OK" if (len(regs) > 6 and regs[6] == 1) else "OK"

            if not rec_num or regs[0] == 0:
                return None

            return {
                "source": "MODBUS_LAN",
                "record_number": rec_num,
                "part_model": "122x992mm",
                "cff_serial": f"CFF-{datetime.date.today().strftime('%Y%m%d')}-{rec_num}",
                "machine_id": f"PHGS-5D-26010050@{self.cff_ip}",
                "test_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "speed_rpm": speed,
                "plane1_g": p1g,
                "plane1_deg": p1d,
                "plane2_g": p2g,
                "plane2_deg": p2d,
                "result_status": st,
                "raw_data": resp.hex(),
            }
        except Exception as e:
            log.debug(f"Modbus poll failed: {e}")
            return None

    def _poll_http(self):
        """Try HTTP API if Modbus fails (some MCGS firmware has web interface)."""
        for port in [80, 8080, 8888, 5000]:
            try:
                s = socket.socket()
                s.settimeout(2)
                s.connect((self.cff_ip, port))
                req = f"GET /cgi-bin/data.cgi?cmd=lastrecord HTTP/1.0\r\nHost: {self.cff_ip}\r\n\r\n"
                s.send(req.encode())
                resp = s.recv(4096).decode(errors='ignore')
                s.close()
                if resp and len(resp) > 100:
                    log.info(f"HTTP response from {self.cff_ip}:{port}: {resp[:300]}")
                    # Try to parse JSON in response
                    json_match = re.search(r'\{.*\}', resp, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group())
                            return self._map_http_data(data)
                        except Exception:
                            pass
            except Exception:
                pass
        return None

    def _map_http_data(self, data: dict):
        return {
            "source": "HTTP_LAN",
            "record_number": str(data.get("no", data.get("id", ""))),
            "part_model": data.get("name", data.get("part", "122x992mm")),
            "cff_serial": data.get("serial", ""),
            "test_timestamp": data.get("time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "speed_rpm": float(data.get("speed", 1100)),
            "plane1_g": float(data.get("p1", data.get("plane1", 0))),
            "plane1_deg": float(data.get("a1", data.get("angle1", 0))),
            "plane2_g": float(data.get("p2", data.get("plane2", 0))),
            "plane2_deg": float(data.get("a2", data.get("angle2", 0))),
            "result_status": "OK",
            "raw_data": str(data),
        }

    def stop(self):
        self.running = False


# ─────────────────────────── STATUS REPORTER ─────────────────
class StatusReporter(threading.Thread):
    """Writes a live status JSON every 10s for the GUI to read."""
    STATUS_FILE = os.path.join(DATA_DIR, "engine_status.json")

    def __init__(self, threads):
        super().__init__(daemon=True, name="StatusReporter")
        self.threads = threads
        self.running = True

    def run(self):
        while self.running:
            status = {
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "threads": {t.name: t.is_alive() for t in self.threads},
                "db_path": DB_PATH,
                "log_path": LOG_PATH,
                "print_queue": os.listdir(PRINT_DIR),
            }
            # Count records
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM balancing_records")
                status["total_records"] = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM balancing_records WHERE is_printed=1")
                status["printed_count"] = cur.fetchone()[0]
                cur.execute("SELECT * FROM balancing_records ORDER BY id DESC LIMIT 1")
                last = cur.fetchone()
                if last:
                    status["last_record"] = {
                        "id": last[0], "time": last[1], "part": last[4],
                        "serial": last[5], "result": last[13]
                    }
                conn.close()
            except Exception:
                pass
            try:
                with open(self.STATUS_FILE, "w") as f:
                    json.dump(status, f, indent=2)
            except Exception:
                pass
            time.sleep(10)

    def stop(self):
        self.running = False


# ─────────────────────────── MAIN ────────────────────────────
def main():
    log.info("=" * 60)
    log.info("  CFF AUTO ENGINE - STARTING")
    log.info(f"  DB:  {DB_PATH}")
    log.info(f"  LOG: {LOG_PATH}")
    log.info("=" * 60)

    db_init()

    # Check for saved CFF IP from discovery
    cff_ip = None
    discovery_json = os.path.join(BASE_DIR, "reports", "cff_discovery_result.json")
    if os.path.exists(discovery_json):
        try:
            with open(discovery_json) as f:
                d = json.load(f)
            cff_ip = d.get("cff_candidate")
            if cff_ip:
                log.info(f"CFF IP from discovery: {cff_ip}")
        except Exception:
            pass

    # Also check command-line argument
    for arg in sys.argv:
        if re.match(r'\d+\.\d+\.\d+\.\d+', arg):
            cff_ip = arg
            log.info(f"CFF IP from command line: {cff_ip}")

    # Start workers
    threads = []

    usb_watcher = USBWatcher(auto_print=True)
    usb_watcher.start()
    threads.append(usb_watcher)
    log.info("✅ USB Watcher: ACTIVE")

    folder_watcher = FolderWatcher(auto_print=True)
    folder_watcher.start()
    threads.append(folder_watcher)
    log.info(f"✅ Folder Watcher: ACTIVE → {FolderWatcher.DROP_FOLDER}")

    if cff_ip:
        lan_poller = LANPoller(cff_ip, auto_print=True)
        lan_poller.start()
        threads.append(lan_poller)
        log.info(f"✅ LAN Poller: ACTIVE → {cff_ip}:502 (Modbus TCP)")
    else:
        log.warning("⚠️  LAN Poller: INACTIVE (no CFF IP found)")
        log.warning("   Run STEP1_Setup_And_Find_CFF.bat as Admin to find CFF IP.")
        log.warning("   Or manually: python CFF_Auto_Engine.py 200.200.200.190")

    reporter = StatusReporter(threads)
    reporter.start()
    threads.append(reporter)

    log.info("")
    log.info("🚀 ALL ENGINES RUNNING. Waiting for balancing data...")
    log.info(f"   Drop folder: {FolderWatcher.DROP_FOLDER}")
    log.info(f"   Status file: {StatusReporter.STATUS_FILE}")
    log.info("   Press Ctrl+C to stop.")
    log.info("")

    # Launch GUI if requested
    if "--with-gui" in sys.argv:
        import subprocess
        gui_path = os.path.join(os.path.dirname(__file__), "CFF_QR_Automation_App.py")
        subprocess.Popen([sys.executable, gui_path])

    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutting down...")
        for t in threads:
            if hasattr(t, 'stop'):
                t.stop()
        log.info("Done.")


if __name__ == "__main__":
    main()
