import sqlite3
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
try:
    cursor.execute("""
    CREATE TABLE "collaborate_sharedresource" (
        "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, 
        "title" varchar(255) NOT NULL, 
        "file" varchar(100), 
        "link" varchar(200), 
        "timestamp" datetime NOT NULL, 
        "room_id" bigint NOT NULL REFERENCES "collaborate_room" ("id") DEFERRABLE INITIALLY DEFERRED, 
        "sender_id" bigint NOT NULL REFERENCES "accounts_customuser" ("id") DEFERRABLE INITIALLY DEFERRED
    )
    """)
    cursor.execute('CREATE INDEX "collaborate_sharedresource_room_id_idx" ON "collaborate_sharedresource" ("room_id")')
    cursor.execute('CREATE INDEX "collaborate_sharedresource_sender_id_idx" ON "collaborate_sharedresource" ("sender_id")')
    conn.commit()
    print("Created collaborate_sharedresource table.")
except Exception as e:
    print(f"Error: {e}")
conn.close()
