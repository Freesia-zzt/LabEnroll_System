"""API 业务逻辑层."""
from typing import List, Optional

from django.core.files.uploadedfile import UploadedFile

from .models import Enrollment, EnrollmentDraft, EnrollmentFile


class EnrollmentService:
    """报名服务类."""

    @staticmethod
    def create_enrollment(user_id: int, data: dict) -> Enrollment:
        """创建报名.

        Args:
            user_id: 用户ID
            data: 报名数据

        Returns:
            创建的报名对象
        """
        return Enrollment.objects.create(
            user_id=user_id,
            course_name=data['course_name'],
            department=data['department'],
            position=data['position'],
            reason=data['reason'],
        )

    @staticmethod
    def get_enrollment(enrollment_id: int) -> Optional[Enrollment]:
        """获取报名详情.

        Args:
            enrollment_id: 报名ID

        Returns:
            报名对象或 None
        """
        try:
            return Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return None

    @staticmethod
    def get_enrollments_by_user(user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取用户的报名列表（分页）.

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页大小

        Returns:
            分页结果字典
        """
        queryset = Enrollment.objects.filter(user_id=user_id).order_by('-submitted_at')
        total = queryset.count()
        items = queryset[(page - 1) * page_size:page * page_size]
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': list(items)
        }

    @staticmethod
    def update_enrollment(enrollment_id: int, data: dict) -> Optional[Enrollment]:
        """更新报名信息.

        Args:
            enrollment_id: 报名ID
            data: 更新数据

        Returns:
            更新后的报名对象或 None
        """
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
            for key, value in data.items():
                if value is not None:
                    setattr(enrollment, key, value)
            enrollment.save()
            return enrollment
        except Enrollment.DoesNotExist:
            return None

    @staticmethod
    def cancel_enrollment(enrollment_id: int) -> bool:
        """取消报名.

        Args:
            enrollment_id: 报名ID

        Returns:
            是否取消成功
        """
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
            enrollment.status = 'cancelled'
            enrollment.save()
            return True
        except Enrollment.DoesNotExist:
            return False


class EnrollmentDraftService:
    """报名草稿服务类."""

    @staticmethod
    def create_draft(user_id: int, data: dict) -> EnrollmentDraft:
        """创建草稿.

        Args:
            user_id: 用户ID
            data: 草稿数据

        Returns:
            创建的草稿对象
        """
        return EnrollmentDraft.objects.create(
            user_id=user_id,
            course_name=data.get('course_name', ''),
            department=data.get('department', ''),
            position=data.get('position', ''),
            reason=data.get('reason', ''),
            draft_data=data.get('draft_data', {}),
        )

    @staticmethod
    def get_draft(draft_id: int) -> Optional[EnrollmentDraft]:
        """获取草稿详情.

        Args:
            draft_id: 草稿ID

        Returns:
            草稿对象或 None
        """
        try:
            return EnrollmentDraft.objects.get(id=draft_id)
        except EnrollmentDraft.DoesNotExist:
            return None

    @staticmethod
    def get_drafts_by_user(user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取用户的草稿列表（分页）.

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页大小

        Returns:
            分页结果字典
        """
        queryset = EnrollmentDraft.objects.filter(user_id=user_id).order_by('-updated_at')
        total = queryset.count()
        items = queryset[(page - 1) * page_size:page * page_size]
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': list(items)
        }

    @staticmethod
    def update_draft(draft_id: int, data: dict) -> Optional[EnrollmentDraft]:
        """更新草稿.

        Args:
            draft_id: 草稿ID
            data: 更新数据

        Returns:
            更新后的草稿对象或 None
        """
        try:
            draft = EnrollmentDraft.objects.get(id=draft_id)
            if 'course_name' in data:
                draft.course_name = data['course_name']
            if 'department' in data:
                draft.department = data['department']
            if 'position' in data:
                draft.position = data['position']
            if 'reason' in data:
                draft.reason = data['reason']
            if 'draft_data' in data:
                draft.draft_data = data['draft_data']
            draft.save()
            return draft
        except EnrollmentDraft.DoesNotExist:
            return None

    @staticmethod
    def delete_draft(draft_id: int) -> bool:
        """删除草稿.

        Args:
            draft_id: 草稿ID

        Returns:
            是否删除成功
        """
        try:
            draft = EnrollmentDraft.objects.get(id=draft_id)
            draft.delete()
            return True
        except EnrollmentDraft.DoesNotExist:
            return False

    @staticmethod
    def clear_all_drafts(user_id: int) -> int:
        """清空所有草稿.

        Args:
            user_id: 用户ID

        Returns:
            删除的草稿数量
        """
        deleted_count, _ = EnrollmentDraft.objects.filter(user_id=user_id).delete()
        return deleted_count


class EnrollmentFileService:
    """报名文件服务类."""

    @staticmethod
    def upload_file(
        file: UploadedFile,
        enrollment_id: Optional[int] = None,
        draft_id: Optional[int] = None
    ) -> EnrollmentFile:
        """上传文件.

        Args:
            file: 上传的文件
            enrollment_id: 报名ID（可选）
            draft_id: 草稿ID（可选）

        Returns:
            文件对象
        """
        return EnrollmentFile.objects.create(
            enrollment_id=enrollment_id,
            draft_id=draft_id,
            file=file,
            file_name=file.name,
            file_size=file.size,
        )

    @staticmethod
    def delete_file(file_id: int) -> bool:
        """删除文件.

        Args:
            file_id: 文件ID

        Returns:
            是否删除成功
        """
        try:
            file_obj = EnrollmentFile.objects.get(id=file_id)
            file_obj.file.delete()  # 删除物理文件
            file_obj.delete()  # 删除数据库记录
            return True
        except EnrollmentFile.DoesNotExist:
            return False

    @staticmethod
    def get_files_by_enrollment(enrollment_id: int) -> List[EnrollmentFile]:
        """获取报名相关文件.

        Args:
            enrollment_id: 报名ID

        Returns:
            文件列表
        """
        return list(EnrollmentFile.objects.filter(enrollment_id=enrollment_id))

    @staticmethod
    def get_files_by_draft(draft_id: int) -> List[EnrollmentFile]:
        """获取草稿相关文件.

        Args:
            draft_id: 草稿ID

        Returns:
            文件列表
        """
        return list(EnrollmentFile.objects.filter(draft_id=draft_id))
