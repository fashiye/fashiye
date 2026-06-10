#!/usr/bin/env python3
"""
数据库迁移脚本 v1: 去除用户名字段唯一约束
执行: cd /www/wwwroot/fashiye && python scripts/migrate_remove_username_unique.py
"""
import asyncio
from sqlalchemy import text
from app.db.session import engine


async def migrate():
    async with engine.begin() as conn:
        print("开始迁移: 去除用户名字段唯一约束...")

        print("修改 users 表 - 移除 username 唯一约束...")
        await conn.execute(text("ALTER TABLE users MODIFY COLUMN username VARCHAR(50) NOT NULL"))

        print("修改 handlers 表 - 移除 username 唯一约束...")
        await conn.execute(text("ALTER TABLE handlers MODIFY COLUMN username VARCHAR(50) NOT NULL"))

        print("修改 admins 表 - 移除 username 唯一约束...")
        await conn.execute(text("ALTER TABLE admins MODIFY COLUMN username VARCHAR(50) NOT NULL"))

        print("迁移完成!")


if __name__ == "__main__":
    asyncio.run(migrate())
