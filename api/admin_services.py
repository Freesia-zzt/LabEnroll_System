"""管理员模块业务逻辑层."""
import logging                         # 导入logging模块，用于记录日志
from typing import Optional            # 从typing导入Optional，用于可选类型注解

from django.utils import timezone      # 从django.utils导入timezone，用于获取当前时间

from .admin_auth import get_role_string  # 从同级目录导入：获取角色名称字符串的函数
from .auth_utils import create_access_token, create_refresh_token  # 从同级目录导入：创建访问Token和刷新Token的函数
from .models import LabUser            # 从同级目录导入：LabUser模型类

logger = logging.getLogger("api.admin")  # 获取名为"api.admin"的日志记录器，用于记录管理员相关日志


class AdminAuthService:                # 定义管理员认证服务类，封装管理员相关的业务逻辑
    """管理员认证服务类."""

    @staticmethod                      # 静态方法装饰器，表示此方法不依赖实例，可直接通过类调用
    def login(                         # 定义登录方法
        username: str,                 # 参数：账号，类型为字符串
        password: str                  # 参数：密码，类型为字符串
    ) -> dict:                         # 返回值类型注解为字典，包含token和用户信息
        """管理员登录.
        
        Args:
            username: 管理员账号
            password: 密码
            
        Returns:
            登录成功返回 token 和用户信息
            
        Raises:
            Exception: 登录失败
        """
        try:                           # try块：尝试查询用户
            user = LabUser.objects.get(account=username)  # 使用Django ORM的get方法，根据account字段查询用户
        except LabUser.DoesNotExist:   # except块：捕获用户不存在的异常
            raise Exception("账号或密码错误")  # 抛出异常，不告诉具体是账号还是密码错误（安全考虑）

        if not user.check_password(password):  # if条件：使用Django的check_password方法验证密码
            raise Exception("账号或密码错误")  # 密码错误，抛出异常

        if user.is_active != 1:        # if条件：检查用户是否激活（is_active为1表示激活）
            raise Exception("账号未激活")  # 账号未激活，抛出异常

        # 检查是否为管理员
        if user.role != 2:             # if条件：检查角色是否为2（2表示管理员）
            raise Exception("需要管理员权限")  # 不是管理员，抛出异常

        token = create_access_token(user)      # 调用auth_utils的函数，创建访问Token
        refresh_token = create_refresh_token(user)  # 调用auth_utils的函数，创建刷新Token

        user.last_login_at = timezone.now()    # 设置用户最后登录时间为当前时间
        user.save(update_fields=["last_login_at"])  # 保存用户，只更新last_login_at字段（优化性能）

        logger.info(f"[管理员登录] 用户 {user.account}({user.username}) 已登录")  # 记录登录日志

        return {                       # 返回字典，包含登录成功后的信息
            "token": token,            # 访问Token
            "user_id": user.id,        # 用户ID
            "username": user.username, # 用户名
            "role": get_role_string(user.role),  # 调用函数将角色代码转为可读字符串
        }

    @staticmethod                      # 静态方法装饰器
    def get_profile(                   # 定义获取用户信息方法
        user: LabUser                  # 参数：用户实例，类型为LabUser模型
    ) -> dict:                         # 返回值类型注解为字典
        """获取管理员信息.
        
        Args:
            user: 用户实例
            
        Returns:
            管理员信息字典
        """
        return {                       # 直接返回字典，包含用户各项信息
            "id": user.id,             # 用户ID
            "username": user.username, # 用户名
            "email": user.email,       # 邮箱
            "phone": user.phone,       # 手机号
            "role": get_role_string(user.role),  # 角色名称
            "date_joined": user.created_at,  # 注册时间（created_at字段）
        }

    @staticmethod                      # 静态方法装饰器
    def change_password(               # 定义修改密码方法
        user: LabUser,                 # 参数：用户实例
        old_password: str,             # 参数：原密码
        new_password: str              # 参数：新密码
    ) -> None:                         # 返回值类型注解为None，表示无返回值
        """修改管理员密码.
        
        Args:
            user: 用户实例
            old_password: 原密码
            new_password: 新密码
            
        Raises:
            Exception: 密码验证失败
        """
        if len(new_password) < 8:      # if条件：检查新密码长度是否小于8位
            raise Exception("新密码长度至少8位")  # 密码太短，抛出异常

        if not user.check_password(old_password):  # if条件：验证原密码是否正确
            raise Exception("原密码错误")  # 原密码错误，抛出异常

        user.set_password(new_password)  # 使用Django的set_password方法设置新密码（自动加密）
        user.save(update_fields=["password"])  # 保存用户，只更新password字段

    @staticmethod                      # 静态方法装饰器
    def logout(token: str, user: LabUser) -> None:  # 定义登出方法，增加user参数
        """管理员登出，将Token加入黑名单.

        Args:
            token: JWT Token字符串
            user: 当前用户实例

        Raises:
            Exception: Token无效或已过期
        """
        from .auth_utils import decode_token, add_token_to_blacklist  # 导入解码和黑名单函数

        payload = decode_token(token)  # 解码Token获取payload
        if payload is None:            # if条件：解码失败返回None
            raise Exception("Token无效或已过期")  # 抛出异常

        jti = payload.get("jti")       # 获取Token的唯一标识
        exp = payload.get("exp")       # 获取Token的过期时间
        token_type = payload.get("token_type", "access")  # 获取Token类型，默认为access

        if jti and exp:                # if条件：确保jti和exp都存在
            add_token_to_blacklist(jti, exp, user, token_type)  # 将Token加入黑名单，传入用户和类型

    @staticmethod                      # 静态方法装饰器
    def forgot_password_send_code(account: str, email: str) -> str:  # 定义发送验证码方法
        """管理员忘记密码-发送验证码.

        Args:
            account: 管理员账号
            email: 注册邮箱

        Returns:
            生成的验证码

        Raises:
            Exception: 用户不存在或邮箱不匹配
        """
        from .models import LabUser     # 导入模型
        from django.utils import timezone  # 导入时区工具
        from datetime import timedelta   # 导入时间差类
        import random                    # 导入随机数模块

        try:                            # try块：查询用户
            user = LabUser.objects.get(account=account)  # 根据账号查询用户
        except LabUser.DoesNotExist:    # except块：用户不存在
            raise Exception("账号不存在")  # 抛出异常

        if user.email != email:         # if条件：检查邮箱是否匹配
            raise Exception("账号与邮箱不匹配")  # 邮箱不匹配，抛出异常

        if user.role != 2:              # if条件：检查是否为管理员
            raise Exception("该账号不是管理员")  # 不是管理员，抛出异常

        # 生成6位数字验证码
        code = f"{random.randint(0, 999999):06d}"  # 生成随机6位数字，不足补0
        user.activation_code = code      # 保存验证码到用户
        user.activation_expire = timezone.now() + timedelta(minutes=10)  # 设置10分钟有效期
        user.save(update_fields=["activation_code", "activation_expire"])  # 保存到数据库

        return code                      # 返回验证码

    @staticmethod                      # 静态方法装饰器
    def forgot_password_reset(account: str, email: str, code: str, new_password: str) -> None:  # 定义重置密码方法
        """管理员忘记密码-重置密码.

        Args:
            account: 管理员账号
            email: 注册邮箱
            code: 验证码
            new_password: 新密码

        Raises:
            Exception: 验证失败或密码不符合要求
        """
        from .models import LabUser     # 导入模型
        from django.utils import timezone  # 导入时区工具

        if len(new_password) < 8:       # if条件：检查密码长度
            raise Exception("新密码长度至少8位")  # 密码太短，抛出异常

        try:                            # try块：查询用户
            user = LabUser.objects.get(account=account, email=email)  # 根据账号和邮箱查询
        except LabUser.DoesNotExist:    # except块：用户不存在
            raise Exception("账号或邮箱错误")  # 抛出异常

        if user.role != 2:              # if条件：检查是否为管理员
            raise Exception("该账号不是管理员")  # 不是管理员，抛出异常

        if user.activation_code != code:  # if条件：检查验证码是否正确
            raise Exception("验证码错误")  # 验证码错误，抛出异常

        if user.activation_expire < timezone.now():  # if条件：检查验证码是否过期
            raise Exception("验证码已过期")  # 验证码过期，抛出异常

        user.set_password(new_password)  # 设置新密码（自动加密）
        user.activation_code = ""        # 清空验证码
        user.activation_expire = None    # 清空过期时间
        user.save(update_fields=["password", "activation_code", "activation_expire"])  # 保存到数据库
