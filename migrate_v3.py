import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "loans.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(loan_applications)")
        columns = [r[1] for r in cursor.fetchall()]
        if 'created_at' not in columns:
            print("Adding created_at column...")
            cursor.execute("ALTER TABLE loan_applications ADD COLUMN created_at TIMESTAMP")
            conn.commit()
            print("Success.")
        else:
            print("Already exists.")
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    migrate()
