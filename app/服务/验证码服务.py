import asyncio
import random
import string
import time
from typing import Optional
from app.核心.配置 import 配置对象
from app.核心.日志 import 获取日志记录器
from app.服务.邮件服务 import 邮件服务对象

日志记录器 = 获取日志记录器(__name__)


class 验证码服务:
    """验证码生成与校验服务，优先使用 Redis，无 Redis 时使用内存存储"""

    def __init__(self):
        self.缓存: dict[str, dict] = {}
        self.清理间隔: int = 300
        self.清理任务: Optional[asyncio.Task] = None
        self.redis客户端 = None
        self._redis可用 = False

    async def _初始化Redis(self):
        """尝试初始化 Redis 连接"""
        if not 配置对象.Redis地址:
            return
        try:
            import redis.asyncio as redis
            self.redis客户端 = redis.from_url(配置对象.Redis地址)
            await self.redis客户端.ping()
            self._redis可用 = True
            日志记录器.info("Redis 连接成功，验证码将使用 Redis 存储")
        except Exception as e:
            日志记录器.warning(f"Redis 连接失败，回退到内存存储: {e}")
            self._redis可用 = False

    async def 启动清理任务(self):
        """启动后台清理任务"""
        await self._初始化Redis()
        self.清理任务 = asyncio.create_task(self.定期清理())

    async def 关闭(self):
        """取消后台清理任务并关闭 Redis 连接"""
        if self.清理任务:
            self.清理任务.cancel()
            try:
                await self.清理任务
            except asyncio.CancelledError:
                pass
        if self.redis客户端:
            await self.redis客户端.close()

    def 生成验证码(self, 长度: int = 6) -> str:
        """生成指定长度的纯数字验证码"""
        return ''.join(random.choices(string.digits, k=长度))

    async def _存储验证码(self, 键: str, 验证码: str, 过期秒数: int):
        """存储验证码到 Redis 或内存"""
        if self._redis可用 and self.redis客户端:
            try:
                await self.redis客户端.setex(键, 过期秒数, 验证码)
                await self.redis客户端.setex(f"{键}:verified", 过期秒数, "0")
                return
            except Exception as e:
                日志记录器.error(f"Redis 存储失败，回退内存: {e}")
                self._redis可用 = False

        self.缓存[键] = {
            "code": 验证码,
            "expires_at": time.time() + 过期秒数,
            "verified": False
        }

    async def 发送并缓存验证码(
        self,
        邮箱: str,
        场景: str,
        过期秒数: int = 900
    ) -> str:
        """生成验证码、发送邮件并写入缓存"""
        验证码 = self.生成验证码()
        缓存键 = f"verify_code:{邮箱}:{场景}"
        await self._存储验证码(缓存键, 验证码, 过期秒数)
        await 邮件服务对象.发送验证码邮件(邮箱, 验证码)
        return 验证码

    async def 发送并缓存重置密码验证码(
        self,
        邮箱: str,
        过期秒数: int = 600
    ) -> str:
        """生成密码重置验证码、发送邮件并写入缓存"""
        验证码 = self.生成验证码()
        缓存键 = f"verify_code:{邮箱}:reset_password"
        await self._存储验证码(缓存键, 验证码, 过期秒数)
        await 邮件服务对象.发送密码重置验证码邮件(邮箱, 验证码)
        return 验证码

    def 校验验证码(self, 邮箱: str, 场景: str, 用户输入验证码: str) -> bool:
        """校验验证码有效性（同步方法，用于内存回退场景）"""
        缓存键 = f"verify_code:{邮箱}:{场景}"

        if self._redis可用 and self.redis客户端:
            raise RuntimeError("Redis 模式下请使用异步校验方法")

        缓存项 = self.缓存.get(缓存键)
        if not 缓存项:
            return False
        if 缓存项.get("verified"):
            return False
        if time.time() > 缓存项["expires_at"]:
            del self.缓存[缓存键]
            return False
        if 缓存项["code"] != 用户输入验证码:
            return False
        缓存项["verified"] = True
        return True

    async def 异步校验验证码(self, 邮箱: str, 场景: str, 用户输入验证码: str) -> bool:
        """校验验证码有效性（异步方法，支持 Redis）"""
        缓存键 = f"verify_code:{邮箱}:{场景}"

        if self._redis可用 and self.redis客户端:
            try:
                存储的验证码 = await self.redis客户端.get(缓存键)
                if not 存储的验证码:
                    return False
                已验证 = await self.redis客户端.get(f"{缓存键}:verified")
                if 已验证 and 已验证.decode() == "1":
                    return False
                if 存储的验证码.decode() != 用户输入验证码:
                    return False
                await self.redis客户端.setex(f"{缓存键}:verified", 600, "1")
                await self.redis客户端.delete(缓存键)
                return True
            except Exception as e:
                日志记录器.error(f"Redis 校验失败，回退内存: {e}")
                self._redis可用 = False

        return self.校验验证码(邮箱, 场景, 用户输入验证码)

    async def 定期清理(self):
        """定期清理过期验证码缓存（内存模式）"""
        while True:
            try:
                await asyncio.sleep(self.清理间隔)
                if not self._redis可用:
                    当前时间 = time.time()
                    过期键列表 = [
                        key for key, val in self.缓存.items()
                        if 当前时间 > val["expires_at"]
                    ]
                    for key in 过期键列表:
                        del self.缓存[key]
                    if 过期键列表:
                        日志记录器.info(f"Cleaned {len(过期键列表)} expired verification codes")
            except asyncio.CancelledError:
                break
            except Exception as e:
                日志记录器.error(f"Error in cleanup task: {e}")


验证码服务对象 = 验证码服务()
