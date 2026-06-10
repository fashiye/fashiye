import base64                                                                  # 用于将二维码图片编码为 base64
import hashlib                                                                  # 用于 MD5 签名计算
import httpx                                                                   # 用于发送 HTTP 请求，调用 iaitouzi 支付API
import re                                                                      # 用于解析 iaitouzi 返回的 HTML，提取支付 URL
import json                                                                    # 用于解析 iaitouzi JSON 响应
from decimal import Decimal
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin                                               # 用于拼接相对 URL

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.核心.配置 import 配置对象
from app.核心.日志 import 获取日志记录器
from app.模型.支付 import 支付记录表
from app.模型.订单 import 订单表, 订单状态枚举

日志记录器 = 获取日志记录器(__name__)


class 支付服务类:
    """
    iaitouzi 支付平台集成服务

    提供创建支付订单、获取支付链接、处理回调通知等核心支付功能。
    iaitouzi 为第三方聚合支付平台，采用 MD5 签名 + 表单跳转支付方式。
    """

    def __init__(self):
        # 调用库函数：初始化配置
        # 传入：iaitouzi 平台的各种配置参数
        # 作用：从配置对象加载支付网关 URL、应用 ID、应用密钥等
        # 传出：无返回值（实例属性被设置）
        self.支付网关地址 = 配置对象.iaitouzi支付网关地址.rstrip("/")
        self.应用ID = 配置对象.iaitouzi应用ID
        self.应用密钥 = 配置对象.iaitouzi应用密钥
        self.异步通知地址 = 配置对象.iaitouzi异步通知地址

    def _生成签名(self, 参数字典: dict) -> str:
        """
        生成 iaitouzi MD5 签名。

        传入：
            参数字典：包含所有请求参数的字典
        作用：
            1. 过滤掉值为空的参数
            2. 将剩余参数按参数名 ASCII 码从小到大排序（字典序）
            3. 取所有参数值依次拼接成字符串（不含 key，仅 value）
            4. 尾部拼接应用密钥
            5. 计算 MD5（32位小写）
        传出：
            32位小写 MD5 签名字符串
        """
        # 第一步：过滤空值参数（文档规定：值的参数为空不参与签名）
        # 第二步：按参数名 ASCII 码从小到大排序
        # 第三步：只取参数值（不含 key）拼接
        # 第四步：尾部追加应用密钥，计算 MD5
        非空参数 = {k: v for k, v in 参数字典.items() if v != "" and v is not None}
        排序后的键 = sorted(非空参数.keys())
        拼接值 = "".join(str(非空参数[键]) for 键 in 排序后的键)
        待签名字符串 = 拼接值 + self.应用密钥
        # 调用库函数：计算 MD5 哈希
        # 传入：待签名字符串（UTF-8 编码）
        # 作用：将待签名字符串进行 MD5 摘要运算
        # 传出：32 位小写十六进制哈希值
        return hashlib.md5(待签名字符串.encode("utf-8")).hexdigest()

    def _从HTML提取支付表单(self, html内容: str, 基址: str = "https://iaitouzi.com") -> Optional[dict]:
        """
        从 iaitouzi 返回的 HTML 中提取实际的支付表单（action + hidden inputs）。

        传入：
            html内容：iaitouzi 返回的完整 HTML 字符串
            基址：用于解析相对路径 URL，默认 iaitouzi.com
        作用：
            1. 匹配 <form action="..."> 中的 action URL（支持相对路径）
            2. 提取所有 <input type="hidden"> 的 name/value
            3. 将相对 action URL 解析为绝对 URL
            4. 返回 action 和 formData
        传出：
            {"action": 绝对URL, "formData": {"name": "value", ...}} 或 None
        """
        # 调用库函数：正则匹配 form 标签的 action 属性
        # 传入：HTML 字符串，正则表达式 pattern
        # 作用：提取 <form action="..."> 中的 URL
        # 传出：re.Match 对象或 None
        匹配结果 = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', html内容, re.IGNORECASE)
        if not 匹配结果:
            return None

        action地址 = 匹配结果.group(1)

        # 将相对路径解析为绝对 URL
        if not action地址.startswith("http"):
            from urllib.parse import urljoin
            action地址 = urljoin(基址.rstrip("/") + "/", action地址.lstrip("/"))

        # 调用库函数：提取所有隐藏 input 字段
        # 传入：HTML 字符串
        # 作用：提取 <input type="hidden" name="..." value="..."> 的参数
        # 传出：list of (name, value) tuples
        隐藏输入列表 = re.findall(
            r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']',
            html内容,
            re.IGNORECASE,
        )
        # 也匹配 value 在 name 之前的变体
        隐藏输入列表2 = re.findall(
            r'<input[^>]*value=["\']([^"\']*)["\'][^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\']',
            html内容,
            re.IGNORECASE,
        )

        # 合并所有隐藏 input，name-value 对
        formData = dict(隐藏输入列表)
        for 值, 名 in 隐藏输入列表2:
            if 名 not in formData:
                formData[名] = 值

        日志记录器.info(f"从 iaitouzi HTML 提取到支付表单: action={action地址[:80]}..., inputs={len(formData)}个")
        return {
            "action": action地址,
            "formData": formData,
        }

    async def 创建支付订单(
        self,
        数据库: AsyncSession,
        内部订单: 订单表,
        联系方式: str,
        支付方式: str = "alipay",
        重定向地址: str = "https://fashiye.cn",
    ) -> dict:
        """
        创建 iaitouzi 支付订单，返回真实的支付跳转 URL 和二维码图片。

        流程：
            1. 组装请求参数（含支付方式 type），计算 MD5 签名
            2. 后端 POST 到 iaitouzi 支付网关
            3. 解析 iaitouzi 返回的 HTML/JSON，提取实际支付 URL
            4. 访问支付页面，提取二维码图片（base64 编码）
            5. 返回 paymentUrl + qrCodeImage 给前端

        传入：
            数据库：异步数据库会话
            内部订单：本地订单表对象
            联系方式：用户下单留的联系方式（用于订单找回）
            支付方式：支付渠道（alipay=支付宝, wechat=微信支付），默认支付宝
            重定向地址：支付成功后浏览器跳转回的前端页面地址
        作用：
            通过后端代理调用 iaitouzi，解析 HTML 提取真实支付 URL，
            再到支付页面上捞取二维码图片，返回给前端直接展示
        传出：
            包含 paymentUrl（支付跳转链接）、qrCodeImage（二维码 base64 图片）、
            paymentOrderId、paymentRecordId 的字典
        异常：
            ValueError: iaitouzi 不可达或返回异常
        """
        # 前端值到 iaitouzi type 参数映射
        # iaitouzi 的 type 参数：alipay=支付宝, wxpay=微信支付
        支付方式映射: dict[str, str] = {
            "alipay": "alipay",
            "wechat": "wxpay",
        }
        iaitouzi支付方式 = 支付方式映射.get(支付方式, "")

        # 订单金额：内部订单以元为单位，iaitouzi 要求以分（fen）为单位
        金额元 = float(内部订单.总金额)
        金额分 = int(round(金额元 * 100))

        # 商户自主生成订单号（使用本地订单 ID + 时间戳确保唯一）
        订单号 = f"{内部订单.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 组装请求参数
        请求参数: dict[str, str] = {
            "app_id": self.应用ID,
            "order_title": f"游戏代肝订单 #{内部订单.id}",
            "order_price": str(金额分),
            "order_num": 订单号,
            "order_remark": 联系方式,
            "notify_url": self.异步通知地址,
            "return_url": 重定向地址,
        }
        # 如果指定了支付方式，加入 type 参数传给 iaitouzi
        if iaitouzi支付方式:
            请求参数["type"] = iaitouzi支付方式

        # 调用库函数：生成 MD5 签名
        签名 = self._生成签名(请求参数)
        请求参数["sign"] = 签名

        # 调用库函数：发送 POST 请求到 iaitouzi 支付网关
        # 传入：支付网关 URL、表单数据、超时时间
        # 作用：向 iaitouzi 提交支付请求，跟随重定向获取最终 HTML
        # 传出：最终 HTTP 响应对象（已跟随所有重定向）
        日志记录器.info(f"向 iaitouzi 发起支付请求，订单号: {订单号}，金额: {金额分}分")

        # 调用库函数：创建 httpx 异步客户端
        # 传入：超时 30 秒，不自动跟随重定向（手动处理以保持 POST 方法）
        # 作用：发送 POST 请求到 iaitouzi 网关
        # 传出：HTTP 响应对象
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as 客户端:
            响应数据 = await 客户端.post(
                self.支付网关地址,
                data=请求参数,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            # iaitouzi 可能返回 301/302 重定向（如 /core/api/request/pay → /core/api/request/pay/）
            # 必须用 POST 方法跟随重定向，否则 POST 数据会丢失
            if 响应数据.status_code in (301, 302, 307, 308):
                重定向地址 = 响应数据.headers.get("Location", "")
                日志记录器.info(f"iaitouzi 返回 {响应数据.status_code}，跟随重定向: {重定向地址}")
                if 重定向地址:
                    if not 重定向地址.startswith("http"):
                        from urllib.parse import urljoin
                        重定向地址 = urljoin("https://iaitouzi.com/", 重定向地址)
                    响应数据 = await 客户端.post(
                        重定向地址,
                        data=请求参数,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

        响应文本 = 响应数据.text.strip()

        # === 第一步：尝试解析 JSON 响应 ===
        # 调用库函数：尝试将响应文本解析为 JSON
        # 传入：响应文本字符串
        # 作用：判断 iaitouzi 是否返回了 JSON 格式的支付 URL
        # 传出：True=解析成功并提取到 URL，抛出异常或返回 False
        try:
            响应JSON = json.loads(响应文本)
            if isinstance(响应JSON, dict):
                # 遍历常见字段名提取支付 URL
                支付URL = (
                    响应JSON.get("payUrl") or
                    响应JSON.get("pay_url") or
                    响应JSON.get("url") or
                    响应JSON.get("data", {}).get("payUrl") or
                    响应JSON.get("data", {}).get("url")
                )
                if 支付URL:
                    # 解析相对 URL
                    if not 支付URL.startswith("http"):
                        from urllib.parse import urljoin
                        支付URL = urljoin("https://iaitouzi.com/", 支付URL.lstrip("/"))
                    日志记录器.info(f"iaitouzi 返回 JSON 支付 URL: {支付URL[:80]}...")
                    # 调用库方法：从支付页面提取二维码图片
                    # 传入：支付页面的 URL
                    # 作用：访问支付页面，捞取其中的二维码图片，转为 base64 编码后返回
                    # 传出：base64 data URL 字符串，或 None（提取失败时返回 None，不阻塞支付流程）
                    二维码图片 = await self._提取二维码图片(支付URL)
                    # 保存支付记录
                    支付记录 = await self._保存支付记录(数据库, 内部订单, 订单号, 金额元, 支付URL)
                    return {
                        "paymentUrl": 支付URL,
                        "qrCodeImage": 二维码图片,
                        "formData": {},
                        "paymentOrderId": 订单号,
                        "paymentRecordId": 支付记录.id,
                    }

                # JSON 返回但无支付 URL，可能是错误信息
                错误信息 = 响应JSON.get("msg") or 响应JSON.get("message") or 响应JSON.get("error") or "未知错误"
                raise ValueError(f"iaitouzi 创建订单失败: {错误信息}")
        except json.JSONDecodeError:
            pass  # 非 JSON 响应，继续处理 HTML

        # === 第二步：从 HTML 中提取支付表单 ===
        # iaitouzi 返回 HTML 页面（含自动提交表单），提取 form action + hidden inputs
        支付表单 = self._从HTML提取支付表单(响应文本)
        if 支付表单 and 支付表单["action"]:
            支付URL = 支付表单["action"]
            formData = 支付表单["formData"]
            日志记录器.info(f"从 iaitouzi HTML 提取到支付表单: action={支付URL[:80]}..., inputs={len(formData)}个")
            # 调用库方法：从支付页面提取二维码图片
            # 传入：支付页面的 URL
            # 作用：访问支付页面，捞取其中的二维码图片，转为 base64 编码后返回
            # 传出：base64 data URL 字符串，或 None（提取失败时返回 None，不阻塞支付流程）
            二维码图片 = await self._提取二维码图片(支付URL)
            支付记录 = await self._保存支付记录(数据库, 内部订单, 订单号, 金额元, 支付URL)
            return {
                "paymentUrl": 支付URL,
                "qrCodeImage": 二维码图片,
                "formData": formData,
                "paymentOrderId": 订单号,
                "paymentRecordId": 支付记录.id,
            }

        # === 第三步：检查响应文本是否为纯 URL ===
        # iaitouzi 可能直接返回支付页面 URL（纯文本，无 HTML 标签）
        if 响应文本.startswith("http://") or 响应文本.startswith("https://"):
            支付URL = 响应文本.strip()
            日志记录器.info(f"iaitouzi 返回纯文本支付 URL: {支付URL[:80]}...")
            # 调用库方法：从支付页面提取二维码图片
            # 传入：支付页面的 URL
            # 作用：访问支付页面，捞取其中的二维码图片，转为 base64 编码后返回
            # 传出：base64 data URL 字符串，或 None（提取失败时返回 None，不阻塞支付流程）
            二维码图片 = await self._提取二维码图片(支付URL)
            支付记录 = await self._保存支付记录(数据库, 内部订单, 订单号, 金额元, 支付URL)
            return {
                "paymentUrl": 支付URL,
                "qrCodeImage": 二维码图片,
                "formData": {},
                "paymentOrderId": 订单号,
                "paymentRecordId": 支付记录.id,
            }

        # === 第四步：兜底 — 无法提取支付 URL ===
        日志记录器.error(f"无法从 iaitouzi 响应中提取支付 URL，响应前500字符: {响应文本[:500]}")
        raise ValueError("iaitouzi 支付网关返回异常，无法获取支付链接")

    async def _提取二维码图片(self, 支付URL: str) -> Optional[str]:
        """
        访问支付页面，提取其中的二维码图片，返回 base64 data URL。

        流程：
            1. 用 httpx GET 请求支付页面（跟随重定向）
            2. 从 HTML 中查找二维码图片
            3. 优先找 base64 编码的 data URL 图片
            4. 其次找含 qr/qrcode 关键词的外链图片，下载后转 base64
            5. 兜底找页面中第一张图片

        传入：
            支付URL：支付页面的完整 URL（如支付宝/微信的支付页面）
        作用：
            访问支付页面，提取其中的二维码图片，转为 base64 编码供前端直接展示
        传出：
            base64 data URL 字符串，或 None（提取失败不阻塞支付流程）
        """
        try:
            # 调用库函数：创建 httpx 异步客户端
            # 传入：超时 15 秒，自动跟随重定向
            # 作用：向支付页面发送 GET 请求，获取 HTML 内容
            # 传出：HTTP 响应对象
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as 客户端:
                # 调用库方法：发送 GET 请求
                # 传入：支付页面 URL，浏览器 User-Agent 头
                # 作用：模拟浏览器访问支付页面，获取页面 HTML
                # 传出：HTTP 响应对象，含状态码和页面内容
                响应 = await 客户端.get(
                    支付URL,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        )
                    },
                )

                if 响应.status_code != 200:
                    日志记录器.warning(f"访问支付页面失败，HTTP {响应.status_code}: {支付URL[:60]}...")
                    return None

                HTML内容: str = 响应.text

                # ---- 策略1：找含 qr/qrcode 关键词的 base64 图片 ----
                # 支付宝/微信支付页面中二维码通常是 base64 编码的 data URL
                # 传入：HTML 字符串，正则 pattern
                # 作用：匹配 <img> 标签，src 为 data:image 且含 qr 关键词
                # 传出：re.Match 对象或 None
                base64含QR = re.search(
                    r'<img[^>]*src=["\'](data:image/[^"\']+)["\'][^>]*(?:alt|class|id)[^>]*([Qq][Rr])[^>]*>',
                    HTML内容,
                )
                if base64含QR:
                    日志记录器.info("策略1匹配：支付页面含 qr 关键词的 base64 二维码图片")
                    return base64含QR.group(1)

                # ---- 策略2：找所有 base64 图片，取第一张 ----
                # 传入：HTML 字符串，正则 pattern
                # 作用：匹配所有 <img src="data:image/..."> 的 base64 图片
                # 传出：匹配结果列表
                base64所有 = re.findall(
                    r'<img[^>]*src=["\'](data:image/[^"\']+(?:;base64)?[^"\']*)["\'][^>]*>',
                    HTML内容,
                    re.IGNORECASE,
                )
                if base64所有:
                    日志记录器.info(f"策略2匹配：支付页面有 {len(base64所有)} 张 base64 图片，取第一张")
                    return base64所有[0]

                # ---- 策略3：找含 qr/qrcode 关键词的外部图片 URL ----
                # 传入：HTML 字符串，正则 pattern
                # 作用：匹配 <img> 标签中 src 为外部 HTTP URL 且文件名含 qr 关键词
                # 传出：re.Match 对象或 None
                外链QR = re.search(
                    r'<img[^>]*src=["\'](https?://[^"\']*(?:qr|qrcode|code|pay)[^"\']*\.(?:png|jpg|jpeg|gif))["\'][^>]*>',
                    HTML内容,
                    re.IGNORECASE,
                )
                if 外链QR:
                    图片URL: str = 外链QR.group(1)
                    日志记录器.info(f"策略3匹配：支付页面含外链二维码图片: {图片URL[:60]}...")
                    # 下载外部图片并转 base64
                    # 传入：图片 URL
                    # 作用：下载二维码图片的二进制数据
                    # 传出：图片响应对象
                    图片响应 = await 客户端.get(图片URL)
                    if 图片响应.status_code == 200:
                        # 调用库函数：将二进制数据编码为 base64 字符串
                        # 传入：图片的原始二进制字节数据
                        # 作用：将图片转换为 base64 文本，用于 data URL
                        # 传出：base64 编码的字符串
                        图片base64: str = base64.b64encode(图片响应.content).decode("utf-8")
                        内容类型: str = 图片响应.headers.get("content-type", "image/png")
                        return f"data:{内容类型};base64,{图片base64}"

                # ---- 策略4：兜底 — 取页面中第一张图片 ----
                # 传入：HTML 字符串，正则 pattern
                # 作用：匹配任意 <img> 标签的 src 外部 URL
                # 传出：匹配结果列表
                任意图片 = re.findall(
                    r'<img[^>]*src=["\'](https?://[^"\']+)["\'][^>]*>',
                    HTML内容,
                    re.IGNORECASE,
                )
                if 任意图片:
                    首张图片URL: str = 任意图片[0]
                    日志记录器.info(f"策略4兜底：取支付页面第一张图片: {首张图片URL[:60]}...")
                    图片响应 = await 客户端.get(首张图片URL)
                    if 图片响应.status_code == 200:
                        图片base64 = base64.b64encode(图片响应.content).decode("utf-8")
                        内容类型 = 图片响应.headers.get("content-type", "image/png")
                        return f"data:{内容类型};base64,{图片base64}"

                日志记录器.warning("支付页面未找到任何图片，无法提取二维码")
                return None

        except Exception as 异常:
            日志记录器.error(f"提取二维码图片异常: {异常}")
            return None

    async def _保存支付记录(
        self,
        数据库: AsyncSession,
        内部订单: 订单表,
        订单号: str,
        金额元: float,
        支付链接: str,
    ) -> 支付记录表:
        """
        保存支付记录到本地数据库。

        传入：
            数据库：异步数据库会话
            内部订单：本地订单表对象
            订单号：商户生成的唯一订单号（用作支付平台订单ID）
            金额元：支付金额（元）
            支付链接：支付平台返回的跳转链接
        作用：
            创建支付记录表条目并写入数据库
        传出：
            支付记录表 ORM 对象
        """
        支付记录 = 支付记录表(
            内部订单ID=内部订单.id,
            支付平台订单ID=订单号,
            支付金额=金额元,
            支付状态="pending",
            支付链接=支付链接,
        )
        数据库.add(支付记录)
        await 数据库.commit()
        await 数据库.refresh(支付记录)
        return 支付记录

    async def 获取支付链接(
        self,
        支付记录: 支付记录表,
        支付方式: str = "",
        重定向地址: Optional[str] = None,
        回调地址: Optional[str] = None,
    ) -> str:
        """
        获取 iaitouzi 支付跳转链接。

        传入：
            支付记录：本地支付记录表对象
            支付方式：本平台忽略（iaitouzi 统一支付页面选择）
            重定向地址：支付成功后跳转的前端页面地址
            回调地址：忽略（创建订单时已固定）
        作用：
            返回存储的支付链接（创建订单时已从 iaitouzi 获取并保存）
        传出：
            支付跳转 URL 字符串
        """
        if not 支付记录.支付链接:
            raise ValueError("支付链接为空，请先创建支付订单")

        支付记录.支付方式 = 支付方式 or "iaitouzi"
        return 支付记录.支付链接

    async def 查询订单状态(
        self,
        支付记录: 支付记录表,
    ) -> str:
        """
        查询 iaitouzi 平台上的订单支付状态。

        注意：iaitouzi 平台未提供主动查询订单状态的 API，
        此方法仅返回本地记录的支付状态。

        传入：
            支付记录：本地支付记录表对象
        作用：
            返回本地数据库记录的支付状态（主动查询需等平台提供 API）
        传出：
            支付状态字符串: pending, paid, expired, refunded
        """
        return 支付记录.支付状态

    def _验证回调签名(self, 回调参数: dict) -> bool:
        """
        验证 iaitouzi 回调通知的签名。

        传入：
            回调参数：iaitouzi 异步通知 POST 的所有参数
        作用：
            1. 提取 sign 字段
            2. 使用除 sign 外的其他参数重新计算签名
            3. 比较计算出的签名与接收到的 sign 是否一致
        传出：
            True=签名验证通过，False=签名验证失败
        """
        接收到的签名 = 回调参数.pop("sign", "")
        if not 接收到的签名:
            日志记录器.warning("iaitouzi 回调缺少 sign 参数")
            return False

        期望签名 = self._生成签名(回调参数)
        if 接收到的签名 != 期望签名:
            日志记录器.warning(f"iaitouzi 回调签名验证失败: 接收={接收到的签名}, 期望={期望签名}")
            return False
        return True

    async def 处理支付回调(
        self,
        数据库: AsyncSession,
        回调数据: dict,
    ) -> dict:
        """
        处理 iaitouzi 支付成功的异步回调通知。

        传入：
            数据库：异步数据库会话
            回调数据：iaitouzi POST 发送的回调参数（order_num, pay_source, order_remark, order_price, sign）
        作用：
            1. 验证回调签名
            2. 根据 order_num 找到本地支付记录
            3. 更新支付状态为 paid
            4. 将本地内部订单状态从待支付更新为待审核
        传出：
            处理结果字典（返回 "success" 字符串表示回调处理成功）
        异常：
            ValueError: 签名验证失败、订单不存在等
        """
        if not self._验证回调签名(dict(回调数据)):
            raise ValueError("回调签名验证失败")

        订单号 = 回调数据.get("order_num")
        if not 订单号:
            raise ValueError("回调数据缺少 order_num")

        查询 = select(支付记录表).where(支付记录表.支付平台订单ID == 订单号)
        结果 = await 数据库.execute(查询)
        支付记录 = 结果.scalar_one_or_none()

        if not 支付记录:
            raise ValueError(f"未找到支付记录: {订单号}")

        支付记录.支付状态 = "paid"
        支付记录.支付时间 = datetime.now()
        支付记录.回调原始数据 = str(回调数据)

        内部订单查询 = select(订单表).where(订单表.id == 支付记录.内部订单ID)
        内部订单结果 = await 数据库.execute(内部订单查询)
        内部订单 = 内部订单结果.scalar_one_or_none()

        if 内部订单 and 内部订单.状态 == 订单状态枚举.待支付.value:
            内部订单.状态 = 订单状态枚举.待审核.value

        await 数据库.commit()

        日志记录器.info(f"iaitouzi 回调处理成功，订单号: {订单号}，金额: {回调数据.get('pay_source', '未知')}分")
        return {"code": 0, "message": "回调处理成功"}

    async def 自动初始化支付平台(self) -> bool:
        """
        自动初始化 iaitouzi 支付平台配置。
        本平台无需要初始化的项目和 SKU，直接返回 True。

        传入：无
        作用：检查配置是否完整
        传出：True=配置完整
        """
        if not self.应用ID or not self.应用密钥:
            日志记录器.error("iaitouzi 配置不完整: 缺少 应用ID 或 应用密钥")
            return False
        日志记录器.info("iaitouzi 支付平台配置检查通过")
        return True


# 全局单例
支付服务对象 = 支付服务类()
