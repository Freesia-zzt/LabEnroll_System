"""报名导出 API 路由."""

from typing import Optional

from django.http import HttpRequest, HttpResponse
from ninja import Query, Router
from ninja.errors import HttpError

from api.common.auth import token_auth
from api.export.services import export_applications

router = Router(tags=["数据导出"])


@router.get(
    "",
    summary="导出报名数据",
    auth=token_auth,
)
def export(
    request: HttpRequest,
    format: Optional[str] = Query(default="csv", description="导出格式: csv 或 xlsx"),
    status: Optional[str] = Query(default=None, description="状态筛选"),
) -> HttpResponse:
    """导出报名数据，支持 CSV 和 Excel 格式."""
    if format not in ["csv", "xlsx"]:
        raise HttpError(400, "不支持的导出格式，仅支持 csv 或 xlsx")

    try:
        return export_applications(status=status, format=format)
    except RuntimeError as e:
        raise HttpError(500, str(e)) from e
