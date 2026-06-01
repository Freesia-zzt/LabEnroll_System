"""管理员后台 — FAQ 问题管理模块路由."""

from django.db.models import Case, Q, Value, When
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import LimitOffsetPagination, paginate

from api.admin_schemas import (
    ErrorResponse,
    FAQBatchDeleteIn,
    FAQBatchSortIn,
    FAQIn,
    FAQOut,
    ForbiddenResponse,
    SuccessResponse,
)
from api.dependencies import get_current_admin_user, permission_required
from api.models import FAQ, AuditLog
from api.utils.audit import audit_log

router = Router(tags=["Admin-FAQs"])


def _faq_to_out(faq: FAQ) -> dict:
    return {
        "id": faq.id,
        "title": faq.title,
        "content": faq.content,
        "answer": faq.answer,
        "status": faq.status,
        "user_name": faq.user.username,
        "answered_by_name": faq.answered_by.username if faq.answered_by else None,
        "sort_order": faq.sort_order,
        "created_at": faq.created_at,
        "updated_at": faq.updated_at,
    }


@router.get(
    "",
    response={200: list[FAQOut]},
    summary="获取 FAQ 列表",
    description="获取 FAQ 问题列表，支持按状态筛选和关键词搜索，分页返回。需要内容编辑权限。",
)
@paginate(LimitOffsetPagination)
@permission_required("content.edit")
def list_faqs(
    request: HttpRequest,
    status: str | None = None,
    search: str | None = None,
) -> list[dict]:
    """获取 FAQ 列表."""
    queryset = FAQ.objects.filter(is_deleted=False).select_related("user", "answered_by")

    if status:
        if status not in ("pending", "answered", "resolved"):
            raise HttpError(400, "无效的状态值，可选：pending / answered / resolved")
        queryset = queryset.filter(status=status)

    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | Q(content__icontains=search)
        )

    return [_faq_to_out(f) for f in queryset]


@router.post(
    "",
    response={200: SuccessResponse, 403: ForbiddenResponse},
    summary="新增 FAQ",
    description="新增 FAQ 问题。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="FAQ管理", action=AuditLog.ActionChoices.CREATE, target_type="FAQ")
def create_faq(request: HttpRequest, payload: FAQIn) -> dict:
    """新增 FAQ."""
    admin = get_current_admin_user(request)

    faq = FAQ.objects.create(
        title=payload.title,
        content=payload.content,
        answer=payload.answer,
        status=payload.status,
        user=admin,
    )

    if payload.answer:
        faq.answered_by = admin
        faq.answered_at = timezone.now()
        faq.save(update_fields=["answered_by", "answered_at"])

    return {
        "code": 200,
        "message": "FAQ 创建成功",
        "data": _faq_to_out(faq),
    }


@router.post(
    "/batch-sort",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse},
    summary="批量排序 FAQ",
    description="前端拖拽后批量保存排序权重，使用单条 SQL 完成。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="FAQ管理", action=AuditLog.ActionChoices.UPDATE, target_type="FAQ")
def batch_sort_faqs(request: HttpRequest, payload: FAQBatchSortIn) -> dict:
    """批量排序 FAQ."""
    ids = [item.id for item in payload.items]
    existing_ids = set(
        FAQ.objects.filter(id__in=ids, is_deleted=False).values_list("id", flat=True)
    )
    for item in payload.items:
        if item.id not in existing_ids:
            raise HttpError(400, f"FAQ ID={item.id} 不存在")

    cases = [
        When(id=item.id, then=Value(item.sort_order))
        for item in payload.items
    ]

    FAQ.objects.filter(id__in=ids).update(
        sort_order=Case(*cases, default="sort_order")
    )

    return {
        "code": 200,
        "message": f"已更新 {len(payload.items)} 个 FAQ 的排序",
        "data": None,
    }


@router.post(
    "/batch-delete",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse},
    summary="批量删除 FAQ",
    description="批量软删除 FAQ（将 is_deleted 设为 True）。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="FAQ管理", action=AuditLog.ActionChoices.DELETE, target_type="FAQ")
def batch_delete_faqs(request: HttpRequest, payload: FAQBatchDeleteIn) -> dict:
    """批量软删除 FAQ."""
    now = timezone.now()
    count = FAQ.objects.filter(id__in=payload.ids, is_deleted=False).update(
        is_deleted=True,
        deleted_at=now,
    )

    return {
        "code": 200,
        "message": f"已删除 {count} 个 FAQ",
        "data": None,
    }


@router.put(
    "/{faq_id}",
    response={200: SuccessResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="更新 FAQ",
    description="更新 FAQ 问题与答案。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="FAQ管理", action=AuditLog.ActionChoices.UPDATE, target_type="FAQ")
def update_faq(request: HttpRequest, faq_id: int, payload: FAQIn) -> dict:
    """更新 FAQ."""
    try:
        faq = FAQ.objects.get(id=faq_id, is_deleted=False)
    except FAQ.DoesNotExist:
        raise HttpError(404, "FAQ 不存在") from None

    admin = get_current_admin_user(request)

    faq.title = payload.title
    faq.content = payload.content
    faq.answer = payload.answer
    faq.status = payload.status

    if payload.answer and not faq.answered_by:
        faq.answered_by = admin
        faq.answered_at = timezone.now()

    faq.save()

    return {
        "code": 200,
        "message": "FAQ 已更新",
        "data": _faq_to_out(faq),
    }
