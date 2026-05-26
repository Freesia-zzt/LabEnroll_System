"""URL 配置文件."""
from django.http import HttpRequest
from django.urls import path
from ninja import NinjaAPI

from api.api import router as api_router

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
                "apiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                },
            }
        }
    },
)

api.add_router("/", api_router)


@api.get("/", tags=["Health"], summary="服务健康检查")
def health_check(request: HttpRequest) -> dict[str, str]:
    """返回服务健康状态."""
    return {"status": "ok", "service": "laboratory-registration-system"}


urlpatterns = [
    path("api/", api.urls),
]
