"""业务逻辑层."""

from typing import Optional

from django.db.models import Q, QuerySet

from api.models import Question, QuestionReply, User


class QuestionService:
    """问题服务类."""
    
    @staticmethod
    def create_question(
        author: User,
        title: str,
        content: str,
        category: str,
        attachments: list[str],
    ) -> Question:
        """创建新问题.
        
        Args:
            author: 提问者
            title: 问题标题
            content: 问题内容
            category: 问题分类
            attachments: 附件URL列表
            
        Returns:
            创建的问题实例
        """
        return Question.objects.create(
            author=author,
            title=title,
            content=content,
            category=category,
            attachments=attachments,
        )
    
    @staticmethod
    def get_question_list(
        user: Optional[User] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[QuerySet[Question], int]:
        """获取问题列表.
        
        Args:
            user: 按用户筛选（None表示不过滤）
            category: 按分类筛选
            status: 按状态筛选
            search: 搜索关键词（搜索标题和内容）
            page: 当前页码
            per_page: 每页数量
            
        Returns:
            (问题查询集, 总数量)
        """
        queryset = Question.objects.all()
        
        # 按用户筛选
        if user:
            queryset = queryset.filter(author=user)
        
        # 按分类筛选
        if category:
            queryset = queryset.filter(category=category)
        
        # 按状态筛选
        if status and status != "all":
            queryset = queryset.filter(status=status)
        
        # 搜索关键词
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        
        total = queryset.count()
        
        # 分页
        start = (page - 1) * per_page
        end = start + per_page
        queryset = queryset[start:end]
        
        return queryset, total
    
    @staticmethod
    def get_question_detail(question_id: int) -> Optional[Question]:
        """获取问题详情.
        
        Args:
            question_id: 问题ID
            
        Returns:
            问题实例，不存在则返回None
        """
        try:
            return Question.objects.prefetch_related("replies", "replies__author").get(
                id=question_id
            )
        except Question.DoesNotExist:
            return None
    
    @staticmethod
    def update_question(
        question: Question,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        attachments: Optional[list[str]] = None,
    ) -> Question:
        """更新问题.
        
        Args:
            question: 要更新的问题实例
            title: 新标题（可选）
            content: 新内容（可选）
            category: 新分类（可选）
            attachments: 新附件列表（可选）
            
        Returns:
            更新后的问题实例
        """
        if title is not None:
            question.title = title
        if content is not None:
            question.content = content
        if category is not None:
            question.category = category
        if attachments is not None:
            question.attachments = attachments
        
        question.save()
        return question
    
    @staticmethod
    def update_question_status(question: Question, status: str) -> Question:
        """更新问题状态.
        
        Args:
            question: 要更新的问题实例
            status: 新状态
            
        Returns:
            更新后的问题实例
        """
        question.status = status
        question.save()
        return question
    
    @staticmethod
    def delete_question(question: Question) -> None:
        """删除问题.
        
        Args:
            question: 要删除的问题实例
        """
        question.delete()


class QuestionReplyService:
    """问题回复服务类."""
    
    @staticmethod
    def create_reply(
        question: Question,
        author: User,
        content: str,
    ) -> QuestionReply:
        """创建问题回复.
        
        Args:
            question: 所属问题
            author: 回复者
            content: 回复内容
            
        Returns:
            创建的回复实例
        """
        reply = QuestionReply.objects.create(
            question=question,
            author=author,
            content=content,
        )
        
        # 更新问题状态为已回复（如果之前是未回复）
        if question.status == Question.STATUS_PENDING:
            question.status = Question.STATUS_REPLIED
            question.save()
        
        return reply