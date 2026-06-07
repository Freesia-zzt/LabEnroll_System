"""JWT 认证工具模块."""

import logging                         # 导入logging模块，用于记录日志
from datetime import timedelta         # 从datetime导入timedelta，用于时间计算
from typing import Any                 # 从typing导入Any，表示任意类型

import jwt                             # 导入PyJWT库，用于JWT Token的生成和验证
from django.conf import settings       # 从django.conf导入settings，用于读取Django配置
from django.utils import timezone      # 从django.utils导入timezone，用于获取当前时间
from ninja.security import HttpBearer  # 从ninja.security导入HttpBearer，Token认证基类

from api.models import LabUser, TokenBlacklist  # 从api.models导入LabUser模型和TokenBlacklist模型

logger = logging.getLogger("api.auth")  # 获取名为"api.auth"的日志记录器


def api_response(                      # 定义统一API响应构造函数
    code: int = 200,                   # 参数：状态码，默认200
    msg: str = "操作成功",              # 参数：消息，默认"操作成功"
    data: Any = None                   # 参数：数据，默认None
) -> dict:                             # 返回值类型为字典
    """统一 API 响应格式. {"code": int, "msg": str, "data": object|null}"""
    return {"code": code, "msg": msg, "data": data}  # 返回构造好的字典


def create_access_token(               # 定义创建访问Token的函数
    user: LabUser,                     # 参数：用户实例
    remember_me: bool = False          # 参数：是否记住我，默认False
) -> str:                              # 返回值类型为字符串（Token）
    """生成 Access Token.

    Args:
        user: 用户实例
        remember_me: 是否记住我（延长有效期到7天）

    Returns:
        JWT access token 字符串
    """
    expire_hours = (                   # 计算过期小时数
        settings.JWT_REMEMBER_ME_EXPIRE_DAYS * 24  # 如果记住我，使用配置的天数转小时
        if remember_me                  # 条件判断
        else settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS  # 否则使用默认小时数
    )
    now = timezone.now()               # 获取当前时间
    payload = {                        # 构造Token载荷（Payload）字典
        "user_id": user.id,            # 用户ID
        "role": user.role,             # 用户角色
        "account": user.account,       # 用户账号
        "token_type": "access",        # Token类型为access（访问Token）
        "jti": f"acc_{user.id}_{int(now.timestamp())}",  # 唯一标识，格式：acc_用户ID_时间戳
        "iat": int(now.timestamp()),   # 签发时间（Issued At）
        "exp": int((now + timedelta(hours=expire_hours)).timestamp()),  # 过期时间（Expiration）
    }
    token = jwt.encode(                # 使用PyJWT编码生成Token
        payload,                       # 载荷数据
        settings.JWT_SECRET,           # 密钥（从Django配置读取）
        algorithm=settings.JWT_ALGORITHM,  # 加密算法（从Django配置读取）
    )
    return token                       # 返回生成的Token字符串


def create_refresh_token(              # 定义创建刷新Token的函数
    user: LabUser                      # 参数：用户实例
) -> str:                              # 返回值类型为字符串
    """生成 Refresh Token.

    Args:
        user: 用户实例

    Returns:
        JWT refresh token 字符串（有效期7天）
    """
    now = timezone.now()               # 获取当前时间
    payload = {                        # 构造载荷
        "user_id": user.id,            # 用户ID
        "token_type": "refresh",       # Token类型为refresh（刷新Token）
        "jti": f"ref_{user.id}_{int(now.timestamp())}",  # 唯一标识，格式：ref_用户ID_时间戳
        "iat": int(now.timestamp()),   # 签发时间
        "exp": int((now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),  # 过期时间
    }
    token = jwt.encode(                # 编码生成Token
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token                       # 返回Token


def decode_token(                      # 定义解码Token的函数
    token: str                         # 参数：Token字符串
) -> dict | None:                      # 返回值类型为字典或None
    """解码并验证 JWT Token.

    Args:
        token: JWT token 字符串

    Returns:
        解码后的 payload 字典，无效返回 None
    """
    try:                               # try块：尝试解码
        payload = jwt.decode(          # 使用PyJWT解码
            token,                     # Token字符串
            settings.JWT_SECRET,       # 密钥
            algorithms=[settings.JWT_ALGORITHM],  # 算法列表（注意是列表）
        )
        return payload                 # 返回解码后的载荷字典
    except jwt.ExpiredSignatureError:  # except块：捕获Token过期异常
        logger.warning("Token 已过期")  # 记录警告日志
        return None                    # 返回None表示解码失败
    except jwt.InvalidTokenError as e:  # except块：捕获Token无效异常
        logger.warning(f"无效 Token: {e}")  # 记录警告日志，包含错误信息
        return None                    # 返回None


def is_token_blacklisted(              # 定义检查Token是否在黑名单的函数
    jti: str                           # 参数：Token的唯一标识（jti）
) -> bool:                             # 返回值类型为布尔值
    """检查 Token 是否在黑名单中.

    Args:
        jti: Token 的唯一标识

    Returns:
        是否在黑名单中
    """
    return TokenBlacklist.objects.filter(jti=jti).exists()  # 使用Django ORM查询是否存在，返回True/False


def add_token_to_blacklist(
    jti: str, 
    exp: int, 
    user: LabUser, 
    token_type: str = "access"
) -> None:  # 定义添加Token到黑名单的函数，增加user和token_type参数
    """将 Token 加入黑名单.

    Args:
        jti: Token 的唯一标识
        exp: Token 的过期时间戳
        user: 所属用户实例
        token_type: Token类型，默认为access
    """
    from datetime import datetime  # 导入datetime类
    expires_at = datetime.fromtimestamp(exp)  # 将时间戳转为datetime对象
    TokenBlacklist.objects.get_or_create(  # 使用get_or_create避免重复添加
        jti=jti,  # 唯一标识
        defaults={
            "expires_at": expires_at,  # 过期时间
            "user": user,  # 所属用户
            "token_type": token_type,  # Token类型
        }
    )


class AuthBearer(HttpBearer):          # 定义认证类，继承HttpBearer基类
    """JWT Bearer 认证类（django-ninja 认证后端）."""

    def authenticate(                  # 重写authenticate方法
        self,                          # self表示实例
        request: Any,                  # 参数：请求对象
        token: str                     # 参数：从请求头提取的Token
    ) -> LabUser | None:               # 返回值类型为LabUser或None
        """验证 Bearer Token.

        Args:
            request: 请求对象
            token: Authorization header 中的 token 字符串

        Returns:
            认证通过返回 LabUser 实例，否则返回 None
        """
        payload = decode_token(token)  # 调用decode_token解码Token
        if payload is None:            # if条件：解码失败
            return None                # 返回None表示认证失败

        if payload.get("token_type") != "access":  # if条件：检查Token类型不是access
            logger.warning("非 Access Token 用于认证")  # 记录警告
            return None                # 认证失败

        if is_token_blacklisted(payload.get("jti", "")):  # if条件：检查Token是否在黑名单
            logger.warning("Token 已被加入黑名单")  # 记录警告
            return None                # 认证失败

        try:                           # try块：尝试查询用户
            user = LabUser.objects.get(id=payload["user_id"])  # 根据user_id查询用户
        except LabUser.DoesNotExist:   # except块：捕获用户不存在异常
            logger.warning(f"用户不存在: {payload.get('user_id')}")  # 记录警告
            return None                # 认证失败

        if user.is_active != 1:        # if条件：检查用户未激活
            logger.warning(f"用户未激活: {user.account}")  # 记录警告
            return None                # 认证失败

        return user                    # 所有检查通过，返回用户对象


auth_bearer = AuthBearer()             # 创建AuthBearer实例，供其他模块使用


class IsAdmin:                         # 定义管理员权限检查类
    """管理员权限验证类.

    用于需要管理员角色的接口：检查用户已认证且 role == 2
    """

    def __call__(                     # 定义__call__方法，使实例可像函数一样调用
        self,                          # self表示实例
        request: Any                   # 参数：请求对象
    ) -> bool:                         # 返回值类型为布尔值
        if not hasattr(request, "auth") or not request.auth:  # if条件：检查request没有auth属性或auth为None
            return False               # 返回False表示无权限
        user: LabUser = request.auth   # 获取当前用户，类型注解为LabUser
        return user.role == 2          # 返回角色是否等于2（管理员）
