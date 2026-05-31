"""管理员后台 Schema 定义."""

from datetime import datetime
from typing import Any, Literal

from ninja import Schema
from pydantic import Field


class SuccessResponse(Schema):
    """统一成功响应."""
    code: int = 200
    message: str = "success"
    data: Any = None


class ErrorResponse(Schema):
    """统一错误响应."""
    detail: str


class ForbiddenResponse(Schema):
    """权限不足响应."""
    detail: str


# ==================== 部门管理 Schema ====================


class DepartmentIn(Schema):
    """创建/更新部门请求."""
    name: str = Field(..., min_length=1, max_length=100, description="部门名称（唯一）")
    intro: str | None = Field(None, description="部门介绍")
    tech_stack: str | None = Field(None, description="技术栈")
    manager_id: int | None = Field(None, description="负责人用户ID")
    sort_order: int = Field(0, ge=0, description="排序顺序")


class DepartmentOut(Schema):
    """部门列表/详情响应."""
    id: int
    name: str
    intro: str | None
    tech_stack: str | None
    manager_name: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ==================== 报名管理 Schema ====================


class BatchAuditIn(Schema):
    """批量审核请求."""
    ids: list[int] = Field(..., min_length=1, max_length=100, description="待审核的报名记录 ID 列表")
    status: Literal["approved", "rejected"] = Field(..., description="审核结果：approved 通过 / rejected 拒绝")
    remark: str | None = Field(None, description="审核备注或拒绝原因")


# ==================== 数据统计 Schema ====================


class DepartmentStatOut(Schema):
    """部门报名统计."""
    department_name: str
    count: int


class StatisticsOverviewOut(Schema):
    """统计看板概览."""
    total_applications: int
    approved_count: int
    pending_count: int
    today_new_count: int
    department_stats: list[DepartmentStatOut]


# ==================== 角色管理 Schema ====================


class RoleIn(Schema):
    """创建/更新角色请求."""
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色编码（唯一）")
    description: str | None = Field(None, description="角色描述")
    permission_ids: list[int] = Field(default_factory=list, description="关联的权限 ID 列表")


class RoleOut(Schema):
    """角色列表/详情响应."""
    id: int
    name: str
    code: str
    description: str | None
    permission_ids: list[int]
    created_at: datetime
    updated_at: datetime


class RoleBriefOut(Schema):
    """角色简要信息."""
    id: int
    name: str
    code: str


# ==================== 管理员管理 Schema ====================


class AdminCreateIn(Schema):
    """创建管理员请求."""
    account: str = Field(..., min_length=1, description="用户账号")
    role_ids: list[int] = Field(default_factory=list, description="分配的角色 ID 列表")


class AdminOut(Schema):
    """管理员列表/详情响应."""
    id: int
    account: str
    username: str
    email: str | None
    phone: str | None
    is_active: int
    role_names: list[str]
    role_ids: list[int]
    last_login_at: datetime | None
    created_at: datetime


# ==================== 实验室配置 Schema ====================


class LabConfigIn(Schema):
    """更新实验室配置请求."""
    name: str = Field(default="", max_length=200, description="实验室名称")
    intro: str | None = Field(None, description="实验室介绍")
    address: str | None = Field(None, description="实验室地址")
    contact: str | None = Field(None, description="联系人")


class LabConfigOut(Schema):
    """实验室配置响应."""
    id: int | None
    name: str
    intro: str | None
    address: str | None
    contact: str | None
    created_at: datetime | None
    updated_at: datetime | None


# ==================== 系统设置 Schema ====================


class SystemConfigOut(Schema):
    """系统配置响应."""
    application_open: bool
    maintenance_mode: bool


class ApplicationToggleIn(Schema):
    """报名通道开关请求."""
    open: bool = Field(..., description="true=开启报名, false=关闭报名")


# ==================== 部门管理-批量排序 Schema ====================


class DepartmentSortItem(Schema):
    """部门排序项."""
    id: int = Field(..., description="部门 ID")
    sort_order: int = Field(..., ge=0, description="排序顺序")


class DepartmentSortIn(Schema):
    """批量排序请求."""
    items: list[DepartmentSortItem] = Field(..., min_length=1, description="部门排序列表")


# ==================== 用户管理 Schema ====================


class UserFilterSchema(Schema):
    """用户列表筛选参数."""
    academy: str | None = Field(None, description="学院筛选（关联报名记录中的学院）")
    major: str | None = Field(None, description="专业筛选（关联报名记录中的专业）")
    search: str | None = Field(None, description="关键词搜索（账号/姓名/手机号）")
    is_active: int | None = Field(None, description="状态筛选（0=未激活, 1=已激活）")


class UserOut(Schema):
    """普通用户列表/详情响应."""
    id: int
    account: str
    username: str
    phone: str | None
    email: str | None
    department_name: str | None
    is_active: int
    role: int
    academy: str | None
    major: str | None
    class_name: str | None
    created_at: datetime
    last_login_at: datetime | None


class UserBanIn(Schema):
    """封禁/解封用户请求."""
    is_banned: bool = Field(..., description="true=封禁, false=解封")
    reason: str | None = Field(None, description="封禁原因")


# ==================== 报名管理 Schema ====================


class ApplicationFilterSchema(Schema):
    """报名列表筛选参数."""
    department_id: int | None = Field(None, description="部门 ID 筛选")
    status: int | None = Field(None, description="状态筛选（1=待审核, 2=已通过, 3=已取消, 4=已拒绝）")
    academy: str | None = Field(None, description="学院筛选")
    major: str | None = Field(None, description="专业筛选")
    search: str | None = Field(None, description="关键词搜索（姓名/学号）")
    date_from: str | None = Field(None, description="开始日期（YYYY-MM-DD）")
    date_to: str | None = Field(None, description="结束日期（YYYY-MM-DD）")


class ApplicationOut(Schema):
    """报名记录列表/详情响应."""
    id: int
    name: str
    status: int
    status_display: str
    audit_time: datetime | None
    audit_remark: str | None
    class_name: str
    academy: str
    major: str
    email: str | None
    director_name: str | None
    sign_reason: str
    department_name: str
    department_id: int
    user_id: int
    user_account: str
    user_username: str
    created_at: datetime


class SingleAuditIn(Schema):
    """单条审核请求."""
    status: Literal["approved", "rejected"] = Field(..., description="审核结果：approved 通过 / rejected 拒绝")
    remark: str | None = Field(None, description="审核备注或拒绝原因")


# ==================== 新闻公告 Schema ====================


class NewsIn(Schema):
    """创建/编辑新闻请求."""
    title: str = Field(..., min_length=1, max_length=200, description="新闻标题")
    content: str = Field(..., description="新闻内容")
    cover: str | None = Field(None, description="封面图片 URL")
    status: Literal["draft", "published"] = Field("draft", description="状态：draft=草稿, published=直接发布")


class NewsOut(Schema):
    """新闻列表/详情响应."""
    id: int
    title: str
    content: str
    cover: str | None
    status: str
    is_pinned: bool
    pin_time: datetime | None
    author_name: str
    author_id: int
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NewsStatusUpdateOut(Schema):
    """新闻发布/撤回响应."""
    id: int
    status: str
    published_at: datetime | None


class NewsPinOut(Schema):
    """新闻置顶响应."""
    id: int
    is_pinned: bool
    pin_time: datetime | None


# ==================== FAQ 管理 Schema ====================


class FAQIn(Schema):
    """创建/更新 FAQ 请求."""
    title: str = Field(..., min_length=1, max_length=200, description="问题标题")
    content: str = Field(..., description="问题内容")
    answer: str | None = Field(None, description="回答内容")
    status: Literal["pending", "answered", "resolved"] = Field("pending", description="问题状态")


class FAQOut(Schema):
    """FAQ 列表/详情响应."""
    id: int
    title: str
    content: str
    answer: str | None
    status: str
    user_name: str
    answered_by_name: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class FAQSortItem(Schema):
    """FAQ 排序项."""
    id: int = Field(..., description="FAQ ID")
    sort_order: int = Field(..., ge=0, description="排序权重")


class FAQBatchSortIn(Schema):
    """FAQ 批量排序请求."""
    items: list[FAQSortItem] = Field(..., min_length=1, description="FAQ 排序列表")


class FAQBatchDeleteIn(Schema):
    """FAQ 批量软删除请求."""
    ids: list[int] = Field(..., min_length=1, max_length=200, description="要删除的 FAQ ID 列表")


# ==================== 培训周次 Schema ====================


class TrainingWeekIn(Schema):
    """创建培训周次请求."""
    week_name: str = Field(..., min_length=1, max_length=100, description="周次名称")
    start_date: str = Field(..., description="开始日期（YYYY-MM-DD）")
    end_date: str = Field(..., description="结束日期（YYYY-MM-DD）")
    description: str | None = Field(None, description="描述")
    is_published: bool = Field(False, description="是否发布")

    @classmethod
    def _validate_dates(cls, data: dict) -> dict:
        from datetime import datetime
        start = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        if end <= start:
            raise ValueError("结束日期必须晚于开始日期")
        return data


class TrainingWeekOut(Schema):
    """培训周次响应."""
    id: int
    week_name: str
    start_date: str
    end_date: str
    description: str | None
    is_published: bool
    published_at: datetime | None
    instructor_ids: list[int]
    instructor_names: list[str]
    created_at: datetime


class AssignInstructorIn(Schema):
    """分配讲师/助教请求."""
    user_ids: list[int] = Field(..., min_length=1, description="讲师/助教用户 ID 列表")
    replace: bool = Field(True, description="true=全量覆盖, false=增量追加")


class AttendanceStatOut(Schema):
    """签到统计响应."""
    total_count: int
    present_count: int
    absent_list: list[dict]


# ==================== 培训通知 Schema ====================


class TrainingNotificationIn(Schema):
    """发布通知请求."""
    title: str = Field(..., min_length=1, max_length=200, description="通知标题")
    content: str = Field(..., description="通知内容")
    training_week_id: int | None = Field(None, description="关联周次 ID")
    send_time_type: Literal["immediate", "scheduled"] = Field("immediate", description="发送时间类型")
    scheduled_time: str | None = Field(None, description="定时发送时间（YYYY-MM-DD HH:MM）")


class TrainingNotificationOut(Schema):
    """通知列表/详情响应."""
    id: int
    title: str
    content: str
    status: str
    training_week_name: str | None
    created_by_name: str
    send_time_type: str
    scheduled_time: datetime | None
    sent_at: datetime | None
    created_at: datetime


# ==================== 作业任务 Schema ====================


class TaskIn(Schema):
    """发布作业请求."""
    title: str = Field(..., min_length=1, max_length=200, description="作业标题")
    description: str | None = Field(None, description="作业描述")
    training_week_id: int = Field(..., description="关联周次 ID")
    deadline: str = Field(..., description="截止时间（YYYY-MM-DD HH:MM）")


class TaskOut(Schema):
    """作业列表/详情响应."""
    id: int
    title: str
    description: str | None
    training_week_id: int
    training_week_name: str
    deadline: datetime
    created_by_name: str
    submission_count: int
    total_students: int
    submission_rate: float
    created_at: datetime


class TaskSubmissionOut(Schema):
    """作业提交列表响应."""
    id: int
    user_id: int
    user_name: str
    content: str | None
    attachment: str | None
    score: int | None
    comment: str | None
    status: str
    submitted_at: datetime


# ==================== 审计日志 Schema ====================


class AuditLogFilterSchema(Schema):
    """审计日志筛选参数."""
    user_id: int | None = Field(None, description="操作人 ID")
    module: str | None = Field(None, description="操作模块")
    action: str | None = Field(None, description="操作类型（CREATE/UPDATE/DELETE/LOGIN/EXPORT）")
    date_from: str | None = Field(None, description="开始日期（YYYY-MM-DD）")
    date_to: str | None = Field(None, description="结束日期（YYYY-MM-DD）")


class AuditLogOut(Schema):
    """审计日志列表响应."""
    id: int
    user_id: int | None
    user_name: str
    action: str
    action_display: str
    module: str
    target_id: str | None
    target_type: str | None
    ip_address: str | None
    details: Any
    created_at: datetime


# ==================== 统计看板 Schema ====================


class TrendItemOut(Schema):
    """趋势数据项."""
    date: str
    count: int


class SourceItemOut(Schema):
    """生源专业分布项."""
    major: str
    count: int
