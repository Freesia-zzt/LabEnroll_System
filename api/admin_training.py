"""管理员后台 — 培训与作业管理模块路由."""

from datetime import datetime

from django.db.models import Count
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import LimitOffsetPagination, paginate

from api.admin_schemas import (
    AssignInstructorIn,
    AttendanceStatOut,
    ErrorResponse,
    ForbiddenResponse,
    SuccessResponse,
    TaskIn,
    TaskOut,
    TaskSubmissionOut,
    TrainingNotificationIn,
    TrainingNotificationOut,
    TrainingWeekIn,
    TrainingWeekOut,
)
from api.dependencies import get_current_admin_user, permission_required
from api.models import (
    Assignment,
    AssignmentSubmission,
    Attendance,
    AuditLog,
    TrainingNotification,
    TrainingWeek,
)
from api.utils.audit import audit_log

router = Router(tags=["Admin-Training"])


# ==================== 培训周次 ====================


def _week_to_out(week: TrainingWeek) -> dict:
    instructors = week.instructors.all()
    return {
        "id": week.id,
        "week_name": week.week_name,
        "start_date": week.start_date.isoformat(),
        "end_date": week.end_date.isoformat(),
        "description": week.description,
        "is_published": week.is_published,
        "published_at": week.published_at,
        "instructor_ids": [u.id for u in instructors],
        "instructor_names": [u.username for u in instructors],
        "created_at": week.created_at,
    }


@router.get(
    "/training-weeks",
    response={200: list[TrainingWeekOut]},
    summary="获取培训周次列表",
    description="获取所有培训周次列表，包含讲师/助教信息。",
)
@paginate(LimitOffsetPagination)
@permission_required("content.edit")
def list_training_weeks(
    request: HttpRequest,
    is_published: bool | None = None,
) -> list[dict]:
    """获取培训周次列表."""
    queryset = TrainingWeek.objects.all().prefetch_related("instructors")
    if is_published is not None:
        queryset = queryset.filter(is_published=is_published)
    return [_week_to_out(w) for w in queryset]


@router.post(
    "/training-weeks",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse},
    summary="创建培训周次",
    description="创建培训周次。结束日期必须晚于开始日期。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="培训管理", action=AuditLog.ActionChoices.CREATE, target_type="TrainingWeek")
def create_training_week(request: HttpRequest, payload: TrainingWeekIn) -> dict:
    """创建培训周次."""
    try:
        start_date = datetime.strptime(payload.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(payload.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HttpError(400, "日期格式错误，应为 YYYY-MM-DD") from None

    if end_date <= start_date:
        raise HttpError(400, "结束日期必须晚于开始日期")

    now = timezone.now()
    week = TrainingWeek.objects.create(
        week_name=payload.week_name,
        start_date=start_date,
        end_date=end_date,
        description=payload.description,
        is_published=payload.is_published,
        published_at=now if payload.is_published else None,
    )

    return {
        "code": 200,
        "message": "培训周次创建成功",
        "data": _week_to_out(week),
    }


@router.post(
    "/training-weeks/{week_id}/assignments",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="分配讲师/助教",
    description="为培训周次分配讲师或助教。replace=true 全量覆盖，false 增量追加。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="培训管理", action=AuditLog.ActionChoices.UPDATE, target_type="TrainingWeek")
def assign_instructors(
    request: HttpRequest,
    week_id: int,
    payload: AssignInstructorIn,
) -> dict:
    """分配讲师/助教."""
    try:
        week = TrainingWeek.objects.get(id=week_id)
    except TrainingWeek.DoesNotExist:
        raise HttpError(404, "培训周次不存在") from None

    if payload.replace:
        week.instructors.set(payload.user_ids)
    else:
        current_ids = set(week.instructors.values_list("id", flat=True))
        new_ids = set(payload.user_ids)
        week.instructors.add(*list(new_ids - current_ids))

    return {
        "code": 200,
        "message": "讲师/助教分配成功",
        "data": _week_to_out(week),
    }


@router.get(
    "/training-weeks/{week_id}/attendance",
    response={200: AttendanceStatOut, 403: ForbiddenResponse, 404: ErrorResponse},
    summary="获取签到统计",
    description="获取该周次的签到统计（应到人数、实到人数、缺席名单），使用 annotate 在数据库层计算。",
)
@permission_required("content.edit")
def get_attendance_stats(
    request: HttpRequest,
    week_id: int,
) -> dict:
    """获取签到统计."""
    try:
        week = TrainingWeek.objects.get(id=week_id)
    except TrainingWeek.DoesNotExist:
        raise HttpError(404, "培训周次不存在") from None

    present_count = Attendance.objects.filter(
        training_week=week, status="present"
    ).count()

    absent_records = Attendance.objects.filter(
        training_week=week, status="absent"
    ).select_related("user")

    return {
        "total_count": Attendance.objects.filter(training_week=week).count(),
        "present_count": present_count,
        "absent_list": [
            {"user_id": r.user_id, "user_name": r.user.username}
            for r in absent_records
        ],
    }


# ==================== 培训通知 ====================


def _notification_to_out(notice: TrainingNotification) -> dict:
    return {
        "id": notice.id,
        "title": notice.title,
        "content": notice.content,
        "status": notice.status,
        "training_week_name": notice.training_week.week_name if notice.training_week else None,
        "created_by_name": notice.created_by.username,
        "send_time_type": notice.send_time_type,
        "scheduled_time": notice.scheduled_time,
        "sent_at": notice.sent_at,
        "created_at": notice.created_at,
    }


@router.get(
    "/training-notifications",
    response={200: list[TrainingNotificationOut]},
    summary="获取通知列表",
    description="获取培训通知列表，支持按状态筛选。",
)
@paginate(LimitOffsetPagination)
@permission_required("content.edit")
def list_notifications(
    request: HttpRequest,
    status: str | None = None,
) -> list[dict]:
    """获取通知列表."""
    queryset = TrainingNotification.objects.all().select_related(
        "created_by", "training_week"
    )
    if status:
        queryset = queryset.filter(status=status)
    return [_notification_to_out(n) for n in queryset]


@router.post(
    "/training-notifications",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse},
    summary="发布通知",
    description="发布培训通知，可关联特定的培训周次。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="培训管理", action=AuditLog.ActionChoices.CREATE, target_type="TrainingNotification")
def create_notification(request: HttpRequest, payload: TrainingNotificationIn) -> dict:
    """发布通知."""
    admin = get_current_admin_user(request)

    training_week = None
    if payload.training_week_id is not None:
        try:
            training_week = TrainingWeek.objects.get(id=payload.training_week_id)
        except TrainingWeek.DoesNotExist:
            raise HttpError(400, "关联的培训周次不存在") from None

    scheduled_time = None
    if payload.scheduled_time:
        try:
            scheduled_time = datetime.strptime(payload.scheduled_time, "%Y-%m-%d %H:%M")
        except ValueError:
            raise HttpError(400, "定时时间格式错误，应为 YYYY-MM-DD HH:MM") from None

    is_draft = payload.send_time_type == "scheduled"
    status = "draft" if is_draft else "sent"

    notice = TrainingNotification.objects.create(
        title=payload.title,
        content=payload.content,
        training_week=training_week,
        send_time_type=payload.send_time_type,
        scheduled_time=scheduled_time,
        is_draft=is_draft,
        status=status,
        created_by=admin,
        sent_at=timezone.now() if status == "sent" else None,
    )

    return {
        "code": 200,
        "message": "通知已发布" if status == "sent" else "通知草稿已保存",
        "data": _notification_to_out(notice),
    }


# ==================== 作业任务 ====================


def _task_to_out(task: Assignment) -> dict:
    submission_count = AssignmentSubmission.objects.filter(assignment=task).count()
    total_students = 0
    submission_rate = 0.0
    if total_students > 0:
        submission_rate = round(submission_count / total_students * 100, 1)

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "training_week_id": task.training_week_id,
        "training_week_name": task.training_week.week_name,
        "deadline": task.deadline,
        "created_by_name": task.created_by.username,
        "submission_count": submission_count,
        "total_students": total_students,
        "submission_rate": submission_rate,
        "created_at": task.created_at,
    }


@router.get(
    "/tasks",
    response={200: list[TaskOut]},
    summary="获取作业列表",
    description="获取作业任务列表，支持按周次筛选。提交率在数据库层计算。",
)
@paginate(LimitOffsetPagination)
@permission_required("content.edit")
def list_tasks(
    request: HttpRequest,
    training_week_id: int | None = None,
) -> list[dict]:
    """获取作业列表."""
    queryset = Assignment.objects.all().select_related(
        "training_week", "created_by"
    )
    if training_week_id is not None:
        queryset = queryset.filter(training_week_id=training_week_id)

    tasks = list(queryset)
    task_ids = [t.id for t in tasks]

    submission_counts = dict(
        AssignmentSubmission.objects.filter(assignment_id__in=task_ids)
        .values("assignment_id")
        .annotate(count=Count("id"))
        .values_list("assignment_id", "count")
    )

    result = []
    for task in tasks:
        data = _task_to_out(task)
        data["submission_count"] = submission_counts.get(task.id, 0)
        result.append(data)

    return result


@router.post(
    "/tasks",
    response={200: SuccessResponse, 400: ErrorResponse, 403: ForbiddenResponse},
    summary="发布作业",
    description="发布作业，设定截止时间和关联周次。截止时间必须晚于当前时间。需要内容编辑权限。",
)
@permission_required("content.edit")
@audit_log(module="培训管理", action=AuditLog.ActionChoices.CREATE, target_type="Assignment")
def create_task(request: HttpRequest, payload: TaskIn) -> dict:
    """发布作业."""
    try:
        deadline = datetime.strptime(payload.deadline, "%Y-%m-%d %H:%M")
        deadline = timezone.make_aware(deadline) if timezone.is_naive(deadline) else deadline
    except ValueError:
        raise HttpError(400, "截止时间格式错误，应为 YYYY-MM-DD HH:MM") from None

    if deadline <= timezone.now():
        raise HttpError(400, "截止时间必须晚于当前时间")

    try:
        week = TrainingWeek.objects.get(id=payload.training_week_id)
    except TrainingWeek.DoesNotExist:
        raise HttpError(400, "关联的培训周次不存在") from None

    admin = get_current_admin_user(request)

    task = Assignment.objects.create(
        title=payload.title,
        description=payload.description,
        training_week=week,
        deadline=deadline,
        created_by=admin,
    )

    return {
        "code": 200,
        "message": "作业发布成功",
        "data": _task_to_out(task),
    }


@router.get(
    "/tasks/{task_id}/submissions",
    response={200: list[TaskSubmissionOut], 403: ForbiddenResponse, 404: ErrorResponse},
    summary="获取作业提交列表",
    description="获取该作业的提交列表（含提交人信息），并计算提交率。",
)
@paginate(LimitOffsetPagination)
@permission_required("content.edit")
def list_submissions(
    request: HttpRequest,
    task_id: int,
) -> list[dict]:
    """获取作业提交列表."""
    try:
        task = Assignment.objects.get(id=task_id)
    except Assignment.DoesNotExist:
        raise HttpError(404, "作业不存在") from None

    submissions = AssignmentSubmission.objects.filter(assignment=task).select_related("user")

    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "user_name": s.user.username,
            "content": s.content,
            "attachment": s.attachment,
            "score": s.score,
            "comment": s.comment,
            "status": s.status,
            "submitted_at": s.submitted_at,
        }
        for s in submissions
    ]
