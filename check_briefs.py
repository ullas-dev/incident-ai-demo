import sqlite3

conn = sqlite3.connect("meeting.db")

rows = conn.execute(
    "SELECT * FROM meeting_briefs"
)

for row in rows:
    print(row)

conn.close()