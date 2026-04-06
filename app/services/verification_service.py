import random
import asyncio
from typing import Optional, Dict
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.core.config import settings


class VerificationService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.in_memory_store: Dict[str, Dict] = {}  # 内存存储作为降级方案
        self._redis_connected = False

    async def _ensure_redis_connected(self):
        """
        连接Redis（只连接一次）
        """
        if self._redis_connected:
            return
        
        if settings.REDIS_URL:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                await self.redis_client.ping()
            except Exception as e:
                print(f"Redis连接失败: {e}")
                self.redis_client = None
        
        self._redis_connected = True

    def generate_code(self) -> str:
        """
        生成6位数字验证码
        """
        return ''.join(random.choices('0123456789', k=6))

    async def store_code(self, email: str, code: str, expire_minutes: int = 15) -> bool:
        """
        存储验证码
        """
        await self._ensure_redis_connected()
        
        try:
            if self.redis_client:
                key = f"verify:{email}"
                await self.redis_client.setex(key, expire_minutes * 60, code)
                return True
            else:
                # 降级到内存存储
                self.in_memory_store[email] = {
                    'code': code,
                    'expire_at': datetime.now() + timedelta(minutes=expire_minutes)
                }
                # 清理过期的验证码
                self._clean_expired_codes()
                return True
        except Exception as e:
            print(f"存储验证码失败: {e}")
            return False

    async def verify_code(self, email: str, code: str) -> bool:
        """
        验证验证码
        """
        await self._ensure_redis_connected()
        
        try:
            if self.redis_client:
                key = f"verify:{email}"
                stored_code = await self.redis_client.get(key)
                if stored_code and stored_code == code:
                    # 验证成功后删除验证码
                    await self.redis_client.delete(key)
                    return True
            else:
                # 从内存存储验证
                if email in self.in_memory_store:
                    stored_data = self.in_memory_store[email]
                    if stored_data['code'] == code and datetime.now() < stored_data['expire_at']:
                        # 验证成功后删除验证码
                        del self.in_memory_store[email]
                        return True
            return False
        except Exception as e:
            print(f"验证验证码失败: {e}")
            return False

    def _clean_expired_codes(self):
        """
        清理过期的内存存储验证码
        """
        now = datetime.now()
        expired_emails = [email for email, data in self.in_memory_store.items() 
                        if now > data['expire_at']]
        for email in expired_emails:
            del self.in_memory_store[email]

    async def close(self):
        """
        关闭Redis连接
        """
        if self.redis_client:
            await self.redis_client.close()


verification_service = VerificationService()
