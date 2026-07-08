import logging
import logging.handlers
import os
import gzip
import shutil
import asyncio                                           # 提供异步定时任务支持，用于定期清理日志归档
from datetime import datetime, timedelta
from pathlib import Path
from app.核心.配置 import 配置对象

_已初始化 = False


def 初始化日志记录():
    """初始化日志系统：配置控制台输出、每日滚动文件、错误日志分离"""
    global _已初始化
    if _已初始化:
        return
    _已初始化 = True

    日志目录 = Path(配置对象.日志目录)
    日志目录.mkdir(parents=True, exist_ok=True)

    根日志记录器 = logging.getLogger()
    根日志记录器.setLevel(_解析日志级别(配置对象.日志级别))
    根日志记录器.handlers.clear()

    格式器 = logging.Formatter(
        fmt=配置对象.日志格式,
        datefmt=配置对象.日志日期格式
    )

    if 配置对象.日志启用控制台:
        控制台处理器 = logging.StreamHandler()
        控制台处理器.setLevel(logging.DEBUG)
        控制台处理器.setFormatter(格式器)
        根日志记录器.addHandler(控制台处理器)

    if 配置对象.日志启用文件:
        文件处理器 = logging.handlers.TimedRotatingFileHandler(
            filename=str(日志目录 / "app.log"),
            when='midnight',
            interval=1,
            backupCount=配置对象.日志备份数量,
            encoding='utf-8'
        )
        文件处理器.setLevel(logging.DEBUG)
        文件处理器.setFormatter(格式器)
        根日志记录器.addHandler(文件处理器)

        错误处理器 = logging.handlers.TimedRotatingFileHandler(
            filename=str(日志目录 / "error.log"),
            when='midnight',
            interval=1,
            backupCount=配置对象.日志备份数量,
            encoding='utf-8'
        )
        错误处理器.setLevel(logging.ERROR)
        错误处理器.setFormatter(格式器)
        根日志记录器.addHandler(错误处理器)

    if 配置对象.日志启用归档:
        _清理旧归档(日志目录, 配置对象.日志归档天数)


def _解析日志级别(级别字符串: str) -> int:
    级别映射 = {
        'DEBUG': logging.DEBUG, 'INFO': logging.INFO,
        'WARNING': logging.WARNING, 'WARN': logging.WARNING,
        'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL,
        'FATAL': logging.CRITICAL
    }
    return 级别映射.get(级别字符串.upper(), logging.INFO)


def _清理旧归档(日志目录: Path, 保留天数: int):
    """压缩超过保留天数的旧日志文件"""
    截止日期 = datetime.now() - timedelta(days=保留天数)
    日志记录器 = logging.getLogger(__name__)
    for 日志文件 in 日志目录.glob("*.log.*"):
        try:
            修改时间 = datetime.fromtimestamp(日志文件.stat().st_mtime)
            if 修改时间 < 截止日期 and not 日志文件.suffix == '.gz':
                压缩路径 = 日志文件.with_suffix(日志文件.suffix + '.gz')
                with open(日志文件, 'rb') as 输入文件:
                    with gzip.open(压缩路径, 'wb') as 输出文件:
                        shutil.copyfileobj(输入文件, 输出文件)
                日志文件.unlink()
                日志记录器.info(f"已压缩并删除归档日志文件: {日志文件}")
        except Exception as 压缩异常:
            日志记录器.error(f"处理日志文件 {日志文件} 时出错: {压缩异常}")


async def 启动定期日志清理(日志目录: Path, 保留天数: int, 间隔小时: int = 1):
    """
    后台任务，定期执行日志归档清理，防止磁盘空间被日志耗尽。

    传入：日志目录（Path），保留天数（int），检查间隔小时（int，默认1）
    作用：在异步事件循环中每隔interval小时调用一次 _清理旧归档
    传出：无返回值（无限运行直到任务被取消）
    """
    日志记录器 = logging.getLogger(__name__)
    日志记录器.info(f"日志清理后台任务已启动（间隔{间隔小时}小时，保留{保留天数}天）")
    while True:
        try:
            _清理旧归档(日志目录, 保留天数)
        except Exception as 任务异常:
            日志记录器.error(f"日志清理任务异常: {任务异常}")
        await asyncio.sleep(间隔小时 * 3600)


def 获取日志记录器(名称: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(名称)
