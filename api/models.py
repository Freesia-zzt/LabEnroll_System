"""API 数据模型定义."""

from django.db import models


class User(models.Model):
    """用户模型（简化版，实际项目中可能已有）."""
    
    name = models.CharField(max_length=50, verbose_name="姓名")
    student_id = models.CharField(max_length=20, unique=True, verbose_name="学号")
    phone = models.CharField(max_length=11, verbose_name="手机号")
    email = models.EmailField(verbose_name="邮箱")
    password_hash = models.CharField(max_length=255, verbose_name="密码哈希")
    avatar = models.URLField(blank=True, verbose_name="头像URL")
    bio = models.TextField(blank=True, verbose_name="个人简介")
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "已激活"),
            ("inactive", "未激活"),
            ("locked", "已锁定"),
        ],
        default="inactive",
        verbose_name="账号状态",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self) -> str:
        return f"{self.name}({self.student_id})"


class Question(models.Model):
    """问题模型."""
    
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
    )
    
    # 问题基本信息
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
    
    # 附件（以JSON格式存储文件URL列表）
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name="附件列表",
    )
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "问题"
        verbose_name_plural = "问题"
        ordering = ["-created_at"]  # 默认按创建时间倒序排列

    def __str__(self) -> str:
        return self.title
    
    @property
    def reply_count(self) -> int:
        """获取回复数量."""
        return self.replies.count()


class QuestionReply(models.Model):
    """问题回复模型."""
    
    # 关联问题
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="所属问题",
    )
    
    # 回复者
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="question_replies",
        verbose_name="回复者",
    )
    
    # 回复内容
    content = models.TextField(verbose_name="回复内容")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "问题回复"
        verbose_name_plural = "问题回复"
        ordering = ["created_at"]  # 按创建时间正序排列

    def __str__(self) -> str:
        return f"回复-{self.question.title[:20]}..."