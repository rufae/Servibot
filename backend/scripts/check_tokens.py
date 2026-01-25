import sqlite3, os

db_path = os.path.join(os.getcwd(), 'data', 'servibot.db')
print('DB path:', db_path)
print('Exists:', os.path.exists(db_path))
if not os.path.exists(db_path):
    raise SystemExit('Database not found')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# List tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', cur.fetchall())

# Try to inspect users table
try:
    cur.execute("PRAGMA table_info(users)")
    schema = cur.fetchall()
    print('Users schema:', schema)
except Exception as e:
    print('Could not read users schema:', e)

# Read first 10 users
try:
    cur.execute("SELECT id, email, google_access_token, google_refresh_token, google_id FROM users LIMIT 10")
    rows = cur.fetchall()
    print('User rows count:', len(rows))
    for r in rows:
        uid, email, access, refresh, gid = r
        print('---')
        print('id:', uid, 'email:', email, 'google_id:', gid)
        print('has access token:', bool(access))
        print('has refresh token:', bool(refresh))
        if access:
            print('access token sample:', access[:40] + '...' if len(access)>40 else access)
        if refresh:
            print('refresh token sample:', refresh[:40] + '...' if len(refresh)>40 else refresh)
except Exception as e:
    print('Error reading users:', e)

conn.close()
print('Done')
