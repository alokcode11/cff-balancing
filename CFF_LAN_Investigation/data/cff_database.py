import sqlite3
import os
import csv
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cff_balancing_records.db")

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS balancing_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_code TEXT UNIQUE,
            cff_serial TEXT,
            machine_model TEXT,
            machine_sn TEXT,
            part_model TEXT,
            test_timestamp TEXT,
            plane1_amount_g REAL,
            plane1_angle_deg REAL,
            plane2_amount_g REAL,
            plane2_angle_deg REAL,
            result_status TEXT,
            qr_payload TEXT,
            created_at TEXT,
            is_printed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def save_record(record_data, db_path=DB_PATH):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cur.execute("""
            INSERT INTO balancing_records (
                unique_code, cff_serial, machine_model, machine_sn,
                part_model, test_timestamp, plane1_amount_g, plane1_angle_deg,
                plane2_amount_g, plane2_angle_deg, result_status,
                qr_payload, created_at, is_printed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record_data.get("unique_code"),
            record_data.get("cff_serial"),
            record_data.get("machine_model", "PHGS-5D"),
            record_data.get("machine_sn", "26010050"),
            record_data.get("part_model"),
            record_data.get("test_timestamp"),
            float(record_data.get("plane1_amount_g", 0.0)),
            float(record_data.get("plane1_angle_deg", 0.0)),
            float(record_data.get("plane2_amount_g", 0.0)),
            float(record_data.get("plane2_angle_deg", 0.0)),
            record_data.get("result_status", "OK"),
            record_data.get("qr_payload"),
            now,
            1 if record_data.get("is_printed") else 0
        ))
        conn.commit()
        record_id = cur.lastrowid
        conn.close()
        return True, record_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Duplicate record"
    except Exception as e:
        conn.close()
        return False, str(e)

def get_recent_records(limit=50, db_path=DB_PATH):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, test_timestamp, part_model, cff_serial,
               plane1_amount_g, plane1_angle_deg, plane2_amount_g, plane2_angle_deg,
               result_status, is_printed
        FROM balancing_records
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def export_records_to_csv(out_filepath, db_path=DB_PATH):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM balancing_records ORDER BY id ASC")
    rows = cur.fetchall()
    headers = [desc[0] for desc in cur.description]
    conn.close()
    
    with open(out_filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    return len(rows)

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
