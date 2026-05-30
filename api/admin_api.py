"""管理员模块 API 路由定义."""
from ninja import Router
from ninja.errors import HttpError

from .admin_auth import AdminAuthBearer, admin_response, require_admin
from .admin_schemas import (
    AdminChangePasswordInput,
    AdminChangePasswordSchema,
    AdminLoginInput,
    AdminProfileSchema,
    AdminResponseSchema,
)
from .admin_services import AdminAuthService

# 创建管理员路由
admin_router = Router(tags=["管理员认证"])

# 认证实例
admin_auth = AdminAuthBearer()


def get_auth_bearer() -> AdminAuthBearer:
    """获取认证实例."""
    return admin_auth


@admin_router.post(
    "/login",
    response=AdminResponseSchema,
    summary="管理员登录",
    auth=None,
)
def admin_login(request, data: AdminLoginInput) -> dict:
    """管理员登录接口.
    
    支持账号密码登录，仅管理员角色可登录。
    """
    try:
        result = AdminAuthService.login(
            username=data.username,
            password=data.password,
        )
        return admin_response(code=200, message="success", data=result)
    except Exception as e:
        raise HttpError(400, str(e))


@admin_router.get(
    "/profile",
    response=AdminResponseSchema,
    summary="获取当前管理员信息",
    auth=admin_auth,
)
def admin_profile(request) -> dict:
    """获取当前登录管理员的详细信息."""
    user = request.auth

    # 检查管理员权限
    try:
        require_admin(user)
    except PermissionError as e:
        raise HttpError(403, str(e))

    profile = AdminAuthService.get_profile(user)
    return admin_response(code=200, message="success", data=profile)


@admin_router.post(
    "/change-password",
    response=AdminChangePasswordSchema,
    summary="修改管理员密码",
    auth=admin_auth,
)
def admin_change_password(request, data: AdminChangePasswordInput) -> dict:
    """修改当前管理员密码.
    
    需要提供原密码验证。
    """
    user = request.auth

    # 检查管理员权限
    try:
        require_admin(user)
    except PermissionError as e:
        raise HttpError(403, str(e))

    try:
        AdminAuthService.change_password(
            user=user,
            old_password=data.old_password,
            new_password=data.new_password,
        )
        return AdminChangePasswordSchema().dict()
    except Exception as e:
        raise HttpError(400, str(e))
