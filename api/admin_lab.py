"""管理员后台 — 实验室配置模块路由."""

from django.http import HttpRequest
from ninja import Router

from api.admin_schemas import (
    ForbiddenResponse,
    LabConfigIn,
    LabConfigOut,
    SuccessResponse,
)
from api.dependencies import permission_required
from api.models import AuditLog, LabConfig
from api.utils.audit import audit_log

router = Router(tags=["Admin-LabConfig"])


def _lab_to_out(config: LabConfig | None) -> dict:
    if config is None:
        return {
            "id": None,
            "name": "",
            "intro": None,
            "address": None,
            "contact": None,
            "created_at": None,
            "updated_at": None,
        }
    return {
        "id": config.id,
        "name": config.name,
        "intro": config.intro,
        "address": config.address,
        "contact": config.contact,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }


@router.get(
    "/lab",
    response={200: LabConfigOut},
    summary="获取实验室配置",
    description="获取实验室配置详情。若没有记录则返回默认空结构。需要实验室编辑权限。",
)
@permission_required("lab.edit")
def get_lab_config(request: HttpRequest) -> dict:
    """获取实验室配置."""
    config = LabConfig.objects.first()
    return _lab_to_out(config)


@router.put(
    "/lab",
    response={200: SuccessResponse, 403: ForbiddenResponse},
    summary="保存/更新实验室配置",
    description="保存或更新实验室配置（单例模式，使用 update_or_create 保证只有一条记录）。需要实验室编辑权限。",
)
@permission_required("lab.edit")
@audit_log(module="实验室配置", action=AuditLog.ActionChoices.UPDATE, target_type="LabConfig")
def update_lab_config(request: HttpRequest, payload: LabConfigIn) -> dict:
    """保存/更新实验室配置（单例模式）."""
    data = payload.model_dump()
    config, created = LabConfig.objects.update_or_create(
        id=LabConfig.objects.first().id if LabConfig.objects.exists() else None,
        defaults=data,
    )

    return {
        "code": 200,
        "message": "实验室配置保存成功" if not created else "实验室配置创建成功",
        "data": _lab_to_out(config),
    }
