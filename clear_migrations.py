import sqlite3
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("DELETE FROM django_migrations WHERE app='collaborate'")
conn.commit()
print("Cleared collaborate migrations from DB.")
conn.close()
