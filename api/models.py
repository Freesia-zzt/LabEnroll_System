"""API 数据模型定义.

包含用户、问题、报名等核心业务模型，所有表和字段均已添加中文注释。
"""

from django.db import models


class User(models.Model):
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


# ==================== 报名相关模型 ====================

class Enrollment(models.Model):
    """报名表单模型
    
    存储用户提交的报名信息，包括课程名称、部门、职位、报名理由等。
    支持审核状态管理：待审核、已通过、已拒绝、已取消。
    """
    
    STATUS_PENDING = "pending"      # 待审核
    STATUS_APPROVED = "approved"    # 已通过
    STATUS_REJECTED = "rejected"    # 已拒绝
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