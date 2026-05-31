"""管理员认证工具模块."""
from typing import Any

from ninja.security import HttpBearer

from .auth_utils import decode_token, is_token_blacklisted
from .models import LabUser


def admin_response(code: int = 200, message: str = "success", data: Any = None) -> dict:
    """统一管理员 API 响应格式.
    
    Args:
        code: 状态码
        message: 消息
        data: 数据
        
    Returns:
        响应字典
    """
    return {"code": code, "message": message, "data": data}


class AdminAuthBearer(HttpBearer):
    """管理员认证类 - 同时兼容 Token 和 Bearer 格式."""

    def authenticate(self, request: Any, token: str) -> LabUser | None:
        """验证 Token.
        
        支持格式:
        - Authorization: Bearer <token>
        - Authorization: Token <token>
        
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
            return None

        if is_token_blacklisted(payload.get("jti", "")):
            return None

        try:
            user = LabUser.objects.get(id=payload["user_id"])
        except LabUser.DoesNotExist:
            return None

        if user.is_active != 1:
            return None

        return user


def require_admin(user: LabUser) -> bool:
    """检查用户是否为管理员.
    
    Args:
        user: 用户实例
        
    Returns:
        是否是管理员
        
    Raises:
        PermissionError: 用户不是管理员
    """
    if user.role != 2:
        raise PermissionError("需要管理员权限")
    return True


def get_role_string(role: int) -> str:
    """将角色数字转换为字符串.
    
    Args:
        role: 角色代码 (1=学员, 2=管理员)
        
    Returns:
        角色字符串
    """
    role_map = {1: "user", 2: "admin"}
    return role_map.get(role, "unknown")
