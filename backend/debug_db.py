import sqlite3

conn = sqlite3.connect('./data/servibot.db')
cursor = conn.cursor()

print("=== oauth_tokens ===")
cursor.execute('SELECT id, provider, user_id, sub, refresh_token FROM oauth_tokens')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Provider: {row[1]}, user_id: {row[2]} (type: {type(row[2])}), sub: {row[3]}, has_refresh: {bool(row[4])}")

print("\n=== users ===")
cursor.execute('SELECT id, google_id, email FROM users')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, google_id: {row[1]}, email: {row[2]}")

conn.close()
