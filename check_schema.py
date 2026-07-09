import sqlite3

conn = sqlite3.connect("database/autointel.db")

tables = [r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
)]

print("TABLES:", tables)
print()

for t in tables:
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({t})")]
    print(f"{t}: {cols}")