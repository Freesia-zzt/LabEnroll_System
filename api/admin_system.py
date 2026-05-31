"""管理员后台 — 系统设置模块路由."""

from django.http import HttpRequest
from ninja import Router

from api.admin_schemas import (
    ApplicationToggleIn,
    ForbiddenResponse,
    SuccessResponse,
    SystemConfigOut,
)
from api.dependencies import permission_required
from api.models import AuditLog, SystemConfig
from api.utils.audit import audit_log

router = Router(tags=["Admin-System"])


def _get_or_create_config() -> SystemConfig:
    config = SystemConfig.objects.first()
    if config is None:
        config = SystemConfig.objects.create()
    return config


@router.get(
    "/config",
    response={200: SystemConfigOut},
    summary="获取系统配置",
    description="获取系统运行配置（如报名开关、维护模式）。需要超管权限。",
)
@permission_required("system.manage")
def get_system_config(request: HttpRequest) -> dict:
    """获取系统配置."""
    config = _get_or_create_config()
    return {
        "application_open": config.application_open,
        "maintenance_mode": config.maintenance_mode,
    }


@router.put(
    "/application-toggle",
    response={200: SuccessResponse, 403: ForbiddenResponse},
    summary="切换报名通道开关",
    description="切换报名通道全局开关。需要超管权限。",
)
@permission_required("system.manage")
@audit_log(module="系统设置", action=AuditLog.ActionChoices.UPDATE, target_type="SystemConfig")
def toggle_application(request: HttpRequest, payload: ApplicationToggleIn) -> dict:
    """切换报名通道开关."""
    config = _get_or_create_config()
    config.application_open = payload.open
    config.save(update_fields=["application_open"])

    status_text = "开启" if payload.open else "关闭"
    return {
        "code": 200,
        "message": f"报名通道已{status_text}",
        "data": {
            "application_open": config.application_open,
            "maintenance_mode": config.maintenance_mode,
        },
    }


@router.delete(
    "/cache",
    response={200: SuccessResponse, 403: ForbiddenResponse},
    summary="清除系统缓存",
    description="清除 Redis/Django 缓存。需要超管权限。",
)
@permission_required("system.manage")
@audit_log(module="系统设置", action=AuditLog.ActionChoices.EXPORT, target_type="Cache")
def clear_cache(request: HttpRequest) -> dict:
    """清除系统缓存.

    当前为占位实现，后续对接 Redis 后取消下面注释启用真实清缓存逻辑：
        from django.core.cache import cache
        cache.clear()
    """
    # TODO: 对接 Redis 后启用真实清缓存
    # from django.core.cache import cache
    # cache.clear()

    return {
        "code": 200,
        "message": "缓存已清除",
        "data": None,
    }
