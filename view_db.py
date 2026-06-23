import sqlite3
from pathlib import Path

path = Path('instance') / 'amulnutriai.db'
conn = sqlite3.connect(path)
cur = conn.cursor()
cur.execute("SELECT name, type, sql FROM sqlite_master WHERE type IN ('table','view') ORDER BY name;")
objs = cur.fetchall()
print('Database:', path)
print()
for name, typ, sql in objs:
    print(f'{typ.upper()}: {name}')
    print('  SQL:', sql.replace('\n', '\\n'))
    if typ == 'table':
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{name}"')
            count = cur.fetchone()[0]
        except Exception as e:
            count = f'ERROR: {e}'
        print('  Rows:', count)
        try:
            cur.execute(f'SELECT * FROM "{name}" LIMIT 5')
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            print('  Columns:', cols)
            for r in rows:
                print('   ', r)
        except Exception as e:
            print('  Sample error:', e)
    print()
conn.close()
