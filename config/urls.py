"""URL 配置文件."""
from django.http import HttpRequest
from django.urls import path
from ninja import NinjaAPI

from api.admin_api import admin_router
from api.api import router as api_router

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

# 创建 v1 API 实例
api_v1 = NinjaAPI(
    title="实验室报名系统 API v1",
    description="API 版本 v1",
    version="1.0.0-v1",
    urls_namespace="api_v1",
)

# 挂载原有路由
api.add_router("/", api_router)

# 挂载 v1 路由（仅管理员接口）
api_v1.add_router("/admin", admin_router)


@api.get("/", tags=["Health"], summary="服务健康检查")
def health_check(request: HttpRequest) -> dict[str, str]:
    """返回服务健康状态."""
    return {"status": "ok", "service": "laboratory-registration-system"}


urlpatterns = [
    path("api/", api.urls),
    path("api/v1/", api_v1.urls),
]
