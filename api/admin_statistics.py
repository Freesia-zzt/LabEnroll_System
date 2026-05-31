"""管理员后台 — 数据统计看板模块路由.

缓存说明：
    - 统计结果使用 Django cache 缓存 5 分钟。
    - 缓存键格式：admin:statistics:{endpoint}:{query_params_hash}
    - 当报名数据发生变化时，使用以下 Signal 清除缓存：

    @receiver([post_save, post_delete], sender=ApplicationForm)
    def clear_statistics_cache(sender, **kwargs):
        from django.core.cache import cache
        cache.delete_pattern("admin:statistics:*")
"""

import hashlib
import json
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router

from api.admin_schemas import (
    DepartmentStatOut,
    SourceItemOut,
    StatisticsOverviewOut,
    TrendItemOut,
)
from api.dependencies import permission_required
from api.models import ApplicationForm

router = Router(tags=["Admin-Statistics"])

CACHE_TTL_SECONDS = 300


def _make_cache_key(endpoint: str, request: HttpRequest) -> str:
    """生成带查询参数的缓存键.

    Args:
        endpoint: 接口名称
        request: 请求对象（从中提取查询参数）

    Returns:
        缓存键字符串
    """
    params = dict(request.GET.items())
    param_hash = hashlib.md5(
        json.dumps(params, sort_keys=True).encode()
    ).hexdigest()[:12]
    return f"admin:statistics:{endpoint}:{param_hash}"


@router.get(
    "/overview",
    response={200: StatisticsOverviewOut},
    summary="统计看板概览",
    description="获取核心指标：总报名数、通过数、待审核数、今日新增数及各部门统计。缓存 5 分钟。",
)
@permission_required()
def statistics_overview(request: HttpRequest) -> dict:
    """获取统计看板概览."""
    cache_key = _make_cache_key("overview", request)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    today_start = timezone.localdate()
    today_end = today_start + timedelta(days=1)

    total_applications = ApplicationForm.objects.count()
    approved_count = ApplicationForm.objects.filter(status=2).count()
    pending_count = ApplicationForm.objects.filter(status=1).count()
    today_new_count = ApplicationForm.objects.filter(
        created_at__gte=today_start,
        created_at__lt=today_end,
    ).count()

    department_qs = (
        ApplicationForm.objects.values("config__department__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    result = {
        "total_applications": total_applications,
        "approved_count": approved_count,
        "pending_count": pending_count,
        "today_new_count": today_new_count,
        "department_stats": [
            {"department_name": item["config__department__name"], "count": item["count"]}
            for item in department_qs
        ],
    }

    cache.set(cache_key, result, CACHE_TTL_SECONDS)
    return result


@router.get(
    "/trend",
    response={200: list[TrendItemOut]},
    summary="近 30 天报名趋势",
    description="按天聚合近 30 天的报名数量。缺失日期自动补 0，确保折线图不断裂。缓存 5 分钟。",
)
@permission_required()
def statistics_trend(request: HttpRequest) -> list[dict]:
    """获取近 30 天报名趋势.

    使用 TruncDate 按天截断时间进行数据库层聚合。
    对于没有数据的日期，在 Python 层补 0 填充。
    """
    cache_key = _make_cache_key("trend", request)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    today = timezone.localdate()
    thirty_days_ago = today - timedelta(days=29)

    qs = (
        ApplicationForm.objects
        .filter(created_at__gte=thirty_days_ago, created_at__lt=today + timedelta(days=1))
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    db_result = {str(item["date"]): item["count"] for item in qs}

    result = []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        date_str = d.isoformat()
        result.append({"date": date_str, "count": db_result.get(date_str, 0)})

    cache.set(cache_key, result, CACHE_TTL_SECONDS)
    return result


@router.get(
    "/departments",
    response={200: list[DepartmentStatOut]},
    summary="部门报名排行",
    description="各部门报名热度排行，按报名数降序排列。缓存 5 分钟。",
)
@permission_required()
def statistics_departments(request: HttpRequest) -> list[dict]:
    """获取部门报名排行."""
    cache_key = _make_cache_key("departments", request)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    department_qs = (
        ApplicationForm.objects.values("config__department__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    result = [
        {"department_name": item["config__department__name"], "count": item["count"]}
        for item in department_qs
    ]

    cache.set(cache_key, result, CACHE_TTL_SECONDS)
    return result


@router.get(
    "/sources",
    response={200: list[SourceItemOut]},
    summary="生源专业分布",
    description="按专业 Group By 统计报名人数，从高到低排列。缓存 5 分钟。",
)
@permission_required()
def statistics_sources(request: HttpRequest) -> list[dict]:
    """获取生源专业分布."""
    cache_key = _make_cache_key("sources", request)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    source_qs = (
        ApplicationForm.objects.values("major")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    result = [
        {"major": item["major"], "count": item["count"]}
        for item in source_qs
        if item["major"]
    ]

    cache.set(cache_key, result, CACHE_TTL_SECONDS)
    return result
