"""API Schema 定义."""

from datetime import datetime
from typing import List, Optional

from ninja import Schema


# ==================== 基础响应 Schema ====================

class MessageSchema(Schema):
    """通用消息响应."""
    message: str


class PaginationSchema(Schema):
    """分页信息."""
    total: int
    current_page: int
    per_page: int
    last_page: int


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
    category: str = "other"  # 默认其他分类
    attachments: List[str] = []  # 附件URL列表


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
    category: Optional[str] = None  # 按分类筛选
    status: Optional[str] = None    # 按状态筛选
    search: Optional[str] = None    # 搜索关键词


class QuestionBriefSchema(Schema):
    """问题列表项（简要信息）."""
    model_config = dict(from_attributes=True)
    
    id: int
    title: str
    category: str
    category_display: str  # 分类的中文显示
    status: str
    status_display: str    # 状态的中文显示
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
    status: str  # pending, replied, resolved