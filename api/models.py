"""API 数据模型定义."""
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
