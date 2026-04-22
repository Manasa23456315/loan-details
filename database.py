import sqlite3
import os

# Absolute path (VERY IMPORTANT for PythonAnywhere)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "loans.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS loan_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            loan_type TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending',
            reason TEXT,
            identity_doc TEXT,
            income_doc TEXT,
            loan_doc TEXT,
            cibil_score INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database created successfully")
