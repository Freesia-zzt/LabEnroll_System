"""API 路由定义."""

from django.http import HttpRequest
from ninja import File, Router, UploadedFile
from ninja.errors import HttpError

from api.models import Enrollment, EnrollmentFile, Question, User
from api.schemas import (
    DraftCreateSchema,
    DraftListSchema,
    DraftSchema,
    DraftUpdateSchema,
    # 报名相关 Schema
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
from api.services import (
    EnrollmentDraftService,
    EnrollmentFileService,
    EnrollmentService,
    QuestionReplyService,
    QuestionService,
)

# 创建问题模块路由
question_router = Router(tags=["问题管理"])


# ==================== 认证相关（简化版）====================


def get_current_user(request: HttpRequest) -> User:
    """获取当前登录用户（简化实现）.

    实际项目中应该从 JWT Token 或 Session 中解析用户
    """
    # 这里简化处理，实际应该从请求头获取 token 并解析
    # 暂时返回第一个用户作为示例
    user = User.objects.first()
    if not user:
        raise HttpError(401, "未登录")
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


# ==================== 报名模块路由 ====================

# 创建报名模块路由
enrollment_router = Router(tags=["报名相关"])

# ==================== 报名接口 ====================


@enrollment_router.post(
    "/enrollments",
    response={201: EnrollmentSchema},
    summary="提交报名表单",
)
def create_enrollment(
    request: HttpRequest,
    data: EnrollmentCreateSchema,
) -> EnrollmentSchema:
    """提交新的培训课程报名申请."""
    user = get_current_user(request)

    enrollment = EnrollmentService.create_enrollment(
        user=user,
        course_name=data.course_name,
        department=data.department,
        position=data.position,
        reason=data.reason,
    )

    return 201, enrollment


@enrollment_router.get(
    "/enrollments",
    response={200: EnrollmentListSchema},
    summary="查看报名状态",
)
def list_enrollments(
    request: HttpRequest,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
) -> EnrollmentListSchema:
    """获取当前用户的报名记录列表（分页）."""
    user = get_current_user(request)

    enrollments, total = EnrollmentService.get_enrollment_list(
        user=user,
        status=status,
        page=page,
        per_page=per_page,
    )

    last_page = (total + per_page - 1) // per_page

    return {
        "data": list(enrollments),
        "pagination": {
            "total": total,
            "current_page": page,
            "per_page": per_page,
            "last_page": max(1, last_page),
        },
    }


@enrollment_router.get(
    "/enrollments/{enrollment_id}",
    response={200: EnrollmentSchema},
    summary="查看报名详情",
)
def get_enrollment(
    request: HttpRequest,
    enrollment_id: int,
) -> EnrollmentSchema:
    """获取指定报名记录的详细信息."""
    user = get_current_user(request)
    enrollment = EnrollmentService.get_enrollment_detail(enrollment_id)

    if not enrollment:
        raise HttpError(404, "报名记录不存在")

    # 检查权限
    if enrollment.user_id != user.id:
        raise HttpError(403, "无权查看此报名记录")

    return enrollment


@enrollment_router.put(
    "/enrollments/{enrollment_id}/cancel",
    response={200: MessageSchema},
    summary="取消报名",
)
def cancel_enrollment(
    request: HttpRequest,
    enrollment_id: int,
) -> MessageSchema:
    """取消指定的报名记录."""
    user = get_current_user(request)
    enrollment = EnrollmentService.get_enrollment_detail(enrollment_id)

    if not enrollment:
        raise HttpError(404, "报名记录不存在")

    # 检查权限
    if enrollment.user_id != user.id:
        raise HttpError(403, "无权操作此报名记录")

    # 已通过的报名不能取消
    if enrollment.status == Enrollment.STATUS_APPROVED:
        raise HttpError(400, "已通过的报名不能取消")

    EnrollmentService.cancel_enrollment(enrollment)

    return {"message": "报名已取消"}


# ==================== 草稿接口 ====================


@enrollment_router.post(
    "/drafts",
    response={201: DraftSchema},
    summary="保存表单草稿",
)
def create_draft(
    request: HttpRequest,
    data: DraftCreateSchema,
) -> DraftSchema:
    """保存未完成的报名表单草稿."""
    user = get_current_user(request)

    draft = EnrollmentDraftService.create_draft(
        user=user,
        course_name=data.course_name or "",
        department=data.department or "",
        position=data.position or "",
        reason=data.reason or "",
        draft_data=data.draft_data,
    )

    return 201, draft


@enrollment_router.get(
    "/drafts",
    response={200: DraftListSchema},
    summary="获取草稿列表",
)
def list_drafts(
    request: HttpRequest,
    page: int = 1,
    per_page: int = 20,
) -> DraftListSchema:
    """获取当前用户的草稿列表（分页）."""
    user = get_current_user(request)

    drafts, total = EnrollmentDraftService.get_draft_list(
        user=user,
        page=page,
        per_page=per_page,
    )

    last_page = (total + per_page - 1) // per_page

    return {
        "data": list(drafts),
        "pagination": {
            "total": total,
            "current_page": page,
            "per_page": per_page,
            "last_page": max(1, last_page),
        },
    }


@enrollment_router.get(
    "/drafts/{draft_id}",
    response={200: DraftSchema},
    summary="获取表单草稿",
)
def get_draft(
    request: HttpRequest,
    draft_id: int,
) -> DraftSchema:
    """获取指定草稿的详细信息（加载表单草稿）."""
    user = get_current_user(request)
    draft = EnrollmentDraftService.get_draft_detail(draft_id, user)

    if not draft:
        raise HttpError(404, "草稿不存在")

    return draft


@enrollment_router.put(
    "/drafts/{draft_id}",
    response={200: DraftSchema},
    summary="更新草稿",
)
def update_draft(
    request: HttpRequest,
    draft_id: int,
    data: DraftUpdateSchema,
) -> DraftSchema:
    """更新指定草稿的内容."""
    user = get_current_user(request)
    draft = EnrollmentDraftService.get_draft_detail(draft_id, user)

    if not draft:
        raise HttpError(404, "草稿不存在")

    updated = EnrollmentDraftService.update_draft(
        draft=draft,
        course_name=data.course_name,
        department=data.department,
        position=data.position,
        reason=data.reason,
        draft_data=data.draft_data,
    )

    return updated


@enrollment_router.delete(
    "/drafts/{draft_id}",
    response={200: MessageSchema},
    summary="删除草稿",
)
def delete_draft(
    request: HttpRequest,
    draft_id: int,
) -> MessageSchema:
    """删除指定的草稿."""
    user = get_current_user(request)
    draft = EnrollmentDraftService.get_draft_detail(draft_id, user)

    if not draft:
        raise HttpError(404, "草稿不存在")

    EnrollmentDraftService.delete_draft(draft)

    return {"message": "草稿已删除"}


@enrollment_router.delete(
    "/drafts",
    response={200: MessageSchema},
    summary="清空所有草稿",
)
def clear_all_drafts(
    request: HttpRequest,
) -> MessageSchema:
    """清空当前用户的所有草稿."""
    user = get_current_user(request)

    deleted_count = EnrollmentDraftService.clear_all_drafts(user)

    return {"message": f"已清空 {deleted_count} 个草稿"}


# ==================== 文件上传接口 ====================


@enrollment_router.post(
    "/files",
    response={201: FileUploadResponseSchema},
    summary="文件上传",
)
def upload_enrollment_file(
    request: HttpRequest,
    file: UploadedFile = File(...),
    enrollment_id: int | None = None,
    draft_id: int | None = None,
) -> FileUploadResponseSchema:
    """上传报名相关文件."""
    user = get_current_user(request)

    # 验证参数（必须指定 enrollment_id 或 draft_id）
    if not enrollment_id and not draft_id:
        raise HttpError(400, "必须指定 enrollment_id 或 draft_id")

    # 获取关联对象
    enrollment = None
    draft = None

    if enrollment_id:
        enrollment = EnrollmentService.get_enrollment_detail(enrollment_id)
        if not enrollment or enrollment.user_id != user.id:
            raise HttpError(404, "报名记录不存在或无权限")

    if draft_id:
        draft = EnrollmentDraftService.get_draft_detail(draft_id, user)
        if not draft:
            raise HttpError(404, "草稿不存在")

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
        raise HttpError(400, "不支持的文件类型")

    # 验证文件大小 (10MB)
    max_size = 10 * 1024 * 1024
    if file.size > max_size:
        raise HttpError(400, "文件大小超过10MB限制")

    uploaded_file = EnrollmentFileService.upload_file(
        file=file,
        enrollment=enrollment,
        draft=draft,
    )

    return uploaded_file


@enrollment_router.delete(
    "/files/{file_id}",
    response={200: MessageSchema},
    summary="删除文件",
)
def delete_enrollment_file(
    request: HttpRequest,
    file_id: int,
) -> MessageSchema:
    """删除指定的文件."""
    user = get_current_user(request)

    try:
        enrollment_file = EnrollmentFile.objects.get(id=file_id)
    except EnrollmentFile.DoesNotExist as err:
        raise HttpError(404, "文件不存在") from err

    # 检查权限
    if enrollment_file.enrollment:
        if enrollment_file.enrollment.user_id != user.id:
            raise HttpError(403, "无权删除此文件")
    elif enrollment_file.draft:
        if enrollment_file.draft.user_id != user.id:
            raise HttpError(403, "无权删除此文件")

    EnrollmentFileService.delete_file(enrollment_file)

    return {"message": "文件已删除"}


# ==================== 主路由 ====================

# 创建主路由
router = Router(tags=["API"])

# 挂载问题管理路由
router.add_router("/questions", question_router)

# 挂载报名模块路由
router.add_router("/", enrollment_router)
