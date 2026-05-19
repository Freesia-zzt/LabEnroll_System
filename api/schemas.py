"""API Schema 定义."""
from datetime import datetime
from typing import List, Optional

from ninja import Schema


class MessageSchema(Schema):
    """通用消息响应."""
    message: str


class EnrollmentSchema(Schema):
    """报名表单 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    user_id: int
    course_name: str
    department: str
    position: str
    reason: str
    status: str
    submitted_at: datetime
    updated_at: datetime


class EnrollmentCreateSchema(Schema):
    """创建报名表单 Schema."""
    course_name: str
    department: str
    position: str
    reason: str


class EnrollmentUpdateSchema(Schema):
    """更新报名表单 Schema."""
    course_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    reason: Optional[str] = None


class EnrollmentStatusSchema(Schema):
    """报名状态 Schema."""
    status: str


class EnrollmentDraftSchema(Schema):
    """报名草稿 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    user_id: int
    course_name: str
    department: str
    position: str
    reason: str
    draft_data: dict
    created_at: datetime
    updated_at: datetime


class EnrollmentDraftCreateSchema(Schema):
    """创建报名草稿 Schema."""
    course_name: Optional[str] = ""
    department: Optional[str] = ""
    position: Optional[str] = ""
    reason: Optional[str] = ""
    draft_data: Optional[dict] = None


class EnrollmentFileSchema(Schema):
    """报名文件 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    enrollment_id: Optional[int]
    draft_id: Optional[int]
    file_name: str
    file_size: int
    uploaded_at: datetime


class PaginatedEnrollmentList(Schema):
    """分页报名列表 Schema."""
    total: int
    page: int
    page_size: int
    items: List[EnrollmentSchema]


class PaginatedDraftList(Schema):
    """分页草稿列表 Schema."""
    total: int
    page: int
    page_size: int
    items: List[EnrollmentDraftSchema]
