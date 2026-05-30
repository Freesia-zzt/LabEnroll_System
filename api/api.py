"""API 路由定义."""

from django.http import HttpRequest
from ninja import File, Router, UploadedFile
from ninja.errors import HttpError

from .auth_utils import api_response, auth_bearer
from .schemas import (
    ApiResponseSchema,
    ChangePasswordInput,
    ForgotPasswordSendCodeInput,
    ForgotPasswordResetInput,
    LoginInput,
    MessageSchema,
    RefreshTokenInput,
    SendActivationCodeInput,
    UpdateInfoInput,
    VerifyActivationCodeInput,
    EnrollmentSchema,
    EnrollmentCreateSchema,
    EnrollmentListSchema,
    EnrollmentSchema,
    FileUploadResponseSchema,
    MessageSchema,
    QuestionBriefSchema,
    QuestionCreateSchema,
    QuestionDetailSchema,
    QuestionFilterSchema,
    QuestionListSchema,
    QuestionReplyCreateSchema,
    QuestionReplySchema,
    QuestionStatusUpdateSchema,
    QuestionUpdateSchema,
)
from .services import (
    AuthService,
    EnrollmentService,
    EnrollmentDraftService,
    EnrollmentFileService,
    EnrollmentService,
    QuestionReplyService,
    QuestionService,
)

router = Router(tags=["API"])
enrollment_router = Router(tags=["报名相关"])
training_router = Router(tags=["培训模块"], auth=auth_bearer)

# ==================== 认证路由（需 JWT 认证）====================

auth_router = Router(tags=["认证管理"], auth=auth_bearer)


@auth_router.post(
    "/login",
    response={200: ApiResponseSchema},
    summary="用户登录",
    auth=None,
)
def login(request, data: LoginInput) -> dict:
    """用户登录接口."""
    result = AuthService.login(
        account=data.account,
        password=data.password,
        remember_me=data.remember_me,
    )
    return api_response(code=200, msg="登录成功", data=result)


@auth_router.post(
    "/send-activation-code",
    response={200: ApiResponseSchema},
    summary="发送激活码",
    auth=None,
)
def send_activation_code(request, data: SendActivationCodeInput) -> dict:
    """发送激活码到用户邮箱."""
    AuthService.send_activation_code(account=data.account)
    return api_response(msg="激活码已发送，请查看邮箱（或服务器日志）")


@auth_router.post(
    "/verify-activation-code",
    response={200: ApiResponseSchema},
    summary="验证激活码",
    auth=None,
)
def verify_activation_code(request, data: VerifyActivationCodeInput) -> dict:
    """验证激活码以激活账号."""
    AuthService.verify_activation_code(
        account=data.account,
        activation_code=data.activation_code,
    )
    return api_response(msg="激活成功，请登录")


@auth_router.post(
    "/logout",
    response={200: ApiResponseSchema},
    summary="用户登出",
)
def logout(request, data: RefreshTokenInput) -> dict:
    """用户登出，将 Refresh Token 加入黑名单."""
    AuthService.logout(refresh_token=data.refresh_token)
    return api_response(msg="登出成功")


@auth_router.get(
    "/me",
    response={200: ApiResponseSchema},
    summary="获取当前用户信息",
)
def get_user_info(request) -> dict:
    """获取当前登录用户的完整信息."""
    user = request.auth
    user_info = AuthService.get_user_info(user)
    return api_response(data=user_info)


@auth_router.post(
    "/update-info",
    response={200: ApiResponseSchema},
    summary="修改个人资料",
)
def update_info(request, data: UpdateInfoInput) -> dict:
    """修改个人资料，可选同时修改密码."""
    user = request.auth
    AuthService.update_info(
        user=user,
        username=data.username,
        phone=data.phone,
        email=data.email,
        old_password=data.old_password,
        new_password=data.new_password,
    )
    return api_response(msg="更新成功")


@auth_router.post(
    "/change-password",
    response={200: ApiResponseSchema},
    summary="修改密码",
)
def change_password(request, data: ChangePasswordInput) -> dict:
    """修改密码（需提供旧密码验证）."""
    user = request.auth
    AuthService.change_password(
        user=user,
        old_password=data.old_password,
        new_password=data.new_password,
        new_password_confirmation=data.new_password_confirmation,
    )
    return api_response(msg="密码修改成功")


@auth_router.post(
    "/refresh-token",
    response={200: ApiResponseSchema},
    summary="刷新 Access Token",
    auth=None,
)
def refresh_token(request, data: RefreshTokenInput) -> dict:
    """使用 Refresh Token 获取新的 Access Token."""
    result = AuthService.refresh_token(refresh_token_str=data.refresh_token)
    return api_response(msg="Token 刷新成功", data=result)


# ==================== 忘记密码路由（公开）====================

forgot_password_router = Router(tags=["忘记密码"])


@forgot_password_router.post(
    "/send-code",
    response={200: ApiResponseSchema},
    summary="发送重置密码验证码",
)
def forgot_password_send_code(request, data: ForgotPasswordSendCodeInput) -> dict:
    """验证账号邮箱匹配后发送重置密码验证码."""
    AuthService.forgot_password_send_code(
        account=data.account,
        email=data.email,
    )
    return api_response(msg="验证码已发送，请查看邮箱（或服务器日志）")


@forgot_password_router.post(
    "/reset",
    response={200: ApiResponseSchema},
    summary="重置密码",
)
def forgot_password_reset(request, data: ForgotPasswordResetInput) -> dict:
    """验证码校验通过后重置密码."""
    AuthService.forgot_password_reset(
        account=data.account,
        email=data.email,
        code=data.code,
        new_password=data.new_password,
        new_password_confirmation=data.new_password_confirmation,
    )
    return api_response(msg="密码重置成功，请重新登录")


question_router = Router(tags=["问题管理"])


# ==================== 认证相关（简化版）====================


def get_current_user(request: HttpRequest) -> User:
    """获取当前登录用户（简化实现）.

    实际项目中应该从 JWT Token 或 Session 中解析用户
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
    user = request.auth
    result = EnrollmentService.get_enrollments_by_user(user.id, page, page_size)
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
    user = request.auth
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
    user = request.auth
    result = EnrollmentDraftService.get_drafts_by_user(user.id, page, page_size)
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
    user = request.auth
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
    user = request.auth
    statistics = TrainingStatisticsService.get_user_statistics(user.id)
    return statistics


@training_router.get("/progress", response=List[LearningProgressSchema])
def get_learning_progress(request):
    """查看学习进度.

    GET /api/v1/training/progress
    """
    user = request.auth
    progress = LearningProgressService.get_user_progress(user.id)
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
    user = request.auth
    result = AssignmentService.get_pending_assignments(user.id, page, page_size)
    return result


@training_router.get("/assignments/review/{submission_id}", response=AssignmentReviewSchema)
def get_assignment_review(request, submission_id: int):
    """查看作业详情.

    GET /api/v1/training/assignments/review/{submission_id}
    """
    user = request.auth
    submission = AssignmentService.get_assignment_detail(submission_id)
    if not submission:
        raise HttpError(404, "作业提交不存在")
    if submission.user_id != user.id and user.role != 1:
        raise HttpError(403, "无权查看此作业")
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
    user = request.auth
    submissions = AssignmentService.get_user_submissions(user.id)
    return submissions


@training_router.get("/submissions/{submission_id}", response=AssignmentSubmissionSchema)
def get_submission_detail(request, submission_id: int):
    """作业回显 - 获取用户提交的作业详情.

    GET /api/v1/training/submissions/{submission_id}
    """
    user = request.auth
    submission = AssignmentService.get_assignment_detail(submission_id)
    if not submission:
        raise HttpError(404, "作业提交不存在")
    if submission.user_id != user.id:
        raise HttpError(403, "无权查看他人的作业")
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
    user = request.auth
    result = CourseService.get_user_courses(user.id, page, page_size)
    return result


@training_router.get("/courses/{course_id}", response=CourseDetailSchema)
def get_course_detail(request, course_id: int):
    """获取课程详情(含课件、章节).

    GET /api/v1/training/courses/{course_id}
    """
    user = request.auth
    course = CourseService.get_course_detail(course_id, user.id)
    if not course:
        raise HttpError(404, "课程不存在或您未报名该课程")
    return course


@training_router.post("/courses/{course_id}/chapters/{chapter_id}/complete", response=ChapterProgressSchema)
def mark_chapter_complete(request, course_id: int, chapter_id: int):
    """标记章节完成(上报学习进度).

    POST /api/v1/training/courses/{course_id}/chapters/{chapter_id}/complete
    """
    user = request.auth
    try:
        enrollment = CourseEnrollment.objects.get(course_id=course_id, user_id=user.id)
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
    user = request.auth
    submission = AssignmentService.submit_assignment(
        assignment_id=assignment_id,
        user_id=user.id,
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
    user = request.auth
    existing = AssignmentService.get_assignment_detail(submission_id)
    if not existing:
        raise HttpError(404, "作业提交不存在")
    if existing.user_id != user.id:
        raise HttpError(403, "无权操作他人的作业")
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
    user = request.auth
    result = NotificationService.get_user_notifications(user.id, page, page_size)
    return result


@training_router.post("/courses/{course_id}/review", response=CourseReviewSchema)
def submit_course_review(request, course_id: int, data: CourseReviewCreateSchema):
    """课程评价提交.

    POST /api/v1/training/courses/{course_id}/review
    """
    user = request.auth
    try:
        enrollment = CourseEnrollment.objects.get(course_id=course_id, user_id=user.id)
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


# ==================== 问题管理 API ====================

def _get_current_user(request):
    """获取当前登录用户（简化实现）."""
    user = Question.objects.first()
    return user


# ==================== 问题 CRUD 接口 ====================


@question_router.get(
    "/categories",
    response={200: list},
    summary="获取问题分类列表",
)
def get_question_categories(request: HttpRequest) -> list:
    """获取所有问题分类列表."""
    return [
        {"value": value, "label": label} for value, label in Question.CATEGORY_CHOICES
    ]


@question_router.post(
    "",
    response={201: QuestionBriefSchema},
    summary="新增问题",
)
def create_question(
    request: HttpRequest,
    data: QuestionCreateSchema,
) -> QuestionBriefSchema:
    """创建新问题.

    需要登录权限
    """
    user = get_current_user(request)

    # 验证分类是否有效
    valid_categories = [c[0] for c in Question.CATEGORY_CHOICES]
    if data.category not in valid_categories:
        raise HttpError(400, f"无效的分类，可选: {valid_categories}")

    question = QuestionService.create_question(
        author=user,
        title=data.title,
        content=data.content,
        category=data.category,
        attachments=data.attachments,
    )

    return 201, question


@question_router.get(
    "",
    response={200: QuestionListSchema},
    summary="获取问题列表",
)
def list_questions(
    request: HttpRequest,
    filters: QuestionFilterSchema = QuestionFilterSchema(),
) -> QuestionListSchema:
    """获取问题列表.

    支持分页、分类筛选、状态筛选、关键词搜索
    """
    user = get_current_user(request)

    # 验证状态参数
    if filters.status and filters.status not in [
        "all",
        "pending",
        "replied",
        "resolved",
    ]:
        raise HttpError(400, "无效的状态参数")

    questions, total = QuestionService.get_question_list(
        user=user,
        category=filters.category,
        status=filters.status,
        search=filters.search,
        page=filters.page,
        per_page=filters.per_page,
    )

    # 计算分页信息
    last_page = (total + filters.per_page - 1) // filters.per_page

    return {
        "data": list(questions),
        "pagination": {
            "total": total,
            "current_page": filters.page,
            "per_page": filters.per_page,
            "last_page": max(1, last_page),
        },
    }


@question_router.get(
    "/{question_id}",
    response={200: QuestionDetailSchema},
    summary="获取问题详情",
)
def get_question(
    request: HttpRequest,
    question_id: int,
) -> QuestionDetailSchema:
    """获取单个问题详情，包含回复列表."""
    question = QuestionService.get_question_detail(question_id)

    if not question:
        raise HttpError(404, "问题不存在")

    return question


@question_router.put(
    "/{question_id}",
    response={200: QuestionBriefSchema},
    summary="修改问题",
)
def update_question(
    request: HttpRequest,
    question_id: int,
    data: QuestionUpdateSchema,
) -> QuestionBriefSchema:
    """修改问题内容.

    仅问题发布者可修改
    """
    user = get_current_user(request)
    question = QuestionService.get_question_detail(question_id)

    if not question:
        raise HttpError(404, "问题不存在")

    # 检查权限
    if question.author_id != user.id:
        raise HttpError(403, "无权修改此问题")

    # 已解决的问题不能修改
    if question.status == Question.STATUS_RESOLVED:
        raise HttpError(400, "已解决的问题不能修改")

    updated = QuestionService.update_question(
        question=question,
        title=data.title,
        content=data.content,
        category=data.category,
        attachments=data.attachments,
    )

    return updated


@question_router.delete(
    "/{question_id}",
    response={200: MessageSchema},
    summary="删除问题",
)
def delete_question(
    request: HttpRequest,
    question_id: int,
) -> MessageSchema:
    """删除问题.

    仅问题发布者可删除
    """
    user = get_current_user(request)
    question = QuestionService.get_question_detail(question_id)

    if not question:
        raise HttpError(404, "问题不存在")

    # 检查权限
    if question.author_id != user.id:
        raise HttpError(403, "无权删除此问题")

    QuestionService.delete_question(question)

    return {"message": "删除成功"}


@question_router.put(
    "/{question_id}/status",
    response={200: QuestionBriefSchema},
    summary="更新问题状态",
)
def update_question_status(
    request: HttpRequest,
    question_id: int,
    data: QuestionStatusUpdateSchema,
) -> QuestionBriefSchema:
    """更新问题状态（标记已解决等）.

    仅问题发布者可操作
    """
    user = get_current_user(request)
    question = QuestionService.get_question_detail(question_id)

    if not question:
        raise HttpError(404, "问题不存在")

    # 检查权限
    if question.author_id != user.id:
        raise HttpError(403, "无权操作此问题")

    # 验证状态值
    valid_statuses = [s[0] for s in Question.STATUS_CHOICES]
    if data.status not in valid_statuses:
        raise HttpError(400, f"无效的状态，可选: {valid_statuses}")

    updated = QuestionService.update_question_status(question, data.status)
    return updated


# ==================== 问题回复接口 ====================


@question_router.post(
    "/{question_id}/replies",
    response={201: QuestionReplySchema},
    summary="回复问题",
)
def create_reply(
    request: HttpRequest,
    question_id: int,
    data: QuestionReplyCreateSchema,
) -> QuestionReplySchema:
    """对问题发表回复."""
    user = get_current_user(request)
    question = QuestionService.get_question_detail(question_id)

    if not question:
        raise HttpError(404, "问题不存在")

    reply = QuestionReplyService.create_reply(
        question=question,
        author=user,
        content=data.content,
    )

    return 201, reply


# ==================== 文件上传接口 ====================


@question_router.post(
    "/upload",
    response={200: dict},
    summary="附件/图片上传",
)
def upload_question_file(
    request: HttpRequest,
    file: UploadedFile = File(...),
) -> dict:
    """上传问题附件或图片.

    支持图片(JPG/PNG/GIF)和文档(PDF/DOC/DOCX)格式
    文件大小限制: 5MB
    """
    import os
    import uuid

    from django.conf import settings

    # 验证文件类型
    allowed_types = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    if file.content_type not in allowed_types:
        raise HttpError(400, "不支持的文件类型，仅支持 JPG/PNG/GIF/PDF/DOC/DOCX")

    # 验证文件大小 (5MB)
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise HttpError(400, "文件大小超过5MB限制")

    # 生成唯一文件名
    ext = os.path.splitext(file.name)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"

    # 确定存储路径 (按日期分目录)
    from datetime import datetime

    today = datetime.now()
    relative_path = f"questions/{today.year}/{today.month:02d}/{filename}"
    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # 保存文件
    with open(full_path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    # 返回文件URL
    file_url = f"{settings.MEDIA_URL}{relative_path}"

    return {
        "code": 200,
        "message": "上传成功",
        "data": {
            "name": file.name,
            "url": file_url,
            "size": file.size,
            "type": file.content_type,
        },
    }


# 挂载子路由
router.add_router("/v1/auth", auth_router)
router.add_router("/v1/forgot-password", forgot_password_router)
router.add_router("/v1", enrollment_router)
router.add_router("/v1/training", training_router)
router.add_router("/v1/questions", question_router)
