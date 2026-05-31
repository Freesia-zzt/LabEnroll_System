"""管理员后台 — 部门管理模块路由."""

from django.db.models import Case, Q, Value, When
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import LimitOffsetPagination, paginate

from api.admin_schemas import (
    DepartmentIn,
    DepartmentOut,
    DepartmentSortIn,
    ErrorResponse,
    ForbiddenResponse,
    SuccessResponse,
)
from api.dependencies import permission_required
from api.models import ApplicationForm, AuditLog, Department, LabUser
from api.utils.audit import audit_log

router = Router(tags=["Admin-Departments"])


def _department_to_out(department: Department) -> dict:
    return {
        "id": department.id,
        "name": department.name,
        "intro": department.intro,
        "tech_stack": department.tech_stack,
        "manager_name": department.manager.username if department.manager else None,
        "sort_order": department.sort_order,
        "is_active": department.is_active,
        "created_at": department.created_at,
        "updated_at": department.updated_at,
    }


@router.get(
    "",
    response={200: list[DepartmentOut]},
    summary="获取部门列表",
    description="获取所有未被软删除的部门列表，支持名称模糊搜索，分页返回。",
)
@paginate(LimitOffsetPagination)
def list_departments(
    request: HttpRequest,
    name: str | None = None,
) -> list[dict]:
    """获取部门列表."""
    queryset = Department.objects.filter(is_deleted=False).select_related("manager")

    if name:
        queryset = queryset.filter(Q(name__icontains=name))

    return [_department_to_out(d) for d in queryset]


@router.post(
    "",
    response={200: SuccessResponse, 403: ForbiddenResponse},
    summary="创建部门",
    description="创建一个新部门，需要管理员权限。name 必须唯一。",
)
@permission_required("enrollments.manage_department")
@audit_log(module="部门管理", action=AuditLog.ActionChoices.CREATE, target_type="Department")
def create_department(
    request: HttpRequest,
    payload: DepartmentIn,
) -> dict:
    """创建部门."""
    if Department.objects.filter(name=payload.name, is_deleted=False).exists():
        raise HttpError(400, f"部门名称「{payload.name}」已存在")

    manager = None
    if payload.manager_id is not None:
        try:
            manager = LabUser.objects.get(id=payload.manager_id)
        except LabUser.DoesNotExist:
            raise HttpError(400, "指定的负责人不存在") from None

    department = Department.objects.create(
        name=payload.name,
        intro=payload.intro,
        tech_stack=payload.tech_stack,
        manager=manager,
        sort_order=payload.sort_order,
    )

    department = Department.objects.select_related("manager").get(id=department.id)

    return {
        "code": 200,
        "message": "部门创建成功",
        "data": _department_to_out(department),
    }


@router.put(
    "/sort",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse},
    summary="批量排序部门",
    description="批量更新部门排序顺序，使用单条 SQL 完成。需要管理员权限。",
)
@permission_required("enrollments.manage_department")
@audit_log(module="部门管理", action=AuditLog.ActionChoices.UPDATE, target_type="Department")
def sort_departments(
    request: HttpRequest,
    payload: DepartmentSortIn,
) -> dict:
    """批量排序部门.

    使用 Django ORM 的 Case/When 构建单条 UPDATE SQL 进行批量更新，
    避免在 for 循环中逐条 save()。
    """
    ids = [item.id for item in payload.items]
    existing_ids = set(
        Department.objects.filter(id__in=ids, is_deleted=False).values_list("id", flat=True)
    )
    for item in payload.items:
        if item.id not in existing_ids:
            raise HttpError(400, f"部门 ID={item.id} 不存在")

    cases = [
        When(id=item.id, then=Value(item.sort_order))
        for item in payload.items
    ]

    Department.objects.filter(id__in=ids).update(
        sort_order=Case(*cases, default="sort_order")
    )

    return {
        "code": 200,
        "message": f"已更新 {len(payload.items)} 个部门的排序",
        "data": None,
    }


@router.put(
    "/{department_id}",
    response={200: SuccessResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="更新部门",
    description="更新指定部门的信息，需要管理员权限。",
)
@permission_required("enrollments.manage_department")
@audit_log(module="部门管理", action=AuditLog.ActionChoices.UPDATE, target_type="Department")
def update_department(
    request: HttpRequest,
    department_id: int,
    payload: DepartmentIn,
) -> dict:
    """更新部门."""
    try:
        department = Department.objects.get(id=department_id, is_deleted=False)
    except Department.DoesNotExist:
        raise HttpError(404, "部门不存在") from None

    name_exists = (
        Department.objects.filter(name=payload.name, is_deleted=False)
        .exclude(id=department_id)
        .exists()
    )
    if name_exists:
        raise HttpError(400, f"部门名称「{payload.name}」已被其他部门使用")

    manager = department.manager
    if payload.manager_id is not None:
        try:
            manager = LabUser.objects.get(id=payload.manager_id)
        except LabUser.DoesNotExist:
            raise HttpError(400, "指定的负责人不存在") from None
    elif payload.manager_id is None:
        manager = None

    department.name = payload.name
    department.intro = payload.intro
    department.tech_stack = payload.tech_stack
    department.manager = manager
    department.sort_order = payload.sort_order
    department.save()

    department = Department.objects.select_related("manager").get(id=department_id)

    return {
        "code": 200,
        "message": "部门更新成功",
        "data": _department_to_out(department),
    }


@router.delete(
    "/{department_id}",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="删除部门",
    description="软删除指定部门。如果该部门下存在未处理的报名记录，则拒绝删除。",
)
@permission_required("enrollments.manage_department")
@audit_log(module="部门管理", action=AuditLog.ActionChoices.DELETE, target_type="Department")
def delete_department(
    request: HttpRequest,
    department_id: int,
) -> dict:
    """软删除部门."""
    try:
        department = Department.objects.get(id=department_id, is_deleted=False)
    except Department.DoesNotExist:
        raise HttpError(404, "部门不存在") from None

    has_pending_applications = ApplicationForm.objects.filter(
        config__department_id=department_id,
        status=1,
    ).exists()

    if has_pending_applications:
        raise HttpError(400, "该部门下存在未处理的报名记录，无法删除")

    department.is_deleted = True
    department.deleted_at = timezone.now()
    department.save(update_fields=["is_deleted", "deleted_at"])

    return {
        "code": 200,
        "message": "部门已删除",
        "data": None,
    }
