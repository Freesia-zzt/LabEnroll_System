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
    model_config = {"from_attributes": True}
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


# ==================== 学员问题管理 Schema ====================

class PaginationSchema(Schema):
    """分页信息."""
    total: int
    current_page: int
    per_page: int
    last_page: int


class UserBriefSchema(Schema):
    """用户简要信息."""
    model_config = dict(from_attributes=True)
    id: int
    name: str
    avatar: Optional[str] = None


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
    status: str
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
    status: str
    attachments: List[str]
    reply_count: int
    created_at: datetime
    updated_at: datetime
    author: UserBriefSchema
    replies: List[QuestionReplySchema]


class QuestionStatusUpdateSchema(Schema):
    """更新问题状态请求."""
    status: str
