"""管理员模块 Schema 定义."""
from datetime import datetime
from typing import Any, Optional

from ninja import Schema


# ==================== 基础响应 Schema ====================

class AdminResponseSchema(Schema):
    """统一管理员 API 响应格式."""
    code: int = 200
    message: str = "success"
    data: Any = None


# ==================== 管理员登录 Schema ====================

class AdminLoginInput(Schema):
    """管理员登录请求."""
    username: str
    password: str


class AdminLoginData(Schema):
    """管理员登录响应数据."""
    token: str
    user_id: int
    username: str
    role: str


# ==================== 管理员信息 Schema ====================

class AdminProfileSchema(Schema):
    """管理员信息 Schema."""
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    date_joined: datetime


# ==================== 修改密码 Schema ====================

class AdminChangePasswordInput(Schema):
    """管理员修改密码请求."""
    old_password: str
    new_password: str


class AdminChangePasswordSchema(Schema):
    """管理员修改密码响应."""
    code: int = 200
    message: str = "密码修改成功"
    data: None = None
