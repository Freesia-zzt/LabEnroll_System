"""API 业务逻辑层."""
import logging
import random
from datetime import datetime, timedelta
from typing import List, Optional

from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone

from .auth_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    is_token_blacklisted,
)
from .email_utils import send_activation_code_email, send_forgot_password_code_email
from .models import (
    Department,
    Enrollment, EnrollmentDraft, EnrollmentFile,
    Course, Chapter, Courseware, CourseEnrollment, ChapterProgress,
    Assignment, AssignmentSubmission, TrainingNotification, CourseReview,
    Question, QuestionReply,
    LabUser,
    TokenBlacklist,
    User,
)


class AuthService:
    """认证服务类."""

    @staticmethod
    def login(account: str, password: str, remember_me: bool = False) -> dict:
        """用户登录."""
        try:
            user = LabUser.objects.get(account=account)
        except LabUser.DoesNotExist:
            raise Exception("账号或密码错误")

        if not user.check_password(password):
            raise Exception("账号或密码错误")

        if user.is_active != 1:
            raise Exception("账号未激活，请先激活")

        token = create_access_token(user, remember_me=remember_me)
        refresh_token = create_refresh_token(user)

        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at"])

        return {
            "user_id": user.id,
            "account": user.account,
            "username": user.username,
            "role": user.role,
            "token": token,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def send_activation_code(account: str) -> None:
        """发送激活码."""
        try:
            user = LabUser.objects.get(account=account)
        except LabUser.DoesNotExist:
            raise Exception("用户不存在")

        if user.is_active == 1:
            raise Exception("账号已激活，无需重复激活")

        if user.activation_expire and user.activation_expire > timezone.now():
            remaining = (user.activation_expire - timezone.now()).total_seconds()
            if remaining > 29 * 60:
                raise Exception("发送太频繁，请1分钟后再试")

        code = f"{random.randint(0, 999999):06d}"
        user.activation_code = code
        user.activation_expire = timezone.now() + timedelta(minutes=30)
        user.save(update_fields=["activation_code", "activation_expire"])

        if user.email:
            success = send_activation_code_email(
                to_email=user.email,
                code=code,
                username=user.username,
            )
            if success:
                pass  # logged in email_utils
        logger.info(f"[激活码] 用户 {user.account}({user.username}) 的激活码: {code}")

    @staticmethod
    def verify_activation_code(account: str, activation_code: str) -> None:
        """验证激活码."""
        try:
            user = LabUser.objects.get(account=account)
        except LabUser.DoesNotExist:
            raise Exception("用户不存在")

        if user.is_active == 1:
            raise Exception("账号已激活")

        if user.activation_code != activation_code:
            raise Exception("激活码错误")

        if not user.activation_expire or user.activation_expire < timezone.now():
            raise Exception("激活码已过期，请重新发送")

        user.is_active = 1
        user.activation_code = None
        user.activation_expire = None
        user.save(update_fields=["is_active", "activation_code", "activation_expire"])

        logger.info(f"[激活成功] 用户 {user.account}({user.username}) 已激活")

    @staticmethod
    def logout(refresh_token: str) -> None:
        """用户登出."""
        payload = decode_token(refresh_token)
        if not payload:
            raise Exception("无效的 Refresh Token")

        if payload.get("token_type") != "refresh":
            raise Exception("请提供 Refresh Token")

        jti = payload.get("jti", "")
        if is_token_blacklisted(jti):
            return

        expires_at = timezone.now() + timedelta(days=7)

        TokenBlacklist.objects.create(
            jti=jti,
            token_type="refresh",
            user_id=payload["user_id"],
            expires_at=expires_at,
        )

        logger.info(f"[登出] 用户 {payload.get('user_id')} 已登出")

    @staticmethod
    def get_user_info(user: LabUser) -> dict:
        """获取用户完整信息."""
        return {
            "id": user.id,
            "account": user.account,
            "username": user.username,
            "phone": user.phone,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "department_id": user.department_id,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }

    @staticmethod
    def update_info(
        user: LabUser,
        username: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        old_password: Optional[str] = None,
        new_password: Optional[str] = None,
    ) -> None:
        """修改个人资料."""
        if username is not None:
            user.username = username
        if phone is not None:
            user.phone = phone
        if email is not None:
            user.email = email

        if old_password and new_password:
            if not user.check_password(old_password):
                raise Exception("旧密码错误")
            user.set_password(new_password)

        user.save()
        logger.info(f"[更新资料] 用户 {user.account} 已更新个人资料")

    @staticmethod
    def change_password(
        user: LabUser,
        old_password: str,
        new_password: str,
        new_password_confirmation: str,
    ) -> None:
        """修改密码."""
        if new_password != new_password_confirmation:
            raise Exception("两次密码不一致")

        if not user.check_password(old_password):
            raise Exception("旧密码错误")

        user.set_password(new_password)
        user.save(update_fields=["password"])
        logger.info(f"[修改密码] 用户 {user.account} 已修改密码")

    @staticmethod
    def forgot_password_send_code(account: str, email: str) -> None:
        """忘记密码-发送验证码."""
        try:
            user = LabUser.objects.get(account=account)
        except LabUser.DoesNotExist:
            raise Exception("用户不存在")

        if user.email != email:
            raise Exception("账号与邮箱不匹配")

        code = f"{random.randint(0, 999999):06d}"
        user.activation_code = code
        user.activation_expire = timezone.now() + timedelta(minutes=10)
        user.save(update_fields=["activation_code", "activation_expire"])

        success = send_forgot_password_code_email(
            to_email=email,
            code=code,
            username=user.username,
        )
        if success:
            pass  # logged in email_utils
        logger.info(f"[找回密码] 用户 {user.account} 的验证码: {code}")

    @staticmethod
    def forgot_password_reset(
        account: str,
        email: str,
        code: str,
        new_password: str,
        new_password_confirmation: str,
    ) -> None:
        """忘记密码-重置密码."""
        if new_password != new_password_confirmation:
            raise Exception("两次密码不一致")

        try:
            user = LabUser.objects.get(account=account, email=email)
        except LabUser.DoesNotExist:
            raise Exception("用户不存在")

        if user.activation_code != code:
            raise Exception("验证码错误")

        if not user.activation_expire or user.activation_expire < timezone.now():
            raise Exception("验证码已过期")

        user.set_password(new_password)
        user.activation_code = None
        user.activation_expire = None
        user.save(update_fields=["password", "activation_code", "activation_expire"])
        logger.info(f"[重置密码] 用户 {user.account} 已重置密码")

    @staticmethod
    def refresh_token(refresh_token_str: str) -> dict:
        """刷新 Access Token."""
        from django.conf import settings

        payload = decode_token(refresh_token_str)
        if not payload:
            raise Exception("Refresh Token 无效或已过期")

        if payload.get("token_type") != "refresh":
            raise Exception("请提供 Refresh Token")

        jti = payload.get("jti", "")
        if is_token_blacklisted(jti):
            raise Exception("Refresh Token 已被吊销")

        try:
            user = LabUser.objects.get(id=payload["user_id"])
        except LabUser.DoesNotExist:
            raise Exception("用户不存在")

        if user.is_active != 1:
            raise Exception("账号未激活")

        new_token = create_access_token(user)
        new_refresh_token = create_refresh_token(user)

        TokenBlacklist.objects.create(
            jti=jti,
            token_type="refresh",
            user=user,
            expires_at=timezone.now() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )

        return {
            "token": new_token,
            "refresh_token": new_refresh_token,
        }



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


# ==================== 培训模块服务 ====================

class TrainingStatisticsService:
    """培训统计服务."""

    @staticmethod
    def get_user_statistics(user_id: int) -> dict:
        """获取用户培训统计.

        Args:
            user_id: 用户ID

        Returns:
            统计数据字典
        """
        enrollments = CourseEnrollment.objects.filter(user_id=user_id)

        total_courses = enrollments.count()
        completed_courses = enrollments.filter(status='completed').count()
        in_progress_courses = enrollments.filter(status='in_progress').count()

        # 计算学习时长
        completed_enrollments = enrollments.filter(status='completed').select_related('course')
        total_learning_hours = sum(
            e.course.duration_hours for e in completed_enrollments if e.course
        ) or 0.0

        # 作业统计
        submissions = AssignmentSubmission.objects.filter(user_id=user_id)
        total_assignments = submissions.count()
        completed_assignments = submissions.filter(status='graded').count()
        pending_assignments = submissions.filter(status__in=['submitted', 'grading']).count()

        # 平均分
        graded_submissions = submissions.filter(status='graded', score__isnull=False)
        average_score = graded_submissions.aggregate(avg=Avg('score'))['avg']

        return {
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'in_progress_courses': in_progress_courses,
            'total_learning_hours': float(total_learning_hours),
            'total_assignments': total_assignments,
            'completed_assignments': completed_assignments,
            'pending_assignments': pending_assignments,
            'average_score': round(average_score, 1) if average_score else None,
        }


class LearningProgressService:
    """学习进度服务."""

    @staticmethod
    def get_user_progress(user_id: int) -> List[dict]:
        """获取用户学习进度列表.

        Args:
            user_id: 用户ID

        Returns:
            学习进度列表
        """
        enrollments = CourseEnrollment.objects.filter(user_id=user_id).select_related('course')

        result = []
        for enrollment in enrollments:
            course = enrollment.course
            total_chapters = course.chapters.count() if course else 0
            completed_chapters = ChapterProgress.objects.filter(
                enrollment=enrollment,
                is_completed=True
            ).count()

            result.append({
                'course_id': course.id if course else 0,
                'course_title': course.title if course else '',
                'status': enrollment.status,
                'progress_percent': enrollment.progress_percent,
                'completed_chapters': completed_chapters,
                'total_chapters': total_chapters,
                'enrolled_at': enrollment.enrolled_at,
                'completed_at': enrollment.completed_at,
            })

        return result

    @staticmethod
    def mark_chapter_completed(enrollment_id: int, chapter_id: int) -> Optional[ChapterProgress]:
        """标记章节完成.

        Args:
            enrollment_id: 选课ID
            chapter_id: 章节ID

        Returns:
            章节进度对象
        """
        try:
            enrollment = CourseEnrollment.objects.get(id=enrollment_id)
            chapter = Chapter.objects.get(id=chapter_id)

            progress, created = ChapterProgress.objects.update_or_create(
                enrollment=enrollment,
                chapter=chapter,
                defaults={
                    'is_completed': True,
                    'completed_at': timezone.now()
                }
            )

            # 更新课程整体进度
            total_chapters = chapter.course.chapters.count()
            completed_count = ChapterProgress.objects.filter(
                enrollment=enrollment,
                is_completed=True
            ).count()

            enrollment.progress_percent = int((completed_count / total_chapters) * 100) if total_chapters > 0 else 0

            if completed_count >= total_chapters:
                enrollment.status = 'completed'
                enrollment.completed_at = timezone.now()
            else:
                enrollment.status = 'in_progress'

            enrollment.save()
            return progress
        except (CourseEnrollment.DoesNotExist, Chapter.DoesNotExist):
            return None


class CourseService:
    """培训课程服务."""

    @staticmethod
    def get_user_courses(user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取用户培训课程列表.

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页大小

        Returns:
            分页结果字典
        """
        enrollments = CourseEnrollment.objects.filter(user_id=user_id).select_related('course', 'course__instructor')

        queryset = []
        for enrollment in enrollments:
            course = enrollment.course
            if course:
                queryset.append({
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'cover_image': course.cover_image,
                    'instructor_name': course.instructor.name if course.instructor else '',
                    'status': course.status,
                    'start_date': course.start_date,
                    'end_date': course.end_date,
                    'duration_hours': course.duration_hours,
                    'enrolled_count': course.enrollments.count(),
                    'enrolled_at': enrollment.enrolled_at,
                })

        total = len(queryset)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': queryset[start:end]
        }

    @staticmethod
    def get_course_detail(course_id: int, user_id: int) -> Optional[dict]:
        """获取课程详情(含课件、章节).

        Args:
            course_id: 课程ID
            user_id: 用户ID

        Returns:
            课程详情字典
        """
        try:
            course = Course.objects.prefetch_related('chapters__coursewares').get(id=course_id)
            enrollment = CourseEnrollment.objects.get(course=course_id, user=user_id)

            chapters_data = []
            for chapter in course.chapters.all():
                # 获取该用户在当前章节的进度
                chapter_progress = ChapterProgress.objects.filter(
                    enrollment=enrollment,
                    chapter=chapter
                ).first()

                coursewares_data = []
                for courseware in chapter.coursewares.all():
                    coursewares_data.append({
                        'id': courseware.id,
                        'title': courseware.title,
                        'type': courseware.type,
                        'file_url': courseware.file_url,
                        'file_size': courseware.file_size,
                        'duration_minutes': courseware.duration_minutes,
                        'order': courseware.order,
                        'created_at': courseware.created_at,
                    })

                chapters_data.append({
                    'id': chapter.id,
                    'title': chapter.title,
                    'description': chapter.description,
                    'order': chapter.order,
                    'duration_minutes': chapter.duration_minutes,
                    'coursewares': coursewares_data,
                    'created_at': chapter.created_at,
                    # 'is_completed': chapter_progress.is_completed if chapter_progress else False,
                })

            return {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'cover_image': course.cover_image,
                'instructor_id': course.instructor.id if course.instructor else None,
                'instructor_name': course.instructor.name if course.instructor else '',
                'status': course.status,
                'start_date': course.start_date,
                'end_date': course.end_date,
                'duration_hours': course.duration_hours,
                'chapters': chapters_data,
                'created_at': course.created_at,
            }
        except (Course.DoesNotExist, CourseEnrollment.DoesNotExist):
            return None


class AssignmentService:
    """作业服务."""

    @staticmethod
    def get_pending_assignments(instructor_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取待批改作业列表(讲师视角).

        Args:
            instructor_id: 讲师ID
            page: 页码
            page_size: 每页大小

        Returns:
            分页结果字典
        """
        # 获取讲师开设课程的所有待批改作业
        courses = Course.objects.filter(instructor_id=instructor_id)
        assignments = Assignment.objects.filter(course__in=courses)

        submissions = AssignmentSubmission.objects.filter(
            assignment__in=assignments,
            status__in=['submitted', 'grading']
        ).select_related('assignment', 'assignment__course', 'user')

        total = submissions.count()
        items = submissions[(page - 1) * page_size:page * page_size]

        result = []
        for submission in items:
            result.append({
                'id': submission.id,
                'assignment_id': submission.assignment.id,
                'assignment_title': submission.assignment.title,
                'course_id': submission.assignment.course.id,
                'course_title': submission.assignment.course.title,
                'user_id': submission.user.id,
                'user_name': submission.user.name,
                'submitted_at': submission.submitted_at,
            })

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': result
        }

    @staticmethod
    def get_assignment_detail(submission_id: int) -> Optional[AssignmentSubmission]:
        """获取作业详情.

        Args:
            submission_id: 提交ID

        Returns:
            作业提交对象
        """
        try:
            return AssignmentSubmission.objects.select_related(
                'assignment', 'assignment__course', 'user'
            ).get(id=submission_id)
        except AssignmentSubmission.DoesNotExist:
            return None

    @staticmethod
    def grade_assignment(submission_id: int, score: int, feedback: str) -> Optional[AssignmentSubmission]:
        """批改作业.

        Args:
            submission_id: 提交ID
            score: 得分
            feedback: 批改反馈

        Returns:
            更新后的提交对象
        """
        try:
            submission = AssignmentSubmission.objects.get(id=submission_id)
            submission.score = score
            submission.feedback = feedback
            submission.status = 'graded'
            submission.graded_at = timezone.now()
            submission.save()
            return submission
        except AssignmentSubmission.DoesNotExist:
            return None

    @staticmethod
    def get_user_submissions(user_id: int) -> List[AssignmentSubmission]:
        """获取用户作业批改情况.

        Args:
            user_id: 用户ID

        Returns:
            作业提交列表
        """
        submissions = AssignmentSubmission.objects.filter(user_id=user_id).select_related(
            'assignment', 'assignment__course'
        ).order_by('-submitted_at')

        result = []
        for s in submissions:
            result.append({
                'id': s.id,
                'assignment_id': s.assignment.id,
                'assignment_title': s.assignment.title,
                'content': s.content,
                'attachment_url': s.attachment_url,
                'status': s.status,
                'score': s.score,
                'feedback': s.feedback,
                'submitted_at': s.submitted_at,
                'graded_at': s.graded_at,
            })
        return result

    @staticmethod
    def submit_assignment(assignment_id: int, user_id: int, content: str, attachment_url: str = "") -> AssignmentSubmission:
        """提交作业.

        Args:
            assignment_id: 作业ID
            user_id: 用户ID
            content: 提交内容
            attachment_url: 附件URL

        Returns:
            作业提交对象
        """
        # 检查是否已有提交
        existing = AssignmentSubmission.objects.filter(
            assignment_id=assignment_id,
            user_id=user_id
        ).first()

        if existing:
            existing.content = content
            existing.attachment_url = attachment_url
            existing.status = 'submitted'
            existing.submitted_at = timezone.now()
            existing.save()
            return existing

        return AssignmentSubmission.objects.create(
            assignment_id=assignment_id,
            user_id=user_id,
            content=content,
            attachment_url=attachment_url,
            status='submitted'
        )

    @staticmethod
    def resubmit_assignment(submission_id: int, content: str, attachment_url: str = "") -> Optional[AssignmentSubmission]:
        """重新提交作业.

        Args:
            submission_id: 提交ID
            content: 提交内容
            attachment_url: 附件URL

        Returns:
            更新后的提交对象
        """
        try:
            submission = AssignmentSubmission.objects.get(id=submission_id)
            # 只有已批改的作业才能重新提交
            if submission.status == 'graded':
                submission.content = content
                submission.attachment_url = attachment_url
                submission.status = 'submitted'
                submission.score = None
                submission.feedback = ""
                submission.submitted_at = timezone.now()
                submission.graded_at = None
                submission.save()
                return submission
            return None
        except AssignmentSubmission.DoesNotExist:
            return None


class NotificationService:
    """培训通知服务."""

    @staticmethod
    def get_user_notifications(user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取培训通知列表.

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页大小

        Returns:
            分页结果字典
        """
        # 获取用户报名的所有课程的通知
        enrolled_courses = CourseEnrollment.objects.filter(user_id=user_id).values_list('course_id', flat=True)

        notifications = TrainingNotification.objects.filter(
            Q(course_id__in=enrolled_courses) | Q(course_id__isnull=True),
            is_published=True
        ).select_related('course').order_by('-created_at')

        total = notifications.count()
        items = notifications[(page - 1) * page_size:page * page_size]

        result = []
        for n in items:
            result.append({
                'id': n.id,
                'course_id': n.course_id,
                'course_title': n.course.title if n.course else None,
                'title': n.title,
                'content': n.content,
                'priority': n.priority,
                'is_published': n.is_published,
                'published_at': n.published_at,
                'created_at': n.created_at,
            })

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': result
        }


class CourseReviewService:
    """课程评价服务."""

    @staticmethod
    def create_review(enrollment_id: int, rating: int, content: str) -> Optional[CourseReview]:
        """提交课程评价.

        Args:
            enrollment_id: 选课ID
            rating: 评分(1-5)
            content: 评价内容

        Returns:
            评价对象或 None
        """
        try:
            enrollment = CourseEnrollment.objects.get(id=enrollment_id)

            # 检查是否已评价
            existing = CourseReview.objects.filter(enrollment=enrollment).first()
            if existing:
                existing.rating = rating
                existing.content = content
                existing.save()
                return existing

            return CourseReview.objects.create(
                enrollment=enrollment,
                rating=rating,
                content=content
            )
        except CourseEnrollment.DoesNotExist:
            return None


# ==================== 学员问题管理服务 ====================

class QuestionService:
    """问题服务类."""

    @staticmethod
    def create_question(
        author,
        title: str,
        content: str,
        category: str,
        attachments: list,
    ):
        return Question.objects.create(
            author=author,
            title=title,
            content=content,
            category=category,
            attachments=attachments,
        )

    @staticmethod
    def get_question_list(
        user=None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ):
        queryset = Question.objects.all()
        if user:
            queryset = queryset.filter(author=user)
        if category:
            queryset = queryset.filter(category=category)
        if status and status != "all":
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) | models.Q(content__icontains=search)
            )
        total = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        queryset = queryset[start:end]
        return queryset, total

    @staticmethod
    def get_question_detail(question_id: int):
        try:
            return Question.objects.prefetch_related("replies", "replies__author").get(
                id=question_id
            )
        except Question.DoesNotExist:
            return None

    @staticmethod
    def update_question(
        question,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        attachments: Optional[list] = None,
    ):
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
    def update_question_status(question, status: str):
        question.status = status
        question.save()
        return question

    @staticmethod
    def delete_question(question):
        question.delete()


class QuestionReplyService:
    """问题回复服务类."""

    @staticmethod
    def create_reply(question, author, content: str):
        reply = QuestionReply.objects.create(
            question=question,
            author=author,
            content=content,
        )
        if question.status == Question.STATUS_PENDING:
            question.status = Question.STATUS_REPLIED
            question.save()
        return reply
