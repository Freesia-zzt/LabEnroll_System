"""业务逻辑层."""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Optional

from django.conf import settings
from django.db.models import Q, QuerySet
from django.utils import timezone
from ninja.errors import HttpError

from api.auth_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    is_token_blacklisted,
)
from api.models import LabUser, Question, QuestionReply, TokenBlacklist, User

logger = logging.getLogger("api.services")


class AuthService:
    """认证服务类."""

    @staticmethod
    def login(account: str, password: str, remember_me: bool = False) -> dict:
        """用户登录."""
        try:
            user = LabUser.objects.get(account=account)
        except LabUser.DoesNotExist:
            raise HttpError(401, "账号或密码错误")

        if not user.check_password(password):
            raise HttpError(401, "账号或密码错误")

        if user.is_active != 1:
            raise HttpError(403, "账号未激活，请先激活")

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
            raise HttpError(404, "用户不存在")

        if user.is_active == 1:
            raise HttpError(400, "账号已激活，无需重复激活")

        if user.activation_expire and user.activation_expire > timezone.now():
            remaining = (user.activation_expire - timezone.now()).total_seconds()
            if remaining > 29 * 60:
                raise HttpError(429, "发送太频繁，请1分钟后再试")

        code = f"{random.randint(0, 999999):06d}"
        user.activation_code = code
        user.activation_expire = timezone.now() + timedelta(minutes=30)
        user.save(update_fields=["activation_code", "activation_expire"])

        logger.info(f"[激活码] 用户 {user.account}({user.username}) 的激活码: {code}")
        if user.email:
            logger.info(f"[邮件] 发送激活码 {code} 到 {user.email}")

    @staticmethod
    def verify_activation_code(account: str, activation_code: str) -> None:
        """验证激活码."""
        try:
            user = LabUser.objects.get(account=account)
        except LabUser.DoesNotExist:
            raise HttpError(404, "用户不存在")

        if user.is_active == 1:
            raise HttpError(400, "账号已激活")

        if user.activation_code != activation_code:
            raise HttpError(400, "激活码错误")

        if not user.activation_expire or user.activation_expire < timezone.now():
            raise HttpError(400, "激活码已过期，请重新发送")

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
            raise HttpError(400, "无效的 Refresh Token")

        if payload.get("token_type") != "refresh":
            raise HttpError(400, "请提供 Refresh Token")

        jti = payload.get("jti", "")
        if is_token_blacklisted(jti):
            return

        exp_value = payload.get("exp")
        if isinstance(exp_value, str):
            expires_at = datetime.fromisoformat(exp_value)
        else:
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
                raise HttpError(400, "旧密码错误")
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
            raise HttpError(400, "两次密码不一致")

        if not user.check_password(old_password):
            raise HttpError(400, "旧密码错误")

        user.set_password(new_password)
        user.save(update_fields=["password"])
        logger.info(f"[修改密码] 用户 {user.account} 已修改密码")

    @staticmethod
    def forgot_password_send_code(account: str, email: str) -> None:
        """忘记密码-发送验证码."""
        try:
            user = LabUser.objects.get(account=account)
        except LabUser.DoesNotExist:
            raise HttpError(404, "用户不存在")

        if user.email != email:
            raise HttpError(400, "账号与邮箱不匹配")

        code = f"{random.randint(0, 999999):06d}"
        user.activation_code = code
        user.activation_expire = timezone.now() + timedelta(minutes=10)
        user.save(update_fields=["activation_code", "activation_expire"])

        logger.info(f"[找回密码] 用户 {user.account} 的验证码: {code}")
        logger.info(f"[邮件] 发送找回密码验证码 {code} 到 {email}")

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
            raise HttpError(400, "两次密码不一致")

        try:
            user = LabUser.objects.get(account=account, email=email)
        except LabUser.DoesNotExist:
            raise HttpError(404, "用户不存在")

        if user.activation_code != code:
            raise HttpError(400, "验证码错误")

        if not user.activation_expire or user.activation_expire < timezone.now():
            raise HttpError(400, "验证码已过期")

        user.set_password(new_password)
        user.activation_code = None
        user.activation_expire = None
        user.save(update_fields=["password", "activation_code", "activation_expire"])
        logger.info(f"[重置密码] 用户 {user.account} 已重置密码")

    @staticmethod
    def refresh_token(refresh_token_str: str) -> dict:
        """刷新 Access Token."""
        payload = decode_token(refresh_token_str)
        if not payload:
            raise HttpError(401, "Refresh Token 无效或已过期")

        if payload.get("token_type") != "refresh":
            raise HttpError(400, "请提供 Refresh Token")

        jti = payload.get("jti", "")
        if is_token_blacklisted(jti):
            raise HttpError(401, "Refresh Token 已被吊销")

        try:
            user = LabUser.objects.get(id=payload["user_id"])
        except LabUser.DoesNotExist:
            raise HttpError(401, "用户不存在")

        if user.is_active != 1:
            raise HttpError(403, "账号未激活")

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
        """创建新问题."""
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
        """获取问题列表."""
        queryset = Question.objects.all()

        if user:
            queryset = queryset.filter(author=user)
        if category:
            queryset = queryset.filter(category=category)
        if status and status != "all":
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        total = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        queryset = queryset[start:end]

        return queryset, total

    @staticmethod
    def get_question_detail(question_id: int) -> Optional[Question]:
        """获取问题详情."""
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
        """更新问题."""
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
        """更新问题状态."""
        question.status = status
        question.save()
        return question

    @staticmethod
    def delete_question(question: Question) -> None:
        """删除问题."""
        question.delete()


class QuestionReplyService:
    """问题回复服务类."""

    @staticmethod
    def create_reply(
        question: Question,
        author: User,
        content: str,
    ) -> QuestionReply:
        """创建问题回复."""
        reply = QuestionReply.objects.create(
            question=question,
            author=author,
            content=content,
        )

        if question.status == Question.STATUS_PENDING:
            question.status = Question.STATUS_REPLIED
            question.save()

        return reply
