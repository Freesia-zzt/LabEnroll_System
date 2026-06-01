"""统计 Schema 定义."""

from typing import Any, Dict, List

from ninja import Schema


class StatusStatsSchema(Schema):
    """状态统计."""
    status: str
    count: int


class GenderStatsSchema(Schema):
    """性别统计."""
    gender: str
    count: int


class MajorStatsSchema(Schema):
    """专业统计."""
    major: str
    count: int


class MonthlyTrendSchema(Schema):
    """月度趋势."""
    month: int
    count: int


class OverviewStatsSchema(Schema):
    """全局统计概览."""
    total_applications: int
    status_distribution: List[StatusStatsSchema]
    total_admitted: int
    public_admitted: int
    gender_distribution: List[GenderStatsSchema]
    college_distribution: List[MajorStatsSchema]


class YearlyStatsSchema(Schema):
    """年度统计."""
    year: int
    total_applications: int
    admitted_count: int
    monthly_trend: List[MonthlyTrendSchema]
