"""数据存档业务逻辑层."""

from typing import Any, Dict

from django.db.models import Count, QuerySet

from api.models import Admin, Admission, DataArchive, StudentApplication


def create_or_update_archive(year: str, user: Admin) -> DataArchive:
    """创建或更新年度存档.

    Args:
        year: 存档年份
        user: 执行存档的用户

    Returns:
        创建或更新的存档实例
    """
    applications = StudentApplication.objects.filter(created_at__year=int(year))
    admissions = Admission.objects.filter(admit_year=year)

    archive_data = _collect_archive_data(applications, admissions)
    major_stats = _calculate_major_stats(applications)
    grade_stats = _calculate_grade_stats(applications)
    total_applications = applications.count()
    admitted_count = admissions.count()

    archive, _ = DataArchive.objects.update_or_create(
        year=year,
        defaults={
            "archive_data": archive_data,
            "major_stats": major_stats,
            "grade_stats": grade_stats,
            "total_applications": total_applications,
            "admitted_count": admitted_count,
            "operator": user,
        },
    )
    return archive


def _collect_archive_data(
    applications: QuerySet[StudentApplication],
    admissions: QuerySet[Admission],
) -> Dict[str, Any]:
    """收集存档数据.

    Args:
        applications: 报名记录查询集
        admissions: 录取记录查询集

    Returns:
        存档数据字典
    """
    applications_data = []
    for app in applications:
        app_data = {
            "student_id": app.student_id,
            "name": app.name,
            "gender": app.gender,
            "grade": app.grade,
            "major": app.major,
            "phone": app.phone,
            "email": app.email,
            "gpa": str(app.gpa) if app.gpa else None,
            "skills": app.skills,
            "experience": app.experience,
            "motivation": app.motivation,
            "status": app.status,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
            "review_comment": app.review_comment,
            "created_at": app.created_at.isoformat(),
        }

        try:
            admission = app.admission_info
            app_data["admission"] = {
                "admit_year": admission.admit_year,
                "lab_group": admission.lab_group,
                "mentor": admission.mentor,
                "start_date": admission.start_date.isoformat(),
                "end_date": admission.end_date.isoformat() if admission.end_date else None,
                "is_public": admission.is_public,
            }
        except Admission.DoesNotExist:
            app_data["admission"] = None

        applications_data.append(app_data)

    return {"applications": applications_data}


def _calculate_major_stats(applications: QuerySet[StudentApplication]) -> Dict[str, Any]:
    """计算专业统计.

    Args:
        applications: 报名记录查询集

    Returns:
        专业统计字典
    """
    stats = (
        applications.values("major")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return {item["major"]: item["count"] for item in stats}


def _calculate_grade_stats(applications: QuerySet[StudentApplication]) -> Dict[str, Any]:
    """计算年级统计.

    Args:
        applications: 报名记录查询集

    Returns:
        年级统计字典
    """
    stats = (
        applications.values("grade")
        .annotate(count=Count("id"))
        .order_by("grade")
    )
    return {item["grade"]: item["count"] for item in stats}


def get_archive_list() -> QuerySet[DataArchive]:
    """获取存档列表.

    Returns:
        存档 QuerySet
    """
    return DataArchive.objects.all().order_by("-year")


def get_archive_detail(archive_id: int) -> DataArchive | None:
    """获取存档详情.

    Args:
        archive_id: 存档ID

    Returns:
        存档实例或None
    """
    try:
        return DataArchive.objects.get(id=archive_id)
    except DataArchive.DoesNotExist:
        return None
