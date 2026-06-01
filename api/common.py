from ninja.responses import Response
from ninja import Schema
from typing import Any, Optional

# ========== 错误码定义 ==========
class ErrorCode:
    # 通用
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

    # 业务错误码
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


# ========== 统一响应 Schema ==========
class ApiResponse(Schema):
    code: int
    message: str
    data: Any = None


def success_response(data: Any = None, message: str = None) -> dict:
    """统一成功响应"""
    return {
        "code": ErrorCode.SUCCESS,
        "message": message or ErrorCode.MSG[ErrorCode.SUCCESS],
        "data": data or {},
    }


def error_response(code: int, message: str = None, data: Any = None) -> dict:
    """统一错误响应"""
    return {
        "code": code,
        "message": message or ErrorCode.MSG.get(code, "未知错误"),
        "data": data or {},
    }