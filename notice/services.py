"""招新公告与系统配置 - 业务逻辑层."""

import logging

from django.db.models import QuerySet

from .models import Notice, SystemConfig

logger = logging.getLogger("notice")


ENROLLMENT_SWITCH_KEY = "enrollment_open"


class NoticeService:
    """招新公告服务类."""

    @staticmethod
    def list_notices(
        page: int = 1,
        per_page: int = 10,
        sort_by: str | None = None,
        sort_order: str = "desc",
        is_published: bool | None = None,
    ) -> tuple[QuerySet[Notice], int]:
        """获取公告列表（支持分页、排序、筛选）.

        Args:
            page: 页码
            per_page: 每页数量
            sort_by: 排序字段
            sort_order: 排序方向
            is_published: 是否已发布

        Returns:
            (公告查询集, 总数量)
        """
        if page < 1:
            raise ValueError("页码必须大于 0")
        if per_page < 1 or per_page > 100:
            raise ValueError("每页数量必须在 1-100 之间")

        queryset = Notice.objects.all()

        if is_published is not None:
            queryset = queryset.filter(is_published=is_published)

        sort_field = NoticeService._resolve_sort_field(sort_by)
        if sort_order == "asc":
            queryset = queryset.order_by(sort_field)
        else:
            queryset = queryset.order_by(f"-{sort_field}")

        total = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        queryset = queryset[start:end]

        return queryset, total

    @staticmethod
    def _resolve_sort_field(sort_by: str | None) -> str:
        """解析排序字段."""
        allowed = {"order": "order", "created_at": "created_at"}
        if sort_by and sort_by in allowed:
            return allowed[sort_by]
        return "order"

    @staticmethod
    def get_notice_by_id(notice_id: int) -> Notice | None:
        """根据 ID 获取公告.

        Args:
            notice_id: 公告ID

        Returns:
            公告实例，不存在返回 None
        """
        try:
            return Notice.objects.get(id=notice_id)
        except Notice.DoesNotExist:
            return None

    @staticmethod
    def create_notice(
        title: str,
        content: str,
        order: int = 0,
        is_published: bool = True,
    ) -> Notice:
        """创建公告.

        Args:
            title: 标题
            content: 内容
            order: 排序值
            is_published: 是否发布

        Returns:
            创建的公告实例
        """
        notice = Notice.objects.create(
            title=title,
            content=content,
            order=order,
            is_published=is_published,
        )
        logger.info(f"[公告创建] id={notice.id}, title={notice.title}")
        return notice

    @staticmethod
    def update_notice(notice: Notice, **kwargs: object) -> Notice:
        """更新公告.

        Args:
            notice: 公告实例
            kwargs: 要更新的字段

        Returns:
            更新后的公告实例
        """
        updated_fields: list[str] = []
        for field, value in kwargs.items():
            if value is not None and hasattr(notice, field):
                setattr(notice, field, value)
                updated_fields.append(field)

        if updated_fields:
            notice.save(update_fields=updated_fields)
            logger.info(f"[公告更新] id={notice.id}, fields={updated_fields}")

        return notice

    @staticmethod
    def delete_notice(notice: Notice) -> None:
        """删除公告.

        Args:
            notice: 公告实例
        """
        notice_id = notice.id
        notice.delete()
        logger.info(f"[公告删除] id={notice_id}")


class SystemConfigService:
    """系统配置服务类."""

    @staticmethod
    def get_enrollment_switch() -> bool:
        """获取报名开关状态.

        Returns:
            True 表示开启，False 表示关闭
        """
        config = SystemConfig.objects.filter(key=ENROLLMENT_SWITCH_KEY).first()
        if config is None:
            return False
        return config.value == "true"

    @staticmethod
    def set_enrollment_switch(is_open: bool) -> SystemConfig:
        """设置报名开关状态.

        Args:
            is_open: 是否开启

        Returns:
            更新后的配置实例
        """
        value = "true" if is_open else "false"
        config = SystemConfig.objects.filter(key=ENROLLMENT_SWITCH_KEY).first()

        if config is None:
            config = SystemConfig.objects.create(
                key=ENROLLMENT_SWITCH_KEY,
                value=value,
                description="报名开关",
            )
        else:
            config.value = value
            config.save(update_fields=["value", "updated_at"])

        logger.info(f"[报名开关] {'开启' if is_open else '关闭'}")
        return config

    @staticmethod
    def get_config(key: str) -> SystemConfig | None:
        """获取指定配置项.

        Args:
            key: 配置键

        Returns:
            配置实例，不存在返回 None
        """
        return SystemConfig.objects.filter(key=key).first()

    @staticmethod
    def set_config(key: str, value: str, description: str = "") -> SystemConfig:
        """设置配置项.

        Args:
            key: 配置键
            value: 配置值
            description: 描述

        Returns:
            配置实例
        """
        config = SystemConfig.objects.filter(key=key).first()
        if config is None:
            config = SystemConfig.objects.create(
                key=key, value=value, description=description
            )
        else:
            config.value = value
            if description:
                config.description = description
            config.save(update_fields=["value", "updated_at", "description"])
        return config
