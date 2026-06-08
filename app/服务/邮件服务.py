import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.核心.配置 import 配置对象
from app.核心.日志 import 获取日志记录器
from typing import Optional

日志记录器 = 获取日志记录器(__name__)


class 邮件服务类:
    """邮件发送服务，支持验证码和通知类邮件"""

    @staticmethod
    async def 发送验证码邮件(收件邮箱: str, 验证码: str) -> bool:
        """
        发送注册验证码邮件

        Args:
            收件邮箱: 收件人邮箱地址
            验证码: 6位数字验证码

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        try:
            邮件对象 = MIMEMultipart()
            邮件对象['From'] = 配置对象.邮件发送者地址
            邮件对象['To'] = 收件邮箱
            邮件对象['Subject'] = '游戏代练平台 - 注册验证码'

            html内容 = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>注册验证码</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                    <h2 style="color: #333; text-align: center;">游戏代练交易平台</h2>
                    <p>尊敬的用户：</p>
                    <p>您正在注册游戏代练交易平台账号，您的验证码是：</p>
                    <div style="background-color: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0; border-radius: 4px;">
                        <span style="font-size: 24px; font-weight: bold; color: #6366f1;">{验证码}</span>
                    </div>
                    <p>验证码有效期为15分钟，请尽快使用。</p>
                    <p>如果您没有请求此验证码，请忽略此邮件。</p>
                    <p style="margin-top: 30px; font-size: 12px; color: #999;">此邮件由系统自动发送，请勿回复。</p>
                </div>
            </body>
            </html>
            """

            邮件对象.attach(MIMEText(html内容, 'html', 'utf-8'))

            if 配置对象.邮件SMTP端口 == 465:
                async with aiosmtplib.SMTP(
                    hostname=配置对象.邮件SMTP主机,
                    port=配置对象.邮件SMTP端口,
                    use_tls=True
                ) as smtp:
                    await smtp.login(配置对象.邮件SMTP用户名, 配置对象.邮件SMTP密码)
                    await smtp.send_message(邮件对象)
            else:
                async with aiosmtplib.SMTP(
                    hostname=配置对象.邮件SMTP主机,
                    port=配置对象.邮件SMTP端口,
                    start_tls=True
                ) as smtp:
                    await smtp.login(配置对象.邮件SMTP用户名, 配置对象.邮件SMTP密码)
                    await smtp.send_message(邮件对象)

            return True
        except Exception as e:
            日志记录器.error(f"邮件发送失败: {e}", exc_info=True)
            return False

    @staticmethod
    async def 发送密码重置验证码邮件(收件邮箱: str, 验证码: str) -> bool:
        """
        发送密码重置验证码邮件

        Args:
            收件邮箱: 收件人邮箱地址
            验证码: 6位数字验证码

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        try:
            邮件对象 = MIMEMultipart()
            邮件对象['From'] = 配置对象.邮件发送者地址
            邮件对象['To'] = 收件邮箱
            邮件对象['Subject'] = '游戏代练平台 - 密码重置验证码'

            html内容 = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>密码重置验证码</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                    <h2 style="color: #333; text-align: center;">游戏代练交易平台</h2>
                    <p>尊敬的用户：</p>
                    <p>您正在重置游戏代练交易平台账号密码，您的验证码是：</p>
                    <div style="background-color: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0; border-radius: 4px;">
                        <span style="font-size: 24px; font-weight: bold; color: #ef4444;">{验证码}</span>
                    </div>
                    <p>验证码有效期为10分钟，请尽快使用。</p>
                    <p style="color: #ef4444; font-weight: bold;">如果这不是您本人的操作，请立即修改密码以保护账号安全。</p>
                    <p>如果您没有请求此验证码，请忽略此邮件。</p>
                    <p style="margin-top: 30px; font-size: 12px; color: #999;">此邮件由系统自动发送，请勿回复。</p>
                </div>
            </body>
            </html>
            """

            邮件对象.attach(MIMEText(html内容, 'html', 'utf-8'))

            if 配置对象.邮件SMTP端口 == 465:
                async with aiosmtplib.SMTP(
                    hostname=配置对象.邮件SMTP主机,
                    port=配置对象.邮件SMTP端口,
                    use_tls=True
                ) as smtp:
                    await smtp.login(配置对象.邮件SMTP用户名, 配置对象.邮件SMTP密码)
                    await smtp.send_message(邮件对象)
            else:
                async with aiosmtplib.SMTP(
                    hostname=配置对象.邮件SMTP主机,
                    port=配置对象.邮件SMTP端口,
                    start_tls=True
                ) as smtp:
                    await smtp.login(配置对象.邮件SMTP用户名, 配置对象.邮件SMTP密码)
                    await smtp.send_message(邮件对象)

            return True
        except Exception as e:
            日志记录器.error(f"密码重置邮件发送失败: {e}", exc_info=True)
            return False


邮件服务对象 = 邮件服务类()
