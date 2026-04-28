"""为 projects 表添加 is_single_per_order 字段"""
import re
import pymysql

# 从 .env 读取数据库连接信息
with open('.env', 'r', encoding='utf-8') as f:
    env_content = f.read()

match = re.search(r'DATABASE_URL=.*?://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)', env_content)
if not match:
    print("无法解析 DATABASE_URL")
    exit(1)

用户, 密码, 主机, 端口, 数据库 = match.groups()

连接 = pymysql.connect(
    host=主机,
    port=int(端口),
    user=用户,
    password=密码,
    database=数据库,
    charset='utf8mb4'
)

try:
    with 连接.cursor() as 游标:
        游标.execute("""
            ALTER TABLE projects
            ADD COLUMN is_single_per_order smallint DEFAULT 0 COMMENT '每单限购一个'
        """)
    连接.commit()
    print("字段 is_single_per_order 添加成功！")
except Exception as e:
    if "Duplicate column" in str(e):
        print("字段已存在，跳过")
    else:
        print(f"错误: {e}")
finally:
    连接.close()
