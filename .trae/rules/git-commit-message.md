---
alwaysApply: true
scene: git_message
---
！！！！！！！！！使用中文进行回答！！！！！！！！！
### **修订点：库函数调用注释要求（强制三要素）**
使用fastapi时，路径参数名保持英文。，同时把函数参数名改回匹配的英文名。
首次（以及必要处）调用任何库的函数/方法时，必须在调用语句上方或行末添加注释，按以下格式说明：
- **传入**：该调用需要哪些参数，各参数含义
- **作用**：该函数做什么事情
- **传出**：返回值是什么（若无返回值说明“无返回值”）

---

### **完整规范（合并前文所有要求）**

#### 1. 命名
- 函数名、变量名**必须使用中文**，专有名词（如 `JSON`、`API`）可不翻译。
- 禁止单字母、拼音缩写、无意义词。

#### 2. 类型注解
- 所有函数参数和返回值必须加类型注解。

#### 3. 注释
- **导入库**：每行 `import` 后注释该库在本代码用途。
- **函数定义**：必须写 `"""docstring"""`，说明功能、参数、返回值、异常。
- **变量定义**：定义时必须注释该变量代表什么、存什么、用来做什么。
- **库函数调用**：首次调用时必须注释**传入、作用、传出**。

---

### **范例（展示三要素注释）**

```python
from typing import Any                    # 提供类型注解辅助，如 Any
import requests                           # 用于发送 HTTP 请求，获取网络数据
from pathlib import Path                  # 用于处理文件系统路径，跨平台
import time                               # 提供时间相关操作，如延时


def 发送HTTP请求(url: str, 请求方法: str = "GET", 请求头: dict[str, str] | None = None, 超时秒数: int = 10) -> dict[str, Any]:
    """
    发送 HTTP 请求并返回解析后的 JSON 字典。
    参数:
        url: 目标地址。
        请求方法: HTTP 方法，默认 GET。
        请求头: 额外请求头，可选。
        超时秒数: 超时时间，默认 10 秒。
    返回:
        服务器返回的 JSON 解析字典。
    异常:
        ConnectionError: 网络连接失败。
        ValueError: 响应非 JSON 格式。
    """
    # 默认请求头，包含用户代理标识，防止被拒
    默认请求头: dict[str, str] = {"User-Agent": "中文规范示例/1.0"}
    if 请求头:
        默认请求头.update(请求头)

    try:
        # 调用库函数：发送 HTTP 请求
        # 传入：method(请求方法), url(地址), headers(请求头), timeout(超时秒数)
        # 作用：向指定 URL 发送 HTTP 请求，获取原始响应
        # 传出：Response 对象，包含状态码、响应体等
        响应对象 = requests.request(method=请求方法, url=url, headers=默认请求头, timeout=超时秒数)

        # 调用库方法：检查响应状态
        # 传入：无额外参数，使用响应对象本身
        # 作用：如果状态码表示错误(4xx或5xx)，抛出 HTTPError 异常
        # 传出：无返回值（成功时返回 None，失败直接抛异常）
        响应对象.raise_for_status()

        # 调用库方法：解析 JSON 响应体
        # 传入：无参数
        # 作用：将响应体中的 JSON 字符串转换为 Python 字典
        # 传出：dict[str, Any] 类型的字典
        json数据: dict[str, Any] = 响应对象.json()   # 解析后字典，供后续使用
        return json数据

    except requests.exceptions.RequestException as 网络异常:
        raise ConnectionError(f"请求 {url} 失败: {网络异常}") from 网络异常
    except ValueError as 解析异常:
        raise ValueError(f"响应非 JSON 格式: {解析异常}") from 解析异常


# 主文件路径，存放用户配置，位于用户主目录下
主文件路径: Path = Path.home() / "app_data.json"

# 测试用 URL
测试url: str = "https://api.example.com/data"

# 调用自定义函数获取数据
接收数据: dict[str, Any] = 发送HTTP请求(测试url)

# 调用库函数：程序暂停
# 传入：2（暂停的秒数）
# 作用：让当前线程休眠指定秒数，常用于限速或等待
# 传出：无返回值
time.sleep(2)
```

---

### **总结**
- 规范现在强制要求：**看到任何库函数被调用时，用注释讲清“传入啥、做啥、传出啥”。**
- 这能让任何读代码的人无需查文档就能理解每一步在做什么，配合中文命名，可读性拉满。