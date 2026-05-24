"""API Schema 定义."""

from datetime import datetime
from typing import Any, List, Optional

from ninja import Schema


# ==================== 基础响应 Schema ====================

class ApiResponseSchema(Schema):
    """统一 API 响应格式."""
    code: int = 200
    msg: str = "操作成功"
    data: Any = None


class MessageSchema(Schema):
    """通用消息响应."""
    message: str


class PaginationSchema(Schema):
    """分页信息."""
    total: int
    current_page: int
    per_page: int
    last_page: int


# ==================== 认证相关 Schema ====================

class LoginInput(Schema):
    """登录请求."""
    account: str
    password: str
    remember_me: bool = False


class LoginData(Schema):
    """登录响应数据."""
    user_id: int
    account: str
    username: str
    role: int
    token: str
    refresh_token: str


class SendActivationCodeInput(Schema):
    """发送激活码请求."""
    account: str


class VerifyActivationCodeInput(Schema):
    """验证激活码请求."""
    account: str
    activation_code: str


class RefreshTokenInput(Schema):
    """刷新 Token 请求."""
    refresh_token: str


class RefreshTokenData(Schema):
    """刷新 Token 响应数据."""
    token: str
    refresh_token: str


class UpdateInfoInput(Schema):
    """修改个人资料请求."""
    username: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None


class ChangePasswordInput(Schema):
    """修改密码请求."""
    old_password: str
    new_password: str
    new_password_confirmation: str


class ForgotPasswordSendCodeInput(Schema):
    """忘记密码-发送验证码请求."""
    account: str
    email: str


class ForgotPasswordResetInput(Schema):
    """忘记密码-重置密码请求."""
    account: str
    email: str
    code: str
    new_password: str
    new_password_confirmation: str


class UserInfoSchema(Schema):
    """用户完整信息（不含敏感字段）."""
    model_config = dict(from_attributes=True)

    id: int
    account: str
    username: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: int
    is_active: int
    department_id: Optional[int] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ==================== 用户相关 Schema ====================

class UserBriefSchema(Schema):
    """用户简要信息."""
    model_config = dict(from_attributes=True)
    
    id: int
    name: str
    avatar: Optional[str] = None


# ==================== 问题回复 Schema ====================

class QuestionReplyCreateSchema(Schema):
    """创建回复请求."""
    content: str


class QuestionReplySchema(Schema):
    """回复详情."""
    model_config = dict(from_attributes=True)
    
    id: int
    content: str
    author: UserBriefSchema
    created_at: datetime
    updated_at: datetime


# ==================== 问题 Schema ====================

class QuestionCreateSchema(Schema):
    """创建问题请求."""
    title: str
    content: str
    category: str = "other"
    attachments: List[str] = []


class QuestionUpdateSchema(Schema):
    """更新问题请求."""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    attachments: Optional[List[str]] = None


class QuestionFilterSchema(Schema):
    """问题列表筛选参数."""
    page: int = 1
    per_page: int = 10
    category: Optional[str] = None
    status: Optional[str] = None
    search: Optional[str] = None


class QuestionBriefSchema(Schema):
    """问题列表项（简要信息）."""
    model_config = dict(from_attributes=True)
    
    id: int
    title: str
    category: str
    category_display: str
    status: str
    status_display: str
    reply_count: int
    created_at: datetime
    author: UserBriefSchema


class QuestionListSchema(Schema):
    """问题列表响应."""
    data: List[QuestionBriefSchema]
    pagination: PaginationSchema


class QuestionDetailSchema(Schema):
    """问题详情."""
    model_config = dict(from_attributes=True)
    
    id: int
    title: str
    content: str
    category: str
    category_display: str
    status: str
    status_display: str
    attachments: List[str]
    reply_count: int
    created_at: datetime
    updated_at: datetime
    author: UserBriefSchema
    replies: List[QuestionReplySchema]


class QuestionStatusUpdateSchema(Schema):
    """更新问题状态请求."""
    status: str
