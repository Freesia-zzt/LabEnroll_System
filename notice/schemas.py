"""招新公告与系统配置 - Schema 定义."""

from datetime import datetime

from ninja import Schema
from pydantic import Field


class NoticeCreateInput(Schema):
    """创建公告请求."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    order: int = Field(default=0)
    is_published: bool = Field(default=True)


class NoticeUpdateInput(Schema):
    """更新公告请求."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    order: int | None = Field(default=None)
    is_published: bool | None = Field(default=None)


class NoticeOut(Schema):
    """公告详情输出."""

    id: int
    title: str
    content: str
    order: int
    is_published: bool
    created_at: datetime
    updated_at: datetime


class NoticeBriefOut(Schema):
    """公告简要输出（前台列表展示）."""

    id: int
    title: str
    order: int
    is_published: bool
    created_at: datetime


class PaginationOut(Schema):
    """分页信息."""

    total: int
    page: int
    per_page: int
    last_page: int


class NoticeListOut(Schema):
    """公告列表响应."""

    list: list[NoticeOut]
    pagination: PaginationOut


class NoticeBriefListOut(Schema):
    """公告简要列表响应."""

    list: list[NoticeBriefOut]
    pagination: PaginationOut


class EnrollmentSwitchOut(Schema):
    """报名开关响应."""

    is_open: bool


class EnrollmentSwitchUpdateInput(Schema):
    """报名开关修改请求."""

    is_open: bool = Field(...)
