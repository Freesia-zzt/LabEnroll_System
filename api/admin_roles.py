"""管理员后台 — 角色与权限管理模块路由."""

from django.db import transaction
from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from api.admin_schemas import (
    AdminCreateIn,
    AdminOut,
    ErrorResponse,
    ForbiddenResponse,
    RoleBriefOut,
    RoleIn,
    RoleOut,
    SuccessResponse,
)
from api.dependencies import get_current_admin_user, permission_required
from api.models import AuditLog, LabUser, Permission, Role, RolePermission, UserRole
from api.utils.audit import audit_log

# ==================== 角色管理路由 ====================

role_router = Router(tags=["Admin-Roles"])


def _role_to_out(role: Role) -> dict:
    permission_ids = list(
        RolePermission.objects.filter(role=role).values_list("permission_id", flat=True)
    )
    return {
        "id": role.id,
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "permission_ids": permission_ids,
        "created_at": role.created_at,
        "updated_at": role.updated_at,
    }


@role_router.get(
    "",
    response={200: list[RoleOut]},
    summary="获取角色列表",
    description="获取所有角色列表，包含关联的权限 ID 集合。需要超管权限。",
)
@permission_required("system.manage")
def list_roles(request: HttpRequest) -> list[dict]:
    """获取角色列表."""
    roles = Role.objects.all().order_by("id")
    return [_role_to_out(r) for r in roles]


@role_router.post(
    "",
    response={200: SuccessResponse, 403: ForbiddenResponse},
    summary="创建角色",
    description="创建新角色并分配权限。需要超管权限。",
)
@permission_required("system.manage")
@audit_log(module="角色管理", action=AuditLog.ActionChoices.CREATE, target_type="Role")
def create_role(request: HttpRequest, payload: RoleIn) -> dict:
    """创建角色."""
    if Role.objects.filter(code=payload.code).exists():
        raise HttpError(400, f"角色编码「{payload.code}」已存在")

    if payload.permission_ids:
        existing = Permission.objects.filter(id__in=payload.permission_ids).count()
        if existing != len(payload.permission_ids):
            raise HttpError(400, "包含无效的权限 ID")

    data = payload.model_dump()
    permission_ids = data.pop("permission_ids", [])

    role = Role.objects.create(**data)

    for pid in permission_ids:
        RolePermission.objects.create(role=role, permission_id=pid)

    role = Role.objects.get(id=role.id)
    return {
        "code": 200,
        "message": "角色创建成功",
        "data": _role_to_out(role),
    }


@role_router.get(
    "/options",
    response={200: list[RoleBriefOut]},
    summary="获取角色选项列表",
    description="获取所有角色的简要信息（ID/名称/编码），用于下拉选择。",
)
@permission_required("system.manage")
def list_role_options(request: HttpRequest) -> list[dict]:
    """获取角色选项列表."""
    return list(Role.objects.all().order_by("id").values("id", "name", "code"))


@role_router.put(
    "/{role_id}",
    response={200: SuccessResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="更新角色",
    description="更新角色信息及权限。需要超管权限。",
)
@permission_required("system.manage")
@audit_log(module="角色管理", action=AuditLog.ActionChoices.UPDATE, target_type="Role")
def update_role(request: HttpRequest, role_id: int, payload: RoleIn) -> dict:
    """更新角色."""
    try:
        role = Role.objects.get(id=role_id)
    except Role.DoesNotExist:
        raise HttpError(404, "角色不存在") from None

    if Role.objects.filter(code=payload.code).exclude(id=role_id).exists():
        raise HttpError(400, f"角色编码「{payload.code}」已被其他角色使用")

    if payload.permission_ids:
        existing = Permission.objects.filter(id__in=payload.permission_ids).count()
        if existing != len(payload.permission_ids):
            raise HttpError(400, "包含无效的权限 ID")

    data = payload.model_dump()
    permission_ids = data.pop("permission_ids", [])

    for field, value in data.items():
        setattr(role, field, value)
    role.save()

    RolePermission.objects.filter(role=role).delete()
    for pid in permission_ids:
        RolePermission.objects.create(role=role, permission_id=pid)

    role = Role.objects.get(id=role_id)
    return {
        "code": 200,
        "message": "角色更新成功",
        "data": _role_to_out(role),
    }


# ==================== 管理员管理路由 ====================

admin_router = Router(tags=["Admin-Admins"])


def _admin_to_out(user: LabUser) -> dict:
    user_roles = UserRole.objects.filter(user=user).select_related("role")
    role_names = [ur.role.name for ur in user_roles]
    role_ids = [ur.role_id for ur in user_roles]
    return {
        "id": user.id,
        "account": user.account,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "role_names": role_names,
        "role_ids": role_ids,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
    }


@admin_router.get(
    "",
    response={200: list[AdminOut]},
    summary="获取管理员列表",
    description="获取所有管理员用户列表，展示其拥有的角色名称。需要超管权限。",
)
@permission_required("system.manage")
def list_admins(request: HttpRequest) -> list[dict]:
    """获取管理员列表."""
    users = LabUser.objects.filter(role__gte=2).order_by("id")
    return [_admin_to_out(u) for u in users]


@admin_router.post(
    "",
    response={200: SuccessResponse, 403: ForbiddenResponse},
    summary="创建管理员",
    description="将普通用户提升为管理员并分配角色。需要超管权限。",
)
@permission_required("system.manage")
@audit_log(module="管理员管理", action=AuditLog.ActionChoices.CREATE, target_type="Admin")
def create_admin(request: HttpRequest, payload: AdminCreateIn) -> dict:
    """创建管理员."""
    try:
        user = LabUser.objects.get(account=payload.account)
    except LabUser.DoesNotExist:
        raise HttpError(404, "用户不存在") from None

    if user.role == 2:
        raise HttpError(400, "该用户已是超管")

    with transaction.atomic():
        user.role = 3
        user.is_active = 1
        user.save(update_fields=["role", "is_active"])

        if payload.role_ids:
            valid_roles = Role.objects.filter(id__in=payload.role_ids).count()
            if valid_roles != len(payload.role_ids):
                raise HttpError(400, "包含无效的角色 ID")

            for rid in payload.role_ids:
                UserRole.objects.get_or_create(user=user, role_id=rid)

    return {
        "code": 200,
        "message": f"用户 {user.username} 已成为管理员",
        "data": _admin_to_out(user),
    }


@admin_router.delete(
    "/{admin_id}",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="移除管理员",
    description="移除管理员身份（解除所有角色关联，降为普通学员）。需要超管权限。",
)
@permission_required("system.manage")
@audit_log(module="管理员管理", action=AuditLog.ActionChoices.DELETE, target_type="Admin")
def remove_admin(request: HttpRequest, admin_id: int) -> dict:
    """移除管理员身份."""
    try:
        user = LabUser.objects.get(id=admin_id, role__gte=2)
    except LabUser.DoesNotExist:
        raise HttpError(404, "管理员不存在") from None

    if user.id == get_current_admin_user(request).id:
        raise HttpError(400, "不能移除自己的管理员身份")

    with transaction.atomic():
        user.role = 1
        user.save(update_fields=["role"])
        UserRole.objects.filter(user=user).delete()

    return {
        "code": 200,
        "message": f"已移除 {user.username} 的管理员身份",
        "data": None,
    }
