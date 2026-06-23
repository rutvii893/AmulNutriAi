import sqlite3
from pathlib import Path

path = Path('instance') / 'amulnutriai.db'
conn = sqlite3.connect(path)
cur = conn.cursor()
cur.execute("SELECT name, type, sql FROM sqlite_master WHERE type IN ('table','view') ORDER BY name;")
for name, typ, sql in cur.fetchall():
    print(f'{typ.upper()}: {name}')
    print('  SQL:', sql.replace('\n', ' '))
    if typ == 'table':
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{name}"')
            count = cur.fetchone()[0]
            print('  Rows:', count)
        except Exception as e:
            print('  Count error:', e)
    print()
conn.close()
