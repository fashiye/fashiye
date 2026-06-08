from fastapi import HTTPException, status


class 业务逻辑错误(Exception):
    """业务逻辑异常，用于返回可预见的业务错误消息"""

    def __init__(self, 错误消息: str, 状态码: int = 400):
        """
        初始化业务逻辑错误

        Args:
            错误消息: 错误描述文本
            状态码: HTTP 状态码，默认 400
        """
        self.错误消息 = 错误消息
        self.状态码 = 状态码


class 认证错误(Exception):
    """认证相关异常，用于身份验证失败场景"""

    def __init__(self, 错误消息: str, 状态码: int = 401):
        """
        初始化认证错误

        Args:
            错误消息: 错误描述文本
            状态码: HTTP 状态码，默认 401
        """
        self.错误消息 = 错误消息
        self.状态码 = 状态码
