"""管理员模块业务逻辑层."""
import logging
from typing import Optional

from django.utils import timezone

from .admin_auth import get_role_string
from .auth_utils import create_access_token, create_refresh_token
from .models import LabUser

logger = logging.getLogger("api.admin")


class AdminAuthService:
    """管理员认证服务类."""

    @staticmethod
    def login(username: str, password: str) -> dict:
        """管理员登录.
        
        Args:
            username: 管理员账号
            password: 密码
            
        Returns:
            登录成功返回 token 和用户信息
            
        Raises:
            Exception: 登录失败
        """
        try:
            user = LabUser.objects.get(account=username)
        except LabUser.DoesNotExist:
            raise Exception("账号或密码错误")

        if not user.check_password(password):
            raise Exception("账号或密码错误")

        if user.is_active != 1:
            raise Exception("账号未激活")

        # 检查是否为管理员
        if user.role != 2:
            raise Exception("需要管理员权限")

        token = create_access_token(user)
        refresh_token = create_refresh_token(user)

        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at"])

        logger.info(f"[管理员登录] 用户 {user.account}({user.username}) 已登录")

        return {
            "token": token,
            "user_id": user.id,
            "username": user.username,
            "role": get_role_string(user.role),
        }

    @staticmethod
    def get_profile(user: LabUser) -> dict:
        """获取管理员信息.
        
        Args:
            user: 用户实例
            
        Returns:
            管理员信息字典
        """
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "role": get_role_string(user.role),
            "date_joined": user.created_at,
        }

    @staticmethod
    def change_password(user: LabUser, old_password: str, new_password: str) -> None:
        """修改管理员密码.
        
        Args:
            user: 用户实例
            old_password: 原密码
            new_password: 新密码
            
        Raises:
            Exception: 密码验证失败
        """
        if len(new_password) < 8:
            raise Exception("新密码长度至少8位")

        if not user.check_password(old_password):
            raise Exception("原密码错误")

        user.set_password(new_password)
        user.save(update_fields=["password"])

        logger.info(f"[管理员改密] 用户 {user.account} 已修改密码")
