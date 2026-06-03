#!/usr/bin/env python
"""修复数据库并创建 Admin Token 的脚本.

用法:
    python fix_db_and_create_token.py

或者直接复制脚本内容到 Django shell 中执行:
    python manage.py shell
    # 然后粘贴脚本内容
"""

import os
import sys
import secrets
import sqlite3

# 设置输出编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 确保在项目根目录运行
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.db import connection
from api.models import Admin


def get_table_columns(cursor, table_name: str) -> set:
    """获取表的现有列名."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return {col[1] for col in columns}


def add_column_if_missing(
    cursor,
    table_name: str,
    column_name: str,
    column_type: str,
    default_value: str = None,
) -> bool:
    """如果列不存在则添加."""
    existing_columns = get_table_columns(cursor, table_name)
    if column_name not in existing_columns:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_value:
            sql += f" DEFAULT {default_value}"
        try:
            cursor.execute(sql)
            print(f"  [+] 添加列: {column_name} ({column_type})")
            return True
        except sqlite3.OperationalError as e:
            print(f"  [!] 添加列失败 {column_name}: {e}")
            return False
    else:
        print(f"  [=] 列已存在: {column_name}")
        return False


def fix_admins_table():
    """修复 admins 表结构."""
    print("\n" + "=" * 60)
    print("Step 1: 检查并修复 admins 表结构")
    print("=" * 60)

    with connection.cursor() as cursor:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admins'")
        if not cursor.fetchone():
            print("  [!] admins 表不存在，将通过迁移创建")
            return

        print("  [OK] admins 表存在")

        # 定义期望的列 (列名, 类型, 默认值)
        expected_columns = [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", None),
            ("name", "VARCHAR(100)", "''"),
            ("username", "VARCHAR(50) UNIQUE", None),
            ("password_hash", "VARCHAR(255)", "''"),
            ("email", "VARCHAR(254)", "''"),
            ("phone", "VARCHAR(11)", "NULL"),
            ("token", "VARCHAR(255)", "NULL"),
            ("is_active", "INTEGER", "1"),
            ("created_at", "DATETIME", None),
            ("updated_at", "DATETIME", None),
        ]

        existing = get_table_columns(cursor, "admins")
        print(f"\n  现有列: {existing}")

        added = 0
        for col_name, col_type, default in expected_columns:
            if col_name != "id":  # id 列是主键，不需要添加
                if add_column_if_missing(cursor, "admins", col_name, col_type, default):
                    added += 1

        if added > 0:
            connection.commit()
            print(f"\n  [OK] 添加了 {added} 个新列")
        else:
            print("\n  [OK] 表结构完整，无需修改")


def create_test_admin():
    """创建或获取测试管理员并生成 Token."""
    print("\n" + "=" * 60)
    print("Step 2: 创建/获取测试管理员")
    print("=" * 60)

    # 生成随机 Token
    token = secrets.token_hex(32)  # 64 字符的十六进制 Token

    # 创建或获取管理员
    admin, created = Admin.objects.get_or_create(
        username="test_admin",
        defaults={
            "name": "测试管理员",
            "password_hash": "not_used",  # 实际应用中应该使用哈希密码
            "email": "test@example.com",
            "phone": "13800138000",
            "token": token,
            "is_active": True,
        },
    )

    if created:
        print(f"  [+] 创建新管理员: {admin.username}")
    else:
        print(f"  [=] 管理员已存在: {admin.username}")
        # 更新 Token
        admin.token = token
        admin.is_active = True
        admin.save()
        print(f"  [+] 更新 Token")

    print(f"\n  管理员信息:")
    print(f"    ID: {admin.id}")
    print(f"    用户名: {admin.username}")
    print(f"    姓名: {admin.name}")
    print(f"    邮箱: {admin.email}")
    print(f"    手机: {admin.phone}")
    print(f"    是否激活: {admin.is_active}")

    return token


def main():
    """主函数."""
    print("\n" + "=" * 60)
    print("数据库修复 & Admin Token 生成脚本")
    print("=" * 60)

    try:
        # Step 1: 修复表结构
        fix_admins_table()

        # Step 2: 创建测试管理员
        token = create_test_admin()

        # 输出 Token
        print("\n" + "=" * 60)
        print("[SUCCESS] 完成!")
        print("=" * 60)
        print(f"\n[TOKEN] (用于 Apifox 测试):")
        print(f"\n    {token}\n")
        print("\n[USAGE] 在 Apifox 中使用:")
        print("    Header: Authorization: Bearer <token>")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
