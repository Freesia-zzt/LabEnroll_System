"""API 路由定义."""
from typing import Optional, List

from ninja import Router, File, UploadedFile
from ninja.errors import HttpError

from .schemas import (
    EnrollmentSchema,
    EnrollmentCreateSchema,
    EnrollmentStatusSchema,
    EnrollmentDraftSchema,
    EnrollmentDraftCreateSchema,
    EnrollmentFileSchema,
    PaginatedEnrollmentList,
    PaginatedDraftList,
    MessageSchema,
    # 培训模块 Schema
    TrainingStatisticsSchema,
    LearningProgressSchema,
    PaginatedCourseList,
    CourseDetailSchema,
    ChapterProgressSchema,
    AssignmentSubmissionSchema,
    AssignmentSubmissionCreateSchema,
    AssignmentGradingSchema,
    AssignmentReviewSchema,
    PaginatedPendingAssignmentList,
    PaginatedNotificationList,
    CourseReviewSchema,
    CourseReviewCreateSchema,
)
from .services import (
    EnrollmentService,
    EnrollmentDraftService,
    EnrollmentFileService,
    TrainingStatisticsService,
    LearningProgressService,
    CourseService,
    AssignmentService,
    NotificationService,
    CourseReviewService,
)
from .models import CourseEnrollment

router = Router(tags=["API"])
enrollment_router = Router(tags=["报名相关"])
training_router = Router(tags=["培训模块"])

# ==================== 报名相关 API ====================

@enrollment_router.post("/enrollments", response=EnrollmentSchema)
def submit_enrollment(request, data: EnrollmentCreateSchema):
    """提交报名表单.

    POST /api/v1/enrollments
    """
    # 这里需要从请求中获取当前用户ID，实际项目中应该通过认证获取
    # 为了演示，假设用户ID为1
    user_id = 1
    enrollment = EnrollmentService.create_enrollment(user_id, data.dict())
    return enrollment

@enrollment_router.get("/enrollments", response=PaginatedEnrollmentList)
def get_enrollment_list(
    request,
    page: int = 1,
    page_size: int = 20,
):
    """查看报名状态列表（分页）.

    GET /api/v1/enrollments?page=1&page_size=20
    """
    user_id = 1  # 实际项目中从认证获取
    result = EnrollmentService.get_enrollments_by_user(user_id, page, page_size)
    return result

@enrollment_router.get("/enrollments/{enrollment_id}", response=EnrollmentSchema)
def get_enrollment(request, enrollment_id: int):
    """查看单个报名详情.

    GET /api/v1/enrollments/{enrollment_id}
    """
    enrollment = EnrollmentService.get_enrollment(enrollment_id)
    if not enrollment:
        raise HttpError(404, "报名记录不存在")
    return enrollment

@enrollment_router.put("/enrollments/{enrollment_id}/cancel", response=MessageSchema)
def cancel_enrollment(request, enrollment_id: int):
    """取消报名.

    PUT /api/v1/enrollments/{enrollment_id}/cancel
    """
    success = EnrollmentService.cancel_enrollment(enrollment_id)
    if not success:
        raise HttpError(404, "报名记录不存在")
    return {"message": "报名已取消"}

# ==================== 草稿相关 API ====================

@enrollment_router.post("/drafts", response=EnrollmentDraftSchema)
def save_draft(request, data: EnrollmentDraftCreateSchema):
    """保存表单草稿.

    POST /api/v1/drafts
    """
    user_id = 1  # 实际项目中从认证获取
    draft = EnrollmentDraftService.create_draft(user_id, data.dict())
    return draft

@enrollment_router.get("/drafts", response=PaginatedDraftList)
def get_draft_list(
    request,
    page: int = 1,
    page_size: int = 20,
):
    """获取草稿列表（分页）.

    GET /api/v1/drafts?page=1&page_size=20
    """
    user_id = 1  # 实际项目中从认证获取
    result = EnrollmentDraftService.get_drafts_by_user(user_id, page, page_size)
    return result

@enrollment_router.get("/drafts/{draft_id}", response=EnrollmentDraftSchema)
def get_draft(request, draft_id: int):
    """获取单个草稿详情.

    GET /api/v1/drafts/{draft_id}
    """
    draft = EnrollmentDraftService.get_draft(draft_id)
    if not draft:
        raise HttpError(404, "草稿不存在")
    return draft

@enrollment_router.put("/drafts/{draft_id}", response=EnrollmentDraftSchema)
def update_draft(request, draft_id: int, data: EnrollmentDraftCreateSchema):
    """更新草稿（加载并修改草稿）.

    PUT /api/v1/drafts/{draft_id}
    """
    draft = EnrollmentDraftService.update_draft(draft_id, data.dict())
    if not draft:
        raise HttpError(404, "草稿不存在")
    return draft

@enrollment_router.delete("/drafts/{draft_id}", response=MessageSchema)
def delete_draft(request, draft_id: int):
    """删除草稿.

    DELETE /api/v1/drafts/{draft_id}
    """
    success = EnrollmentDraftService.delete_draft(draft_id)
    if not success:
        raise HttpError(404, "草稿不存在")
    return {"message": "草稿已删除"}

@enrollment_router.delete("/drafts", response=MessageSchema)
def clear_all_drafts(request):
    """清空所有草稿.

    DELETE /api/v1/drafts
    """
    user_id = 1  # 实际项目中从认证获取
    deleted_count = EnrollmentDraftService.clear_all_drafts(user_id)
    return {"message": f"已删除 {deleted_count} 个草稿"}

# ==================== 文件相关 API ====================

@enrollment_router.post("/files", response=EnrollmentFileSchema)
def upload_file(
    request,
    file: UploadedFile = File(...),
    enrollment_id: Optional[int] = None,
    draft_id: Optional[int] = None,
):
    """文件上传.

    POST /api/v1/files?enrollment_id=&draft_id=
    """
    if not enrollment_id and not draft_id:
        raise HttpError(400, "必须指定 enrollment_id 或 draft_id")
    file_obj = EnrollmentFileService.upload_file(file, enrollment_id, draft_id)
    return file_obj

@enrollment_router.delete("/files/{file_id}", response=MessageSchema)
def delete_file(request, file_id: int):
    """删除文件.

    DELETE /api/v1/files/{file_id}
    """
    success = EnrollmentFileService.delete_file(file_id)
    if not success:
        raise HttpError(404, "文件不存在")
    return {"message": "文件已删除"}


# ==================== 培训模块 API ====================

@training_router.get("/statistics", response=TrainingStatisticsSchema)
def get_training_statistics(request):
    """查看培训统计.

    GET /api/v1/training/statistics
    """
    user_id = 1  # 实际项目中从认证获取
    statistics = TrainingStatisticsService.get_user_statistics(user_id)
    return statistics


@training_router.get("/progress", response=List[LearningProgressSchema])
def get_learning_progress(request):
    """查看学习进度.

    GET /api/v1/training/progress
    """
    user_id = 1  # 实际项目中从认证获取
    progress = LearningProgressService.get_user_progress(user_id)
    return progress


@training_router.get("/assignments/pending", response=PaginatedPendingAssignmentList)
def get_pending_assignments(
    request,
    page: int = 1,
    page_size: int = 20,
):
    """查看待批改作业(讲师视角).

    GET /api/v1/training/assignments/pending
    """
    instructor_id = 1  # 实际项目中从认证获取
    result = AssignmentService.get_pending_assignments(instructor_id, page, page_size)
    return result


@training_router.get("/assignments/review/{submission_id}", response=AssignmentReviewSchema)
def get_assignment_review(request, submission_id: int):
    """查看作业详情.

    GET /api/v1/training/assignments/review/{submission_id}
    """
    submission = AssignmentService.get_assignment_detail(submission_id)
    if not submission:
        raise HttpError(404, "作业提交不存在")
    return {
        'id': submission.id,
        'assignment_id': submission.assignment.id,
        'assignment_title': submission.assignment.title,
        'course_id': submission.assignment.course.id,
        'course_title': submission.assignment.course.title,
        'content': submission.content,
        'attachment_url': submission.attachment_url,
        'status': submission.status,
        'score': submission.score,
        'feedback': submission.feedback,
        'submitted_at': submission.submitted_at,
        'graded_at': submission.graded_at,
    }


@training_router.get("/submissions/me", response=List[AssignmentSubmissionSchema])
def get_my_assignment_reviews(request):
    """查看个人作业批改情况.

    GET /api/v1/training/submissions/me
    """
    user_id = 1  # 实际项目中从认证获取
    submissions = AssignmentService.get_user_submissions(user_id)
    return submissions


@training_router.get("/submissions/{submission_id}", response=AssignmentSubmissionSchema)
def get_submission_detail(request, submission_id: int):
    """作业回显 - 获取用户提交的作业详情.

    GET /api/v1/training/submissions/{submission_id}
    """
    submission = AssignmentService.get_assignment_detail(submission_id)
    if not submission:
        raise HttpError(404, "作业提交不存在")
    return {
        'id': submission.id,
        'assignment_id': submission.assignment.id,
        'assignment_title': submission.assignment.title,
        'content': submission.content,
        'attachment_url': submission.attachment_url,
        'status': submission.status,
        'score': submission.score,
        'feedback': submission.feedback,
        'submitted_at': submission.submitted_at,
        'graded_at': submission.graded_at,
    }


@training_router.get("/courses", response=PaginatedCourseList)
def get_my_courses(
    request,
    page: int = 1,
    page_size: int = 20,
):
    """获取我的培训课程列表.

    GET /api/v1/training/courses
    """
    user_id = 1  # 实际项目中从认证获取
    result = CourseService.get_user_courses(user_id, page, page_size)
    return result


@training_router.get("/courses/{course_id}", response=CourseDetailSchema)
def get_course_detail(request, course_id: int):
    """获取课程详情(含课件、章节).

    GET /api/v1/training/courses/{course_id}
    """
    user_id = 1  # 实际项目中从认证获取
    course = CourseService.get_course_detail(course_id, user_id)
    if not course:
        raise HttpError(404, "课程不存在或您未报名该课程")
    return course


@training_router.post("/courses/{course_id}/chapters/{chapter_id}/complete", response=ChapterProgressSchema)
def mark_chapter_complete(request, course_id: int, chapter_id: int):
    """标记章节完成(上报学习进度).

    POST /api/v1/training/courses/{course_id}/chapters/{chapter_id}/complete
    """
    user_id = 1  # 实际项目中从认证获取
    try:
        enrollment = CourseEnrollment.objects.get(course_id=course_id, user_id=user_id)
    except:
        raise HttpError(404, "您未报名该课程")

    progress = LearningProgressService.mark_chapter_completed(enrollment.id, chapter_id)
    if not progress:
        raise HttpError(404, "章节不存在")
    return {
        'id': progress.id,
        'chapter_id': progress.chapter_id,
        'is_completed': progress.is_completed,
        'completed_at': progress.completed_at,
    }


@training_router.post("/assignments/{assignment_id}/submit", response=AssignmentSubmissionSchema)
def submit_assignment(request, assignment_id: int, data: AssignmentSubmissionCreateSchema):
    """提交作业.

    POST /api/v1/training/assignments/{assignment_id}/submit
    """
    user_id = 1  # 实际项目中从认证获取
    submission = AssignmentService.submit_assignment(
        assignment_id=assignment_id,
        user_id=user_id,
        content=data.content,
        attachment_url=data.attachment_url or ""
    )
    return {
        'id': submission.id,
        'assignment_id': submission.assignment.id,
        'assignment_title': submission.assignment.title,
        'content': submission.content,
        'attachment_url': submission.attachment_url,
        'status': submission.status,
        'score': submission.score,
        'feedback': submission.feedback,
        'submitted_at': submission.submitted_at,
        'graded_at': submission.graded_at,
    }


@training_router.post("/submissions/{submission_id}/resubmit", response=AssignmentSubmissionSchema)
def resubmit_assignment(request, submission_id: int, data: AssignmentSubmissionCreateSchema):
    """重新提交作业.

    POST /api/v1/training/submissions/{submission_id}/resubmit
    """
    submission = AssignmentService.resubmit_assignment(
        submission_id=submission_id,
        content=data.content,
        attachment_url=data.attachment_url or ""
    )
    if not submission:
        raise HttpError(400, "只有已批改的作业才能重新提交")
    return {
        'id': submission.id,
        'assignment_id': submission.assignment.id,
        'assignment_title': submission.assignment.title,
        'content': submission.content,
        'attachment_url': submission.attachment_url,
        'status': submission.status,
        'score': submission.score,
        'feedback': submission.feedback,
        'submitted_at': submission.submitted_at,
        'graded_at': submission.graded_at,
    }


@training_router.get("/notifications", response=PaginatedNotificationList)
def get_training_notifications(
    request,
    page: int = 1,
    page_size: int = 20,
):
    """获取培训通知列表.

    GET /api/v1/training/notifications
    """
    user_id = 1  # 实际项目中从认证获取
    result = NotificationService.get_user_notifications(user_id, page, page_size)
    return result


@training_router.post("/courses/{course_id}/review", response=CourseReviewSchema)
def submit_course_review(request, course_id: int, data: CourseReviewCreateSchema):
    """课程评价提交.

    POST /api/v1/training/courses/{course_id}/review
    """
    user_id = 1  # 实际项目中从认证获取
    try:
        enrollment = CourseEnrollment.objects.get(course_id=course_id, user_id=user_id)
    except:
        raise HttpError(404, "您未报名该课程")

    if data.rating < 1 or data.rating > 5:
        raise HttpError(400, "评分必须在1-5之间")

    review = CourseReviewService.create_review(enrollment.id, data.rating, data.content)
    if not review:
        raise HttpError(500, "评价提交失败")
    return {
        'id': review.id,
        'course_id': course_id,
        'rating': review.rating,
        'content': review.content,
        'created_at': review.created_at,
    }


# 挂载子路由
router.add_router("/v1", enrollment_router)
router.add_router("/v1/training", training_router)
