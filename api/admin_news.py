"""管理员后台 — 新闻公告管理模块路由."""

from django.db.models import Q
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import LimitOffsetPagination, paginate

from api.admin_schemas import (
    ErrorResponse,
    ForbiddenResponse,
    NewsIn,
    NewsOut,
    SuccessResponse,
)
from api.dependencies import get_current_admin_user, permission_required
from api.models import AuditLog, LabNews
from api.utils.audit import audit_log

router = Router(tags=["Admin-News"])

_VALID_TRANSITIONS = {
    "draft": ["published"],
    "published": ["withdrawn"],
    "withdrawn": ["published"],
}


def _news_to_out(news: LabNews) -> dict:
    return {
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "cover": news.cover,
        "status": news.status,
        "is_pinned": news.is_pinned,
        "pin_time": news.pin_time,
        "author_name": news.author.username,
        "author_id": news.author_id,
        "published_at": news.published_at,
        "created_at": news.created_at,
        "updated_at": news.updated_at,
    }


@router.get(
    "",
    response={200: list[NewsOut]},
    summary="获取新闻列表",
    description="获取新闻公告列表，支持按状态筛选（草稿/已发布/已撤回），分页返回。",
)
@paginate(LimitOffsetPagination)
@permission_required("content.edit")
def list_news(
    request: HttpRequest,
    status: str | None = None,
    search: str | None = None,
) -> list[dict]:
    """获取新闻列表."""
    queryset = LabNews.objects.filter(is_deleted=False).select_related("author")

    if status:
        if status not in ("draft", "published", "withdrawn"):
            raise HttpError(400, "无效的状态值，可选：draft / published / withdrawn")
        queryset = queryset.filter(status=status)

    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(content__icontains=search))

    return [_news_to_out(n) for n in queryset]


@router.post(
    "",
    response={200: SuccessResponse, 403: ForbiddenResponse},
    summary="发布/保存草稿",
    description="创建新闻公告，可选择保存为草稿或直接发布。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="新闻管理", action=AuditLog.ActionChoices.CREATE, target_type="News")
def create_news(request: HttpRequest, payload: NewsIn) -> dict:
    """发布/保存草稿."""
    admin = get_current_admin_user(request)

    now = timezone.now()
    published_at = now if payload.status == "published" else None

    news = LabNews.objects.create(
        title=payload.title,
        content=payload.content,
        cover=payload.cover,
        status=payload.status,
        author=admin,
        published_at=published_at,
    )

    return {
        "code": 200,
        "message": "新闻已发布" if payload.status == "published" else "草稿已保存",
        "data": _news_to_out(news),
    }


@router.put(
    "/{news_id}",
    response={200: SuccessResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="编辑新闻",
    description="编辑新闻公告内容。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="新闻管理", action=AuditLog.ActionChoices.UPDATE, target_type="News")
def update_news(request: HttpRequest, news_id: int, payload: NewsIn) -> dict:
    """编辑新闻内容."""
    try:
        news = LabNews.objects.get(id=news_id, is_deleted=False)
    except LabNews.DoesNotExist:
        raise HttpError(404, "新闻不存在") from None

    news.title = payload.title
    news.content = payload.content
    news.cover = payload.cover
    if payload.status == "published" and news.status == "draft":
        news.status = "published"
        news.published_at = timezone.now()
    news.save()

    return {
        "code": 200,
        "message": "新闻已更新",
        "data": _news_to_out(news),
    }


@router.put(
    "/{news_id}/publish",
    response={200: SuccessResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="发布或撤回",
    description="执行发布或撤回动作。状态机：草稿→已发布→已撤回→已发布。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="新闻管理", action=AuditLog.ActionChoices.UPDATE, target_type="News")
def publish_news(request: HttpRequest, news_id: int) -> dict:
    """发布或撤回新闻."""
    try:
        news = LabNews.objects.get(id=news_id, is_deleted=False)
    except LabNews.DoesNotExist:
        raise HttpError(404, "新闻不存在") from None

    allowed = _VALID_TRANSITIONS.get(news.status, [])
    if not allowed:
        raise HttpError(400, f"当前状态「{news.status}」不允许任何操作")

    now = timezone.now()

    if news.status == "draft":
        news.status = "published"
        news.published_at = now
        message = "新闻已发布"
    elif news.status == "published":
        news.status = "withdrawn"
        message = "新闻已撤回"
    elif news.status == "withdrawn":
        news.status = "published"
        news.published_at = now
        message = "新闻已重新发布"

    news.save(update_fields=["status", "published_at"])

    return {
        "code": 200,
        "message": message,
        "data": {"id": news.id, "status": news.status, "published_at": news.published_at},
    }


@router.put(
    "/{news_id}/pin",
    response={200: SuccessResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="切换置顶状态",
    description="切换新闻置顶状态。置顶时记录置顶时间，取消置顶时清空。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="新闻管理", action=AuditLog.ActionChoices.UPDATE, target_type="News")
def pin_news(request: HttpRequest, news_id: int) -> dict:
    """切换置顶状态."""
    try:
        news = LabNews.objects.get(id=news_id, is_deleted=False)
    except LabNews.DoesNotExist:
        raise HttpError(404, "新闻不存在") from None

    now = timezone.now()

    if news.is_pinned:
        news.is_pinned = False
        news.pin_time = None
        message = "已取消置顶"
    else:
        news.is_pinned = True
        news.pin_time = now
        message = "已置顶"

    news.save(update_fields=["is_pinned", "pin_time"])

    return {
        "code": 200,
        "message": message,
        "data": {"id": news.id, "is_pinned": news.is_pinned, "pin_time": news.pin_time},
    }
