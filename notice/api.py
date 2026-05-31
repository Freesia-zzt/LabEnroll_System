"""招新公告与系统配置 - API 路由定义."""

from django.http import HttpRequest
from ninja import Router

from api.auth_utils import IsAdmin, auth_bearer

from .common import ErrorCode, NoticeErrorCode, error_response, success_response
from .schemas import (
    EnrollmentSwitchUpdateInput,
    NoticeCreateInput,
    NoticeUpdateInput,
)
from .services import NoticeService, SystemConfigService

admin_router = Router(tags=["招新公告管理"], auth=auth_bearer)

public_router = Router(tags=["招新公告（前台）"])


# ==================== 后台管理接口（需管理员权限）====================


@admin_router.post(
    "/notices",
    response={201: dict},
    summary="创建公告",
)
def create_notice(request: HttpRequest, data: NoticeCreateInput) -> dict:
    """创建招新公告（管理员权限）."""
    if not IsAdmin()(request):
        return error_response(ErrorCode.FORBIDDEN)

    try:
        notice = NoticeService.create_notice(
            title=data.title,
            content=data.content,
            order=data.order,
            is_published=data.is_published,
        )
        return success_response(
            data={
                "id": notice.id,
                "title": notice.title,
                "content": notice.content,
                "order": notice.order,
                "is_published": notice.is_published,
                "created_at": notice.created_at.isoformat(),
                "updated_at": notice.updated_at.isoformat(),
            },
            msg="公告创建成功",
            code=ErrorCode.SUCCESS,
        )
    except Exception as e:
        return error_response(NoticeErrorCode.NOTICE_CREATE_FAILED, msg=str(e))


@admin_router.get(
    "/notices",
    response={200: dict},
    summary="获取公告列表",
)
def list_notices(
    request: HttpRequest,
    page: int = 1,
    per_page: int = 10,
    sort_by: str | None = None,
    sort_order: str = "desc",
    is_published: bool | None = None,
) -> dict:
    """获取公告列表（管理员，支持分页、排序、筛选）."""
    if not IsAdmin()(request):
        return error_response(ErrorCode.FORBIDDEN)

    try:
        queryset, total = NoticeService.list_notices(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            is_published=is_published,
        )

        items = [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "order": n.order,
                "is_published": n.is_published,
                "created_at": n.created_at.isoformat(),
                "updated_at": n.updated_at.isoformat(),
            }
            for n in queryset
        ]

        last_page = max(1, (total + per_page - 1) // per_page)
        return success_response(
            data={
                "list": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "last_page": last_page,
                },
            }
        )
    except ValueError as e:
        return error_response(NoticeErrorCode.PAGINATION_INVALID, msg=str(e))


@admin_router.get(
    "/notices/{notice_id}",
    response={200: dict},
    summary="获取公告详情",
)
def get_notice(request: HttpRequest, notice_id: int) -> dict:
    """获取公告详情（管理员）."""
    if not IsAdmin()(request):
        return error_response(ErrorCode.FORBIDDEN)

    notice = NoticeService.get_notice_by_id(notice_id)
    if notice is None:
        return error_response(ErrorCode.NOTICE_NOT_EXIST)

    return success_response(
        data={
            "id": notice.id,
            "title": notice.title,
            "content": notice.content,
            "order": notice.order,
            "is_published": notice.is_published,
            "created_at": notice.created_at.isoformat(),
            "updated_at": notice.updated_at.isoformat(),
        }
    )


@admin_router.put(
    "/notices/{notice_id}",
    response={200: dict},
    summary="更新公告",
)
def update_notice(
    request: HttpRequest, notice_id: int, data: NoticeUpdateInput
) -> dict:
    """更新公告（管理员权限）."""
    if not IsAdmin()(request):
        return error_response(ErrorCode.FORBIDDEN)

    notice = NoticeService.get_notice_by_id(notice_id)
    if notice is None:
        return error_response(ErrorCode.NOTICE_NOT_EXIST)

    try:
        update_data = data.dict(exclude_unset=True)
        if not update_data:
            return error_response(ErrorCode.BAD_REQUEST, msg="没有需要更新的字段")

        notice = NoticeService.update_notice(notice, **update_data)
        return success_response(
            data={
                "id": notice.id,
                "title": notice.title,
                "content": notice.content,
                "order": notice.order,
                "is_published": notice.is_published,
                "created_at": notice.created_at.isoformat(),
                "updated_at": notice.updated_at.isoformat(),
            },
            msg="公告更新成功",
        )
    except Exception as e:
        return error_response(NoticeErrorCode.NOTICE_UPDATE_FAILED, msg=str(e))


@admin_router.delete(
    "/notices/{notice_id}",
    response={200: dict},
    summary="删除公告",
)
def delete_notice(request: HttpRequest, notice_id: int) -> dict:
    """删除公告（管理员权限）."""
    if not IsAdmin()(request):
        return error_response(ErrorCode.FORBIDDEN)

    notice = NoticeService.get_notice_by_id(notice_id)
    if notice is None:
        return error_response(ErrorCode.NOTICE_NOT_EXIST)

    try:
        NoticeService.delete_notice(notice)
        return success_response(msg="公告删除成功")
    except Exception as e:
        return error_response(NoticeErrorCode.NOTICE_DELETE_FAILED, msg=str(e))


# ==================== 报名开关管理接口 ====================


@admin_router.get(
    "/enrollment-switch",
    response={200: dict},
    summary="查询报名开关",
)
def get_enrollment_switch_admin(request: HttpRequest) -> dict:
    """查询报名开关状态（管理员）."""
    if not IsAdmin()(request):
        return error_response(ErrorCode.FORBIDDEN)

    is_open = SystemConfigService.get_enrollment_switch()
    return success_response(data={"is_open": is_open})


@admin_router.put(
    "/enrollment-switch",
    response={200: dict},
    summary="修改报名开关",
)
def update_enrollment_switch(
    request: HttpRequest, data: EnrollmentSwitchUpdateInput
) -> dict:
    """修改报名开关状态（管理员权限）."""
    if not IsAdmin()(request):
        return error_response(ErrorCode.FORBIDDEN)

    try:
        SystemConfigService.set_enrollment_switch(is_open=data.is_open)
        return success_response(
            data={"is_open": data.is_open},
            msg=f"报名已{'开启' if data.is_open else '关闭'}",
        )
    except Exception as e:
        return error_response(NoticeErrorCode.CONFIG_UPDATE_FAILED, msg=str(e))


# ==================== 前台公开接口（无需认证）====================


@public_router.get(
    "/notices",
    response={200: dict},
    summary="前台获取公告列表",
    auth=None,
)
def public_list_notices(
    request: HttpRequest,
    page: int = 1,
    per_page: int = 10,
    sort_by: str | None = None,
    sort_order: str = "desc",
) -> dict:
    """前台获取已发布公告列表（无需认证，支持分页、排序）."""
    try:
        queryset, total = NoticeService.list_notices(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            is_published=True,
        )

        items = [
            {
                "id": n.id,
                "title": n.title,
                "order": n.order,
                "is_published": n.is_published,
                "created_at": n.created_at.isoformat(),
            }
            for n in queryset
        ]

        last_page = max(1, (total + per_page - 1) // per_page)
        return success_response(
            data={
                "list": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "last_page": last_page,
                },
            }
        )
    except ValueError as e:
        return error_response(NoticeErrorCode.PAGINATION_INVALID, msg=str(e))


@public_router.get(
    "/notices/{notice_id}",
    response={200: dict},
    summary="前台获取公告详情",
    auth=None,
)
def public_get_notice(request: HttpRequest, notice_id: int) -> dict:
    """前台获取公告详情（无需认证，仅返回已发布公告）."""
    notice = NoticeService.get_notice_by_id(notice_id)
    if notice is None or not notice.is_published:
        return error_response(ErrorCode.NOTICE_NOT_EXIST)

    return success_response(
        data={
            "id": notice.id,
            "title": notice.title,
            "content": notice.content,
            "order": notice.order,
            "is_published": notice.is_published,
            "created_at": notice.created_at.isoformat(),
            "updated_at": notice.updated_at.isoformat(),
        }
    )


@public_router.get(
    "/enrollment-switch",
    response={200: dict},
    summary="前台查询报名开关",
    auth=None,
)
def public_get_enrollment_switch(request: HttpRequest) -> dict:
    """前台查询报名开关状态（无需认证）."""
    is_open = SystemConfigService.get_enrollment_switch()
    return success_response(data={"is_open": is_open})
