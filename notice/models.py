"""招新公告与系统配置 - 数据模型."""

from django.db import models


class Notice(models.Model):
    """招新公告表."""

    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    order = models.IntegerField(
        default=0, db_index=True, verbose_name="排序值（越大越靠前）"
    )
    is_published = models.BooleanField(default=True, verbose_name="是否发布")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "notice"
        ordering = ["-order", "-created_at"]
        verbose_name = "招新公告"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return self.title


class SystemConfig(models.Model):
    """系统配置表（键值对）."""

    key = models.CharField(
        max_length=100, unique=True, db_index=True, verbose_name="配置键"
    )
    value = models.TextField(blank=True, null=True, verbose_name="配置值")
    description = models.CharField(max_length=200, blank=True, verbose_name="描述")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "system_config"
        verbose_name = "系统配置"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"{self.key}: {self.value}"
