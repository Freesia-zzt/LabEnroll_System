"""统一响应模块.

提供标准化的 API 响应格式。
"""

from typing import Any, Optional


class ErrorCode:
    """错误码定义."""

    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

    NOTICE_NOT_EXIST = 3001
    CONFIG_KEY_INVALID = 3002

    MSG = {
        SUCCESS: "成功",
        BAD_REQUEST: "请求参数错误",
        UNAUTHORIZED: "未认证",
        FORBIDDEN: "无权限",
        NOT_FOUND: "资源不存在",
        INTERNAL_ERROR: "服务器内部错误",
        NOTICE_NOT_EXIST: "公告不存在",
        CONFIG_KEY_INVALID: "配置键无效",
    }


def api_response(
    code: int = 200,
    message: str = "success",
    data: Optional[Any] = None,
) -> dict[str, Any]:
    """构建统一响应格式.

    Args:
        code: 状态码，默认 200
        message: 响应消息，默认 "success"
        data: 响应数据，默认 None

    Returns:
        标准化的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
    }
