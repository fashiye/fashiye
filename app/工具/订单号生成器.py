import time
import secrets


def 生成订单号() -> str:
    """
    生成唯一订单号

    格式: BO + 13位毫秒时间戳 + 4位随机数字

    Returns:
        形如 "BO17123456789011234" 的订单号字符串
    """
    时间戳 = str(int(time.time() * 1000))
    随机部分 = ''.join(secrets.choice('0123456789') for _ in range(4))
    return f"BO{时间戳}{随机部分}"
