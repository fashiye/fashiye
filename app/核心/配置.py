from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """应用程序全局配置类，从 .env 文件加载"""
    项目名称: str = Field("Game Boost Platform", alias="PROJECT_NAME")
    版本号: str = Field("1.0.0", alias="VERSION")
    调试模式: bool = Field(False, alias="DEBUG")

    密钥: str = Field(alias="SECRET_KEY")
    加密算法: str = Field("HS256", alias="ALGORITHM")
    访问令牌过期分钟数: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    数据库连接字符串: str = Field(alias="DATABASE_URL")

    AES密钥: str = Field(alias="AES_SECRET_KEY")
    AES向量: str = Field(alias="AES_IV")

    Redis地址: Optional[str] = Field(None, alias="REDIS_URL")

    # CORS 设置（逗号分隔的域名列表，如 "http://localhost:5173,https://example.com"）
    允许的跨域来源: str = Field("*", alias="CORS_ORIGINS")

    # 邮件服务器设置
    邮件SMTP主机: str = Field(alias="SMTP_HOST")
    邮件SMTP端口: int = Field(alias="SMTP_PORT")
    邮件SMTP用户名: str = Field(alias="SMTP_USER")
    邮件SMTP密码: str = Field(alias="SMTP_PASSWORD")
    邮件发送者地址: str = Field(alias="SMTP_FROM")

    # iaitouzi 支付平台设置（MD5签名+表单跳转支付）
    iaitouzi应用ID: str = Field("2258", alias="IAITOUZI_APP_ID")
    iaitouzi应用密钥: str = Field(alias="IAITOUZI_APP_SECRET")
    iaitouzi支付网关地址: str = Field("https://iaitouzi.com/core/api/request/pay/", alias="IAITOUZI_BASE_URL")
    iaitouzi异步通知地址: str = Field("http://localhost:8002/api/v1/payment/callback", alias="IAITOUZI_NOTIFY_URL")

    # 日志记录设置
    日志级别: str = Field("INFO", alias="LOG_LEVEL")
    日志目录: str = Field("logs", alias="LOG_DIR")
    日志最大字节数: int = Field(10485760, alias="LOG_MAX_BYTES")
    日志备份数量: int = Field(5, alias="LOG_BACKUP_COUNT")
    日志日期格式: str = Field("%Y-%m-%d %H:%M:%S", alias="LOG_DATE_FORMAT")
    日志格式: str = Field("%(asctime)s - %(levelname)s - %(name)s - %(message)s", alias="LOG_FORMAT")
    日志归档天数: int = Field(30, alias="LOG_ARCHIVE_DAYS")
    日志启用控制台: bool = Field(True, alias="LOG_ENABLE_CONSOLE")
    日志启用文件: bool = Field(True, alias="LOG_ENABLE_FILE")
    日志启用归档: bool = Field(True, alias="LOG_ENABLE_ARCHIVE")

    model_config = {"populate_by_name": True, "env_file": ".env"}


配置对象 = Settings()
