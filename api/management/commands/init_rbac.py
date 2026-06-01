"""初始化 RBAC 权限数据的管理命令.

用法：
    python manage.py init_rbac

功能：
    1. 创建 4 个默认角色（超管、管理员、审核员、编辑）
    2. 创建系统所有权限 code
    3. 超管角色绑定所有权限
    4. 为历史 role=2 的用户分配超管角色

幂等设计：重复执行不会报错或产生重复数据。
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import LabUser, Permission, Role, RolePermission, UserRole

# 系统所有权限定义
SYSTEM_PERMISSIONS = [
    {"name": "实验室管理", "code": "lab.manage"},
    {"name": "部门管理", "code": "enrollments.manage_department"},
    {"name": "报名审核", "code": "enrollments.audit_application"},
    {"name": "内容编辑", "code": "content.edit"},
    {"name": "新闻管理", "code": "news.manage"},
    {"name": "用户管理", "code": "user.manage"},
    {"name": "系统配置", "code": "system.config"},
    {"name": "数据导出", "code": "data.export"},
]

# 默认角色定义
DEFAULT_ROLES = [
    {"name": "超管", "code": "super_admin", "description": "超级管理员，拥有系统所有权限"},
    {"name": "管理员", "code": "admin", "description": "普通管理员，管理日常运营"},
    {"name": "审核员", "code": "auditor", "description": "报名审核人员，负责审核报名记录"},
    {"name": "内容编辑", "code": "editor", "description": "内容编辑人员，负责新闻和公告维护"},
]

# 角色-权限映射（超管自动拥有所有权限，不在此配置）
ROLE_PERMISSIONS_MAP = {
    "admin": ["enrollments.manage_department", "enrollments.audit_application", "news.manage", "user.manage"],
    "auditor": ["enrollments.audit_application"],
    "editor": ["content.edit", "news.manage"],
}


class Command(BaseCommand):
    help = "初始化 RBAC 角色和权限数据（幂等）"

    def handle(self, *args, **options):
        self.stdout.write("=" * 50)
        self.stdout.write("开始初始化 RBAC 权限数据...")
        self.stdout.write("=" * 50)

        with transaction.atomic():
            self._init_permissions()
            self._init_roles()
            self._init_role_permissions()
            self._assign_super_admin_roles()

        self.stdout.write(self.style.SUCCESS("RBAC 权限数据初始化完成！"))

    def _init_permissions(self):
        """初始化权限表（幂等）."""
        created_count = 0
        for perm in SYSTEM_PERMISSIONS:
            _, created = Permission.objects.get_or_create(
                code=perm["code"],
                defaults={"name": perm["name"]},
            )
            if created:
                created_count += 1
                self.stdout.write(f"  创建权限: {perm['name']} ({perm['code']})")

        if created_count == 0:
            self.stdout.write("  权限表无新增（已全部存在）")

    def _init_roles(self):
        """初始化角色表（幂等）."""
        created_count = 0
        for role in DEFAULT_ROLES:
            _, created = Role.objects.get_or_create(
                code=role["code"],
                defaults={
                    "name": role["name"],
                    "description": role["description"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  创建角色: {role['name']} ({role['code']})")

        if created_count == 0:
            self.stdout.write("  角色表无新增（已全部存在）")

    def _init_role_permissions(self):
        """初始化角色-权限映射（幂等）.

        超管角色自动获得所有权限。
        """
        all_perms = list(Permission.objects.all())
        perm_codes = {p.code: p for p in all_perms}

        super_admin_role = Role.objects.get(code="super_admin")
        sa_count = 0
        for perm in all_perms:
            _, created = RolePermission.objects.get_or_create(
                role=super_admin_role,
                permission=perm,
            )
            if created:
                sa_count += 1
        if sa_count > 0:
            self.stdout.write(f"  超管绑定权限: {sa_count} 条")

        for role_code, perm_codes_list in ROLE_PERMISSIONS_MAP.items():
            try:
                role = Role.objects.get(code=role_code)
            except Role.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  角色 {role_code} 不存在，跳过"))
                continue

            rp_count = 0
            for pc in perm_codes_list:
                perm = perm_codes.get(pc)
                if perm is None:
                    self.stdout.write(self.style.WARNING(f"  权限 {pc} 不存在，跳过"))
                    continue
                _, created = RolePermission.objects.get_or_create(
                    role=role,
                    permission=perm,
                )
                if created:
                    rp_count += 1
            if rp_count > 0:
                self.stdout.write(f"  角色 {role_code} 绑定权限: {rp_count} 条")

        if sa_count == 0:
            for role_code in ROLE_PERMISSIONS_MAP:
                role = Role.objects.get(code=role_code)
                existing = RolePermission.objects.filter(role=role).count()
                if existing > 0:
                    self.stdout.write(f"  角色 {role_code} 已有 {existing} 个权限（无新增）")

    def _assign_super_admin_roles(self):
        """为历史 role=2（超管）的用户分配超管角色.

        幂等设计：已分配过的不会重复分配。
        """
        super_admin_role = Role.objects.get(code="super_admin")
        super_admin_users = LabUser.objects.filter(role=2)

        assigned_count = 0
        for user in super_admin_users:
            _, created = UserRole.objects.get_or_create(
                user=user,
                role=super_admin_role,
            )
            if created:
                assigned_count += 1
                self.stdout.write(f"  为用户 {user.username}({user.account}) 分配超管角色")

        if assigned_count == 0:
            self.stdout.write("  无新增超管角色分配（已全部存在或无 role=2 用户）")
        else:
            self.stdout.write(self.style.SUCCESS(f"  共为 {assigned_count} 个用户分配超管角色"))
