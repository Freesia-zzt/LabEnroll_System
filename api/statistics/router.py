"""统计 API 路由."""

from datetime import datetime
from typing import Optional

from django.http import HttpRequest
from ninja import Query, Router

from api.common.auth import token_auth
from api.common.responses import api_response
from api.statistics.schemas import OverviewStatsSchema, YearlyStatsSchema
from api.statistics.services import get_overview_stats, get_yearly_stats

router = Router(tags=["统计分析"])


@router.get(
    "/overview",
    summary="获取全局统计概览",
    auth=token_auth,
)
def overview(request: HttpRequest) -> dict:
    """获取全局统计数据."""
    stats = get_overview_stats()

    overview_data = OverviewStatsSchema(
        total_applications=stats["total_applications"],
        status_distribution=[
            {"status": item["status"], "count": item["count"]}
            for item in stats["status_distribution"]
        ],
        total_admitted=stats["total_admitted"],
        public_admitted=stats["public_admitted"],
        gender_distribution=[
            {"gender": item["gender"], "count": item["count"]}
            for item in stats["gender_distribution"]
        ],
        college_distribution=[
            {"major": item["major"], "count": item["count"]}
            for item in stats["college_distribution"]
        ],
    )

    return api_response(code=200, message="获取成功", data=overview_data.model_dump())


@router.get(
    "/yearly",
    summary="获取年度统计",
    auth=token_auth,
)
def yearly(
    request: HttpRequest,
    year: Optional[int] = Query(default=None, description="年份，默认当前年份"),
) -> dict:
    """获取指定年份的统计数据."""
    if year is None:
        year = datetime.now().year

    if year < 2020 or year > 2030:
        return api_response(code=400, message="年份范围应在 2020-2030 之间")

    stats = get_yearly_stats(year)

    yearly_data = YearlyStatsSchema(
        year=stats["year"],
        total_applications=stats["total_applications"],
        admitted_count=stats["admitted_count"],
        monthly_trend=stats["monthly_trend"],
    )

    return api_response(code=200, message="获取成功", data=yearly_data.model_dump())
