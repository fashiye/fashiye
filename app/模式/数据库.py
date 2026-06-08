from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class 列类型枚举(str, Enum):
    """数据库列类型的枚举"""
    整数 = "integer"
    字符串 = "string"
    文本 = "text"
    小数 = "decimal"
    日期时间 = "datetime"
    布尔 = "boolean"
    枚举 = "enum"
    其他 = "other"


class 列信息(BaseModel):
    """数据库列的结构信息"""
    name: str
    type: 列类型枚举
    nullable: bool = False
    primary_key: bool = False
    foreign_key: Optional[str] = None
    default: Optional[str] = None
    comment: Optional[str] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None


class 表信息(BaseModel):
    """数据库表的结构信息"""
    name: str
    comment: Optional[str] = None
    row_count: Optional[int] = None
    columns: List[列信息] = []


class 表数据查询(BaseModel):
    """查询表数据时的过滤和分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: str = Field("asc", description="排序方向: asc/desc")
    search: Optional[str] = Field(None, description="全局搜索")


class 表数据响应(BaseModel):
    """表数据的查询结果"""
    table_name: str
    columns: List[列信息]
    data: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class 数据更新请求(BaseModel):
    """更新数据行的请求体"""
    data: Dict[str, Any] = Field(..., description="要更新的数据")


class 数据创建请求(BaseModel):
    """创建数据行的请求体"""
    data: Dict[str, Any] = Field(..., description="要创建的数据")


class 执行SQL请求(BaseModel):
    """执行自定义 SQL 语句的请求体"""
    sql: str = Field(..., description="SQL语句")
    parameters: Optional[Dict[str, Any]] = Field(None, description="参数")


class 执行SQL响应(BaseModel):
    """执行 SQL 语句的响应结果"""
    success: bool
    message: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    affected_rows: Optional[int] = None


class 数据库统计信息(BaseModel):
    """数据库的整体统计信息"""
    total_tables: int
    total_rows: int
    table_stats: List[Dict[str, Any]] = []
