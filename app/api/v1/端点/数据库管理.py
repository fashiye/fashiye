from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Any
import re

from app.数据库.会话 import 获取数据库会话
from app.api.依赖.认证 import 要求角色
from app.模式.数据库 import (
    表信息, 列信息, 列类型枚举, 表数据查询, 表数据响应,
    数据更新请求, 数据创建请求, 执行SQL请求, 执行SQL响应,
    数据库统计信息
)
from app.核心.日志 import 获取日志记录器

日志记录器 = 获取日志记录器(__name__)
router = APIRouter()

# 允许操作的表名白名单
允许的表名白名单 = ["users", "handlers", "admins", "admin_permissions", "orders",
                     "order_items", "order_logs", "games", "projects",
                     "conversations", "messages", "message_read_status"]

# 仅允许 SELECT 查询的前缀
只读SQL前缀 = ["SELECT", "select", "WITH", "with"]

# 允许的表名前缀校验正则
表名校验正则 = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def 验证表名格式(表名: str) -> str:
    """验证表名格式，仅允许字母数字和下划线，防止 SQL 注入"""
    if not 表名校验正则.match(表名):
        raise HTTPException(status_code=400, detail=f"表名 '{表名}' 格式不合法")
    return 表名


def 验证列名格式(列名: str):
    """验证列名格式，仅允许字母数字和下划线，防止 SQL 注入"""
    if not 表名校验正则.match(列名):
        raise HTTPException(status_code=400, detail=f"列名 '{列名}' 格式不合法")


async def 验证表名并检查表是否存在(数据库: AsyncSession, 表名: str) -> str:
    """
    验证表名格式并检查表是否存在于数据库中

    Args:
        数据库: 异步数据库会话
        表名: 待验证的表名

    Returns:
        验证通过的表名

    Raises:
        HTTPException: 表名不合法或表不存在时抛出
    """
    验证表名格式(表名)

    # 检查表是否存在
    查询 = text("""
        SELECT TABLE_NAME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = (SELECT DATABASE())
        AND TABLE_NAME = :table_name
    """)
    结果 = await 数据库.execute(查询, {"table_name": 表名})
    if not 结果.fetchone():
        raise HTTPException(status_code=404, detail=f"表 '{表名}' 不存在")

    return 表名


@router.get("/database/tables", response_model=list[表信息])
async def 获取所有表列表接口(
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """获取数据库中所有非系统表的列表及其结构信息"""
    try:
        # 获取当前数据库名
        数据库名结果 = await 数据库.execute(text("SELECT DATABASE()"))
        数据库名 = 数据库名结果.scalar()

        # 获取所有表
        表查询 = text("""
            SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_TYPE = 'BASE TABLE'
            AND TABLE_NAME NOT LIKE 'alembic_%'
            ORDER BY TABLE_NAME
        """)
        表结果 = await 数据库.execute(表查询, {"db_name": 数据库名})
        表列表 = 表结果.fetchall()

        结果 = []
        for 表 in 表列表:
            表名 = 表[0]

            # 获取列信息
            列查询 = text("""
                SELECT
                    COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE,
                    COLUMN_KEY, COLUMN_DEFAULT, COLUMN_COMMENT,
                    CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = :db_name
                AND TABLE_NAME = :table_name
                ORDER BY ORDINAL_POSITION
            """)
            列结果 = await 数据库.execute(列查询, {"db_name": 数据库名, "table_name": 表名})
            列列表 = 列结果.fetchall()

            列信息列表 = []
            for 列 in 列列表:
                列类型 = 列类型枚举.其他
                原始类型 = 列[1].lower()
                if any(t in 原始类型 for t in ["int", "tinyint", "bigint"]):
                    列类型 = 列类型枚举.整数
                elif any(t in 原始类型 for t in ["varchar", "char"]):
                    列类型 = 列类型枚举.字符串
                elif any(t in 原始类型 for t in ["text", "longtext"]):
                    列类型 = 列类型枚举.文本
                elif any(t in 原始类型 for t in ["decimal", "double", "float"]):
                    列类型 = 列类型枚举.小数
                elif "datetime" in 原始类型 or "timestamp" in 原始类型:
                    列类型 = 列类型枚举.日期时间
                elif "bool" in 原始类型:
                    列类型 = 列类型枚举.布尔
                elif "enum" in 原始类型:
                    列类型 = 列类型枚举.枚举

                列信息列表.append(列信息(
                    name=列[0],
                    type=列类型,
                    nullable=列[2] == "YES",
                    primary_key=列[3] == "PRI",
                    default=列[4],
                    comment=列[5],
                    max_length=列[6],
                    precision=列[7],
                    scale=列[8]
                ))

            结果.append(表信息(
                name=表名,
                comment=表[2] or "",
                row_count=表[1],
                columns=列信息列表
            ))

        return 结果

    except Exception as e:
        日志记录器.error(f"获取表列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取表列表失败: {str(e)}")


@router.post("/database/tables/{table_name}/data", response_model=表数据响应)
async def 查询表数据接口(
    table_name: str,
    查询参数: 表数据查询,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """分页查询指定表的数据，支持过滤和排序"""
    try:
        表名 = await 验证表名并检查表是否存在(数据库, table_name)
        偏移量 = (查询参数.page - 1) * 查询参数.page_size

        # 获取列信息
        数据库名结果 = await 数据库.execute(text("SELECT DATABASE()"))
        数据库名 = 数据库名结果.scalar()

        列查询 = text("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY,
                   CHARACTER_MAXIMUM_LENGTH
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = :table_name
            ORDER BY ORDINAL_POSITION
        """)
        列结果 = await 数据库.execute(列查询, {"db_name": 数据库名, "table_name": 表名})
        列列表 = 列结果.fetchall()

        列信息列表 = []
        for 列 in 列列表:
            列信息列表.append(列信息(
                name=列[0],
                type=列[1],
                nullable=列[2] == "YES",
                primary_key=列[3] == "PRI",
                max_length=列[4]
            ))

        # 构建查询
        where子句 = ""
        查询参数列表 = {}

        if 查询参数.search:
            # 遍历所有字符串类型的列进行模糊搜索
            搜索条件 = []
            for 列 in 列列表:
                列名 = 列[0]
                验证列名格式(列名)
                列类型 = 列[1].lower()
                if any(t in 列类型 for t in ["varchar", "char", "text"]):
                    搜索条件.append(f"`{列名}` LIKE :search_param")
            查询参数列表["search_param"] = f"%{查询参数.search}%"
            if 搜索条件:
                where子句 = " WHERE " + " OR ".join(搜索条件)
        elif 查询参数.filters:
            过滤条件 = []
            for key, value in 查询参数.filters.items():
                验证列名格式(key)
                过滤条件.append(f"`{key}` = :filter_{key}")
                查询参数列表[f"filter_{key}"] = value
            if 过滤条件:
                where子句 = " WHERE " + " AND ".join(过滤条件)

        # 排序
        排序子句 = ""
        if 查询参数.sort_by:
            验证列名格式(查询参数.sort_by)
            排序方向 = "ASC" if 查询参数.sort_order.lower() == "asc" else "DESC"
            排序子句 = f" ORDER BY `{查询参数.sort_by}` {排序方向}"

        # 总记录数
        计数SQL = f"SELECT COUNT(*) FROM `{表名}`{where子句}"
        计数结果 = await 数据库.execute(text(计数SQL), 查询参数列表)
        总记录数 = 计数结果.scalar()

        # 数据查询
        数据SQL = f"SELECT * FROM `{表名}`{where子句}{排序子句} LIMIT :page_limit OFFSET :page_offset"
        查询参数列表["page_limit"] = 查询参数.page_size
        查询参数列表["page_offset"] = 偏移量

        数据结果 = await 数据库.execute(text(数据SQL), 查询参数列表)
        行数据 = 数据结果.fetchall()
        列名 = 数据结果.keys()

        总页数 = (总记录数 + 查询参数.page_size - 1) // 查询参数.page_size

        return 表数据响应(
            table_name=表名,
            columns=列信息列表,
            data=[dict(zip(列名, 行)) for 行 in 行数据],
            total=总记录数,
            page=查询参数.page,
            page_size=查询参数.page_size,
            total_pages=总页数
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        日志记录器.error(f"查询数据失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"查询数据失败: {str(e)}")
    except Exception as e:
        日志记录器.error(f"查询数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询数据失败: {str(e)}")


@router.post("/database/tables/{table_name}/data/create", response_model=dict)
async def 创建表数据接口(
    table_name: str,
    请求数据: 数据创建请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """在指定表中创建新数据行"""
    try:
        表名 = await 验证表名并检查表是否存在(数据库, table_name)

        数据库名结果 = await 数据库.execute(text("SELECT DATABASE()"))
        数据库名 = 数据库名结果.scalar()

        # 获取列信息
        列查询 = text("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = :table_name
        """)
        列结果 = await 数据库.execute(列查询, {"db_name": 数据库名, "table_name": 表名})
        列名称列表 = [col[0] for col in 列结果.fetchall()]

        # 验证字段
        for field in 请求数据.data.keys():
            if field not in 列名称列表:
                raise HTTPException(status_code=400, detail=f"字段 '{field}' 不存在于表 '{表名}'")
            验证列名格式(field)

        列名 = ", ".join([f"`{field}`" for field in 请求数据.data.keys()])
        值占位 = ", ".join([f":{field}" for field in 请求数据.data.keys()])

        sql = f"INSERT INTO `{表名}` ({列名}) VALUES ({值占位})"
        result = await 数据库.execute(text(sql), 请求数据.data)
        await 数据库.commit()

        return {
            "success": True,
            "message": "数据创建成功",
            "inserted_id": result.lastrowid
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await 数据库.rollback()
        日志记录器.error(f"创建数据失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"创建数据失败: {str(e)}")


@router.put("/database/tables/{table_name}/data/{row_id}")
async def 更新表数据接口(
    table_name: str,
    row_id: int,
    请求数据: 数据更新请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """更新指定表中指定行的数据"""
    try:
        表名 = await 验证表名并检查表是否存在(数据库, table_name)

        数据库名结果 = await 数据库.execute(text("SELECT DATABASE()"))
        数据库名 = 数据库名结果.scalar()

        # 获取主键
        pk查询 = text("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = :table_name
            AND COLUMN_KEY = 'PRI'
            LIMIT 1
        """)
        pk结果 = await 数据库.execute(pk查询, {"db_name": 数据库名, "table_name": 表名})
        pk行 = pk结果.fetchone()

        if not pk行:
            raise HTTPException(status_code=400, detail=f"表 '{表名}' 没有主键")

        主键 = pk行[0]
        验证列名格式(主键)

        # 获取列信息
        列查询 = text("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = :table_name
        """)
        列结果 = await 数据库.execute(列查询, {"db_name": 数据库名, "table_name": 表名})
        列名称列表 = [col[0] for col in 列结果.fetchall()]

        # 验证数据字段
        for field in 请求数据.data.keys():
            if field not in 列名称列表:
                raise HTTPException(status_code=400, detail=f"字段 '{field}' 不存在于表 '{表名}'")
            验证列名格式(field)

        # 构建UPDATE语句
        set子句 = [f"`{field}` = :{field}" for field in 请求数据.data.keys()]
        sql = f"UPDATE `{表名}` SET {', '.join(set子句)} WHERE `{主键}` = :row_id"

        参数 = 请求数据.data.copy()
        参数["row_id"] = row_id

        result = await 数据库.execute(text(sql), 参数)
        await 数据库.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"ID为 {row_id} 的记录不存在")

        return {
            "success": True,
            "message": "数据更新成功",
            "affected_rows": result.rowcount
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await 数据库.rollback()
        日志记录器.error(f"更新数据失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"更新数据失败: {str(e)}")
    except Exception as e:
        await 数据库.rollback()
        日志记录器.error(f"更新数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新数据失败: {str(e)}")


@router.delete("/database/tables/{table_name}/data/{row_id}")
async def 删除表数据接口(
    table_name: str,
    row_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """删除指定表中指定行的数据（仅超级管理员可操作）"""
    try:
        表名 = await 验证表名并检查表是否存在(数据库, table_name)

        数据库名结果 = await 数据库.execute(text("SELECT DATABASE()"))
        数据库名 = 数据库名结果.scalar()

        # 获取主键列名
        pk查询 = text("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = :table_name
            AND COLUMN_KEY = 'PRI'
            LIMIT 1
        """)
        pk结果 = await 数据库.execute(pk查询, {"db_name": 数据库名, "table_name": 表名})
        pk行 = pk结果.fetchone()

        if not pk行:
            raise HTTPException(status_code=400, detail=f"表 '{表名}' 没有主键")

        主键 = pk行[0]
        验证列名格式(主键)

        sql = f"DELETE FROM `{表名}` WHERE `{主键}` = :row_id"

        result = await 数据库.execute(text(sql), {"row_id": row_id})
        await 数据库.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"ID为 {row_id} 的记录不存在")

        return {
            "success": True,
            "message": "数据删除成功",
            "affected_rows": result.rowcount
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await 数据库.rollback()
        日志记录器.error(f"删除数据失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"删除数据失败: {str(e)}")
    except Exception as e:
        await 数据库.rollback()
        日志记录器.error(f"删除数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除数据失败: {str(e)}")


@router.get("/database/stats", response_model=数据库统计信息)
async def 获取数据库统计接口(
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """获取数据库的统计信息（表数量、行数等，仅超级管理员可访问）"""
    try:
        数据库名结果 = await 数据库.execute(text("SELECT DATABASE()"))
        数据库名 = 数据库名结果.scalar()

        表查询 = text("""
            SELECT TABLE_NAME, TABLE_ROWS
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_TYPE = 'BASE TABLE'
        """)
        表结果 = await 数据库.execute(表查询, {"db_name": 数据库名})
        表列表 = 表结果.fetchall()

        总表数 = 0
        总行数 = 0
        表统计 = []

        for 表 in 表列表:
            表名 = 表[0]
            if 表名.startswith("alembic_"):
                continue

            try:
                表名 = 验证表名格式(表名)
            except HTTPException:
                日志记录器.warning(f"跳过格式不合法的表名: {表名}")
                continue

            总表数 += 1

            计数查询 = text(f"SELECT COUNT(*) FROM `{表名}`")
            计数结果 = await 数据库.execute(计数查询)
            行数 = 计数结果.scalar()

            总行数 += 行数
            表统计.append({
                "name": 表名,
                "rows": 行数
            })

        return 数据库统计信息(
            total_tables=总表数,
            total_rows=总行数,
            database_name=数据库名,
            table_stats=表统计
        )

    except Exception as e:
        日志记录器.error(f"获取数据库统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据库统计信息失败: {str(e)}")
