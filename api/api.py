"""API 路由定义."""
from typing import Optional

from ninja import Router, File, UploadedFile
from ninja.errors import HttpError

from .schemas import (
    EnrollmentSchema,
    EnrollmentCreateSchema,
    EnrollmentStatusSchema,
    EnrollmentDraftSchema,
    EnrollmentDraftCreateSchema,
    EnrollmentFileSchema,
    PaginatedEnrollmentList,
    PaginatedDraftList,
    MessageSchema,
)
from .services import (
    EnrollmentService,
    EnrollmentDraftService,
    EnrollmentFileService,
)

router = Router(tags=["API"])
enrollment_router = Router(tags=["报名相关"])

# ==================== 报名相关 API ====================

@enrollment_router.post("/enrollments", response=EnrollmentSchema)
def submit_enrollment(request, data: EnrollmentCreateSchema):
    """提交报名表单.

    POST /api/v1/enrollments
    """
    # 这里需要从请求中获取当前用户ID，实际项目中应该通过认证获取
    # 为了演示，假设用户ID为1
    user_id = 1
    enrollment = EnrollmentService.create_enrollment(user_id, data.dict())
    return enrollment

@enrollment_router.get("/enrollments", response=PaginatedEnrollmentList)
def get_enrollment_list(
    request,
    page: int = 1,
    page_size: int = 20,
):
    """查看报名状态列表（分页）.

    GET /api/v1/enrollments?page=1&page_size=20
    """
    user_id = 1  # 实际项目中从认证获取
    result = EnrollmentService.get_enrollments_by_user(user_id, page, page_size)
    return result

@enrollment_router.get("/enrollments/{enrollment_id}", response=EnrollmentSchema)
def get_enrollment(request, enrollment_id: int):
    """查看单个报名详情.

    GET /api/v1/enrollments/{enrollment_id}
    """
    enrollment = EnrollmentService.get_enrollment(enrollment_id)
    if not enrollment:
        raise HttpError(404, "报名记录不存在")
    return enrollment

@enrollment_router.put("/enrollments/{enrollment_id}/cancel", response=MessageSchema)
def cancel_enrollment(request, enrollment_id: int):
    """取消报名.

    PUT /api/v1/enrollments/{enrollment_id}/cancel
    """
    success = EnrollmentService.cancel_enrollment(enrollment_id)
    if not success:
        raise HttpError(404, "报名记录不存在")
    return {"message": "报名已取消"}

# ==================== 草稿相关 API ====================

@enrollment_router.post("/drafts", response=EnrollmentDraftSchema)
def save_draft(request, data: EnrollmentDraftCreateSchema):
    """保存表单草稿.

    POST /api/v1/drafts
    """
    user_id = 1  # 实际项目中从认证获取
    draft = EnrollmentDraftService.create_draft(user_id, data.dict())
    return draft

@enrollment_router.get("/drafts", response=PaginatedDraftList)
def get_draft_list(
    request,
    page: int = 1,
    page_size: int = 20,
):
    """获取草稿列表（分页）.

    GET /api/v1/drafts?page=1&page_size=20
    """
    user_id = 1  # 实际项目中从认证获取
    result = EnrollmentDraftService.get_drafts_by_user(user_id, page, page_size)
    return result

@enrollment_router.get("/drafts/{draft_id}", response=EnrollmentDraftSchema)
def get_draft(request, draft_id: int):
    """获取单个草稿详情.

    GET /api/v1/drafts/{draft_id}
    """
    draft = EnrollmentDraftService.get_draft(draft_id)
    if not draft:
        raise HttpError(404, "草稿不存在")
    return draft

@enrollment_router.put("/drafts/{draft_id}", response=EnrollmentDraftSchema)
def update_draft(request, draft_id: int, data: EnrollmentDraftCreateSchema):
    """更新草稿（加载并修改草稿）.

    PUT /api/v1/drafts/{draft_id}
    """
    draft = EnrollmentDraftService.update_draft(draft_id, data.dict())
    if not draft:
        raise HttpError(404, "草稿不存在")
    return draft

@enrollment_router.delete("/drafts/{draft_id}", response=MessageSchema)
def delete_draft(request, draft_id: int):
    """删除草稿.

    DELETE /api/v1/drafts/{draft_id}
    """
    success = EnrollmentDraftService.delete_draft(draft_id)
    if not success:
        raise HttpError(404, "草稿不存在")
    return {"message": "草稿已删除"}

@enrollment_router.delete("/drafts", response=MessageSchema)
def clear_all_drafts(request):
    """清空所有草稿.

    DELETE /api/v1/drafts
    """
    user_id = 1  # 实际项目中从认证获取
    deleted_count = EnrollmentDraftService.clear_all_drafts(user_id)
    return {"message": f"已删除 {deleted_count} 个草稿"}

# ==================== 文件相关 API ====================

@enrollment_router.post("/files", response=EnrollmentFileSchema)
def upload_file(
    request,
    file: UploadedFile = File(...),
    enrollment_id: Optional[int] = None,
    draft_id: Optional[int] = None,
):
    """文件上传.

    POST /api/v1/files?enrollment_id=&draft_id=
    """
    if not enrollment_id and not draft_id:
        raise HttpError(400, "必须指定 enrollment_id 或 draft_id")
    file_obj = EnrollmentFileService.upload_file(file, enrollment_id, draft_id)
    return file_obj

@enrollment_router.delete("/files/{file_id}", response=MessageSchema)
def delete_file(request, file_id: int):
    """删除文件.

    DELETE /api/v1/files/{file_id}
    """
    success = EnrollmentFileService.delete_file(file_id)
    if not success:
        raise HttpError(404, "文件不存在")
    return {"message": "文件已删除"}

# 挂载子路由
router.add_router("/v1", enrollment_router)
