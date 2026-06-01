"""URL 配置文件."""
from django.http import HttpRequest
from django.urls import path
from ninja import NinjaAPI

from api.admin_api import admin_router
from api.api import router as api_router
from notice.api import admin_router as notice_admin_router, public_router as notice_public_router

# 创建主 API 实例
api = NinjaAPI(
    title="实验室报名系统 API",
    description="基于 Django + django-ninja 的 RESTful API",
    version="1.0.0",
    openapi_extra={
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                },
            }
        }
    },
)

# 挂载原有路由
api.add_router("/", api_router)

# 挂载管理员路由到主 API（带 v1 版本）
api.add_router("/v1/admin", admin_router)

api.add_router("/notice/admin", notice_admin_router)
api.add_router("/notice/public", notice_public_router)


@api.get("/", tags=["Health"], summary="服务健康检查")
def health_check(request: HttpRequest) -> dict[str, str]:
    """返回服务健康状态."""
    return {"status": "ok", "service": "laboratory-registration-system"}


urlpatterns = [
    path("api/", api.urls),
]
