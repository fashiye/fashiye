import time
from collections import defaultdict
from fastapi import Request
from app.核心.异常 import 业务逻辑错误


class 接口限流器:
    """简单的滑动窗口接口限流器（内存存储）"""

    def __init__(self, 最大请求数: int = 10, 时间窗口秒: int = 60):
        self.最大请求数 = 最大请求数
        self.时间窗口秒 = 时间窗口秒
        self.请求记录: dict[str, list[float]] = defaultdict(list)

    def 清理过期记录(self, 标识: str):
        当前时间 = time.time()
        if 标识 in self.请求记录:
            self.请求记录[标识] = [
                ts for ts in self.请求记录[标识]
                if 当前时间 - ts < self.时间窗口秒
            ]

    def 检查(self, 标识: str) -> bool:
        """
        检查请求是否超过频率限制

        Returns:
            bool: 未超限返回 True，超限返回 False
        """
        self.清理过期记录(标识)
        return len(self.请求记录[标识]) < self.最大请求数

    def 记录(self, 标识: str):
        self.请求记录[标识].append(time.time())


# 各接口的限流配置
登录限流器 = 接口限流器(最大请求数=10, 时间窗口秒=60)
注册限流器 = 接口限流器(最大请求数=3, 时间窗口秒=60)
发送验证码限流器 = 接口限流器(最大请求数=1, 时间窗口秒=60)


async def 限流依赖(限流器: 接口限流器, 请求: Request):
    """FastAPI 依赖注入，基于客户端 IP 进行限流"""
    客户端IP = 请求.client.host if 请求.client else "unknown"
    标识 = f"{客户端IP}:{请求.url.path}"
    if not 限流器.检查(标识):
        raise 业务逻辑错误("请求过于频繁，请稍后再试")
    限流器.记录(标识)
