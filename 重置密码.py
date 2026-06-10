from passlib.context import CryptContext
import pymysql

# 生成 Argon2 哈希
密码上下文 = CryptContext(schemes=["argon2"], deprecated="auto")
新密码哈希 = 密码上下文.hash("as010415")

# 连接数据库更新超级管理员密码
conn = pymysql.connect(
    host="154.9.253.155", port=3306,
    user="dailiang_01", password="M3me6PjTAxfhRC4z",
    database="dailiang_01", charset="utf8mb4"
)
cur = conn.cursor()
cur.execute("UPDATE admins SET password = %s WHERE role = 'super'", (新密码哈希,))
print(f"更新了 {cur.rowcount} 条记录")
conn.commit()
cur.close()
conn.close()
print("超级管理员密码已重置为: as010415")
