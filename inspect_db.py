import sqlite3
import pathlib

path = pathlib.Path('instance') / 'amulnutriai.db'
conn = sqlite3.connect(path)
cur = conn.cursor()
cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY name;")
rows = cur.fetchall()
print('Database:', path)
print('Schema objects:')
for name, typ in rows:
    print(f'{typ}: {name}')
conn.close()
