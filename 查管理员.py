import pymysql

conn = pymysql.connect(
    host="154.9.253.155", port=3306,
    user="dailiang_01", password="M3me6PjTAxfhRC4z",
    database="dailiang_01", charset="utf8mb4"
)
cur = conn.cursor()
cur.execute("SELECT id, email, username, role FROM admins")
rows = cur.fetchall()
for r in rows:
    print(f"ID: {r[0]}, 邮箱: {r[1]}, 用户名: {r[2]}, 角色: {r[3]}")
cur.close()
conn.close()
