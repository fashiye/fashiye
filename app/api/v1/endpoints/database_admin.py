from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.permissions import require_role
from app.schemas.database import (
    TableInfo, ColumnInfo, ColumnType, TableDataQuery, TableDataResponse,
    DataUpdateRequest, DataCreateRequest, DatabaseStats
)
from app.core.exceptions import BusinessError
import logging
import re

router = APIRouter(prefix="/admin/database", tags=["database-admin"])

logger = logging.getLogger(__name__)


def validate_table_name(table_name: str) -> str:
    """
    验证表名是否安全
    只允许字母、数字、下划线，且必须以字母或下划线开头
    防止SQL注入
    """
    if not table_name:
        raise HTTPException(status_code=400, detail="表名不能为空")
    
    # 检查表名格式：只允许字母、数字、下划线，长度1-64
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]{0,63}$', table_name):
        raise HTTPException(
            status_code=400, 
            detail=f"表名 '{table_name}' 格式不合法，只允许字母、数字、下划线，且必须以字母或下划线开头"
        )
    
    return table_name


def validate_column_name(column_name: str) -> str:
    """
    验证列名是否安全
    只允许字母、数字、下划线，且必须以字母或下划线开头
    防止SQL注入
    """
    if not column_name:
        raise HTTPException(status_code=400, detail="列名不能为空")
    
    # 检查列名格式：只允许字母、数字、下划线，长度1-64
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]{0,63}$', column_name):
        raise HTTPException(
            status_code=400, 
            detail=f"列名 '{column_name}' 格式不合法，只允许字母、数字、下划线，且必须以字母或下划线开头"
        )
    
    return column_name


async def validate_table_exists(db: AsyncSession, table_name: str) -> str:
    """
    验证表是否存在，并返回验证后的表名
    这是一个白名单验证，确保表名来自数据库
    """
    table_name = validate_table_name(table_name)
    
    # 获取当前数据库名
    db_name_result = await db.execute(text("SELECT DATABASE()"))
    db_name = db_name_result.scalar()
    
    # 检查表是否存在
    check_query = text("""
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = :db_name
        AND TABLE_NAME = :table_name
    """)
    check_result = await db.execute(check_query, {
        "db_name": db_name,
        "table_name": table_name
    })
    
    if check_result.scalar() == 0:
        raise HTTPException(status_code=404, detail=f"表 '{table_name}' 不存在")
    
    return table_name


def get_column_type(col_type: str) -> ColumnType:
    """将MySQL类型映射为ColumnType"""
    col_type_lower = col_type.lower()
    
    if "int" in col_type_lower:
        return ColumnType.INTEGER
    elif "char" in col_type_lower or "varchar" in col_type_lower:
        return ColumnType.STRING
    elif "text" in col_type_lower:
        return ColumnType.TEXT
    elif "decimal" in col_type_lower or "numeric" in col_type_lower or "float" in col_type_lower or "double" in col_type_lower:
        return ColumnType.DECIMAL
    elif "date" in col_type_lower or "time" in col_type_lower or "datetime" in col_type_lower or "timestamp" in col_type_lower:
        return ColumnType.DATETIME
    elif "bool" in col_type_lower or "tinyint(1)" in col_type_lower:
        return ColumnType.BOOLEAN
    elif "enum" in col_type_lower:
        return ColumnType.ENUM
    else:
        return ColumnType.OTHER


@router.get("/tables", response_model=List[TableInfo])
async def get_tables(
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(require_role(["super"]))
):
    """
    获取所有表列表
    仅超级管理员可访问
    """
    try:
        # 获取当前数据库名
        db_name_result = await db.execute(text("SELECT DATABASE()"))
        db_name = db_name_result.scalar()
        
        # 使用information_schema获取表信息
        tables_query = text("""
            SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables_result = await db.execute(tables_query, {"db_name": db_name})
        tables = tables_result.fetchall()
        
        result = []
        for table in tables:
            table_name = table[0]
            
            # 跳过系统表
            if table_name.startswith("alembic_"):
                continue
            
            # 验证表名格式（防御性编程）
            try:
                table_name = validate_table_name(table_name)
            except HTTPException:
                # 跳过格式不合法的表
                logger.warning(f"跳过格式不合法的表名: {table_name}")
                continue
            
            # 获取列信息
            columns_query = text("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_KEY,
                    COLUMN_DEFAULT,
                    COLUMN_COMMENT,
                    EXTRA
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = :db_name
                AND TABLE_NAME = :table_name
                ORDER BY ORDINAL_POSITION
            """)
            columns_result = await db.execute(columns_query, {
                "db_name": db_name,
                "table_name": table_name
            })
            columns = columns_result.fetchall()
            
            column_infos = []
            for col in columns:
                column_info = ColumnInfo(
                    name=col[0],
                    type=get_column_type(col[1]),
                    nullable=col[2] == "YES",
                    primary_key=col[3] == "PRI",
                    default=col[4],
                    comment=col[5] if col[5] else None
                )
                column_infos.append(column_info)
            
            # 获取实际行数（TABLE_ROWS是估算值）
            # 使用验证后的表名构建查询
            count_query = text(f"SELECT COUNT(*) FROM `{table_name}`")
            count_result = await db.execute(count_query)
            row_count = count_result.scalar()
            
            table_info = TableInfo(
                name=table_name,
                row_count=row_count,
                columns=column_infos
            )
            result.append(table_info)
        
        return result
        
    except Exception as e:
        logger.error(f"获取表列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取表列表失败: {str(e)}")


@router.get("/tables/{table_name}/schema", response_model=TableInfo)
async def get_table_schema(
    table_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(require_role(["super"]))
):
    """
    获取表结构
    仅超级管理员可访问
    """
    try:
        # 验证表名并检查表是否存在
        table_name = await validate_table_exists(db, table_name)
        
        # 获取当前数据库名
        db_name_result = await db.execute(text("SELECT DATABASE()"))
        db_name = db_name_result.scalar()
        
        # 获取列信息
        columns_query = text("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_KEY,
                COLUMN_DEFAULT,
                COLUMN_COMMENT,
                EXTRA
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = :table_name
            ORDER BY ORDINAL_POSITION
        """)
        columns_result = await db.execute(columns_query, {
            "db_name": db_name,
            "table_name": table_name
        })
        columns = columns_result.fetchall()
        
        column_infos = []
        for col in columns:
            column_info = ColumnInfo(
                name=col[0],
                type=get_column_type(col[1]),
                nullable=col[2] == "YES",
                primary_key=col[3] == "PRI",
                default=col[4],
                comment=col[5] if col[5] else None
            )
            column_infos.append(column_info)
        
        return TableInfo(
            name=table_name,
            columns=column_infos
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取表结构失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取表结构失败: {str(e)}")


@router.get("/tables/{table_name}/data", response_model=TableDataResponse)
async def get_table_data(
    table_name: str,
    query: TableDataQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(require_role(["super"]))
):
    """
    获取表数据（带分页、过滤、排序）
    仅超级管理员可访问
    """
    try:
        # 验证表名并检查表是否存在
        table_name = await validate_table_exists(db, table_name)
        
        # 获取当前数据库名
        db_name_result = await db.execute(text("SELECT DATABASE()"))
        db_name = db_name_result.scalar()
        
        # 获取列信息
        columns_query = text("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_KEY,
                COLUMN_DEFAULT,
                COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = :table_name
            ORDER BY ORDINAL_POSITION
        """)
        columns_result = await db.execute(columns_query, {
            "db_name": db_name,
            "table_name": table_name
        })
        columns = columns_result.fetchall()
        
        column_infos = []
        column_names = []
        
        for col in columns:
            column_info = ColumnInfo(
                name=col[0],
                type=get_column_type(col[1]),
                nullable=col[2] == "YES",
                primary_key=col[3] == "PRI",
                default=col[4],
                comment=col[5] if col[5] else None
            )
            column_infos.append(column_info)
            column_names.append(col[0])
        
        # 构建基础查询（使用验证后的表名）
        sql = f"SELECT * FROM `{table_name}`"
        count_sql = f"SELECT COUNT(*) FROM `{table_name}`"
        
        where_conditions = []
        params = {}
        
        # 应用过滤条件
        if query.filters:
            for field, value in query.filters.items():
                if field in column_names:
                    # 验证字段名
                    validate_column_name(field)
                    where_conditions.append(f"`{field}` = :{field}")
                    params[field] = value
        
        # 应用全局搜索
        if query.search:
            search_conditions = []
            for column in column_names:
                # 验证字段名
                validate_column_name(column)
                # 只对字符串类型的列进行搜索
                col_info = next((c for c in column_infos if c.name == column), None)
                if col_info and col_info.type in [ColumnType.STRING, ColumnType.TEXT]:
                    search_conditions.append(f"`{column}` LIKE :search")
            if search_conditions:
                where_conditions.append(f"({' OR '.join(search_conditions)})")
                params["search"] = f"%{query.search}%"
        
        # 添加WHERE子句
        if where_conditions:
            where_clause = " AND ".join(where_conditions)
            sql += f" WHERE {where_clause}"
            count_sql += f" WHERE {where_clause}"
        
        # 应用排序
        if query.sort_by and query.sort_by in column_names:
            # 验证排序字段名
            validate_column_name(query.sort_by)
            order = "ASC" if query.sort_order.lower() == "asc" else "DESC"
            sql += f" ORDER BY `{query.sort_by}` {order}"
        
        # 应用分页
        offset = (query.page - 1) * query.page_size
        sql += f" LIMIT {query.page_size} OFFSET {offset}"
        
        # 执行查询
        count_result = await db.execute(text(count_sql), params)
        total = count_result.scalar()
        
        data_result = await db.execute(text(sql), params)
        rows = data_result.fetchall()
        
        # 转换结果为字典列表
        data = []
        for row in rows:
            row_dict = {}
            for i, column_name in enumerate(column_names):
                row_dict[column_name] = row[i]
            data.append(row_dict)
        
        total_pages = (total + query.page_size - 1) // query.page_size
        
        return TableDataResponse(
            table_name=table_name,
            columns=column_infos,
            data=data,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取表数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取表数据失败: {str(e)}")


@router.post("/tables/{table_name}/data")
async def create_table_data(
    table_name: str,
    request: DataCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(require_role(["super"]))
):
    """
    创建新数据行
    仅超级管理员可访问
    """
    try:
        # 验证表名并检查表是否存在
        table_name = await validate_table_exists(db, table_name)
        
        # 获取当前数据库名
        db_name_result = await db.execute(text("SELECT DATABASE()"))
        db_name = db_name_result.scalar()
        
        # 获取列信息
        columns_query = text("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = :table_name
        """)
        columns_result = await db.execute(columns_query, {
            "db_name": db_name,
            "table_name": table_name
        })
        columns = columns_result.fetchall()
        column_names = [col[0] for col in columns]
        
        # 验证数据字段
        for field in request.data.keys():
            if field not in column_names:
                raise HTTPException(status_code=400, detail=f"字段 '{field}' 不存在于表 '{table_name}'")
            # 验证字段名格式
            validate_column_name(field)
        
        # 构建INSERT语句（使用验证后的表名和字段名）
        fields = list(request.data.keys())
        placeholders = [f":{field}" for field in fields]
        
        sql = f"INSERT INTO `{table_name}` ({', '.join([f'`{f}`' for f in fields])}) VALUES ({', '.join(placeholders)})"
        
        # 执行插入
        result = await db.execute(text(sql), request.data)
        await db.commit()
        
        # 获取插入的ID
        last_id = result.lastrowid
        
        return {
            "success": True,
            "message": "数据创建成功",
            "id": last_id,
            "data": request.data
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"创建数据失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"创建数据失败: {str(e)}")
    except Exception as e:
        await db.rollback()
        logger.error(f"创建数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建数据失败: {str(e)}")


@router.put("/tables/{table_name}/data/{id}")
async def update_table_data(
    table_name: str,
    id: int,
    request: DataUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(require_role(["super"]))
):
    """
    更新数据行
    仅超级管理员可访问
    """
    try:
        # 验证表名并检查表是否存在
        table_name = await validate_table_exists(db, table_name)
        
        # 获取当前数据库名
        db_name_result = await db.execute(text("SELECT DATABASE()"))
        db_name = db_name_result.scalar()
        
        # 获取主键列名
        pk_query = text("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = :table_name
            AND COLUMN_KEY = 'PRI'
            LIMIT 1
        """)
        pk_result = await db.execute(pk_query, {
            "db_name": db_name,
            "table_name": table_name
        })
        pk_row = pk_result.fetchone()
        
        if not pk_row:
            raise HTTPException(status_code=400, detail=f"表 '{table_name}' 没有主键")
        
        primary_key = pk_row[0]
        # 验证主键字段名
        validate_column_name(primary_key)
        
        # 获取列信息
        columns_query = text("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = :table_name
        """)
        columns_result = await db.execute(columns_query, {
            "db_name": db_name,
            "table_name": table_name
        })
        columns = columns_result.fetchall()
        column_names = [col[0] for col in columns]
        
        # 验证数据字段
        for field in request.data.keys():
            if field not in column_names:
                raise HTTPException(status_code=400, detail=f"字段 '{field}' 不存在于表 '{table_name}'")
            # 验证字段名格式
            validate_column_name(field)
        
        # 构建UPDATE语句（使用验证后的表名和字段名）
        set_clauses = [f"`{field}` = :{field}" for field in request.data.keys()]
        sql = f"UPDATE `{table_name}` SET {', '.join(set_clauses)} WHERE `{primary_key}` = :id"
        
        params = request.data.copy()
        params["id"] = id
        
        # 执行更新
        result = await db.execute(text(sql), params)
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"ID为 {id} 的记录不存在")
        
        return {
            "success": True,
            "message": "数据更新成功",
            "affected_rows": result.rowcount
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"更新数据失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"更新数据失败: {str(e)}")
    except Exception as e:
        await db.rollback()
        logger.error(f"更新数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新数据失败: {str(e)}")


@router.delete("/tables/{table_name}/data/{id}")
async def delete_table_data(
    table_name: str,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(require_role(["super"]))
):
    """
    删除数据行
    仅超级管理员可访问
    """
    try:
        # 验证表名并检查表是否存在
        table_name = await validate_table_exists(db, table_name)
        
        # 获取当前数据库名
        db_name_result = await db.execute(text("SELECT DATABASE()"))
        db_name = db_name_result.scalar()
        
        # 获取主键列名
        pk_query = text("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_NAME = :table_name
            AND COLUMN_KEY = 'PRI'
            LIMIT 1
        """)
        pk_result = await db.execute(pk_query, {
            "db_name": db_name,
            "table_name": table_name
        })
        pk_row = pk_result.fetchone()
        
        if not pk_row:
            raise HTTPException(status_code=400, detail=f"表 '{table_name}' 没有主键")
        
        primary_key = pk_row[0]
        # 验证主键字段名
        validate_column_name(primary_key)
        
        # 构建DELETE语句（使用验证后的表名和字段名）
        sql = f"DELETE FROM `{table_name}` WHERE `{primary_key}` = :id"
        
        # 执行删除
        result = await db.execute(text(sql), {"id": id})
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"ID为 {id} 的记录不存在")
        
        return {
            "success": True,
            "message": "数据删除成功",
            "affected_rows": result.rowcount
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"删除数据失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"删除数据失败: {str(e)}")
    except Exception as e:
        await db.rollback()
        logger.error(f"删除数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除数据失败: {str(e)}")


@router.get("/stats", response_model=DatabaseStats)
async def get_database_stats(
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(require_role(["super"]))
):
    """
    获取数据库统计信息
    仅超级管理员可访问
    """
    try:
        # 获取当前数据库名
        db_name_result = await db.execute(text("SELECT DATABASE()"))
        db_name = db_name_result.scalar()
        
        # 获取表列表
        tables_query = text("""
            SELECT TABLE_NAME, TABLE_ROWS
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = :db_name
            AND TABLE_TYPE = 'BASE TABLE'
        """)
        tables_result = await db.execute(tables_query, {"db_name": db_name})
        tables = tables_result.fetchall()
        
        total_tables = 0
        total_rows = 0
        table_stats = []
        
        for table in tables:
            table_name = table[0]
            
            # 跳过系统表
            if table_name.startswith("alembic_"):
                continue
            
            # 验证表名格式（防御性编程）
            try:
                table_name = validate_table_name(table_name)
            except HTTPException:
                # 跳过格式不合法的表
                logger.warning(f"跳过格式不合法的表名: {table_name}")
                continue
                
            total_tables += 1
            
            # 获取实际行数（使用验证后的表名）
            count_query = text(f"SELECT COUNT(*) FROM `{table_name}`")
            count_result = await db.execute(count_query)
            row_count = count_result.scalar()
            
            total_rows += row_count
            
            table_stats.append({
                "name": table_name,
                "rows": row_count
            })
        
        return DatabaseStats(
            total_tables=total_tables,
            total_rows=total_rows,
            database_name=db_name,
            table_stats=table_stats
        )
        
    except Exception as e:
        logger.error(f"获取数据库统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据库统计信息失败: {str(e)}")