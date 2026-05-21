"""API 路由定义."""

from typing import Optional

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from api.models import Question, User
from api.schemas import (
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
)
from api.services import QuestionReplyService, QuestionService

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


# ==================== 主路由 ====================

# 创建主路由
router = Router(tags=["API"])

# 注册问题模块路由
router.add_router("/questions", question_router)