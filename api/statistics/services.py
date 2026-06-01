"""统计业务逻辑层."""

from datetime import datetime
from typing import Any, Dict, List

from django.db.models import Count

from api.models import Admission, StudentApplication


def get_overview_stats() -> Dict[str, Any]:
    """获取全局统计概览.

    Returns:
        全局统计数据字典
    """
    total_applications = StudentApplication.objects.count()

    status_distribution = list(
        StudentApplication.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )

    total_admitted = Admission.objects.count()

    public_admitted = Admission.objects.filter(is_public=True).count()

    gender_distribution = list(
        StudentApplication.objects.values("gender")
        .annotate(count=Count("id"))
        .order_by("gender")
    )

    college_distribution = list(
        StudentApplication.objects.values("major")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    return {
        "total_applications": total_applications,
        "status_distribution": status_distribution,
        "total_admitted": total_admitted,
        "public_admitted": public_admitted,
        "gender_distribution": gender_distribution,
        "college_distribution": college_distribution,
    }


def get_yearly_stats(year: int) -> Dict[str, Any]:
    """获取年度统计.

    Args:
        year: 年份

    Returns:
        年度统计数据字典
    """
    applications = StudentApplication.objects.filter(created_at__year=year)
    total_applications = applications.count()

    admitted_count = Admission.objects.filter(admit_year=str(year)).count()

    monthly_trend_raw = list(
        applications.dates("created_at", "month")
    )

    monthly_trend: List[Dict[str, int]] = []
    for month_date in monthly_trend_raw:
        month_num = month_date.month
        count = applications.filter(
            created_at__year=month_date.year,
            created_at__month=month_num,
        ).count()
        monthly_trend.append({"month": month_num, "count": count})

    return {
        "year": year,
        "total_applications": total_applications,
        "admitted_count": admitted_count,
        "monthly_trend": monthly_trend,
    }
