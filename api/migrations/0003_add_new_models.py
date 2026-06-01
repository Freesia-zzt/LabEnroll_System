"""Generated migration for new models.

手动创建的迁移文件，包含 Admin, StudentApplication, Admission, Notice, DataArchive 模型。
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_auto_20260524_1846"),
    ]

    operations = [
        migrations.CreateModel(
            name="Admin",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(help_text="管理员登录用户名", max_length=50, unique=True, verbose_name="用户名")),
                ("password_hash", models.CharField(help_text="加密后的密码", max_length=255, verbose_name="密码哈希")),
                ("name", models.CharField(help_text="管理员真实姓名", max_length=50, verbose_name="姓名")),
                ("email", models.EmailField(help_text="管理员邮箱", max_length=254, verbose_name="邮箱")),
                ("token", models.CharField(blank=True, help_text="用于API认证的Token", max_length=64, null=True, unique=True, verbose_name="认证Token")),
                ("role", models.CharField(choices=[("super_admin", "超级管理员"), ("admin", "普通管理员"), ("viewer", "只读管理员")], default="admin", help_text="管理员角色", max_length=20, verbose_name="角色")),
                ("is_active", models.BooleanField(default=True, help_text="账号是否可用", verbose_name="是否激活")),
                ("is_superuser", models.BooleanField(default=False, help_text="是否拥有超级管理员权限", verbose_name="是否超级管理员")),
                ("last_login", models.DateTimeField(blank=True, help_text="管理员最后登录时间", null=True, verbose_name="最后登录时间")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "管理员",
                "verbose_name_plural": "管理员",
                "db_table": "admins",
            },
        ),
        migrations.CreateModel(
            name="StudentApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("student_id", models.CharField(help_text="学生唯一学号标识", max_length=20, unique=True, verbose_name="学号")),
                ("name", models.CharField(help_text="学生姓名", max_length=50, verbose_name="姓名")),
                ("gender", models.CharField(choices=[("male", "男"), ("female", "女")], help_text="学生性别", max_length=10, verbose_name="性别")),
                ("grade", models.CharField(choices=[("2021", "2021级"), ("2022", "2022级"), ("2023", "2023级"), ("2024", "2024级"), ("2025", "2025级")], help_text="学生年级", max_length=10, verbose_name="年级")),
                ("major", models.CharField(help_text="学生专业", max_length=100, verbose_name="专业")),
                ("phone", models.CharField(help_text="学生手机号", max_length=11, verbose_name="手机号")),
                ("email", models.EmailField(help_text="学生邮箱", max_length=254, verbose_name="邮箱")),
                ("gpa", models.DecimalField(blank=True, decimal_places=2, help_text="学生GPA成绩", max_digits=4, null=True, verbose_name="GPA")),
                ("skills", models.JSONField(blank=True, default=list, help_text="学生技能标签列表", verbose_name="技能标签")),
                ("experience", models.TextField(blank=True, help_text="学生项目经验描述", verbose_name="项目经验")),
                ("motivation", models.TextField(help_text="学生报名实验室的动机说明", verbose_name="报名动机")),
                ("status", models.CharField(choices=[("draft", "草稿"), ("submitted", "已提交"), ("reviewing", "审核中"), ("approved", "已通过"), ("rejected", "已拒绝"), ("withdrawn", "已撤回")], default="draft", help_text="报名申请状态", max_length=20, verbose_name="报名状态")),
                ("submitted_at", models.DateTimeField(blank=True, help_text="报名提交时间", null=True, verbose_name="提交时间")),
                ("reviewed_at", models.DateTimeField(blank=True, help_text="报名审核时间", null=True, verbose_name="审核时间")),
                ("review_comment", models.TextField(blank=True, help_text="管理员审核意见", verbose_name="审核意见")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("reviewer", models.ForeignKey(blank=True, help_text="审核该申请的管理员", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_applications", to="api.admin", verbose_name="审核人")),
            ],
            options={
                "verbose_name": "学生报名",
                "verbose_name_plural": "学生报名",
                "db_table": "student_applications",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Admission",
            fields=[
                ("admission", models.OneToOneField(help_text="关联的报名申请", on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name="admission_info", serialize=False, to="api.studentapplication", verbose_name="报名申请")),
                ("admit_year", models.CharField(help_text="学生被录取的年份", max_length=4, verbose_name="录取年份")),
                ("lab_group", models.CharField(help_text="分配的实验室分组", max_length=100, verbose_name="实验室分组")),
                ("mentor", models.CharField(blank=True, help_text="分配的导师姓名", max_length=50, verbose_name="导师")),
                ("start_date", models.DateField(help_text="实验室学习开始日期", verbose_name="开始日期")),
                ("end_date", models.DateField(blank=True, help_text="实验室学习结束日期", null=True, verbose_name="结束日期")),
                ("is_public", models.BooleanField(default=False, help_text="录取结果是否已公示", verbose_name="是否公示")),
                ("notes", models.TextField(blank=True, help_text="录取相关备注信息", verbose_name="备注")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "录取信息",
                "verbose_name_plural": "录取信息",
                "db_table": "admissions",
            },
        ),
        migrations.CreateModel(
            name="Notice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(help_text="公告标题", max_length=200, verbose_name="标题")),
                ("content", models.TextField(help_text="公告内容", verbose_name="内容")),
                ("notice_type", models.CharField(choices=[("announcement", "公告"), ("notice", "通知"), ("urgent", "紧急通知")], default="notice", help_text="公告类型", max_length=20, verbose_name="公告类型")),
                ("is_published", models.BooleanField(default=False, help_text="公告是否已发布", verbose_name="是否发布")),
                ("is_pinned", models.BooleanField(default=False, help_text="公告是否置顶显示", verbose_name="是否置顶")),
                ("published_at", models.DateTimeField(blank=True, help_text="公告发布时间", null=True, verbose_name="发布时间")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("author", models.ForeignKey(help_text="发布公告的管理员", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notices", to="api.admin", verbose_name="发布人")),
            ],
            options={
                "verbose_name": "公告",
                "verbose_name_plural": "公告",
                "db_table": "notices",
                "ordering": ["-is_pinned", "-published_at"],
            },
        ),
        migrations.CreateModel(
            name="DataArchive",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.CharField(help_text="存档年份", max_length=4, unique=True, verbose_name="年份")),
                ("archive_data", models.JSONField(default=dict, help_text="完整的报名数据存档", verbose_name="存档数据")),
                ("major_stats", models.JSONField(default=dict, help_text="按专业统计的数据", verbose_name="专业统计")),
                ("grade_stats", models.JSONField(default=dict, help_text="按年级统计的数据", verbose_name="年级统计")),
                ("total_applications", models.IntegerField(default=0, help_text="该年度总报名数量", verbose_name="总报名数")),
                ("admitted_count", models.IntegerField(default=0, help_text="该年度录取人数", verbose_name="录取人数")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("operator", models.ForeignKey(blank=True, help_text="执行存档操作的管理员", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="archives", to="api.admin", verbose_name="存档人")),
            ],
            options={
                "verbose_name": "数据存档",
                "verbose_name_plural": "数据存档",
                "db_table": "data_archives",
                "ordering": ["-year"],
            },
        ),
    ]
