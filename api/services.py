"""业务逻辑层."""

from typing import Optional

from django.db.models import Q, QuerySet

from api.models import Question, QuestionReply, User, Enrollment, EnrollmentDraft, EnrollmentFile


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


# ==================== 报名服务类 ====================

class EnrollmentService:
    """报名服务类."""
    
    @staticmethod
    def create_enrollment(
        user: User,
        course_name: str,
        department: str,
        position: str,
        reason: str,
    ) -> Enrollment:
        """创建报名记录.
        
        Args:
            user: 报名用户
            course_name: 课程名称
            department: 部门
            position: 职位
            reason: 报名理由
            
        Returns:
            创建的报名实例
        """
        return Enrollment.objects.create(
            user=user,
            course_name=course_name,
            department=department,
            position=position,
            reason=reason,
        )
    
    @staticmethod
    def get_enrollment_list(
        user: Optional[User] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[QuerySet[Enrollment], int]:
        """获取报名列表.
        
        Args:
            user: 按用户筛选
            status: 按状态筛选
            page: 当前页码
            per_page: 每页数量
            
        Returns:
            (报名查询集, 总数量)
        """
        queryset = Enrollment.objects.all()
        
        if user:
            queryset = queryset.filter(user=user)
        
        if status and status != "all":
            queryset = queryset.filter(status=status)
        
        total = queryset.count()
        
        # 分页
        start = (page - 1) * per_page
        end = start + per_page
        queryset = queryset[start:end]
        
        return queryset, total
    
    @staticmethod
    def get_enrollment_detail(enrollment_id: int) -> Optional[Enrollment]:
        """获取报名详情.
        
        Args:
            enrollment_id: 报名ID
            
        Returns:
            报名实例，不存在则返回None
        """
        try:
            return Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return None
    
    @staticmethod
    def update_enrollment(
        enrollment: Enrollment,
        **kwargs,
    ) -> Enrollment:
        """更新报名信息.
        
        Args:
            enrollment: 报名实例
            kwargs: 要更新的字段
            
        Returns:
            更新后的报名实例
        """
        for key, value in kwargs.items():
            if value is not None and hasattr(enrollment, key):
                setattr(enrollment, key, value)
        
        enrollment.save()
        return enrollment
    
    @staticmethod
    def cancel_enrollment(enrollment: Enrollment) -> Enrollment:
        """取消报名.
        
        Args:
            enrollment: 报名实例
            
        Returns:
            更新后的报名实例
        """
        enrollment.status = Enrollment.STATUS_CANCELLED
        enrollment.save()
        return enrollment
    
    @staticmethod
    def delete_enrollment(enrollment: Enrollment) -> None:
        """删除报名记录.
        
        Args:
            enrollment: 报名实例
        """
        enrollment.delete()


class EnrollmentDraftService:
    """报名草稿服务类."""
    
    @staticmethod
    def create_draft(
        user: User,
        course_name: str = "",
        department: str = "",
        position: str = "",
        reason: str = "",
        draft_data: dict = None,
    ) -> EnrollmentDraft:
        """创建草稿.
        
        Args:
            user: 用户
            course_name: 课程名称
            department: 部门
            position: 职位
            reason: 报名理由
            draft_data: 额外草稿数据
            
        Returns:
            创建的草稿实例
        """
        return EnrollmentDraft.objects.create(
            user=user,
            course_name=course_name,
            department=department,
            position=position,
            reason=reason,
            draft_data=draft_data or {},
        )
    
    @staticmethod
    def get_draft_list(
        user: User,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[QuerySet[EnrollmentDraft], int]:
        """获取草稿列表.
        
        Args:
            user: 用户
            page: 当前页码
            per_page: 每页数量
            
        Returns:
            (草稿查询集, 总数量)
        """
        queryset = EnrollmentDraft.objects.filter(user=user)
        total = queryset.count()
        
        # 分页
        start = (page - 1) * per_page
        end = start + per_page
        queryset = queryset[start:end]
        
        return queryset, total
    
    @staticmethod
    def get_draft_detail(draft_id: int, user: User) -> Optional[EnrollmentDraft]:
        """获取草稿详情.
        
        Args:
            draft_id: 草稿ID
            user: 用户（用于权限验证）
            
        Returns:
            草稿实例，不存在或无权限则返回None
        """
        try:
            return EnrollmentDraft.objects.get(id=draft_id, user=user)
        except EnrollmentDraft.DoesNotExist:
            return None
    
    @staticmethod
    def update_draft(
        draft: EnrollmentDraft,
        **kwargs,
    ) -> EnrollmentDraft:
        """更新草稿.
        
        Args:
            draft: 草稿实例
            kwargs: 要更新的字段
            
        Returns:
            更新后的草稿实例
        """
        for key, value in kwargs.items():
            if value is not None and hasattr(draft, key):
                setattr(draft, key, value)
        
        draft.save()
        return draft
    
    @staticmethod
    def delete_draft(draft: EnrollmentDraft) -> None:
        """删除草稿.
        
        Args:
            draft: 草稿实例
        """
        draft.delete()
    
    @staticmethod
    def clear_all_drafts(user: User) -> int:
        """清空用户所有草稿.
        
        Args:
            user: 用户
            
        Returns:
            删除的草稿数量
        """
        deleted_count, _ = EnrollmentDraft.objects.filter(user=user).delete()
        return deleted_count


class EnrollmentFileService:
    """报名文件服务类."""
    
    @staticmethod
    def upload_file(
        file,
        enrollment: Enrollment = None,
        draft: EnrollmentDraft = None,
    ) -> EnrollmentFile:
        """上传文件.
        
        Args:
            file: 上传的文件对象
            enrollment: 关联的报名记录（二选一）
            draft: 关联的草稿（二选一）
            
        Returns:
            创建的文件实例
        """
        import os
        import uuid
        from django.conf import settings
        from datetime import datetime
        
        # 生成唯一文件名
        ext = os.path.splitext(file.name)[1].lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        
        # 确定存储路径
        today = datetime.now()
        relative_path = f"enrollments/{today.year}/{today.month:02d}/{filename}"
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 保存文件
        with open(full_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        return EnrollmentFile.objects.create(
            enrollment=enrollment,
            draft=draft,
            file_name=file.name,
            file_path=relative_path,
            file_size=file.size,
        )
    
    @staticmethod
    def delete_file(enrollment_file: EnrollmentFile) -> None:
        """删除文件.
        
        Args:
            enrollment_file: 文件实例
        """
        import os
        from django.conf import settings
        
        # 删除物理文件
        full_path = os.path.join(settings.MEDIA_ROOT, enrollment_file.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
        
        # 删除数据库记录
        enrollment_file.delete()