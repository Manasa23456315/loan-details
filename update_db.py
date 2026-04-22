import sqlite3
conn=sqlite3.connect("loans.db")
conn.execute("ALTER TABLE loan_applications ADD COLUMN status TEXT DEFAULT 'pending'")
conn.execute("ALTER TABLE loan_applications ADD COLUMN reason TEXT")
conn.commit()
conn.close()

print("Database updated successfully")
