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


# ==================== 培训模块 Schema ====================

class CoursewareSchema(Schema):
    """课件 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    title: str
    type: str
    file_url: str
    file_size: int
    duration_minutes: int
    order: int
    created_at: datetime


class ChapterSchema(Schema):
    """章节 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    title: str
    description: str
    order: int
    duration_minutes: int
    coursewares: List[CoursewareSchema]
    created_at: datetime


class CourseListSchema(Schema):
    """课程列表 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    title: str
    description: str
    cover_image: str
    instructor_name: str
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    duration_hours: int
    enrolled_count: int
    enrolled_at: Optional[datetime]


class CourseDetailSchema(Schema):
    """课程详情 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    title: str
    description: str
    cover_image: str
    instructor_id: int
    instructor_name: str
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    duration_hours: int
    chapters: List[ChapterSchema]
    created_at: datetime


class ChapterProgressSchema(Schema):
    """章节进度 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    chapter_id: int
    is_completed: bool
    completed_at: Optional[datetime]


class LearningProgressSchema(Schema):
    """学习进度 Schema."""
    course_id: int
    course_title: str
    status: str
    progress_percent: int
    completed_chapters: int
    total_chapters: int
    enrolled_at: datetime
    completed_at: Optional[datetime]


class TrainingStatisticsSchema(Schema):
    """培训统计 Schema."""
    total_courses: int
    completed_courses: int
    in_progress_courses: int
    total_learning_hours: float
    total_assignments: int
    completed_assignments: int
    pending_assignments: int
    average_score: Optional[float]


class AssignmentSchema(Schema):
    """作业 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    course_id: int
    course_title: str
    title: str
    description: str
    due_date: datetime
    max_score: int
    created_at: datetime


class AssignmentSubmissionSchema(Schema):
    """作业提交 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    assignment_id: int
    assignment_title: str
    content: str
    attachment_url: str
    status: str
    score: Optional[int]
    feedback: str
    submitted_at: datetime
    graded_at: Optional[datetime]


class AssignmentSubmissionCreateSchema(Schema):
    """创建作业提交 Schema."""
    content: str
    attachment_url: Optional[str] = ""


class AssignmentGradingSchema(Schema):
    """作业批改 Schema."""
    score: int
    feedback: str


class AssignmentReviewSchema(Schema):
    """作业批改详情 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    assignment_id: int
    assignment_title: str
    course_id: int
    course_title: str
    content: str
    attachment_url: str
    status: str
    score: Optional[int]
    feedback: str
    submitted_at: datetime
    graded_at: Optional[datetime]


class PendingAssignmentSchema(Schema):
    """待批改作业 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    assignment_id: int
    assignment_title: str
    course_id: int
    course_title: str
    user_id: int
    user_name: str
    submitted_at: datetime


class TrainingNotificationSchema(Schema):
    """培训通知 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    course_id: Optional[int]
    course_title: Optional[str]
    title: str
    content: str
    priority: str
    is_published: bool
    published_at: Optional[datetime]
    created_at: datetime


class CourseReviewCreateSchema(Schema):
    """创建课程评价 Schema."""
    rating: int
    content: str


class CourseReviewSchema(Schema):
    """课程评价 Schema."""
    model_config = dict(from_attributes=True)
    id: int
    course_id: int
    rating: int
    content: str
    created_at: datetime


class PaginatedCourseList(Schema):
    """分页课程列表 Schema."""
    total: int
    page: int
    page_size: int
    items: List[CourseListSchema]


class PaginatedNotificationList(Schema):
    """分页通知列表 Schema."""
    total: int
    page: int
    page_size: int
    items: List[TrainingNotificationSchema]


class PaginatedPendingAssignmentList(Schema):
    """分页待批改作业列表 Schema."""
    total: int
    page: int
    page_size: int
    items: List[PendingAssignmentSchema]
