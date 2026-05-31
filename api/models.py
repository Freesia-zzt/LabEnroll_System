"""API 数据模型定义.

包含用户、问题、报名等核心业务模型，所有表和字段均已添加中文注释。
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

# ==============================================================================
# 原有模型（保留）
# ==============================================================================


class User(models.Model):
    """用户模型（简化版，实际项目中可能已有）."""

    name = models.CharField(max_length=50, verbose_name="姓名")
    student_id = models.CharField(max_length=20, unique=True, verbose_name="学号")
    phone = models.CharField(max_length=11, verbose_name="手机号")
    email = models.EmailField(verbose_name="邮箱")
    password_hash = models.CharField(max_length=255, verbose_name="密码哈希")
    avatar = models.URLField(blank=True, verbose_name="头像URL")
    bio = models.TextField(blank=True, verbose_name="个人简介")
    """用户模型

    存储系统用户的基本信息，包括身份认证、个人资料等数据。
    该模型用于用户登录、注册、个人中心等功能。
    """

    name = models.CharField(
        max_length=50,
        verbose_name="姓名",
        help_text="用户真实姓名",
    )
    student_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="学号",
        help_text="用户唯一学号标识，系统唯一",
    )
    phone = models.CharField(
        max_length=11,
        verbose_name="手机号",
        help_text="用户手机号码，用于接收验证码",
    )
    email = models.EmailField(
        verbose_name="邮箱",
        help_text="用户邮箱地址，用于接收通知和密码找回",
    )
    password_hash = models.CharField(
        max_length=255,
        verbose_name="密码哈希",
        help_text="加密后的密码存储，使用BCrypt算法",
    )
    avatar = models.URLField(
        blank=True,
        verbose_name="头像URL",
        help_text="用户头像的URL地址，可选字段",
    )
    bio = models.TextField(
        blank=True,
        verbose_name="个人简介",
        help_text="用户个人简介或自我介绍",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "已激活"),
            ("inactive", "未激活"),
            ("locked", "已锁定"),
        ],
        default="inactive",
        verbose_name="账号状态",
        help_text="账号状态：已激活/未激活/已锁定",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
        help_text="账号创建时间，自动生成",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
        help_text="账号最后更新时间，自动更新",
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        db_table = "users"  # 数据库表名

    def __str__(self) -> str:
        return f"{self.name}({self.student_id})"


class Question(models.Model):
    """问题模型."""

    """问题模型

    存储学员提交的问题信息，支持分类管理、状态追踪和附件上传。
    用于学员问题管理功能模块。
    """

    # 问题状态枚举
    STATUS_PENDING = "pending"  # 未回复
    STATUS_REPLIED = "replied"  # 已回复
    STATUS_RESOLVED = "resolved"  # 已解决

    STATUS_CHOICES = [
        (STATUS_PENDING, "未回复"),
        (STATUS_REPLIED, "已回复"),
        (STATUS_RESOLVED, "已解决"),
    ]

    # 问题分类枚举
    CATEGORY_TECH = "technical"  # 技术问题
    CATEGORY_ENV = "environment"  # 环境问题
    CATEGORY_PROCESS = "process"  # 流程问题
    CATEGORY_OTHER = "other"  # 其他

    CATEGORY_CHOICES = [
        (CATEGORY_TECH, "技术问题"),
        (CATEGORY_ENV, "环境问题"),
        (CATEGORY_PROCESS, "流程问题"),
        (CATEGORY_OTHER, "其他"),
    ]

    # 关联用户
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="提问者",
        help_text="提问用户的外键关联",
    )

    # 问题基本信息
    title = models.CharField(
        max_length=200,
        verbose_name="问题标题",
        help_text="问题的简短标题，便于快速浏览",
    )
    content = models.TextField(
        verbose_name="问题内容",
        help_text="问题的详细描述",
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_OTHER,
        verbose_name="问题分类",
        help_text="问题分类：技术问题/环境问题/流程问题/其他",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="问题状态",
        help_text="问题处理状态：未回复/已回复/已解决",
    )

    # 附件（以JSON格式存储文件URL列表）
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name="附件列表",
        help_text="问题相关附件的URL列表，JSON格式存储",
    )

    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
        help_text="问题创建时间，自动生成",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
        help_text="问题最后更新时间，自动更新",
    )

    class Meta:
        verbose_name = "问题"
        verbose_name_plural = "问题"
        db_table = "questions"  # 数据库表名
        ordering = ["-created_at"]  # 默认按创建时间倒序排列

    def __str__(self) -> str:
        return self.title

    @property
    def reply_count(self) -> int:
        """获取回复数量

        通过关联的回复模型统计该问题的回复总数。
        """
        return self.replies.count()


class QuestionReply(models.Model):
    """问题回复模型."""

    """问题回复模型

    存储对问题的回复信息，支持一对一的问题关联和回复者追踪。
    """

    # 关联问题
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="所属问题",
        help_text="关联的问题外键",
    )

    # 回复者
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="question_replies",
        verbose_name="回复者",
        help_text="回复用户的外键关联",
    )

    # 回复内容
    content = models.TextField(verbose_name="回复内容")

    content = models.TextField(
        verbose_name="回复内容",
        help_text="回复的详细内容",
    )

    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
        help_text="回复创建时间，自动生成",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
        help_text="回复最后更新时间，自动更新",
    )

    class Meta:
        verbose_name = "问题回复"
        verbose_name_plural = "问题回复"
        db_table = "question_replies"  # 数据库表名
        ordering = ["created_at"]  # 按创建时间正序排列

    def __str__(self) -> str:
        return f"回复-{self.question.title[:20]}..."


# ==============================================================================
# 新增：实验室管理系统模型
# ==============================================================================


class LabUserManager(BaseUserManager):
    """LabUser 的自定义管理器."""

    def create_user(self, account: str, password: str = None, **extra_fields):
        if not account:
            raise ValueError("账号不能为空")
        user = self.model(account=account, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, account: str, password: str = None, **extra_fields):
        extra_fields.setdefault("is_active", 1)
        extra_fields.setdefault("role", 2)
        return self.create_user(account, password, **extra_fields)


class Department(models.Model):
    """部门表."""

    name = models.CharField(max_length=100, unique=True, verbose_name="部门名称")
    intro = models.TextField(blank=True, null=True, verbose_name="部门介绍")
    tech_stack = models.CharField(max_length=255, blank=True, null=True, verbose_name="技术栈")
    manager = models.ForeignKey(
        "LabUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
        verbose_name="负责人",
    )
    sort_order = models.IntegerField(default=0, verbose_name="排序顺序")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class LabUser(AbstractBaseUser, PermissionsMixin):
    """用户表 — 自定义用户模型（用于实验室管理系统）."""

    account = models.CharField(max_length=50, unique=True, verbose_name="学号/账号")
    username = models.CharField(max_length=100, verbose_name="用户名/姓名")
    phone = models.CharField(max_length=11, blank=True, null=True, verbose_name="手机号")
    email = models.EmailField(blank=True, null=True, verbose_name="邮箱")
    is_active = models.IntegerField(default=0, verbose_name="是否激活(0未激活/1已激活)")
    role = models.IntegerField(
        default=1,
        choices=[
            (1, "学员"),
            (2, "超管"),
            (3, "管理员"),
            (4, "审核员"),
            (5, "内容编辑"),
        ],
        verbose_name="角色(1=学员, 2=超管, 3=管理员, 4=审核员, 5=编辑)",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="所属部门",
    )
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name="最后登录时间")
    activation_code = models.CharField(max_length=6, null=True, blank=True, verbose_name="6位激活码")
    activation_expire = models.DateTimeField(null=True, blank=True, verbose_name="激活码过期时间")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    objects = LabUserManager()

    USERNAME_FIELD = "account"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "实验室用户"
        verbose_name_plural = "实验室用户"

    def __str__(self) -> str:
        return f"{self.username}({self.account})"

    @property
    def is_staff(self) -> bool:
        return self.role >= 2


class LabConfig(models.Model):
    """实验室配置表（单例表，只应有一条记录）."""

    name = models.CharField(max_length=200, verbose_name="实验室名称")
    intro = models.TextField(blank=True, null=True, verbose_name="实验室介绍")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="实验室地址")
    contact = models.CharField(max_length=100, blank=True, null=True, verbose_name="联系人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "实验室配置"
        verbose_name_plural = "实验室配置"

    def __str__(self) -> str:
        return self.name


class LabNews(models.Model):
    """新闻公告表."""

    class StatusChoices(models.TextChoices):
        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"
        WITHDRAWN = "withdrawn", "已撤回"

    title = models.CharField(max_length=200, verbose_name="新闻标题")
    content = models.TextField(verbose_name="新闻内容")
    cover = models.CharField(max_length=500, blank=True, null=True, verbose_name="封面图")
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
        verbose_name="状态",
    )
    is_pinned = models.BooleanField(default=False, verbose_name="是否置顶")
    pin_time = models.DateTimeField(null=True, blank=True, verbose_name="置顶时间")
    author = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        related_name="news",
        verbose_name="作者",
    )
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "新闻公告"
        verbose_name_plural = "新闻公告"
        ordering = ["-is_pinned", "-pin_time", "-created_at"]

    def __str__(self) -> str:
        return self.title


class RegistrationConfig(models.Model):
    """报名配置表."""

    title = models.CharField(max_length=200, verbose_name="报名表标题")
    reg_start_time = models.DateTimeField(verbose_name="报名开始时间")
    reg_end_time = models.DateTimeField(verbose_name="报名截止时间")
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        verbose_name="所属部门",
    )
    is_open = models.IntegerField(default=1, verbose_name="是否开启报名(0关/1开)")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "报名配置"
        verbose_name_plural = "报名配置"

    def __str__(self) -> str:
        return f"{self.title}-{self.department.name}"


class ApplicationForm(models.Model):
    """报名表."""

    STATUS_CHOICES = [
        (1, "待审核"),
        (2, "已通过"),
        (3, "已取消"),
        (4, "已拒绝"),
    ]

    config = models.ForeignKey(
        RegistrationConfig,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name="报名配置",
    )
    user = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        related_name="application_form",
        verbose_name="用户",
    )
    name = models.CharField(max_length=50, verbose_name="姓名")
    status = models.IntegerField(default=1, choices=STATUS_CHOICES, verbose_name="状态")
    audit_time = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")
    audit_remark = models.TextField(blank=True, null=True, verbose_name="审核备注/拒绝原因")
    class_name = models.CharField(max_length=100, verbose_name="班级")
    academy = models.CharField(max_length=100, verbose_name="学院")
    major = models.CharField(max_length=100, verbose_name="专业")
    email = models.EmailField(blank=True, null=True, verbose_name="邮箱")
    director_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="导员姓名")
    sign_reason = models.TextField(verbose_name="报名理由")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "报名表"
        verbose_name_plural = "报名表"
        unique_together = ("config", "user")

    def __str__(self) -> str:
        return f"{self.name}-{self.get_status_display()}"


class FormDraft(models.Model):
    """表单草稿表（支持断点续填）."""

    device_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="设备标识")
    user = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="用户",
    )
    form_type = models.CharField(max_length=100, verbose_name="表单类型")
    config = models.ForeignKey(
        RegistrationConfig,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="报名配置",
    )
    form_data = models.JSONField(verbose_name="表单数据")
    current_step = models.IntegerField(default=1, verbose_name="当前步骤")
    total_steps = models.IntegerField(default=1, verbose_name="总步骤数")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "表单草稿"
        verbose_name_plural = "表单草稿"

    def __str__(self) -> str:
        user_info = self.user.username if self.user else self.device_id or "未知"
        return f"{user_info}-{self.form_type}"


class FAQ(models.Model):
    """问题/FAQ表（与原有 Question 模型并存，结构不同）."""

    STATUS_CHOICES = [
        ("pending", "待回答"),
        ("answered", "已回答"),
        ("resolved", "已解决"),
    ]

    user = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        related_name="faq_questions",
        verbose_name="提问者",
    )
    title = models.CharField(max_length=200, verbose_name="问题标题")
    content = models.TextField(verbose_name="问题内容")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="问题状态",
    )
    answer = models.TextField(blank=True, null=True, verbose_name="回答内容")
    answered_by = models.ForeignKey(
        LabUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faq_answers",
        verbose_name="回答者",
    )
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name="回答时间")
    sort_order = models.IntegerField(default=0, verbose_name="排序权重")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "FAQ问题"
        verbose_name_plural = "FAQ问题"
        ordering = ["sort_order", "-created_at"]

    def __str__(self) -> str:
        return self.title


class TrainingWeek(models.Model):
    """培训周次表."""

    week_name = models.CharField(max_length=100, verbose_name="周次名称")
    start_date = models.DateField(verbose_name="开始日期")
    end_date = models.DateField(verbose_name="结束日期")
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    is_published = models.BooleanField(default=False, verbose_name="是否发布")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")
    instructors = models.ManyToManyField(
        "LabUser",
        blank=True,
        related_name="teaching_weeks",
        verbose_name="讲师/助教",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "培训周次"
        verbose_name_plural = "培训周次"

    def __str__(self) -> str:
        return self.week_name


class TrainingNotification(models.Model):
    """培训通知表."""

    SEND_TIME_CHOICES = [
        ("immediate", "立即发送"),
        ("scheduled", "定时发送"),
    ]

    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("sent", "已发送"),
        ("failed", "发送失败"),
    ]

    title = models.CharField(max_length=200, verbose_name="通知标题")
    content = models.TextField(verbose_name="通知内容")
    target = models.CharField(max_length=100, verbose_name="目标群体类型")
    target_ids = models.JSONField(null=True, blank=True, verbose_name="目标ID列表")
    send_time_type = models.CharField(
        max_length=20,
        choices=SEND_TIME_CHOICES,
        verbose_name="发送时间类型",
    )
    scheduled_time = models.DateTimeField(null=True, blank=True, verbose_name="定时发送时间")
    is_draft = models.BooleanField(default=True, verbose_name="是否为草稿")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name="状态",
    )
    training_week = models.ForeignKey(
        "TrainingWeek",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联周次",
    )
    created_by = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        verbose_name="创建者",
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="发送时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "培训通知"
        verbose_name_plural = "培训通知"

    def __str__(self) -> str:
        return self.title


class Assignment(models.Model):
    """作业任务表（培训周次关联的作业）.每个培训周次可以发布多个作业。"""

    title = models.CharField(max_length=200, verbose_name="作业标题")
    description = models.TextField(blank=True, null=True, verbose_name="作业描述")
    training_week = models.ForeignKey(
        TrainingWeek,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="关联周次",
    )
    deadline = models.DateTimeField(verbose_name="截止时间")
    created_by = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        related_name="created_assignments",
        verbose_name="发布人",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "作业任务"
        verbose_name_plural = "作业任务"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title}({self.training_week.week_name})"


class AssignmentSubmission(models.Model):
    """作业提交记录表."""

    STATUS_CHOICES = [
        ("submitted", "已提交"),
        ("pending", "待批改"),
        ("corrected", "已批改"),
    ]

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="所属作业",
    )
    user = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
        verbose_name="提交人",
    )
    content = models.TextField(blank=True, null=True, verbose_name="提交内容")
    attachment = models.CharField(max_length=500, blank=True, null=True, verbose_name="附件路径")
    score = models.IntegerField(null=True, blank=True, verbose_name="分数")
    comment = models.TextField(blank=True, null=True, verbose_name="批改评语")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="submitted",
        verbose_name="提交状态",
    )
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="提交时间")

    class Meta:
        verbose_name = "作业提交"
        verbose_name_plural = "作业提交"
        unique_together = ("assignment", "user")

    def __str__(self) -> str:
        return f"{self.user.username}-{self.assignment.title}"


class Attendance(models.Model):
    """培训签到表."""

    training_week = models.ForeignKey(
        TrainingWeek,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name="关联周次",
    )
    user = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name="签到人",
    )
    check_in_time = models.DateTimeField(auto_now_add=True, verbose_name="签到时间")
    status = models.CharField(
        max_length=20,
        choices=[("present", "已签到"), ("absent", "未签到"), ("late", "迟到")],
        default="present",
        verbose_name="签到状态",
    )

    class Meta:
        verbose_name = "培训签到"
        verbose_name_plural = "培训签到"
        unique_together = ("training_week", "user")

    def __str__(self) -> str:
        return f"{self.user.username}-{self.training_week.week_name}-{self.get_status_display()}"


class Homework(models.Model):
    """作业表."""

    STATUS_CHOICES = [
        ("submitted", "已提交"),
        ("pending", "待批改"),
        ("corrected", "已批改"),
    ]

    user = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        verbose_name="用户",
    )
    content = models.TextField(verbose_name="作业内容")
    attachment = models.CharField(max_length=500, blank=True, null=True, verbose_name="附件路径")
    score = models.IntegerField(null=True, blank=True, verbose_name="分数")
    comment = models.TextField(blank=True, null=True, verbose_name="批改评语")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="作业状态",
    )
    week = models.CharField(max_length=100, verbose_name="所属周次")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "作业"
        verbose_name_plural = "作业"

    def __str__(self) -> str:
        return f"{self.user.username}-{self.week}"


class LabModel(models.Model):
    """AI模型表."""

    model_name = models.CharField(max_length=200, verbose_name="模型名称")
    model_desc = models.TextField(blank=True, null=True, verbose_name="模型描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "AI模型"
        verbose_name_plural = "AI模型"

    def __str__(self) -> str:
        return self.model_name


class DataSet(models.Model):
    """数据集表."""

    data_set_name = models.CharField(max_length=200, verbose_name="数据集名称")
    data_set_desc = models.TextField(blank=True, null=True, verbose_name="数据集描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "数据集"
        verbose_name_plural = "数据集"

    def __str__(self) -> str:
        return self.data_set_name


class Task(models.Model):
    """任务表."""

    STATUS_CHOICES = [
        ("pending", "待执行"),
        ("running", "运行中"),
        ("completed", "已完成"),
        ("failed", "失败"),
    ]

    task_name = models.CharField(max_length=200, verbose_name="任务名称")
    model = models.ForeignKey(
        LabModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联模型",
    )
    train_params = models.JSONField(null=True, blank=True, verbose_name="训练参数")
    data_set = models.ForeignKey(
        DataSet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="数据集",
    )
    submit_desc = models.TextField(blank=True, null=True, verbose_name="提交描述")
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    task_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="任务状态",
    )
    progress = models.IntegerField(default=0, verbose_name="进度(%)")
    compute_resource = models.CharField(max_length=100, blank=True, null=True, verbose_name="计算资源")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务"

    def __str__(self) -> str:
        return self.task_name


class TokenBlacklist(models.Model):
    """Token 黑名单表（用于登出失效）."""

    jti = models.CharField(max_length=255, unique=True, verbose_name="Token JTI")
    token_type = models.CharField(max_length=20, verbose_name="Token 类型(access/refresh)")
    user = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        verbose_name="所属用户",
    )
    expires_at = models.DateTimeField(verbose_name="过期时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "Token黑名单"
        verbose_name_plural = "Token黑名单"

    def __str__(self) -> str:
        return f"{self.user.username}-{self.jti[:8]}..."


class TaskCorrect(models.Model):
    """任务批改表."""

    CORRECT_STATUS_CHOICES = [
        ("pending", "待批改"),
        ("corrected", "已批改"),
    ]

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="correct",
        verbose_name="关联任务",
    )
    correct_status = models.CharField(
        max_length=20,
        choices=CORRECT_STATUS_CHOICES,
        verbose_name="批改状态",
    )
    score = models.IntegerField(null=True, blank=True, verbose_name="分数")
    comment = models.TextField(blank=True, null=True, verbose_name="评语")
    corrector = models.ForeignKey(
        LabUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="批改人",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "任务批改"
        verbose_name_plural = "任务批改"

    def __str__(self) -> str:
        return f"{self.task.task_name}-批改"
# ==================== 报名相关模型 ====================


class Enrollment(models.Model):
    """报名表单模型

    存储用户提交的报名信息，包括课程名称、部门、职位、报名理由等。
    支持审核状态管理：待审核、已通过、已拒绝、已取消。
    """

    STATUS_PENDING = "pending"  # 待审核
    STATUS_APPROVED = "approved"  # 已通过
    STATUS_REJECTED = "rejected"  # 已拒绝
    STATUS_CANCELLED = "cancelled"  # 已取消

    STATUS_CHOICES = [
        (STATUS_PENDING, "待审核"),
        (STATUS_APPROVED, "已通过"),
        (STATUS_REJECTED, "已拒绝"),
        (STATUS_CANCELLED, "已取消"),
    ]

    # 关联用户
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="报名人",
        help_text="报名用户的外键关联",
    )

    # 报名信息
    course_name = models.CharField(
        max_length=200,
        verbose_name="课程名称",
        help_text="报名的课程名称",
    )
    department = models.CharField(
        max_length=100,
        verbose_name="部门",
        help_text="报名者所在部门",
    )
    position = models.CharField(
        max_length=100,
        verbose_name="职位",
        help_text="报名者职位",
    )
    reason = models.TextField(
        verbose_name="报名理由",
        help_text="报名该课程的原因说明",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="报名状态",
        help_text="报名状态：待审核/已通过/已拒绝/已取消",
    )

    # 时间戳
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="提交时间",
        help_text="报名提交时间，自动生成",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
        help_text="报名最后更新时间，自动更新",
    )

    class Meta:
        verbose_name = "报名记录"
        verbose_name_plural = "报名记录"
        db_table = "enrollments"  # 数据库表名
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"{self.user.name} - {self.course_name}"


class EnrollmentDraft(models.Model):
    """报名草稿模型

    存储用户未完成的报名表单草稿，支持保存、编辑、删除操作。
    用户可以在提交前保存草稿，稍后继续填写。
    """

    # 关联用户
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="enrollment_drafts",
        verbose_name="用户",
        help_text="草稿所属用户的外键关联",
    )

    # 草稿信息
    course_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="课程名称",
        help_text="课程名称（可空）",
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="部门",
        help_text="部门（可空）",
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="职位",
        help_text="职位（可空）",
    )
    reason = models.TextField(
        blank=True,
        verbose_name="报名理由",
        help_text="报名理由（可空）",
    )
    draft_data = models.JSONField(
        default=dict,
        verbose_name="草稿数据",
        help_text="额外的草稿数据，JSON格式存储",
    )

    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
        help_text="草稿创建时间，自动生成",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
        help_text="草稿最后更新时间，自动更新",
    )

    class Meta:
        verbose_name = "报名草稿"
        verbose_name_plural = "报名草稿"
        db_table = "enrollment_drafts"  # 数据库表名
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"草稿-{self.user.name}-{self.course_name[:20]}"


class EnrollmentFile(models.Model):
    """报名文件模型

    存储报名相关的附件文件，支持关联到报名记录或草稿。
    文件实际存储在文件系统中，本模型记录文件的元数据信息。
    """

    # 关联报名或草稿（二选一）
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="files",
        null=True,
        blank=True,
        verbose_name="报名记录",
        help_text="关联的报名记录，与draft二选一",
    )
    draft = models.ForeignKey(
        EnrollmentDraft,
        on_delete=models.CASCADE,
        related_name="files",
        null=True,
        blank=True,
        verbose_name="草稿",
        help_text="关联的草稿，与enrollment二选一",
    )

    # 文件信息
    file_name = models.CharField(
        max_length=255,
        verbose_name="文件名",
        help_text="原始文件名",
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name="文件路径",
        help_text="文件在服务器上的存储路径",
    )
    file_size = models.IntegerField(
        verbose_name="文件大小(字节)",
        help_text="文件大小，单位为字节",
    )

    # 时间戳
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="上传时间",
        help_text="文件上传时间，自动生成",
    )

    class Meta:
        verbose_name = "报名文件"
        verbose_name_plural = "报名文件"
        db_table = "enrollment_files"  # 数据库表名

    def __str__(self) -> str:
        return self.file_name


# ==============================================================================
# 系统设置模型
# ==============================================================================


class SystemConfig(models.Model):
    """系统配置表（单例表，只应有一条记录）."""

    application_open = models.BooleanField(default=True, verbose_name="报名通道是否开启")
    maintenance_mode = models.BooleanField(default=False, verbose_name="维护模式")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "系统配置"
        verbose_name_plural = "系统配置"

    def __str__(self) -> str:
        return f"系统配置(报名={'开' if self.application_open else '关'}, 维护={'开' if self.maintenance_mode else '关'})"


# ==============================================================================
# RBAC 权限模型
# ==============================================================================


class Role(models.Model):
    """角色表."""

    name = models.CharField(max_length=50, unique=True, verbose_name="角色名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="角色编码")
    description = models.TextField(blank=True, null=True, verbose_name="角色描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色"
        db_table = "roles"

    def __str__(self) -> str:
        return self.name


class Permission(models.Model):
    """权限表."""

    name = models.CharField(max_length=100, verbose_name="权限名称")
    code = models.CharField(max_length=100, unique=True, verbose_name="权限编码")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "权限"
        verbose_name_plural = "权限"
        db_table = "permissions"

    def __str__(self) -> str:
        return f"{self.name}({self.code})"


class RolePermission(models.Model):
    """角色-权限关联表."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions", verbose_name="角色")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_permissions", verbose_name="权限")

    class Meta:
        verbose_name = "角色权限"
        verbose_name_plural = "角色权限"
        db_table = "role_permissions"
        unique_together = ("role", "permission")

    def __str__(self) -> str:
        return f"{self.role.name} - {self.permission.name}"


class UserRole(models.Model):
    """用户-角色关联表（支持多角色）."""

    user = models.ForeignKey(
        LabUser,
        on_delete=models.CASCADE,
        related_name="user_roles",
        verbose_name="用户",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
        verbose_name="角色",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="分配时间")

    class Meta:
        verbose_name = "用户角色"
        verbose_name_plural = "用户角色"
        db_table = "user_roles"
        unique_together = ("user", "role")

    def __str__(self) -> str:
        return f"{self.user.username} - {self.role.name}"


# ==============================================================================
# 审计日志模型
# ==============================================================================


class AuditLog(models.Model):
    """审计日志表.

    记录管理员的所有敏感操作，用于安全审计和操作追溯。
    """

    class ActionChoices(models.TextChoices):
        CREATE = "CREATE", "新增"
        UPDATE = "UPDATE", "修改"
        DELETE = "DELETE", "删除"
        LOGIN = "LOGIN", "登录"
        EXPORT = "EXPORT", "导出"

    user = models.ForeignKey(
        LabUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="操作人",
    )
    action = models.CharField(
        max_length=20,
        choices=ActionChoices.choices,
        verbose_name="操作类型",
    )
    module = models.CharField(max_length=100, verbose_name="操作模块")
    target_id = models.CharField(max_length=50, null=True, blank=True, verbose_name="被操作对象ID")
    target_type = models.CharField(max_length=100, null=True, blank=True, verbose_name="被操作对象模型")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="操作IP")
    details = models.JSONField(null=True, blank=True, verbose_name="操作详情/变更差异")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")

    class Meta:
        verbose_name = "审计日志"
        verbose_name_plural = "审计日志"
        db_table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        user_info = self.user.username if self.user else "未知用户"
        return f"{user_info} - {self.get_action_display()} - {self.module}"
