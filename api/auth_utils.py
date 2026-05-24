"""JWT 认证工具模块."""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
from django.conf import settings
from django.utils import timezone
from ninja.security import HttpBearer

from api.models import LabUser, TokenBlacklist

logger = logging.getLogger("api.auth")


def api_response(code: int = 200, msg: str = "操作成功", data: Any = None) -> dict:
    """统一 API 响应格式. {"code": int, "msg": str, "data": object|null}"""
    return {"code": code, "msg": msg, "data": data}


def create_access_token(user: LabUser, remember_me: bool = False) -> str:
    """生成 Access Token.

    Args:
        user: 用户实例
        remember_me: 是否记住我（延长有效期到7天）

    Returns:
        JWT access token 字符串
    """
    expire_hours = (
        settings.JWT_REMEMBER_ME_EXPIRE_DAYS * 24
        if remember_me
        else settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS
    )
    now = timezone.now()
    payload = {
        "user_id": user.id,
        "role": user.role,
        "account": user.account,
        "token_type": "access",
        "jti": f"acc_{user.id}_{int(now.timestamp())}",
        "iat": now,
        "exp": now + timedelta(hours=expire_hours),
    }
    token = jwt.encode(
        {k: v.isoformat() if isinstance(v, datetime) else v for k, v in payload.items()},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def create_refresh_token(user: LabUser) -> str:
    """生成 Refresh Token.

    Args:
        user: 用户实例

    Returns:
        JWT refresh token 字符串（有效期7天）
    """
    now = timezone.now()
    payload = {
        "user_id": user.id,
        "token_type": "refresh",
        "jti": f"ref_{user.id}_{int(now.timestamp())}",
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    token = jwt.encode(
        {k: v.isoformat() if isinstance(v, datetime) else v for k, v in payload.items()},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def decode_token(token: str) -> Optional[dict]:
    """解码并验证 JWT Token.

    Args:
        token: JWT token 字符串

    Returns:
        解码后的 payload 字典，无效返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token 已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"无效 Token: {e}")
        return None


def is_token_blacklisted(jti: str) -> bool:
    """检查 Token 是否在黑名单中.

    Args:
        jti: Token 的唯一标识

    Returns:
        是否在黑名单中
    """
    return TokenBlacklist.objects.filter(jti=jti).exists()


class AuthBearer(HttpBearer):
    """JWT Bearer 认证类（django-ninja 认证后端）."""

    def authenticate(self, request: Any, token: str) -> Optional[LabUser]:
        """验证 Bearer Token.

        Args:
            request: 请求对象
            token: Authorization header 中的 token 字符串

        Returns:
            认证通过返回 LabUser 实例，否则返回 None
        """
        payload = decode_token(token)
        if payload is None:
            return None

        if payload.get("token_type") != "access":
            logger.warning("非 Access Token 用于认证")
            return None

        if is_token_blacklisted(payload.get("jti", "")):
            logger.warning("Token 已被加入黑名单")
            return None

        try:
            user = LabUser.objects.get(id=payload["user_id"])
        except LabUser.DoesNotExist:
            logger.warning(f"用户不存在: {payload.get('user_id')}")
            return None

        if user.is_active != 1:
            logger.warning(f"用户未激活: {user.account}")
            return None

        return user


auth_bearer = AuthBearer()


class IsAdmin:
    """管理员权限验证类.

    用于需要管理员角色的接口：检查用户已认证且 role == 2
    """

    def __call__(self, request: Any) -> bool:
        if not hasattr(request, "auth") or not request.auth:
            return False
        user: LabUser = request.auth
        return user.role == 2
