import sqlite3

conn = sqlite3.connect('./data/servibot.db')
cursor = conn.cursor()

# Update the existing token to have the correct user_id
cursor.execute('UPDATE oauth_tokens SET user_id = ? WHERE id = ?', ('1', 2))
conn.commit()

print("Updated oauth_tokens:")
cursor.execute('SELECT id, provider, user_id, sub FROM oauth_tokens')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Provider: {row[1]}, user_id: {row[2]}, sub: {row[3]}")

conn.close()
print("\n✅ Token updated successfully!")
