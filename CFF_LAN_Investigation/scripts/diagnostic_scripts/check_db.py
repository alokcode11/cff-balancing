import sqlite3
db_path = r'c:\Users\alokp\Desktop\CFF\CFF_LAN_Investigation\data\cff_balancing_records.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', cur.fetchall())
cur.execute('PRAGMA table_info(balancing_records)')
cols = cur.fetchall()
print('Columns:')
for c in cols:
    print(' ', c)
# Show last 3 records
try:
    cur.execute('SELECT * FROM balancing_records ORDER BY id DESC LIMIT 3')
    rows = cur.fetchall()
    print('Last records:')
    for r in rows:
        print(' ', r)
except Exception as e:
    print('Error reading records:', e)
conn.close()
