"""依赖注入模块 — 权限校验、通用依赖.

用法示例：

    # 使用 @permission_required 装饰器
    from api.dependencies import permission_required

    @router.post("/audit")
    @permission_required("app.audit")
    def audit_endpoint(request: HttpRequest, payload: SomeIn) -> dict:
        ...

    # 直接在函数内部调用 get_current_admin_user
    @router.get("/stats")
    def stats_endpoint(request: HttpRequest) -> dict:
        admin = get_current_admin_user(request)
        ...
"""

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from django.http import HttpRequest
from ninja.errors import HttpError

from api.auth_utils import decode_token
from api.models import LabUser

logger = logging.getLogger("api.dependencies")

F = TypeVar("F", bound=Callable[..., Any])

# 超管角色编码 — 拥有所有权限
SUPER_ADMIN_ROLE_CODE = "super_admin"

# 角色编码与 role 字段值的映射
ROLE_CODE_MAP: dict[int, str] = {
    2: SUPER_ADMIN_ROLE_CODE,
    3: "admin",
    4: "auditor",
    5: "editor",
}


def get_current_admin_user(request: HttpRequest) -> LabUser:
    """从请求中获取当前管理员用户.

    解析 JWT Token 获取用户，校验是否为已激活的管理人员（role >= 2）。

    Returns:
        通过校验的 LabUser 实例

    Raises:
        HttpError 401: 未登录或 Token 无效
        HttpError 403: 非管理人员
    """
    token_header = request.headers.get("Authorization", "")
    if not token_header.startswith("Bearer "):
        raise HttpError(401, "未登录")

    token = token_header.removeprefix("Bearer ")
    payload = decode_token(token)
    if payload is None:
        raise HttpError(401, "未登录")

    if payload.get("token_type") != "access":
        raise HttpError(401, "未登录")

    try:
        user = LabUser.objects.get(id=payload["user_id"])
    except LabUser.DoesNotExist:
        raise HttpError(401, "未登录") from None

    if user.is_active != 1:
        raise HttpError(403, "非管理员")

    if not user.is_staff:
        raise HttpError(403, "非管理员")

    return user


def _user_has_permission(user: LabUser, perm_code: str) -> bool:
    """检查用户是否拥有指定权限.

    RBAC 校验逻辑：
    1. 超管（role=2）直接放行，拥有所有权限。
    2. 其他角色通过 UserRole -> Role -> RolePermission -> Permission 链查询。

    Args:
        user: 用户实例
        perm_code: 权限标识（如 "lab.manage", "app.audit"）

    Returns:
        是否拥有权限
    """
    if user.role == 2:
        return True

    from api.models import UserRole

    return UserRole.objects.filter(
        user=user,
        role__role_permissions__permission__code=perm_code,
    ).exists()


def _get_user_permissions(user: LabUser) -> set[str]:
    """获取用户所有权限 code 集合.

    Args:
        user: 用户实例

    Returns:
        权限 code 集合
    """
    if user.role == 2:
        from api.models import Permission
        return set(Permission.objects.values_list("code", flat=True))

    from api.models import UserRole

    codes = UserRole.objects.filter(user=user).values(
        "role__role_permissions__permission__code"
    ).distinct()
    return {c["role__role_permissions__permission__code"] for c in codes if c["role__role_permissions__permission__code"]}


def permission_required(perm_code: str | None = None) -> Callable[[F], F]:
    """权限校验装饰器.

    用于 django-ninja Router 视图函数，校验当前用户是否为管理员，
    并进一步校验指定权限（如提供权限标识）。

    - `@permission_required()` — 仅校验管理员身份
    - `@permission_required("lab.manage")` — 校验管理员 + 指定权限

    Args:
        perm_code: 权限标识（如 "app.audit"），为 None 时仅校验管理员身份

    Returns:
        装饰器函数

    Raises:
        HttpError 401: 未登录
        HttpError 403: 非管理员或权限不足
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
            admin_user = get_current_admin_user(request)

            if perm_code is not None and not _user_has_permission(admin_user, perm_code):
                raise HttpError(403, "权限不足")

            return func(request, *args, **kwargs)

        return wrapper  # type: ignore[return-value]
    return decorator


def require_permission(perm_code: str) -> Callable[[HttpRequest], None]:
    """权限校验高阶依赖函数（兼容旧版调用方式）.

    推荐使用 @permission_required 装饰器替代。

    Args:
        perm_code: 权限标识（如 "app.audit"）

    Returns:
        校验函数
    """
    def _check_permission(request: HttpRequest) -> None:
        admin_user = get_current_admin_user(request)

        if not _user_has_permission(admin_user, perm_code):
            raise HttpError(403, "权限不足")

    return _check_permission


def check_admin_permission(request: HttpRequest) -> LabUser:
    """校验当前用户是否为管理员（兼容旧版调用方式）.

    推荐使用 @permission_required() 装饰器替代。

    Returns:
        通过验证的 LabUser 实例
    """
    return get_current_admin_user(request)
