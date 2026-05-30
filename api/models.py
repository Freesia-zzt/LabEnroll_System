"""API 数据模型定义."""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class User(models.Model):
    """用户模型."""
    username = models.CharField(max_length=100, unique=True, verbose_name="用户名")
    email = models.EmailField(unique=True, verbose_name="邮箱")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="手机号")
    name = models.CharField(max_length=100, verbose_name="姓名")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return self.username


# ==================== 培训模块模型 ====================

class Course(models.Model):
    """培训课程模型."""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    title = models.CharField(max_length=200, verbose_name="课程标题")
    description = models.TextField(verbose_name="课程描述")
    cover_image = models.CharField(max_length=500, blank=True, verbose_name="封面图片")
    instructor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='taught_courses', verbose_name="讲师"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="状态")
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="开始日期")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="结束日期")
    duration_hours = models.IntegerField(default=0, verbose_name="课程时长(小时)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "培训课程"
        verbose_name_plural = "培训课程"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Chapter(models.Model):
    """课程章节模型."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters', verbose_name="课程")
    title = models.CharField(max_length=200, verbose_name="章节标题")
    description = models.TextField(blank=True, verbose_name="章节描述")
    order = models.IntegerField(default=0, verbose_name="排序")
    duration_minutes = models.IntegerField(default=0, verbose_name="章节时长(分钟)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "课程章节"
        verbose_name_plural = "课程章节"
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Courseware(models.Model):
    """课件模型."""
    TYPE_CHOICES = [
        ('video', '视频'),
        ('document', '文档'),
        ('image', '图片'),
        ('other', '其他'),
    ]

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='coursewares', verbose_name="章节")
    title = models.CharField(max_length=200, verbose_name="课件标题")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='document', verbose_name="课件类型")
    file_url = models.CharField(max_length=500, verbose_name="文件URL")
    file_size = models.BigIntegerField(default=0, verbose_name="文件大小(字节)")
    duration_minutes = models.IntegerField(default=0, verbose_name="视频时长(分钟)")
    order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "课件"
        verbose_name_plural = "课件"
        ordering = ['order']

    def __str__(self):
        return f"{self.chapter.title} - {self.title}"


class CourseEnrollment(models.Model):
    """课程选课模型."""
    STATUS_CHOICES = [
        ('enrolled', '已报名'),
        ('in_progress', '学习中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_enrollments', verbose_name="用户")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name="课程")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled', verbose_name="状态")
    progress_percent = models.IntegerField(default=0, verbose_name="学习进度(%)")
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="报名时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "课程选课"
        verbose_name_plural = "课程选课"
        unique_together = ['user', 'course']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.name} - {self.course.title}"


class ChapterProgress(models.Model):
    """章节学习进度模型."""
    enrollment = models.ForeignKey(
        CourseEnrollment, on_delete=models.CASCADE,
        related_name='chapter_progress', verbose_name="选课"
    )
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, verbose_name="章节")
    is_completed = models.BooleanField(default=False, verbose_name="是否完成")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "章节学习进度"
        verbose_name_plural = "章节学习进度"
        unique_together = ['enrollment', 'chapter']
        ordering = ['chapter__order']

    def __str__(self):
        return f"{self.enrollment.user.name} - {self.chapter.title}"


class Assignment(models.Model):
    """作业模型."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments', verbose_name="课程")
    title = models.CharField(max_length=200, verbose_name="作业标题")
    description = models.TextField(verbose_name="作业描述")
    due_date = models.DateTimeField(verbose_name="截止日期")
    max_score = models.IntegerField(default=100, verbose_name="满分")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "作业"
        verbose_name_plural = "作业"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class AssignmentSubmission(models.Model):
    """作业提交模型."""
    STATUS_CHOICES = [
        ('submitted', '已提交'),
        ('grading', '批改中'),
        ('graded', '已批改'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions', verbose_name="作业")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions', verbose_name="用户")
    content = models.TextField(verbose_name="提交内容")
    attachment_url = models.CharField(max_length=500, blank=True, verbose_name="附件URL")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted', verbose_name="状态")
    score = models.IntegerField(null=True, blank=True, verbose_name="得分")
    feedback = models.TextField(blank=True, verbose_name="批改反馈")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="提交时间")
    graded_at = models.DateTimeField(null=True, blank=True, verbose_name="批改时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "作业提交"
        verbose_name_plural = "作业提交"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.name} - {self.assignment.title}"


class TrainingNotification(models.Model):
    """培训通知模型."""
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, null=True, blank=True,
        related_name='notifications', verbose_name="关联课程"
    )
    title = models.CharField(max_length=200, verbose_name="通知标题")
    content = models.TextField(verbose_name="通知内容")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', verbose_name="优先级")
    is_published = models.BooleanField(default=False, verbose_name="是否发布")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "培训通知"
        verbose_name_plural = "培训通知"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CourseReview(models.Model):
    """课程评价模型."""
    enrollment = models.ForeignKey(
        CourseEnrollment, on_delete=models.CASCADE,
        related_name='review', verbose_name="选课"
    )
    rating = models.IntegerField(verbose_name="评分(1-5)")
    content = models.TextField(verbose_name="评价内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "课程评价"
        verbose_name_plural = "课程评价"
        unique_together = ['enrollment']

    def __str__(self):
        return f"{self.enrollment.user.name} - {self.enrollment.course.title}"


# ==================== 报名相关模型 ====================

class Enrollment(models.Model):
    """报名表单模型."""
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    course_name = models.CharField(max_length=200, verbose_name="课程名称")
    department = models.CharField(max_length=100, verbose_name="部门")
    position = models.CharField(max_length=100, verbose_name="职位")
    reason = models.TextField(verbose_name="报名理由")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="提交时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "报名"
        verbose_name_plural = "报名"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.name} - {self.course_name}"


class EnrollmentDraft(models.Model):
    """报名草稿模型."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    course_name = models.CharField(max_length=200, blank=True, verbose_name="课程名称")
    department = models.CharField(max_length=100, blank=True, verbose_name="部门")
    position = models.CharField(max_length=100, blank=True, verbose_name="职位")
    reason = models.TextField(blank=True, verbose_name="报名理由")
    draft_data = models.JSONField(default=dict, verbose_name="草稿数据")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "报名草稿"
        verbose_name_plural = "报名草稿"
        ordering = ['-updated_at']

    def __str__(self):
        return f"草稿 - {self.user.name} - {self.course_name}"


class EnrollmentFile(models.Model):
    """报名文件模型."""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, blank=True, null=True, verbose_name="报名")
    draft = models.ForeignKey(EnrollmentDraft, on_delete=models.CASCADE, blank=True, null=True, verbose_name="草稿")
    file = models.FileField(upload_to='enrollment_files/', verbose_name="文件")
    file_name = models.CharField(max_length=255, verbose_name="文件名")
    file_size = models.BigIntegerField(verbose_name="文件大小")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    class Meta:
        verbose_name = "报名文件"
        verbose_name_plural = "报名文件"

    def __str__(self):
        return self.file_name


# ==================== 学员问题管理模块 ====================

class Question(models.Model):
    """问题模型."""

    STATUS_PENDING = "pending"
    STATUS_REPLIED = "replied"
    STATUS_RESOLVED = "resolved"

    STATUS_CHOICES = [
        (STATUS_PENDING, "未回复"),
        (STATUS_REPLIED, "已回复"),
        (STATUS_RESOLVED, "已解决"),
    ]

    CATEGORY_TECH = "technical"
    CATEGORY_ENV = "environment"
    CATEGORY_PROCESS = "process"
    CATEGORY_OTHER = "other"

    CATEGORY_CHOICES = [
        (CATEGORY_TECH, "技术问题"),
        (CATEGORY_ENV, "环境问题"),
        (CATEGORY_PROCESS, "流程问题"),
        (CATEGORY_OTHER, "其他"),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="提问者",
    )

    title = models.CharField(max_length=200, verbose_name="问题标题")
    content = models.TextField(verbose_name="问题内容")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_OTHER,
        verbose_name="问题分类",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="问题状态",
    )

    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name="附件列表",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "问题"
        verbose_name_plural = "问题"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def reply_count(self) -> int:
        """获取回复数量."""
        return self.replies.count()


class QuestionReply(models.Model):
    """问题回复模型."""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="所属问题",
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="question_replies",
        verbose_name="回复者",
    )

    content = models.TextField(verbose_name="回复内容")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "问题回复"
        verbose_name_plural = "问题回复"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"回复-{self.question.title[:20]}..."


# ==================== 认证模块模型 ====================


class Department(models.Model):
    """部门表."""

    name = models.CharField(max_length=100, verbose_name="部门名称")
    intro = models.TextField(blank=True, null=True, verbose_name="部门介绍")
    tech_stack = models.CharField(max_length=255, blank=True, null=True, verbose_name="技术栈")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门"

    def __str__(self) -> str:
        return self.name


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


class LabUser(AbstractBaseUser, PermissionsMixin):
    """用户表 — 自定义用户模型（用于实验室管理系统）."""

    account = models.CharField(max_length=50, unique=True, verbose_name="学号/账号")
    username = models.CharField(max_length=100, verbose_name="用户名/姓名")
    phone = models.CharField(max_length=11, blank=True, null=True, verbose_name="手机号")
    email = models.EmailField(blank=True, null=True, verbose_name="邮箱")
    is_active = models.IntegerField(default=0, verbose_name="是否激活(0未激活/1已激活)")
    role = models.IntegerField(default=1, verbose_name="角色(1=学员, 2=管理员)")
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
        return self.role == 2


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
