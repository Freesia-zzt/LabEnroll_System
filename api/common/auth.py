"""Token认证模块.

基于 django-ninja 的 HttpBearer 实现 Token 认证。
"""

from typing import Optional

from django.http import HttpRequest
from ninja.errors import AuthenticationError
from ninja.security import HttpBearer

from api.models import Admin


class TokenAuth(HttpBearer):
    """Token 认证类.

    继承自 ninja.security.HttpBearer，实现基于 Token 的认证。
    从请求头 Authorization: Bearer <token> 中提取 token 并验证。
    """

    def authenticate(
        self,
        request: HttpRequest,
        token: str,
    ) -> Optional[Admin]:
        """验证 Token 并返回对应的用户.

        Args:
            request: HTTP 请求对象
            token: 从请求头提取的 token 字符串

        Returns:
            验证成功返回 Admin 实例，失败返回 None

        Raises:
            AuthenticationError: Token 无效或用户不存在
        """
        try:
            admin = Admin.objects.get(token=token, is_active=True)
            request.admin = admin
            return admin
        except Admin.DoesNotExist as err:
            raise AuthenticationError("无效的Token或用户已被禁用") from err


token_auth = TokenAuth()
