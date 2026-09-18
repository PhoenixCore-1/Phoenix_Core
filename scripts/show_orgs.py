import sqlite3

db = sqlite3.connect(".local/phoenix_core_v1_dev.db")
rows = db.execute("SELECT id, code, name FROM organisations").fetchall()

for row in rows:
    print(row)

db.close()
