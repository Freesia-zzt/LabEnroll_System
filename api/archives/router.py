"""数据存档 API 路由."""

from typing import List

from django.http import HttpRequest
from ninja import Router
from ninja.pagination import paginate

from api.archives.schemas import (
    ArchiveCreateSchema,
    ArchiveDetailSchema,
    ArchiveOutSchema,
)
from api.archives.services import (
    create_or_update_archive,
    get_archive_detail,
    get_archive_list,
)
from api.common.auth import token_auth
from api.common.responses import api_response

router = Router(tags=["数据存档"])


@router.post(
    "",
    summary="创建/更新年度存档",
    auth=token_auth,
)
def create_archive(
    request: HttpRequest,
    data: ArchiveCreateSchema,
) -> dict:
    """创建或更新指定年份的数据存档."""
    user = request.auth

    try:
        year_int = int(data.archive_year)
        if year_int < 2020 or year_int > 2030:
            return api_response(code=400, message="年份范围应在 2020-2030 之间")
    except ValueError:
        return api_response(code=400, message="年份格式错误")

    archive = create_or_update_archive(
        year=data.archive_year,
        user=user,
    )

    return api_response(
        code=200,
        message="存档创建/更新成功",
        data={"id": archive.id, "year": archive.year},
    )


@router.get(
    "",
    response=List[ArchiveOutSchema],
    summary="获取存档列表",
    auth=token_auth,
)
@paginate
def list_archives(request: HttpRequest):
    """获取数据存档列表."""
    return get_archive_list()


@router.get(
    "/{archive_id}",
    summary="获取存档详情",
    auth=token_auth,
)
def get_archive(
    request: HttpRequest,
    archive_id: int,
) -> dict:
    """获取指定存档的详细信息，包含完整存档数据."""
    archive = get_archive_detail(archive_id)

    if not archive:
        return api_response(code=404, message="存档不存在")

    detail = ArchiveDetailSchema(
        id=archive.id,
        year=archive.year,
        total_applications=archive.total_applications,
        admitted_count=archive.admitted_count,
        major_stats=archive.major_stats,
        grade_stats=archive.grade_stats,
        archive_data=archive.archive_data,
        created_at=archive.created_at,
        operator_name=archive.operator.username if archive.operator else None,
    )

    return api_response(code=200, message="获取成功", data=detail.model_dump())
