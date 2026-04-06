import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from typing import Optional


class EmailService:
    @staticmethod
    async def send_verification_code(email: str, code: str) -> bool:
        """
        发送验证码邮件
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_FROM
            msg['To'] = email
            msg['Subject'] = '游戏代练平台 - 注册验证码'

            html_content = f"""
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
                        <span style="font-size: 24px; font-weight: bold; color: #6366f1;">{code}</span>
                    </div>
                    <p>验证码有效期为15分钟，请尽快使用。</p>
                    <p>如果您没有请求此验证码，请忽略此邮件。</p>
                    <p style="margin-top: 30px; font-size: 12px; color: #999;">此邮件由系统自动发送，请勿回复。</p>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 根据端口选择连接方式：465端口使用SSL，587端口使用STARTTLS
            if settings.SMTP_PORT == 465:
                async with aiosmtplib.SMTP(
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    use_tls=True
                ) as smtp:
                    await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    await smtp.send_message(msg)
            else:
                async with aiosmtplib.SMTP(
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    start_tls=True
                ) as smtp:
                    await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    await smtp.send_message(msg)

            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False


email_service = EmailService()
