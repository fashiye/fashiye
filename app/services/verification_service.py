import secrets
import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

LUA_VERIFY_AND_DELETE = """
local key = KEYS[1]
local input_code = ARGV[1]
local stored = redis.call('GET', key)
if stored and stored == input_code then
    redis.call('DEL', key)
    return 1
end
return 0
"""

MAX_VERIFY_ATTEMPTS = 5
VERIFY_ATTEMPT_EXPIRE = 3600


class VerificationService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.in_memory_store: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        self._redis_connected = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def _ensure_redis_connected(self) -> Optional[redis.Redis]:
        """
        确保Redis连接，支持断线重连
        """
        if not settings.REDIS_URL:
            return None

        if self.redis_client:
            try:
                await self.redis_client.ping()
                return self.redis_client
            except Exception as e:
                logger.warning(f"Redis连接断开，尝试重连: {e}")
                self.redis_client = None

        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self.redis_client.ping()
            logger.info("Redis连接成功")
            return self.redis_client
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.redis_client = None
            return None

    def generate_code(self) -> str:
        """
        生成6位数字验证码（使用加密级随机数）
        """
        return ''.join(secrets.choice('0123456789') for _ in range(6))

    async def store_reset_code(self, email: str, code: str, expire_minutes: int = 10) -> bool:
        """
        存储密码重置验证码（独立于注册验证码）
        """
        redis_client = await self._ensure_redis_connected()
        
        try:
            if redis_client:
                key = f"reset:{email}"
                await redis_client.setex(key, expire_minutes * 60, code)
                await redis_client.delete(f"reset_attempts:{email}")
                logger.info(f"密码重置验证码已存储到Redis: {email}")
                return True
            else:
                async with self._lock:
                    self._clean_expired_codes_sync()
                    
                    reset_key = f"reset:{email}"
                    self.in_memory_store[reset_key] = {
                        'code': code,
                        'expire_at': datetime.now() + timedelta(minutes=expire_minutes),
                        'attempts': 0
                    }
                    logger.info(f"密码重置验证码已存储到内存: {email}")
                return True
        except Exception as e:
            logger.error(f"存储密码重置验证码失败: {e}")
            return False

    async def verify_reset_code(self, email: str, code: str) -> bool:
        """
        验证密码重置验证码（原子操作，支持尝试次数限制）
        """
        redis_client = await self._ensure_redis_connected()
        
        try:
            if redis_client:
                attempts_key = f"reset_attempts:{email}"
                attempts = await redis_client.get(attempts_key)
                if attempts and int(attempts) >= MAX_VERIFY_ATTEMPTS:
                    logger.warning(f"密码重置验证码尝试次数超限: {email}")
                    return False

                reset_key = f"reset:{email}"
                result = await redis_client.eval(
                    LUA_VERIFY_AND_DELETE, 
                    1, 
                    reset_key, 
                    code
                )
                
                if result:
                    await redis_client.delete(attempts_key)
                    logger.info(f"密码重置验证码验证成功: {email}")
                    return True
                else:
                    await redis_client.incr(attempts_key)
                    await redis_client.expire(attempts_key, VERIFY_ATTEMPT_EXPIRE)
                    logger.warning(f"密码重置验证码验证失败: {email}")
                    return False
            else:
                async with self._lock:
                    reset_key = f"reset:{email}"
                    if reset_key not in self.in_memory_store:
                        return False
                    
                    stored_data = self.in_memory_store[reset_key]
                    
                    if stored_data.get('attempts', 0) >= MAX_VERIFY_ATTEMPTS:
                        logger.warning(f"密码重置验证码尝试次数超限: {email}")
                        del self.in_memory_store[reset_key]
                        return False
                    
                    if datetime.now() >= stored_data['expire_at']:
                        del self.in_memory_store[reset_key]
                        return False
                    
                    if stored_data['code'] == code:
                        del self.in_memory_store[reset_key]
                        logger.info(f"密码重置验证码验证成功: {email}")
                        return True
                    else:
                        stored_data['attempts'] = stored_data.get('attempts', 0) + 1
                        logger.warning(f"密码重置验证码验证失败: {email}")
                        return False
        except Exception as e:
            logger.error(f"验证密码重置验证码失败: {e}")
            return False

    async def store_code(self, email: str, code: str, expire_minutes: int = 15) -> bool:
        """
        存储验证码
        """
        redis_client = await self._ensure_redis_connected()
        
        try:
            if redis_client:
                key = f"verify:{email}"
                await redis_client.setex(key, expire_minutes * 60, code)
                await redis_client.delete(f"verify_attempts:{email}")
                logger.info(f"验证码已存储到Redis: {email}")
                return True
            else:
                async with self._lock:
                    self._clean_expired_codes_sync()
                    
                    self.in_memory_store[email] = {
                        'code': code,
                        'expire_at': datetime.now() + timedelta(minutes=expire_minutes),
                        'attempts': 0
                    }
                    logger.info(f"验证码已存储到内存: {email}")
                return True
        except Exception as e:
            logger.error(f"存储验证码失败: {e}")
            return False

    async def verify_code(self, email: str, code: str) -> bool:
        """
        验证验证码（原子操作，支持尝试次数限制）
        """
        redis_client = await self._ensure_redis_connected()
        
        try:
            if redis_client:
                attempts_key = f"verify_attempts:{email}"
                attempts = await redis_client.get(attempts_key)
                if attempts and int(attempts) >= MAX_VERIFY_ATTEMPTS:
                    logger.warning(f"验证码尝试次数超限: {email}")
                    return False

                verify_key = f"verify:{email}"
                result = await redis_client.eval(
                    LUA_VERIFY_AND_DELETE, 
                    1, 
                    verify_key, 
                    code
                )
                
                if result:
                    await redis_client.delete(attempts_key)
                    logger.info(f"验证码验证成功: {email}")
                    return True
                else:
                    await redis_client.incr(attempts_key)
                    await redis_client.expire(attempts_key, VERIFY_ATTEMPT_EXPIRE)
                    logger.warning(f"验证码验证失败: {email}")
                    return False
            else:
                async with self._lock:
                    if email not in self.in_memory_store:
                        return False
                    
                    stored_data = self.in_memory_store[email]
                    
                    if stored_data.get('attempts', 0) >= MAX_VERIFY_ATTEMPTS:
                        logger.warning(f"验证码尝试次数超限: {email}")
                        del self.in_memory_store[email]
                        return False
                    
                    if datetime.now() >= stored_data['expire_at']:
                        del self.in_memory_store[email]
                        return False
                    
                    if stored_data['code'] == code:
                        del self.in_memory_store[email]
                        logger.info(f"验证码验证成功: {email}")
                        return True
                    else:
                        stored_data['attempts'] = stored_data.get('attempts', 0) + 1
                        logger.warning(f"验证码验证失败: {email}")
                        return False
        except Exception as e:
            logger.error(f"验证验证码失败: {e}")
            return False

    async def start_cleanup_task(self):
        """
        启动后台定期清理任务
        """
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("验证码清理任务已启动")

    async def _periodic_cleanup(self):
        """
        定期清理过期验证码（每5分钟）
        """
        while True:
            try:
                await asyncio.sleep(300)
                await self._clean_expired_codes()
            except asyncio.CancelledError:
                logger.info("验证码清理任务已停止")
                break
            except Exception as e:
                logger.error(f"清理过期验证码失败: {e}")

    def _clean_expired_codes_sync(self):
        """
        同步清理过期的内存存储验证码（在锁内调用）
        """
        now = datetime.now()
        expired_emails = [
            email for email, data in self.in_memory_store.items()
            if now > data['expire_at']
        ]
        for email in expired_emails:
            del self.in_memory_store[email]
        
        if expired_emails:
            logger.info(f"已清理 {len(expired_emails)} 个过期验证码")

    async def _clean_expired_codes(self):
        """
        异步清理过期的内存存储验证码
        """
        async with self._lock:
            self._clean_expired_codes_sync()

    async def check_rate_limit(self, key: str, max_requests: int = 3, window_seconds: int = 60) -> bool:
        """
        检查请求速率限制
        :param key: 限制键（如 email 或 IP）
        :param max_requests: 时间窗口内最大请求数
        :param window_seconds: 时间窗口（秒）
        :return: True 表示允许请求，False 表示被限制
        """
        redis_client = await self._ensure_redis_connected()
        rate_key = f"rate_limit:{key}"
        
        try:
            if redis_client:
                current = await redis_client.get(rate_key)
                if current and int(current) >= max_requests:
                    logger.warning(f"速率限制触发: {key}")
                    return False
                
                pipe = redis_client.pipeline()
                pipe.incr(rate_key)
                pipe.expire(rate_key, window_seconds)
                await pipe.execute()
                return True
            else:
                async with self._lock:
                    now = datetime.now()
                    if key not in self.in_memory_store:
                        self.in_memory_store[key] = {
                            'count': 1,
                            'expire_at': now + timedelta(seconds=window_seconds)
                        }
                        return True
                    
                    stored = self.in_memory_store[key]
                    if now > stored['expire_at']:
                        stored['count'] = 1
                        stored['expire_at'] = now + timedelta(seconds=window_seconds)
                        return True
                    
                    if stored['count'] >= max_requests:
                        logger.warning(f"速率限制触发: {key}")
                        return False
                    
                    stored['count'] += 1
                    return True
        except Exception as e:
            logger.error(f"速率限制检查失败: {e}")
            return True

    async def get_rate_limit_remaining(self, key: str) -> int:
        """
        获取速率限制剩余时间（秒）
        """
        redis_client = await self._ensure_redis_connected()
        rate_key = f"rate_limit:{key}"
        
        try:
            if redis_client:
                ttl = await redis_client.ttl(rate_key)
                return max(0, ttl)
            else:
                async with self._lock:
                    if key in self.in_memory_store:
                        remaining = (self.in_memory_store[key]['expire_at'] - datetime.now()).total_seconds()
                        return max(0, int(remaining))
                return 0
        except Exception as e:
            logger.error(f"获取速率限制剩余时间失败: {e}")
            return 0

    async def close(self):
        """
        关闭Redis连接和清理任务
        """
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis连接已关闭")


verification_service = VerificationService()
