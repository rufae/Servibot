import sqlite3, os

db_path = os.path.join(os.getcwd(), 'data', 'servibot.db')
print('DB path:', db_path)
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA table_info(oauth_tokens)")
print('oauth_tokens schema:', cur.fetchall())

cur.execute("SELECT id, user_id, provider, access_token IS NOT NULL as has_access, refresh_token IS NOT NULL as has_refresh, scope, created_at FROM oauth_tokens LIMIT 20")
rows = cur.fetchall()
print('rows count:', len(rows))
for r in rows:
    print(r)

conn.close()
print('Done')
