"""邮件发送工具模块."""

import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger("api.email")


@dataclass
class EmailConfig:
    """邮件配置."""

    subject: str
    to_email: str
    html_content: str
    text_content: str | None = None


def _build_html_template(title: str, code: str, expire_minutes: int, purpose: str) -> str:
    """构建 HTML 邮件模板.

    Args:
        title: 邮件标题
        code: 验证码
        expire_minutes: 过期时间（分钟）
        purpose: 用途说明

    Returns:
        HTML 字符串
    """
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:'Microsoft YaHei','PingFang SC',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;padding:30px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
<tr><td style="background:linear-gradient(135deg,#4A90D9,#357ABD);padding:40px 30px;text-align:center;">
<h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:500;">{title}</h1>
</td></tr>
<tr><td style="padding:40px 30px;">
<p style="margin:0 0 20px;font-size:16px;color:#333;line-height:1.8;">您好：</p>
<p style="margin:0 0 20px;font-size:16px;color:#333;line-height:1.8;">
您收到这封邮件是因为您正在进行<span style="color:#4A90D9;font-weight:bold;">{purpose}</span>操作。
</p>
<div style="background:#f8f9fa;border-radius:8px;padding:30px;text-align:center;margin:25px 0;">
<p style="margin:0 0 10px;font-size:14px;color:#888;">您的验证码为：</p>
<p style="margin:0;font-size:42px;font-weight:bold;color:#4A90D9;letter-spacing:8px;font-family:Consolas,monospace;">{code}</p>
</div>
<p style="margin:0 0 10px;font-size:14px;color:#999;line-height:1.6;">
验证码有效期为 <strong>{expire_minutes} 分钟</strong>，请尽快完成验证。
</p>
<p style="margin:0 0 10px;font-size:14px;color:#999;line-height:1.6;">
如果这不是您本人的操作，请忽略此邮件。
</p>
</td></tr>
<tr><td style="background:#f8f9fa;padding:20px 30px;text-align:center;border-top:1px solid #eee;">
<p style="margin:0;font-size:12px;color:#bbb;">此邮件由系统自动发送，请勿回复</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def send_email(config: EmailConfig) -> bool:
    """发送邮件.

    Args:
        config: 邮件配置

    Returns:
        是否发送成功
    """
    text_content = config.text_content or strip_tags(config.html_content)

    msg = EmailMultiAlternatives(
        subject=config.subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[config.to_email],
    )
    msg.attach_alternative(config.html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        logger.info(f"[邮件发送成功] 收件人: {config.to_email}, 主题: {config.subject}")
        return True
    except Exception as e:
        logger.error(f"[邮件发送失败] 收件人: {config.to_email}, 错误: {e}")
        return False


def send_activation_code_email(to_email: str, code: str, username: str) -> bool:
    """发送账号激活验证码邮件.

    Args:
        to_email: 收件人邮箱
        code: 6位验证码
        username: 用户名

    Returns:
        是否发送成功
    """
    subject = "实验室报名系统 - 账号激活"
    html = _build_html_template(
        title="账号激活",
        code=code,
        expire_minutes=30,
        purpose="账号激活",
    )
    config = EmailConfig(
        subject=subject,
        to_email=to_email,
        html_content=html,
    )
    return send_email(config)


def send_forgot_password_code_email(to_email: str, code: str, username: str) -> bool:
    """发送忘记密码验证码邮件.

    Args:
        to_email: 收件人邮箱
        code: 6位验证码
        username: 用户名

    Returns:
        是否发送成功
    """
    subject = "实验室报名系统 - 密码重置"
    html = _build_html_template(
        title="密码重置",
        code=code,
        expire_minutes=10,
        purpose="找回密码",
    )
    config = EmailConfig(
        subject=subject,
        to_email=to_email,
        html_content=html,
    )
    return send_email(config)
