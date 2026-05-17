import sqlite3
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(collaborate_room)")
columns = cursor.fetchall()
print("collaborate_room columns:")
for c in columns:
    print(f" - {c[1]}")
conn.close()
