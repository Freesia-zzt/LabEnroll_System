"""URL 配置文件."""
from django.http import HttpRequest    # HTTP请求对象
from django.urls import path           # URL路由函数
from ninja import NinjaAPI             # API框架

from api.admin_api import admin_router                          # 管理员路由
from api.api import router as api_router                         # 主业务路由
from notice.api import admin_router as notice_admin_router       # 通知管理路由
from notice.api import public_router as notice_public_router     # 通知公开路由

api = NinjaAPI(
    title="实验室报名系统 API",                    # API标题
    description="基于 Django + django-ninja 的 RESTful API",  # API描述
    version="1.0.0",                               # 版本号
    openapi_extra={                                # OpenAPI扩展配置
        "components": {
            "securitySchemes": {                   # 认证方案
                "bearerAuth": {                    # Bearer Token认证
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                },
            }
        }
    },
)

api.add_router("/", api_router)                     # 挂载主业务路由
api.add_router("/v1/admin", admin_router)           # 挂载管理员路由
api.add_router("/notice/admin", notice_admin_router)  # 挂载通知管理路由
api.add_router("/notice/public", notice_public_router)  # 挂载通知公开路由


@api.get("/", tags=["Health"], summary="服务健康检查")  # 健康检查接口
def health_check(request: HttpRequest) -> dict[str, str]:
    """返回服务健康状态."""
    return {"status": "ok", "service": "laboratory-registration-system"}


urlpatterns = [
    path("api/", api.urls),    # 所有API以/api/开头
]
