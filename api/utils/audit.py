"""审计日志工具模块.

提供 @audit_log 装饰器，自动记录管理员的操作日志。
日志写入独立于主事务，不会影响业务操作。
"""

import functools
import json
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from django.http import HttpRequest

from api.models import AuditLog, LabUser

logger = logging.getLogger("api.audit")

F = TypeVar("F", bound=Callable[..., Any])


def get_client_ip(request: HttpRequest) -> str:
    """从请求中提取客户端 IP 地址.

    优先取 X-Forwarded-For 头部（反向代理场景），
    回退到 REMOTE_ADDR。

    Args:
        request: HTTP 请求对象

    Returns:
        IP 地址字符串
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "127.0.0.1")


def compute_diff(old_data: dict[str, Any] | None, new_data: dict[str, Any] | None) -> dict[str, dict[str, Any]] | None:
    """计算两个数据字典之间的差异.

    用于 UPDATE 操作，记录修改前和修改后的字段值。

    Args:
        old_data: 修改前的数据字典
        new_data: 修改后的数据字典

    Returns:
        差异字典，格式 {field_name: {"old": old_value, "new": new_value}}
    """
    if old_data is None and new_data is None:
        return None

    if old_data is None:
        return {k: {"old": None, "new": v} for k, v in (new_data or {}).items()}

    if new_data is None:
        return {k: {"old": v, "new": None} for k, v in old_data.items()}

    diff = {}
    all_keys = set(old_data.keys()) | set(new_data.keys())
    for key in all_keys:
        old_val = old_data.get(key)
        new_val = new_data.get(key)
        try:
            if json.dumps(old_val, default=str, sort_keys=True) != json.dumps(new_val, default=str, sort_keys=True):
                diff[key] = {"old": old_val, "new": new_val}
        except (TypeError, ValueError):
            if old_val != new_val:
                diff[key] = {"old": str(old_val), "new": str(new_val)}

    return diff if diff else None


def audit_log(
    module: str,
    action: str,
    target_type: str | None = None,
    get_target_id: Callable[..., str | None] | None = None,
    get_old_data: Callable[..., dict[str, Any] | None] | None = None,
) -> Callable[[F], F]:
    """审计日志装饰器.

    自动在接口执行成功后写入 AuditLog 表。
    通过 transaction.on_commit 确保日志写入不影响主事务。

    Args:
        module: 操作模块名称（如 "部门管理"）
        action: 操作类型（AuditLog.ActionChoices 枚举值）
        target_type: 被操作对象模型名（可选，也可在装饰器内自动设置）
        get_target_id: 从函数参数中提取 target_id 的回调函数
        get_old_data: 获取修改前数据的回调函数（用于 UPDATE 操作计算 diff）

    Returns:
        装饰器函数

    Example:
        @router.delete("/{department_id}")
        @audit_log(module="部门管理", action=AuditLog.ActionChoices.DELETE, target_type="Department")
        def delete_department(request, department_id):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
            result = func(request, *args, **kwargs)

            try:
                from django.db import transaction

                target_id = get_target_id(**kwargs) if get_target_id else kwargs.get("department_id") or kwargs.get("id")
                old_data = get_old_data(**kwargs) if get_old_data else None
                new_data = None

                if isinstance(result, dict) and action == AuditLog.ActionChoices.UPDATE:
                    new_data = result.get("data")

                details = None
                if old_data is not None:
                    diff = compute_diff(old_data, new_data)
                    if diff:
                        details = diff

                user = _extract_user(request)

                def _write_log():
                    try:
                        AuditLog.objects.create(
                            user=user,
                            action=action,
                            module=module,
                            target_id=str(target_id) if target_id else None,
                            target_type=target_type,
                            ip_address=get_client_ip(request),
                            details=details,
                        )
                    except Exception as e:
                        logger.warning(f"审计日志写入失败（不阻断主流程）: {e}")

                transaction.on_commit(_write_log)

            except Exception as e:
                logger.warning(f"审计日志处理异常（不阻断主流程）: {e}")

            return result

        return wrapper  # type: ignore[return-value]
    return decorator


def _extract_user(request: HttpRequest) -> LabUser | None:
    """从请求中提取当前用户.

    优先从 request.auth 获取（适用于配置了 auth= 的 Router），
    回退到解析 Authorization 头手动获取。

    Args:
        request: HTTP 请求对象

    Returns:
        LabUser 实例，无法获取时返回 None
    """
    try:
        if hasattr(request, "auth") and request.auth:
            return request.auth
    except Exception:
        pass

    try:
        from api.dependencies import get_current_admin_user
        return get_current_admin_user(request)
    except Exception:
        return None
