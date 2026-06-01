"""管理员后台 — 用户管理模块路由."""

import io

from django.db.models import Q
from django.http import HttpRequest, StreamingHttpResponse
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import LimitOffsetPagination, paginate

from api.admin_schemas import (
    ErrorResponse,
    ForbiddenResponse,
    SuccessResponse,
    UserBanIn,
    UserOut,
)
from api.dependencies import permission_required
from api.models import AuditLog, LabUser
from api.utils.audit import audit_log

router = Router(tags=["Admin-Users"])


def _user_to_out(user: LabUser) -> dict:
    return {
        "id": user.id,
        "account": user.account,
        "username": user.username,
        "phone": user.phone,
        "email": user.email,
        "department_name": user.department.name if user.department else None,
        "is_active": user.is_active,
        "role": user.role,
        "academy": None,
        "major": None,
        "class_name": None,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


@router.get(
    "",
    response={200: list[UserOut]},
    summary="获取用户列表",
    description="获取普通用户（role=1 学员）分页列表，支持专业、年级、学院筛选。",
)
@paginate(LimitOffsetPagination)
@permission_required("user.manage")
def list_users(
    request: HttpRequest,
    academy: str | None = None,
    major: str | None = None,
    search: str | None = None,
    is_active: int | None = None,
) -> list[dict]:
    """获取普通用户列表.

    支持学院、专业筛选，以及关键词搜索（账号/姓名/手机号）。
    """
    queryset = LabUser.objects.filter(role=1, is_deleted=False).select_related("department")

    if academy:
        queryset = queryset.filter(academy__icontains=academy)

    if major:
        queryset = queryset.filter(major__icontains=major)

    if search:
        queryset = queryset.filter(
            Q(account__icontains=search)
            | Q(username__icontains=search)
            | Q(phone__icontains=search)
        )

    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    return [_user_to_out(u) for u in queryset]


@router.put(
    "/{user_id}/ban",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="封禁/解封用户",
    description="封禁或解封指定用户。需要用户管理权限。",
)
@permission_required("user.manage")
@audit_log(module="用户管理", action=AuditLog.ActionChoices.UPDATE, target_type="User")
def ban_user(
    request: HttpRequest,
    user_id: int,
    payload: UserBanIn,
) -> dict:
    """封禁或解封用户."""
    try:
        user = LabUser.objects.get(id=user_id, role=1, is_deleted=False)
    except LabUser.DoesNotExist:
        raise HttpError(404, "用户不存在") from None

    new_active = 0 if payload.is_banned else 1
    user.is_active = new_active
    user.save(update_fields=["is_active"])

    action_text = "已封禁" if payload.is_banned else "已解封"
    return {
        "code": 200,
        "message": f"用户 {user.username} {action_text}",
        "data": _user_to_out(user),
    }


@router.get(
    "/export",
    summary="导出用户 Excel",
    description="导出普通用户列表为 Excel 文件（xlsx），使用 StreamingHttpResponse 流式下载。",
)
@permission_required("data.export")
def export_users(request: HttpRequest) -> StreamingHttpResponse:
    """导出用户 Excel.

    使用 openpyxl 生成 xlsx 文件，通过 StreamingHttpResponse 流式返回。
    使用 iterator() 分块查询避免内存溢出。
    """
    import openpyxl
    from openpyxl.styles import Font

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "用户列表"

    headers = ["学号/账号", "姓名", "手机号", "邮箱", "部门", "状态", "注册时间"]
    header_font = Font(bold=True)
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font

    row_num = 2
    for user in LabUser.objects.filter(role=1, is_deleted=False).select_related("department").iterator():
        ws.cell(row=row_num, column=1, value=user.account)
        ws.cell(row=row_num, column=2, value=user.username)
        ws.cell(row=row_num, column=3, value=user.phone or "")
        ws.cell(row=row_num, column=4, value=user.email or "")
        ws.cell(row=row_num, column=5, value=user.department.name if user.department else "")
        ws.cell(row=row_num, column=6, value="已激活" if user.is_active else "未激活")
        ws.cell(row=row_num, column=7, value=user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "")
        row_num += 1

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = StreamingHttpResponse(
        output,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="users.xlsx"'
    return response
