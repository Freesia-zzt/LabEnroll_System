"""管理员模块 API 路由定义."""
from ninja import Router              # 从ninja导入Router类，用于创建API路由
from ninja.errors import HttpError    # 从ninja.errors导入HttpError，用于抛出HTTP错误

from .admin_auth import AdminAuthBearer, admin_response, require_admin  # 从同级目录admin_auth模块导入：认证类、响应构造工具、权限检查函数
from .admin_schemas import (          # 从同级目录admin_schemas模块导入各种数据模型（Schema）
    AdminChangePasswordInput,         # 修改密码请求Schema
    AdminChangePasswordSchema,        # 修改密码响应Schema
    AdminForgotPasswordResetInput,    # 忘记密码重置请求Schema
    AdminForgotPasswordSendCodeInput, # 忘记密码发送验证码请求Schema
    AdminLoginInput,                  # 登录请求Schema
    AdminProfileSchema,               # 管理员信息Schema
    AdminResponseSchema,              # 统一响应Schema
)
from .admin_services import AdminAuthService  # 从同级目录admin_services模块导入业务逻辑服务类

admin_router = Router(tags=["管理员认证"])  # 创建路由实例，tags参数用于API文档分组显示

admin_auth = AdminAuthBearer()          # 实例化认证类，用于需要Token认证的接口


def get_auth_bearer() -> AdminAuthBearer:  # 定义函数，返回类型为AdminAuthBearer
    """获取认证实例."""                    # 函数文档字符串
    return admin_auth                     # 返回认证实例


@admin_router.post(                       # 使用POST方法装饰器，定义POST接口
    "/login",                             # URL路径为/login
    response=AdminResponseSchema,         # 响应数据格式使用AdminResponseSchema
    summary="管理员登录",                  # 接口在文档中显示的简短描述
    auth=None,                            # auth=None表示此接口不需要认证
)
def admin_login(                          # 定义登录处理函数
    request,                              # 第一个参数：Django请求对象，自动传入
    data: AdminLoginInput                 # 第二个参数：请求体数据，类型为AdminLoginInput，自动解析校验
) -> dict:                                # 返回值类型注解为字典
    """管理员登录接口."""
    try:                                  # try块：捕获可能发生的异常
        result = AdminAuthService.login(  # 调用业务逻辑层的login方法
            username=data.username,       # 从data中获取username字段传入
            password=data.password,       # 从data中获取password字段传入
        )
        return admin_response(            # 调用admin_response构造统一响应
            code=200,                     # 状态码200表示成功
            message="success",            # 消息为success
            data=result                   # 数据为login返回的结果
        )
    except Exception as e:                # except块：捕获所有异常
        raise HttpError(400, str(e))      # 抛出HttpError，400表示客户端错误，str(e)将异常转为字符串


@admin_router.get(                        # 使用GET方法装饰器，定义GET接口
    "/profile",                           # URL路径为/profile
    response=AdminResponseSchema,         # 响应数据格式使用AdminResponseSchema
    summary="获取当前管理员信息",          # 接口在文档中显示的简短描述
    auth=admin_auth,                      # auth=admin_auth表示此接口需要Token认证
)
def admin_profile(                        # 定义获取信息处理函数
    request                               # 参数：Django请求对象
) -> dict:                                # 返回值类型注解为字典
    """获取当前登录管理员的详细信息."""
    user = request.auth                   # 从request.auth获取当前登录用户对象（由认证类提供）
    try:                                  # try块：捕获权限检查异常
        require_admin(user)               # 调用require_admin检查用户是否为管理员
    except PermissionError as e:          # except块：捕获权限错误
        raise HttpError(403, str(e))      # 抛出403错误，表示无权限访问
    profile = AdminAuthService.get_profile(user)  # 调用业务逻辑层获取用户信息
    return admin_response(                # 构造统一响应
        code=200,
        message="success",
        data=profile                      # 数据为用户信息
    )


@admin_router.post(                       # 使用POST方法装饰器
    "/change-password",                   # URL路径为/change-password
    response=AdminChangePasswordSchema,   # 响应使用AdminChangePasswordSchema
    summary="修改管理员密码",              # 接口描述
    auth=admin_auth,                      # 需要Token认证
)
def admin_change_password(                # 定义修改密码处理函数
    request,                              # 参数：Django请求对象
    data: AdminChangePasswordInput        # 参数：请求体，类型为AdminChangePasswordInput
) -> dict:                                # 返回值类型注解为字典
    """修改当前管理员密码."""
    user = request.auth                   # 获取当前登录用户
    try:                                  # try块：权限检查
        require_admin(user)               # 检查是否为管理员
    except PermissionError as e:          # 捕获权限错误
        raise HttpError(403, str(e))      # 抛出403错误
    try:                                  # try块：业务处理
        AdminAuthService.change_password( # 调用业务逻辑层修改密码
            user=user,                    # 传入用户对象
            old_password=data.old_password,  # 传入旧密码
            new_password=data.new_password,  # 传入新密码
        )
        return AdminChangePasswordSchema().dict()  # 创建Schema实例并转为字典返回
    except Exception as e:                # 捕获所有异常
        raise HttpError(400, str(e))      # 抛出400错误


@admin_router.post(                       # 使用POST方法装饰器
    "/logout",                            # URL路径为/logout
    response=AdminResponseSchema,         # 响应使用AdminResponseSchema
    summary="管理员登出",                  # 接口描述
    auth=admin_auth,                      # 需要Token认证
)
def admin_logout(                         # 定义登出处理函数
    request                               # 参数：Django请求对象
) -> dict:                                # 返回值类型注解为字典
    """管理员登出，将当前Token加入黑名单."""
    user = request.auth                   # 获取当前登录用户
    try:                                  # try块：权限检查
        require_admin(user)               # 检查是否为管理员
    except PermissionError as e:          # 捕获权限错误
        raise HttpError(403, str(e))      # 抛出403错误
    try:                                  # try块：业务处理
        # 从请求头中获取Token
        auth_header = request.headers.get("Authorization", "")  # 获取Authorization头
        if auth_header.startswith("Bearer "):  # if条件：检查是否以Bearer开头
            token = auth_header[7:]           # 提取Token（去掉"Bearer "前缀）
            AdminAuthService.logout(token, user)  # 调用业务逻辑层登出方法，传入用户
        return admin_response(               # 构造统一响应
            code=200,
            message="登出成功",
            data=None
        )
    except Exception as e:                  # 捕获所有异常
        raise HttpError(400, str(e))        # 抛出400错误


@admin_router.post(                       # 使用POST方法装饰器
    "/forgot-password/send-code",         # URL路径为/forgot-password/send-code
    response=AdminResponseSchema,         # 响应使用AdminResponseSchema
    summary="管理员忘记密码-发送验证码",   # 接口描述
    auth=None,                            # 不需要认证
)
def admin_forgot_password_send_code(      # 定义发送验证码处理函数
    request,                              # 参数：Django请求对象
    data: AdminForgotPasswordSendCodeInput  # 参数：请求体
) -> dict:                                # 返回值类型注解为字典
    """管理员忘记密码-发送验证码到邮箱."""
    try:                                  # try块：业务处理
        # 生成验证码
        code = AdminAuthService.forgot_password_send_code(
            account=data.account,         # 传入账号
            email=data.email              # 传入邮箱
        )

        # 发送邮件
        from .email_utils import send_forgot_password_code_email  # 导入邮件发送函数
        success = send_forgot_password_code_email(
            to_email=data.email,          # 收件人邮箱
            code=code,                    # 验证码
            username=data.account         # 用户名（显示用）
        )

        if success:                       # if条件：邮件发送成功
            return admin_response(        # 构造成功响应
                code=200,
                message="验证码已发送到邮箱",
                data=None
            )
        else:                             # else块：邮件发送失败
            # 邮件发送失败，但验证码已生成，返回验证码（仅开发环境）
            return admin_response(        # 构造响应，包含验证码
                code=200,
                message=f"邮件发送失败，验证码：{code}（仅开发环境显示）",
                data={"code": code}
            )
    except Exception as e:                # 捕获所有异常
        raise HttpError(400, str(e))      # 抛出400错误


@admin_router.post(                       # 使用POST方法装饰器
    "/forgot-password/reset",             # URL路径为/forgot-password/reset
    response=AdminResponseSchema,         # 响应使用AdminResponseSchema
    summary="管理员忘记密码-重置密码",     # 接口描述
    auth=None,                            # 不需要认证
)
def admin_forgot_password_reset(          # 定义重置密码处理函数
    request,                              # 参数：Django请求对象
    data: AdminForgotPasswordResetInput   # 参数：请求体
) -> dict:                                # 返回值类型注解为字典
    """管理员忘记密码-使用验证码重置密码."""
    try:                                  # try块：业务处理
        AdminAuthService.forgot_password_reset(
            account=data.account,         # 传入账号
            email=data.email,             # 传入邮箱
            code=data.code,               # 传入验证码
            new_password=data.new_password  # 传入新密码
        )
        return admin_response(            # 构造成功响应
            code=200,
            message="密码重置成功",
            data=None
        )
    except Exception as e:                # 捕获所有异常
        raise HttpError(400, str(e))      # 抛出400错误
