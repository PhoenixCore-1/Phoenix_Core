import sqlite3

db = sqlite3.connect("phoenix_core.db")

rows = db.execute(
    "SELECT id, username FROM users"
).fetchall()

print(rows)

db.close()