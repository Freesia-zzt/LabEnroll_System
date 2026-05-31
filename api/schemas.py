"""API Schema 定义."""

from datetime import datetime
from typing import Any, List, Optional

from ninja import Schema

# ==================== 基础响应 Schema ====================


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

class RegisterInput(Schema):
    """注册请求."""
    account: str
    password: str
    password_confirmation: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None


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
    name: str
    avatar: str | None = None


# ==================== 基础 Schema（前置定义，避免循环引用）===================


class PaginationSchema(Schema):
    """分页信息."""

    total: int
    current_page: int
    per_page: int
    last_page: int


class UserBriefSchema(Schema):
    """用户简要信息."""

    model_config = {"from_attributes": True}
    id: int
    name: str
    avatar: str | None = None


# ==================== 问题回复 Schema ====================


class QuestionReplyCreateSchema(Schema):
    """创建回复请求."""

    content: str


class QuestionReplySchema(Schema):
    """回复详情."""

    model_config = {"from_attributes": True}

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
    attachments: list[str] = []  # 附件URL列表


class QuestionUpdateSchema(Schema):
    """更新问题请求."""

    title: str | None = None
    content: str | None = None
    category: str | None = None
    attachments: list[str] | None = None


class QuestionFilterSchema(Schema):
    """问题列表筛选参数."""

    page: int = 1
    per_page: int = 10
    category: str | None = None  # 按分类筛选
    status: str | None = None  # 按状态筛选
    search: str | None = None  # 搜索关键词


class QuestionBriefSchema(Schema):
    """问题列表项（简要信息）."""

    model_config = {"from_attributes": True}

    id: int
    title: str
    category: str
    category_display: str  # 分类的中文显示
    status: str
    status_display: str  # 状态的中文显示
    reply_count: int
    created_at: datetime
    author: UserBriefSchema


class QuestionListSchema(Schema):
    """问题列表响应."""

    data: list[QuestionBriefSchema]
    pagination: PaginationSchema


class QuestionDetailSchema(Schema):
    """问题详情."""

    model_config = {"from_attributes": True}

    id: int
    title: str
    content: str
    category: str
    category_display: str
    status: str
    status_display: str
    attachments: list[str]
    reply_count: int
    created_at: datetime
    updated_at: datetime
    author: UserBriefSchema
    replies: list[QuestionReplySchema]


class QuestionStatusUpdateSchema(Schema):
    """更新问题状态请求."""
    status: str  # pending, replied, resolved


# ==================== 报名相关 Schema ====================


class EnrollmentCreateSchema(Schema):
    """创建报名请求."""

    course_name: str
    department: str
    position: str
    reason: str


class EnrollmentUpdateSchema(Schema):
    """更新报名请求."""

    course_name: str | None = None
    department: str | None = None
    position: str | None = None
    reason: str | None = None


class EnrollmentSchema(Schema):
    """报名记录详情."""

    model_config = {"from_attributes": True}

    id: int
    user_id: int
    user_account: str
    user_name: str
    batch_id: Optional[int] = None
    batch_name: Optional[str] = None
    course_name: str
    department: str
    position: str
    student_class: Optional[str] = None
    exam_direction: Optional[str] = None
    reason: str
    status: str
    status_display: str
    submitted_at: datetime
    updated_at: datetime


class EnrollmentListSchema(Schema):
    """报名列表响应."""

    data: list[EnrollmentSchema]
    pagination: PaginationSchema


class EnrollmentStatusUpdateSchema(Schema):
    """更新报名状态请求."""

    status: str  # pending, approved, rejected, cancelled


class PaginatedEnrollmentList(Schema):
    """分页报名列表 Schema."""

    data: list[EnrollmentSchema]
    pagination: PaginationSchema


class EnrollmentFileSchema(Schema):
    """报名文件 Schema."""

    model_config = {"from_attributes": True}
    id: int
    file_name: str
    file_size: int
    uploaded_at: datetime


# ==================== 草稿相关 Schema ====================


class DraftCreateSchema(Schema):
    """创建草稿请求."""

    course_name: str | None = None
    department: str | None = None
    position: str | None = None
    reason: str | None = None
    draft_data: dict = {}


class DraftUpdateSchema(Schema):
    """更新草稿请求."""

    course_name: str | None = None
    department: str | None = None
    position: str | None = None
    reason: str | None = None
    draft_data: dict | None = None


class DraftSchema(Schema):
    """草稿详情."""

    model_config = {"from_attributes": True}

    id: int
    user_id: int
    batch_id: Optional[int] = None
    course_name: str
    department: str
    position: str
    student_class: Optional[str] = None
    exam_direction: Optional[str] = None
    reason: str
    draft_data: dict
    created_at: datetime
    updated_at: datetime


class DraftListSchema(Schema):
    """草稿列表响应."""

    data: list[DraftSchema]
    pagination: PaginationSchema


# ==================== 文件相关 Schema ====================


class FileUploadResponseSchema(Schema):
    """文件上传响应."""

    id: int
    file_name: str
    file_path: str
    file_size: int
    uploaded_at: datetime


# ==================== 培训模块 Schema ====================


class CoursewareSchema(Schema):
    """课件 Schema."""

    model_config = {"from_attributes": True}
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

    model_config = {"from_attributes": True}
    id: int
    title: str
    description: str
    order: int
    duration_minutes: int
    coursewares: list[CoursewareSchema]
    created_at: datetime


class CourseListSchema(Schema):
    """课程列表 Schema."""

    model_config = {"from_attributes": True}
    id: int
    title: str
    description: str
    cover_image: str
    instructor_name: str
    status: str
    start_date: datetime | None
    end_date: datetime | None
    duration_hours: int
    enrolled_count: int
    enrolled_at: datetime | None


class CourseDetailSchema(Schema):
    """课程详情 Schema."""

    model_config = {"from_attributes": True}
    id: int
    title: str
    description: str
    cover_image: str
    instructor_id: int
    instructor_name: str
    status: str
    start_date: datetime | None
    end_date: datetime | None
    duration_hours: int
    chapters: list[ChapterSchema]
    created_at: datetime


class ChapterProgressSchema(Schema):
    """章节进度 Schema."""

    model_config = {"from_attributes": True}
    id: int
    chapter_id: int
    is_completed: bool
    completed_at: datetime | None


class LearningProgressSchema(Schema):
    """学习进度 Schema."""

    course_id: int
    course_title: str
    status: str
    progress_percent: int
    completed_chapters: int
    total_chapters: int
    enrolled_at: datetime
    completed_at: datetime | None


class TrainingStatisticsSchema(Schema):
    """培训统计 Schema."""

    total_courses: int
    completed_courses: int
    in_progress_courses: int
    total_learning_hours: float
    total_assignments: int
    completed_assignments: int
    pending_assignments: int
    average_score: float | None


class AssignmentSchema(Schema):
    """作业 Schema."""

    model_config = {"from_attributes": True}
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

    model_config = {"from_attributes": True}
    id: int
    assignment_id: int
    assignment_title: str
    content: str
    attachment_url: str
    status: str
    score: int | None
    feedback: str
    submitted_at: datetime
    graded_at: datetime | None


class AssignmentSubmissionCreateSchema(Schema):
    """创建作业提交 Schema."""

    content: str
    attachment_url: str | None = ""


class AssignmentGradingSchema(Schema):
    """作业批改 Schema."""

    score: int
    feedback: str


class AssignmentReviewSchema(Schema):
    """作业批改详情 Schema."""

    model_config = {"from_attributes": True}
    id: int
    assignment_id: int
    assignment_title: str
    course_id: int
    course_title: str
    content: str
    attachment_url: str
    status: str
    score: int | None
    feedback: str
    submitted_at: datetime
    graded_at: datetime | None


class PendingAssignmentSchema(Schema):
    """待批改作业 Schema."""

    model_config = {"from_attributes": True}
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

    model_config = {"from_attributes": True}
    id: int
    course_id: int | None
    course_title: str | None
    title: str
    content: str
    priority: str
    is_published: bool
    published_at: datetime | None
    created_at: datetime


class CourseReviewCreateSchema(Schema):
    """创建课程评价 Schema."""

    rating: int
    content: str


class CourseReviewSchema(Schema):
    """课程评价 Schema."""

    model_config = {"from_attributes": True}
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
    items: list[CourseListSchema]


class PaginatedNotificationList(Schema):
    """分页通知列表 Schema."""

    total: int
    page: int
    page_size: int
    items: list[TrainingNotificationSchema]


class PaginatedPendingAssignmentList(Schema):
    """分页待批改作业列表 Schema."""

    total: int
    page: int
    page_size: int
    items: list[PendingAssignmentSchema]


# ==================== 录取与公示管理 Schema ====================


class AdmitInput(Schema):
    """录取请求 Schema."""
    enrollment_id: int
    notes: str = ""


class BatchAdmitInput(Schema):
    """批量录取请求 Schema."""
    enrollment_ids: list[int]
    notes: str = ""


class AdmissionRecordSchema(Schema):
    """录取记录 Schema."""
    model_config = {"from_attributes": True}
    id: int
    enrollment_id: int
    user_name: str
    course_name: str
    department: str
    position: str
    publish_status: str
    publish_time: Optional[datetime] = None
    admitted_at: datetime
    admitted_by_name: Optional[str] = None


class AdmissionDetailSchema(Schema):
    """录取详情 Schema."""
    model_config = {"from_attributes": True}
    id: int
    enrollment_id: int
    user_id: int
    user_name: str
    course_name: str
    department: str
    position: str
    reason: str
    status: str
    publish_status: str
    publish_time: Optional[datetime] = None
    admitted_at: datetime
    admitted_by_name: Optional[str] = None
    notes: str


class PublishInput(Schema):
    """公示请求 Schema."""
    admission_id: int


class BatchPublishInput(Schema):
    """批量公示请求 Schema."""
    admission_ids: list[int]


class UnpublishInput(Schema):
    """取消公示请求 Schema."""
    admission_id: int


class PublishedRecordSchema(Schema):
    """已公示记录 Schema."""
    model_config = {"from_attributes": True}
    id: int
    user_name: str
    course_name: str
    department: str
    position: str
    publish_time: Optional[datetime] = None


# ==================== 数据存档 Schema ====================


class ArchiveCreateInput(Schema):
    """创建存档请求 Schema."""
    year: int
    archive_type: str
    data: dict
    summary: dict


class ArchiveUpdateInput(Schema):
    """更新存档请求 Schema."""
    data: dict
    summary: dict


class ArchiveSchema(Schema):
    """存档记录 Schema."""
    model_config = {"from_attributes": True}
    id: int
    year: int
    archive_type: str
    archive_type_display: str
    summary: dict
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ArchiveDetailSchema(Schema):
    """存档详情 Schema."""
    model_config = {"from_attributes": True}
    id: int
    year: int
    archive_type: str
    archive_type_display: str
    data: dict
    summary: dict
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ==================== 统计分析 Schema ====================


class GlobalStatsSchema(Schema):
    """全局统计 Schema."""
    total_enrollments: int
    total_admissions: int
    total_users: int
    total_courses: int
    total_questions: int


class YearStatsSchema(Schema):
    """年度统计 Schema."""
    year: int
    total_enrollments: int
    total_admissions: int
    enrollments_by_status: dict


class EnrollmentStatsSchema(Schema):
    """报名统计 Schema."""
    total: int
    by_status: dict
    by_department: dict


class AdmissionStatsSchema(Schema):
    """录取统计 Schema."""
    total: int
    by_publish_status: dict
    recent_admissions: list[dict]


class TrainingStatsSchema(Schema):
    """培训统计 Schema."""
    total_courses: int
    total_enrollments: int
    total_completed: int
    total_assignments: int
    total_submissions: int
    average_score: Optional[float] = None


class QuestionStatsSchema(Schema):
    """问题统计 Schema."""
    total: int
    by_status: dict
    by_category: dict


# ==================== 分页列表 Schema ====================


class PaginatedAdmissionList(Schema):
    """分页录取列表 Schema."""
    total: int
    page: int
    per_page: int
    items: list[AdmissionRecordSchema]


class PaginatedPublishedList(Schema):
    """分页公示列表 Schema."""
    total: int
    page: int
    per_page: int
    items: list[PublishedRecordSchema]


class PaginatedArchiveList(Schema):
    """分页存档列表 Schema."""
    total: int
    page: int
    per_page: int
    items: list[ArchiveSchema]


# ==================== 批次管理 Schema ====================


class BatchCreateInput(Schema):
    """创建批次请求 Schema."""
    name: str
    batch_type: str = "new_student"
    description: str = ""
    start_time: datetime
    end_time: datetime
    max_enrollments: int = 0


class BatchUpdateInput(Schema):
    """更新批次请求 Schema."""
    name: Optional[str] = None
    batch_type: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    max_enrollments: Optional[int] = None


class BatchSchema(Schema):
    """批次 Schema."""
    model_config = {"from_attributes": True}
    id: int
    name: str
    batch_type: str
    batch_type_display: str
    description: str
    start_time: datetime
    end_time: datetime
    status: str
    status_display: str
    max_enrollments: int
    enrolled_count: int
    created_by_name: Optional[str] = None
    created_at: datetime


class BatchDetailSchema(Schema):
    """批次详情 Schema."""
    model_config = {"from_attributes": True}
    id: int
    name: str
    batch_type: str
    batch_type_display: str
    description: str
    start_time: datetime
    end_time: datetime
    status: str
    status_display: str
    max_enrollments: int
    enrolled_count: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaginatedBatchList(Schema):
    """分页批次列表 Schema."""
    total: int
    page: int
    per_page: int
    items: list[BatchSchema]


# ==================== 导入导出 Schema ====================


class ImportResultSchema(Schema):
    """导入结果 Schema."""
    total: int
    success: int
    failed: int
    errors: list[str]


class ExportQuerySchema(Schema):
    """导出查询参数 Schema."""
    status: Optional[str] = None
    batch_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
