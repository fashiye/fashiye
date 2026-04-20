import logging
import logging.handlers
import os
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from app.core.config import settings


class LogLevelFilter(logging.Filter):
    def __init__(self, level: int):
        super().__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= self.level


class ModuleFilter(logging.Filter):
    def __init__(self, modules: Optional[List[str]] = None):
        super().__init__()
        self.modules = modules or []

    def filter(self, record: logging.LogRecord) -> bool:
        if not self.modules:
            return True
        return any(module in record.name for module in self.modules)


class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}.gz")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i + 1}.gz")
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            
            dfn = self.rotation_filename(f"{self.baseFilename}.1.gz")
            with open(self.baseFilename, 'rb') as f_in:
                with gzip.open(dfn, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            os.remove(self.baseFilename)
        
        self.stream = self._open()


class DailyRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    def __init__(self, filename, backupCount=0, encoding=None, delay=False, utc=False):
        super().__init__(
            filename,
            when='midnight',
            interval=1,
            backupCount=backupCount,
            encoding=encoding,
            delay=delay,
            utc=utc
        )
    
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        
        dfn = self.rotation_filename(f"{self.baseFilename}.{datetime.now().strftime('%Y-%m-%d')}")
        
        if os.path.exists(self.baseFilename):
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
            
            if self.backupCount > 0:
                self._archive_old_logs()
        
        if not self.delay:
            self.stream = self._open()
    
    def _archive_old_logs(self):
        log_dir = os.path.dirname(self.baseFilename)
        archive_date = datetime.now() - timedelta(days=settings.LOG_ARCHIVE_DAYS)
        
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                try:
                    file_date_str = filename.split('.')[-1]
                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                    
                    if file_date < archive_date:
                        filepath = os.path.join(log_dir, filename)
                        archive_path = f"{filepath}.gz"
                        
                        with open(filepath, 'rb') as f_in:
                            with gzip.open(archive_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        os.remove(filepath)
                except (ValueError, IndexError):
                    continue


class LoggerFactory:
    _instance: Optional['LoggerFactory'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._loggers = {}
            self._setup_root_logger()
            self._initialized = True
    
    def _setup_root_logger(self):
        log_dir = Path(settings.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(self._get_log_level(settings.LOG_LEVEL))
        
        root_logger.handlers.clear()
        
        formatter = logging.Formatter(
            fmt=settings.LOG_FORMAT,
            datefmt=settings.LOG_DATE_FORMAT
        )
        
        if settings.LOG_ENABLE_CONSOLE:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        if settings.LOG_ENABLE_FILE:
            log_file = log_dir / "app.log"
            
            file_handler = DailyRotatingFileHandler(
                filename=str(log_file),
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            error_log_file = log_dir / "error.log"
            error_handler = DailyRotatingFileHandler(
                filename=str(error_log_file),
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            error_handler.addFilter(LogLevelFilter(logging.ERROR))
            root_logger.addHandler(error_handler)
    
    def _get_log_level(self, level_str: str) -> int:
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARN': logging.WARNING,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'FATAL': logging.CRITICAL,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(level_str.upper(), logging.INFO)
    
    def get_logger(self, name: str) -> logging.Logger:
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]
    
    def add_module_filter(self, logger_name: str, modules: List[str]):
        logger = self.get_logger(logger_name)
        module_filter = ModuleFilter(modules)
        logger.addFilter(module_filter)
    
    def set_level(self, logger_name: str, level: str):
        logger = self.get_logger(logger_name)
        logger.setLevel(self._get_log_level(level))


def setup_logging():
    LoggerFactory()


def get_logger(name: str) -> logging.Logger:
    return LoggerFactory().get_logger(name)


logger = get_logger(__name__)
