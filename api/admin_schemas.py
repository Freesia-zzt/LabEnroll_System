"""管理员后台 Schema 定义."""

from datetime import datetime          # 导入datetime，用于日期时间类型
from typing import Any, Literal        # 从typing导入Any（任意类型）和Literal（字面量类型）

from ninja import Schema               # 从ninja导入Schema，用于定义数据模型
from pydantic import Field             # 从pydantic导入Field，用于字段校验和描述


# ==================== 基础响应 Schema ====================

class AdminResponseSchema(Schema):     # 定义统一管理员响应Schema
    """统一管理员 API 响应格式."""       # 文档字符串
    code: int = 200                    # 状态码字段，类型int，默认值200
    message: str = "success"           # 消息字段，类型str，默认值"success"
    data: Any = None                   # 数据字段，类型Any（任意类型），默认None


class SuccessResponse(Schema):         # 定义成功响应Schema，继承Schema基类
    """统一成功响应."""                # 文档字符串，说明Schema用途
    code: int = 200                    # 状态码字段，类型int，默认值200
    message: str = "success"           # 消息字段，类型str，默认值"success"
    data: Any = None                   # 数据字段，类型Any（任意类型），默认None


class ErrorResponse(Schema):           # 定义错误响应Schema
    """统一错误响应."""
    detail: str                        # 错误详情，必填字符串


class ForbiddenResponse(Schema):       # 定义权限不足响应Schema
    """权限不足响应."""
    detail: str                        # 错误详情


# ==================== 部门管理 Schema ====================

class DepartmentIn(Schema):            # 定义部门创建/更新请求Schema
    """创建/更新部门请求."""
    name: str = Field(..., min_length=1, max_length=100, description="部门名称（唯一）")  # 必填，长度1-100
    intro: str | None = Field(None, description="部门介绍")  # 可选，默认None
    tech_stack: str | None = Field(None, description="技术栈")  # 可选
    manager_id: int | None = Field(None, description="负责人用户ID")  # 可选，int或None
    sort_order: int = Field(0, ge=0, description="排序顺序")  # 默认0，必须>=0


class DepartmentOut(Schema):           # 定义部门响应Schema
    """部门列表/详情响应."""
    id: int                            # 部门ID
    name: str                          # 部门名称
    intro: str | None                  # 部门介绍，可选
    tech_stack: str | None             # 技术栈，可选
    manager_name: str | None           # 负责人姓名，可选
    sort_order: int                    # 排序顺序
    is_active: bool                    # 是否激活
    created_at: datetime               # 创建时间
    updated_at: datetime               # 更新时间


# ==================== 报名管理 Schema ====================

class BatchAuditIn(Schema):            # 定义批量审核请求Schema
    """批量审核请求."""
    ids: list[int] = Field(..., min_length=1, max_length=100, description="待审核的报名记录 ID 列表")  # 整数列表，1-100个
    status: Literal["approved", "rejected"] = Field(..., description="审核结果")  # 只能是approved或rejected
    remark: str | None = Field(None, description="审核备注或拒绝原因")  # 可选


# ==================== 数据统计 Schema ====================

class DepartmentStatOut(Schema):       # 定义部门统计Schema
    """部门报名统计."""
    department_name: str               # 部门名称
    count: int                         # 报名数量


class StatisticsOverviewOut(Schema):   # 定义统计看板Schema
    """统计看板概览."""
    total_applications: int            # 总报名数
    approved_count: int                # 已通过数
    pending_count: int                 # 待审核数
    today_new_count: int               # 今日新增
    department_stats: list[DepartmentStatOut]  # 部门统计列表，嵌套DepartmentStatOut


# ==================== 角色管理 Schema ====================

class RoleIn(Schema):                  # 定义角色创建/更新请求
    """创建/更新角色请求."""
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色编码（唯一）")
    description: str | None = Field(None, description="角色描述")
    permission_ids: list[int] = Field(default_factory=list, description="关联的权限 ID 列表")  # 默认空列表


class RoleOut(Schema):                 # 定义角色响应
    """角色列表/详情响应."""
    id: int
    name: str
    code: str
    description: str | None
    permission_ids: list[int]
    created_at: datetime
    updated_at: datetime


class RoleBriefOut(Schema):            # 定义角色简要信息
    """角色简要信息."""
    id: int
    name: str
    code: str


# ==================== 管理员管理 Schema ====================

class AdminCreateIn(Schema):           # 定义创建管理员请求
    """创建管理员请求."""
    account: str = Field(..., min_length=1, description="用户账号")
    role_ids: list[int] = Field(default_factory=list, description="分配的角色 ID 列表")


class AdminOut(Schema):                # 定义管理员响应
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

class LabConfigIn(Schema):             # 定义实验室配置更新请求
    """更新实验室配置请求."""
    name: str = Field(default="", max_length=200, description="实验室名称")
    intro: str | None = Field(None, description="实验室介绍")
    address: str | None = Field(None, description="实验室地址")
    contact: str | None = Field(None, description="联系人")


class LabConfigOut(Schema):            # 定义实验室配置响应
    """实验室配置响应."""
    id: int | None
    name: str
    intro: str | None
    address: str | None
    contact: str | None
    created_at: datetime | None
    updated_at: datetime | None


# ==================== 系统设置 Schema ====================

class SystemConfigOut(Schema):         # 定义系统配置响应
    """系统配置响应."""
    application_open: bool             # 报名是否开放
    maintenance_mode: bool             # 是否维护模式


class ApplicationToggleIn(Schema):     # 定义报名开关请求
    """报名通道开关请求."""
    open: bool = Field(..., description="true=开启报名, false=关闭报名")


# ==================== 部门管理-批量排序 Schema ====================

class DepartmentSortItem(Schema):      # 定义部门排序项
    """部门排序项."""
    id: int = Field(..., description="部门 ID")
    sort_order: int = Field(..., ge=0, description="排序顺序")


class DepartmentSortIn(Schema):        # 定义批量排序请求
    """批量排序请求."""
    items: list[DepartmentSortItem] = Field(..., min_length=1, description="部门排序列表")


# ==================== 用户管理 Schema ====================

class UserFilterSchema(Schema):        # 定义用户筛选参数
    """用户列表筛选参数."""
    academy: str | None = Field(None, description="学院筛选")
    major: str | None = Field(None, description="专业筛选")
    search: str | None = Field(None, description="关键词搜索（账号/姓名/手机号）")
    is_active: int | None = Field(None, description="状态筛选（0=未激活, 1=已激活）")


class UserOut(Schema):                 # 定义用户响应
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


class UserBanIn(Schema):               # 定义封禁/解封请求
    """封禁/解封用户请求."""
    is_banned: bool = Field(..., description="true=封禁, false=解封")
    reason: str | None = Field(None, description="封禁原因")


# ==================== 报名管理 Schema ====================

class ApplicationFilterSchema(Schema): # 定义报名筛选参数
    """报名列表筛选参数."""
    department_id: int | None = Field(None, description="部门 ID 筛选")
    status: int | None = Field(None, description="状态筛选（1=待审核, 2=已通过, 3=已取消, 4=已拒绝）")
    academy: str | None = Field(None, description="学院筛选")
    major: str | None = Field(None, description="专业筛选")
    search: str | None = Field(None, description="关键词搜索（姓名/学号）")
    date_from: str | None = Field(None, description="开始日期（YYYY-MM-DD）")
    date_to: str | None = Field(None, description="结束日期（YYYY-MM-DD）")


class ApplicationOut(Schema):          # 定义报名记录响应
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


class SingleAuditIn(Schema):           # 定义单条审核请求
    """单条审核请求."""
    status: Literal["approved", "rejected"] = Field(..., description="审核结果：approved 通过 / rejected 拒绝")
    remark: str | None = Field(None, description="审核备注或拒绝原因")


# ==================== 新闻公告 Schema ====================

class NewsIn(Schema):                  # 定义新闻创建/编辑请求
    """创建/编辑新闻请求."""
    title: str = Field(..., min_length=1, max_length=200, description="新闻标题")
    content: str = Field(..., description="新闻内容")
    cover: str | None = Field(None, description="封面图片 URL")
    status: Literal["draft", "published"] = Field("draft", description="状态：draft=草稿, published=直接发布")


class NewsOut(Schema):                 # 定义新闻响应
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


class NewsStatusUpdateOut(Schema):     # 定义新闻发布/撤回响应
    """新闻发布/撤回响应."""
    id: int
    status: str
    published_at: datetime | None


class NewsPinOut(Schema):              # 定义新闻置顶响应
    """新闻置顶响应."""
    id: int
    is_pinned: bool
    pin_time: datetime | None


# ==================== FAQ 管理 Schema ====================

class FAQIn(Schema):                   # 定义FAQ创建/更新请求
    """创建/更新 FAQ 请求."""
    title: str = Field(..., min_length=1, max_length=200, description="问题标题")
    content: str = Field(..., description="问题内容")
    answer: str | None = Field(None, description="回答内容")
    status: Literal["pending", "answered", "resolved"] = Field("pending", description="问题状态")


class FAQOut(Schema):                  # 定义FAQ响应
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


class FAQSortItem(Schema):             # 定义FAQ排序项
    """FAQ 排序项."""
    id: int = Field(..., description="FAQ ID")
    sort_order: int = Field(..., ge=0, description="排序权重")


class FAQBatchSortIn(Schema):          # 定义FAQ批量排序请求
    """FAQ 批量排序请求."""
    items: list[FAQSortItem] = Field(..., min_length=1, description="FAQ 排序列表")


class FAQBatchDeleteIn(Schema):        # 定义FAQ批量删除请求
    """FAQ 批量软删除请求."""
    ids: list[int] = Field(..., min_length=1, max_length=200, description="要删除的 FAQ ID 列表")


# ==================== 培训周次 Schema ====================

class TrainingWeekIn(Schema):          # 定义培训周次创建请求
    """创建培训周次请求."""
    week_name: str = Field(..., min_length=1, max_length=100, description="周次名称")
    start_date: str = Field(..., description="开始日期（YYYY-MM-DD）")
    end_date: str = Field(..., description="结束日期（YYYY-MM-DD）")
    description: str | None = Field(None, description="描述")
    is_published: bool = Field(False, description="是否发布")

    @classmethod                       # 类方法装饰器，定义类级别的方法
    def _validate_dates(cls, data: dict) -> dict:  # 自定义日期校验方法
        from datetime import datetime
        start = datetime.strptime(data["start_date"], "%Y-%m-%d").date()  # 解析开始日期
        end = datetime.strptime(data["end_date"], "%Y-%m-%d").date()      # 解析结束日期
        if end <= start:                   # 如果结束日期<=开始日期
            raise ValueError("结束日期必须晚于开始日期")  # 抛出值错误异常
        return data                        # 返回校验后的数据


class TrainingWeekOut(Schema):         # 定义培训周次响应
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


class AssignInstructorIn(Schema):      # 定义分配讲师请求
    """分配讲师/助教请求."""
    user_ids: list[int] = Field(..., min_length=1, description="讲师/助教用户 ID 列表")
    replace: bool = Field(True, description="true=全量覆盖, false=增量追加")


class AttendanceStatOut(Schema):       # 定义签到统计响应
    """签到统计响应."""
    total_count: int
    present_count: int
    absent_list: list[dict]


# ==================== 培训通知 Schema ====================

class TrainingNotificationIn(Schema):  # 定义培训通知发布请求
    """发布通知请求."""
    title: str = Field(..., min_length=1, max_length=200, description="通知标题")
    content: str = Field(..., description="通知内容")
    training_week_id: int | None = Field(None, description="关联周次 ID")
    send_time_type: Literal["immediate", "scheduled"] = Field("immediate", description="发送时间类型")
    scheduled_time: str | None = Field(None, description="定时发送时间（YYYY-MM-DD HH:MM）")


class TrainingNotificationOut(Schema): # 定义培训通知响应
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

class TaskIn(Schema):                  # 定义作业发布请求
    """发布作业请求."""
    title: str = Field(..., min_length=1, max_length=200, description="作业标题")
    description: str | None = Field(None, description="作业描述")
    training_week_id: int = Field(..., description="关联周次 ID")
    deadline: str = Field(..., description="截止时间（YYYY-MM-DD HH:MM）")


class TaskOut(Schema):                 # 定义作业响应
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


class TaskSubmissionOut(Schema):       # 定义作业提交响应
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

class AuditLogFilterSchema(Schema):    # 定义审计日志筛选参数
    """审计日志筛选参数."""
    user_id: int | None = Field(None, description="操作人 ID")
    module: str | None = Field(None, description="操作模块")
    action: str | None = Field(None, description="操作类型（CREATE/UPDATE/DELETE/LOGIN/EXPORT）")
    date_from: str | None = Field(None, description="开始日期（YYYY-MM-DD）")
    date_to: str | None = Field(None, description="结束日期（YYYY-MM-DD）")


class AuditLogOut(Schema):             # 定义审计日志响应
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

class TrendItemOut(Schema):            # 定义趋势数据项
    """趋势数据项."""
    date: str                          # 日期字符串
    count: int                         # 数量


class SourceItemOut(Schema):           # 定义生源专业分布项
    """生源专业分布项."""
    major: str                         # 专业名称
    count: int                         # 数量


# ==================== 管理员登录 Schema ====================
# 以下是你负责的管理员认证相关Schema

class AdminLoginInput(Schema):         # 定义管理员登录请求Schema
    """管理员登录请求."""
    username: str                      # 账号，必填字符串
    password: str                      # 密码，必填字符串


class AdminLoginData(Schema):          # 定义管理员登录响应数据Schema
    """管理员登录响应数据."""
    token: str                         # JWT Token
    user_id: int                       # 用户ID
    username: str                      # 用户名
    role: str                          # 角色字符串


# ==================== 管理员信息 Schema ====================

class AdminProfileSchema(Schema):      # 定义管理员信息Schema
    """管理员信息 Schema."""
    id: int                            # ID
    username: str                      # 用户名
    email: str | None = None           # 邮箱，可选，默认None
    phone: str | None = None           # 手机号，可选，默认None
    role: str                          # 角色
    date_joined: datetime              # 注册时间


# ==================== 修改密码 Schema ====================

class AdminChangePasswordInput(Schema):  # 定义修改密码请求Schema
    """管理员修改密码请求."""
    old_password: str                  # 旧密码，必填
    new_password: str                  # 新密码，必填


class AdminChangePasswordSchema(Schema):  # 定义修改密码响应Schema
    """管理员修改密码响应."""
    code: int = 200                    # 状态码，默认200
    message: str = "密码修改成功"       # 消息，默认"密码修改成功"
    data: None = None                  # 数据，默认None


# ==================== 管理员忘记密码 Schema ====================

class AdminForgotPasswordSendCodeInput(Schema):  # 定义忘记密码发送验证码请求Schema
    """管理员忘记密码-发送验证码请求."""
    account: str = Field(..., description="管理员账号")  # 账号，必填
    email: str = Field(..., description="注册邮箱")      # 邮箱，必填


class AdminForgotPasswordResetInput(Schema):  # 定义忘记密码重置请求Schema
    """管理员忘记密码-重置密码请求."""
    account: str = Field(..., description="管理员账号")           # 账号，必填
    email: str = Field(..., description="注册邮箱")               # 邮箱，必填
    code: str = Field(..., description="验证码")                  # 验证码，必填
    new_password: str = Field(..., min_length=8, description="新密码（至少8位）")  # 新密码，至少8位
