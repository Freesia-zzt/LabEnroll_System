"""统一响应模块.

提供标准化的 API 响应格式。
"""

from typing import Any, Optional


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
