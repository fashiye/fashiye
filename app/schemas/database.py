from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class ColumnType(str, Enum):
    """数据库列类型"""
    INTEGER = "integer"
    STRING = "string"
    TEXT = "text"
    DECIMAL = "decimal"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    ENUM = "enum"
    OTHER = "other"


class ColumnInfo(BaseModel):
    """列信息"""
    name: str
    type: ColumnType
    nullable: bool = False
    primary_key: bool = False
    foreign_key: Optional[str] = None
    default: Optional[str] = None
    comment: Optional[str] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None


class TableInfo(BaseModel):
    """表信息"""
    name: str
    comment: Optional[str] = None
    row_count: Optional[int] = None
    columns: List[ColumnInfo] = []


class TableDataQuery(BaseModel):
    """表数据查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: str = Field("asc", description="排序方向: asc/desc")
    search: Optional[str] = Field(None, description="全局搜索")


class TableDataResponse(BaseModel):
    """表数据响应"""
    table_name: str
    columns: List[ColumnInfo]
    data: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class DataUpdateRequest(BaseModel):
    """数据更新请求"""
    data: Dict[str, Any] = Field(..., description="要更新的数据")


class DataCreateRequest(BaseModel):
    """数据创建请求"""
    data: Dict[str, Any] = Field(..., description="要创建的数据")


class ExecuteSQLRequest(BaseModel):
    """执行SQL请求"""
    sql: str = Field(..., description="SQL语句")
    parameters: Optional[Dict[str, Any]] = Field(None, description="参数")


class ExecuteSQLResponse(BaseModel):
    """执行SQL响应"""
    success: bool
    message: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    affected_rows: Optional[int] = None


class DatabaseStats(BaseModel):
    """数据库统计信息"""
    total_tables: int
    total_rows: int
    table_stats: List[Dict[str, Any]] = []