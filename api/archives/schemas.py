"""数据存档 Schema 定义."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ninja import Schema


class ArchiveCreateSchema(Schema):
    """创建存档请求."""
    archive_year: str


class ArchiveOutSchema(Schema):
    """存档输出 Schema."""
    id: int
    year: str
    total_applications: int
    admitted_count: int
    major_stats: Dict[str, Any]
    grade_stats: Dict[str, Any]
    created_at: datetime
    operator_name: Optional[str] = None


class ArchiveDetailSchema(Schema):
    """存档详情 Schema."""
    id: int
    year: str
    total_applications: int
    admitted_count: int
    major_stats: Dict[str, Any]
    grade_stats: Dict[str, Any]
    archive_data: Dict[str, Any]
    created_at: datetime
    operator_name: Optional[str] = None
