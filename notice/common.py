"""招新公告模块 - 响应封装与错误码扩展."""

from typing import Any

from ninja import Schema

from api.common import ErrorCode


class NoticeErrorCode:
    """公告模块扩展错误码（不影响 api.common.ErrorCode）."""

    NOTICE_CREATE_FAILED = 3002
    NOTICE_UPDATE_FAILED = 3003
    NOTICE_DELETE_FAILED = 3004
    CONFIG_UPDATE_FAILED = 3102
    ENROLLMENT_CLOSED = 3103
    PAGINATION_INVALID = 3201

    MSG: dict[int, str] = {
        NOTICE_CREATE_FAILED: "公告创建失败",
        NOTICE_UPDATE_FAILED: "公告更新失败",
        NOTICE_DELETE_FAILED: "公告删除失败",
        CONFIG_UPDATE_FAILED: "系统配置更新失败",
        ENROLLMENT_CLOSED: "报名已关闭",
        PAGINATION_INVALID: "分页参数无效",
    }

    @classmethod
    def get_msg(cls, code: int) -> str:
        return cls.MSG.get(code, ErrorCode.MSG.get(code, "未知错误"))


class NoticeApiResponseSchema(Schema):
    """公告模块统一 API 响应 Schema."""

    code: int = ErrorCode.SUCCESS
    msg: str = ErrorCode.MSG[ErrorCode.SUCCESS]
    data: Any = None


def success_response(
    data: Any = None,
    msg: str | None = None,
    code: int = ErrorCode.SUCCESS,
) -> dict[str, Any]:
    """构建统一成功响应.

    Args:
        data: 响应数据
        msg: 自定义消息，不传则使用默认消息
        code: 业务状态码

    Returns:
        {"code": int, "msg": str, "data": Any}
    """
    return {
        "code": code,
        "msg": msg or NoticeErrorCode.get_msg(code),
        "data": data or {},
    }


def error_response(
    code: int,
    msg: str | None = None,
    data: Any = None,
) -> dict[str, Any]:
    """构建统一错误响应.

    Args:
        code: 错误码
        msg: 自定义错误消息
        data: 附加错误数据

    Returns:
        {"code": int, "msg": str, "data": Any}
    """
    return {
        "code": code,
        "msg": msg or NoticeErrorCode.get_msg(code),
        "data": data or {},
    }
