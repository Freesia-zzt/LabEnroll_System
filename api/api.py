"""API 路由定义 - 学员问题管理模块."""

from typing import Optional

from django.http import HttpRequest
from ninja import Router, File, UploadedFile
from ninja.errors import HttpError

from api.auth_utils import api_response, auth_bearer
from api.models import Question, User
from api.schemas import (
    ApiResponseSchema,
    ChangePasswordInput,
    ForgotPasswordResetInput,
    ForgotPasswordSendCodeInput,
    LoginInput,
    MessageSchema,
    PaginationSchema,
    QuestionBriefSchema,
    QuestionCreateSchema,
    QuestionDetailSchema,
    QuestionFilterSchema,
    QuestionListSchema,
    QuestionReplyCreateSchema,
    QuestionReplySchema,
    QuestionStatusUpdateSchema,
    QuestionUpdateSchema,
    RefreshTokenInput,
    SendActivationCodeInput,
    UpdateInfoInput,
    VerifyActivationCodeInput,
)
from api.services import AuthService, QuestionReplyService, QuestionService


# ==================== 认证路由（需 JWT 认证）====================

auth_router = Router(tags=["认证管理"], auth=auth_bearer)


@auth_router.post(
    "/login",
    response={200: ApiResponseSchema},
    summary="用户登录",
    auth=None,
)
def login(request: HttpRequest, data: LoginInput) -> dict:
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
def send_activation_code(request: HttpRequest, data: SendActivationCodeInput) -> dict:
    """发送激活码到用户邮箱（开发阶段打印到日志）."""
    AuthService.send_activation_code(account=data.account)
    return api_response(msg="激活码已发送，请查看邮箱（或服务器日志）")


@auth_router.post(
    "/verify-activation-code",
    response={200: ApiResponseSchema},
    summary="验证激活码",
    auth=None,
)
def verify_activation_code(request: HttpRequest, data: VerifyActivationCodeInput) -> dict:
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
def logout(request: HttpRequest, data: RefreshTokenInput) -> dict:
    """用户登出，将 Refresh Token 加入黑名单."""
    AuthService.logout(refresh_token=data.refresh_token)
    return api_response(msg="登出成功")


@auth_router.get(
    "/me",
    response={200: ApiResponseSchema},
    summary="获取当前用户信息",
)
def get_user_info(request: HttpRequest) -> dict:
    """获取当前登录用户的完整信息."""
    user = request.auth
    user_info = AuthService.get_user_info(user)
    return api_response(data=user_info)


@auth_router.post(
    "/update-info",
    response={200: ApiResponseSchema},
    summary="修改个人资料",
)
def update_info(request: HttpRequest, data: UpdateInfoInput) -> dict:
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
def change_password(request: HttpRequest, data: ChangePasswordInput) -> dict:
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
def refresh_token(request: HttpRequest, data: RefreshTokenInput) -> dict:
    """使用 Refresh Token 获取新的 Access Token 对."""
    result = AuthService.refresh_token(refresh_token_str=data.refresh_token)
    return api_response(msg="Token 刷新成功", data=result)


# ==================== 忘记密码路由（公开）====================

forgot_password_router = Router(tags=["忘记密码"])


@forgot_password_router.post(
    "/send-code",
    response={200: ApiResponseSchema},
    summary="发送重置密码验证码",
)
def forgot_password_send_code(request: HttpRequest, data: ForgotPasswordSendCodeInput) -> dict:
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
def forgot_password_reset(request: HttpRequest, data: ForgotPasswordResetInput) -> dict:
    """验证码校验通过后重置密码."""
    AuthService.forgot_password_reset(
        account=data.account,
        email=data.email,
        code=data.code,
        new_password=data.new_password,
        new_password_confirmation=data.new_password_confirmation,
    )
    return api_response(msg="密码重置成功，请重新登录")


# ==================== 问题模块路由 ====================

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
        {"value": value, "label": label}
        for value, label in Question.CATEGORY_CHOICES
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
    if filters.status and filters.status not in ["all", "pending", "replied", "resolved"]:
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
        "image/jpeg", "image/png", "image/gif",
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


# ==================== 主路由 ====================

# 创建主路由
router = Router(tags=["API"])

# 注册认证模块路由
router.add_router("/user", auth_router)
router.add_router("/forgot-password", forgot_password_router)

# 注册问题模块路由
router.add_router("/questions", question_router)


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


# ==================== 主路由 ====================

# 创建主路由
router = Router(tags=["API"])

# 注册认证模块路由
router.add_router("/user", auth_router)
router.add_router("/forgot-password", forgot_password_router)

# 注册问题模块路由
router.add_router("/questions", question_router)
# 挂载问题管理路由
router.add_router("/questions", question_router)

