from decimal import Decimal


def 计算项目价格(项目, 数量: int = 1) -> dict:
    """
    根据项目的计价方式计算价格

    Args:
        项目: 项目模型实例，包含 价格类型, 价格 等属性
        数量: 购买数量（按量计价时生效）

    Returns:
        dict: 包含 unit_price（单价）、total（总价）、quantity（实际数量）

    Raises:
        ValueError: 当 价格类型 无效时抛出
    """
    if 项目.价格类型 == 'fixed':
        return {
            'unit_price': 项目.价格,
            'total': 项目.价格,
            'quantity': 1
        }
    elif 项目.价格类型 == 'unit':
        有效数量 = max(数量, 1)
        return {
            'unit_price': 项目.价格,
            'total': 项目.价格 * 有效数量,
            'quantity': 有效数量
        }
    else:
        raise ValueError(f"无效的价格类型: {项目.价格类型}")
