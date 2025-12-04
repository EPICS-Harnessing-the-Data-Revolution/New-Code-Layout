"""
Inspect Measurements.db: file size, tables, row counts, and sample rows.
Run from project root.
"""
import os
import sqlite3
from pprint import pprint

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Measurements.db')

print('DB_PATH =', DB_PATH)
try:
    size = os.path.getsize(DB_PATH)
except Exception as e:
    print('Could not stat DB file:', e)
    raise SystemExit(1)
print('File size (bytes):', size)

if size == 0:
    print('Measurements.db appears empty (0 bytes). That explains zero results from queries.')
    raise SystemExit(0)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY name")
objs = cur.fetchall()
if not objs:
    print('No tables or views found in DB.')
    conn.close()
    raise SystemExit(0)

print('\nTables/views found:')
for name, typ in objs:
    print('-', name, f'({typ})')

print('\nTable details:')
for name, typ in objs:
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{name}"')
        count = cur.fetchone()[0]
    except Exception as e:
        count = f'ERROR: {e}'
    print(f'\n{name}: rows={count}')
    # show schema
    try:
        cur.execute(f'PRAGMA table_info("{name}")')
        cols = cur.fetchall()
        print(' Columns:')
        for cid, colname, coltype, notnull, dflt_value, pk in cols:
            print('  -', colname, coltype)
    except Exception as e:
        print('  Could not read schema:', e)

    # sample rows
    try:
        cur.execute(f'SELECT * FROM "{name}" LIMIT 5')
        rows = cur.fetchall()
        if rows:
            print(' Sample rows:')
            pprint(rows)
    except Exception as e:
        print('  Could not read rows:', e)

conn.close()
print('\nDone.')
