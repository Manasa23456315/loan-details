import sqlite3
import datetime

def backfill():
    conn = sqlite3.connect('loans.db')
    cursor = conn.cursor()
    rows = cursor.execute('SELECT id, created_at FROM loan_applications ORDER BY created_at ASC').fetchall()
    dates = {}
    print(f"Processing {len(rows)} rows...")
    for row_id, created_at in rows:
        d = created_at[:10] if created_at else '2000-01-01'
        dates[d] = dates.get(d, 0) + 1
        cursor.execute('UPDATE loan_applications SET daily_id = ? WHERE id = ?', (dates[d], row_id))
    conn.commit()
    conn.close()
    print("Backfill complete.")

if __name__ == "__main__":
    backfill()
