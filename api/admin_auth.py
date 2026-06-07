"""管理员认证工具模块."""
from typing import Any               # 从typing导入Any，表示任意类型

from ninja.security import HttpBearer  # 从ninja.security导入HttpBearer，用于Token认证基类

from .auth_utils import decode_token, is_token_blacklisted  # 从同级目录导入：Token解码函数、检查Token是否在黑名单的函数
from .models import LabUser          # 从同级目录导入：LabUser模型类


def admin_response(                  # 定义统一响应构造函数
    code: int = 200,                 # 参数：状态码，默认200，类型为整数
    message: str = "success",        # 参数：消息，默认"success"，类型为字符串
    data: Any = None                 # 参数：数据，默认None，类型为任意
) -> dict:                           # 返回值类型注解为字典
    """统一管理员 API 响应格式.
    
    Args:
        code: 状态码
        message: 消息
        data: 数据
        
    Returns:
        响应字典
    """
    return {"code": code, "message": message, "data": data}  # 返回构造好的字典


class AdminAuthBearer(HttpBearer):   # 定义认证类，继承HttpBearer基类
    """管理员认证类 - 同时兼容 Token 和 Bearer 格式."""

    def authenticate(                # 重写authenticate方法，这是HttpBearer要求的方法
        self,                        # self表示实例本身
        request: Any,                # 参数：请求对象，类型为Any
        token: str                   # 参数：从请求头中提取的Token字符串
    ) -> LabUser | None:             # 返回值类型注解为LabUser或None，认证成功返回用户，失败返回None
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
        payload = decode_token(token)  # 调用auth_utils的decode_token函数解码Token，返回载荷字典
        if payload is None:           # if条件：如果解码失败返回None
            return None               # 返回None表示认证失败

        if payload.get("token_type") != "access":  # if条件：检查Token类型是否为access（访问Token）
            return None               # 不是访问Token（可能是刷新Token），认证失败

        if is_token_blacklisted(payload.get("jti", "")):  # if条件：检查Token是否在黑名单（jti是Token唯一标识）
            return None               # Token已被拉黑（用户已登出），认证失败

        try:                          # try块：尝试查询用户
            user = LabUser.objects.get(id=payload["user_id"])  # 从载荷中获取user_id，查询对应用户
        except LabUser.DoesNotExist:  # except块：捕获用户不存在异常
            return None               # 用户不存在，认证失败

        if user.is_active != 1:       # if条件：检查用户是否激活（1表示激活）
            return None               # 用户未激活，认证失败

        return user                   # 所有检查通过，返回用户对象，认证成功


def require_admin(                   # 定义检查管理员权限的函数
    user: LabUser                    # 参数：用户实例，类型为LabUser
) -> bool:                           # 返回值类型注解为布尔值
    """检查用户是否为管理员.
    
    Args:
        user: 用户实例
        
    Returns:
        是否是管理员
        
    Raises:
        PermissionError: 用户不是管理员
    """
    if user.role != 2:                # if条件：检查用户角色是否不等于2（2表示管理员）
        raise PermissionError("需要管理员权限")  # 不是管理员，抛出PermissionError异常
    return True                       # 是管理员，返回True


def get_role_string(                 # 定义角色代码转字符串的函数
    role: int                        # 参数：角色代码，类型为整数
) -> str:                            # 返回值类型注解为字符串
    """将角色数字转换为字符串.
    
    Args:
        role: 角色代码 (1=学员, 2=管理员)
        
    Returns:
        角色字符串
    """
    role_map = {1: "user", 2: "admin"}  # 定义角色映射字典，1对应"user"，2对应"admin"
    return role_map.get(role, "unknown")  # 使用get方法查询，找不到返回"unknown"
