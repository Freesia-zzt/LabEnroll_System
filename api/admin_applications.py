"""管理员后台 — 报名管理模块路由."""

from datetime import datetime

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import LimitOffsetPagination, paginate

from api.admin_schemas import (
    ApplicationOut,
    BatchAuditIn,
    ErrorResponse,
    ForbiddenResponse,
    SingleAuditIn,
    SuccessResponse,
)
from api.dependencies import permission_required
from api.models import ApplicationForm, AuditLog
from api.utils.audit import audit_log

router = Router(tags=["Admin-Applications"])

_STATUS_MAP = {
    "approved": 2,
    "rejected": 4,
}

_STATUS_DISPLAY = dict(ApplicationForm.STATUS_CHOICES)


def _application_to_out(app: ApplicationForm) -> dict:
    return {
        "id": app.id,
        "name": app.name,
        "status": app.status,
        "status_display": _STATUS_DISPLAY.get(app.status, "未知"),
        "audit_time": app.audit_time,
        "audit_remark": app.audit_remark,
        "class_name": app.class_name,
        "academy": app.academy,
        "major": app.major,
        "email": app.email,
        "director_name": app.director_name,
        "sign_reason": app.sign_reason,
        "department_name": app.config.department.name,
        "department_id": app.config.department_id,
        "user_id": app.user_id,
        "user_account": app.user.account,
        "user_username": app.user.username,
        "created_at": app.created_at,
    }


@router.get(
    "",
    response={200: list[ApplicationOut]},
    summary="获取报名列表",
    description="获取报名记录列表，支持按部门、状态、学院、专业、时间范围等复杂筛选。",
)
@paginate(LimitOffsetPagination)
@permission_required("enrollments.audit_application")
def list_applications(
    request: HttpRequest,
    department_id: int | None = None,
    status: int | None = None,
    academy: str | None = None,
    major: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """获取报名列表.

    使用 select_related 关联用户和部门，避免 N+1 查询。
    """
    queryset = ApplicationForm.objects.filter(is_deleted=False).select_related(
        "config__department", "user"
    )

    if department_id is not None:
        queryset = queryset.filter(config__department_id=department_id)

    if status is not None:
        queryset = queryset.filter(status=status)

    if academy:
        queryset = queryset.filter(academy__icontains=academy)

    if major:
        queryset = queryset.filter(major__icontains=major)

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(user__account__icontains=search)
        )

    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            queryset = queryset.filter(created_at__gte=dt_from)
        except ValueError:
            raise HttpError(400, "date_from 格式错误，应为 YYYY-MM-DD") from None

    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            queryset = queryset.filter(created_at__lte=dt_to)
        except ValueError:
            raise HttpError(400, "date_to 格式错误，应为 YYYY-MM-DD") from None

    return [_application_to_out(app) for app in queryset]


@router.put(
    "/{application_id}/audit",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="单条审核报名",
    description="审核单条报名记录，更新状态和备注。",
)
@permission_required("enrollments.audit_application")
@audit_log(module="报名管理", action=AuditLog.ActionChoices.UPDATE, target_type="Application")
def audit_application(
    request: HttpRequest,
    application_id: int,
    payload: SingleAuditIn,
) -> dict:
    """单条审核报名记录."""
    try:
        record = ApplicationForm.objects.get(id=application_id, is_deleted=False)
    except ApplicationForm.DoesNotExist:
        raise HttpError(404, "报名记录不存在") from None

    if record.status != 1:
        raise HttpError(400, "该报名记录已审核，无法重复审核")

    target_status = _STATUS_MAP[payload.status]
    now = timezone.now()

    record.status = target_status
    record.audit_time = now
    if payload.remark:
        record.audit_remark = payload.remark
    record.save(update_fields=["status", "audit_time", "audit_remark"])

    status_text = "通过" if payload.status == "approved" else "拒绝"
    return {
        "code": 200,
        "message": f"报名记录已{status_text}",
        "data": _application_to_out(record),
    }


@router.post(
    "/batch-audit",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse},
    summary="批量审核报名",
    description="批量审核报名记录，支持通过或拒绝操作。使用事务 + 行级锁防止并发。",
)
@permission_required("enrollments.audit_application")
@audit_log(module="报名管理", action=AuditLog.ActionChoices.UPDATE, target_type="Application")
def batch_audit_applications(
    request: HttpRequest,
    payload: BatchAuditIn,
) -> dict:
    """批量审核报名记录."""
    target_status = _STATUS_MAP[payload.status]
    now = timezone.now()

    with transaction.atomic():
        records = list(
            ApplicationForm.objects.select_for_update().filter(id__in=payload.ids)
        )

        if len(records) != len(payload.ids):
            raise HttpError(400, "包含无效或已审核的报名记录")

        for record in records:
            if record.status != 1:
                raise HttpError(400, "包含无效或已审核的报名记录")

            record.status = target_status
            record.audit_time = now
            if payload.remark:
                record.audit_remark = payload.remark

        ApplicationForm.objects.bulk_update(
            records,
            fields=["status", "audit_time", "audit_remark"],
        )

    # TODO: 触发 Celery 异步任务发送通知邮件

    return {
        "code": 200,
        "message": f"成功审核 {len(records)} 条报名记录",
        "data": None,
    }
