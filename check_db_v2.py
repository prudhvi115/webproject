import sqlite3
import os

db_path = 'db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'collaborate_%'")
tables = cursor.fetchall()
print("Collaborate Tables:")
for t in tables:
    print(t[0])
conn.close()
