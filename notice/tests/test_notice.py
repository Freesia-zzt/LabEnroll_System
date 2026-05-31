"""招新公告与系统配置 - 测试用例."""

import pytest
from ninja import NinjaAPI
from ninja.testing import TestClient

from notice.api import admin_router, public_router

api = NinjaAPI()
api.add_router("/notice/admin", admin_router)
api.add_router("/notice/public", public_router)

client = TestClient(api)


class TestPublicNoticeEndpoints:
    """前台公告接口测试（无认证）."""

    @pytest.mark.django_db
    def test_public_list_notices_empty(self) -> None:
        response = client.get("/notice/public/notices")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["list"] == []

    @pytest.mark.django_db
    def test_public_list_notices_with_pagination(self) -> None:
        response = client.get(
            "/notice/public/notices?page=1&per_page=5&sort_by=order&sort_order=desc"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "pagination" in data["data"]

    def test_public_list_notices_invalid_page(self) -> None:
        response = client.get("/notice/public/notices?page=0")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 200

    @pytest.mark.django_db
    def test_public_get_notice_not_found(self) -> None:
        response = client.get("/notice/public/notices/99999")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 200


class TestPublicEnrollmentSwitch:
    """前台报名开关接口测试（无认证）."""

    @pytest.mark.django_db
    def test_get_enrollment_switch(self) -> None:
        response = client.get("/notice/public/enrollment-switch")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "is_open" in data["data"]


class TestAdminNoticesWithoutAuth:
    """后台公告接口 - 无认证时测试."""

    def test_create_notice_without_auth(self) -> None:
        payload = {"title": "测试公告", "content": "测试内容"}
        response = client.post("/notice/admin/notices", json=payload)
        assert response.status_code == 401

    def test_list_notices_without_auth(self) -> None:
        response = client.get("/notice/admin/notices")
        assert response.status_code == 401

    def test_get_notice_without_auth(self) -> None:
        response = client.get("/notice/admin/notices/1")
        assert response.status_code == 401

    def test_update_notice_without_auth(self) -> None:
        payload = {"title": "更新标题"}
        response = client.put("/notice/admin/notices/1", json=payload)
        assert response.status_code == 401

    def test_delete_notice_without_auth(self) -> None:
        response = client.delete("/notice/admin/notices/1")
        assert response.status_code == 401

    def test_get_enrollment_switch_admin_without_auth(self) -> None:
        response = client.get("/notice/admin/enrollment-switch")
        assert response.status_code == 401

    def test_update_enrollment_switch_without_auth(self) -> None:
        payload = {"is_open": True}
        response = client.put("/notice/admin/enrollment-switch", json=payload)
        assert response.status_code == 401


class TestErrorResponseFormat:
    """错误响应格式统一性测试."""

    @pytest.mark.django_db
    def test_not_found_response_format(self) -> None:
        response = client.get("/notice/public/notices/99999")
        data = response.json()
        assert "code" in data
        assert "msg" in data
        assert "data" in data

    def test_invalid_pagination_response_format(self) -> None:
        response = client.get("/notice/public/notices?page=-1")
        data = response.json()
        assert "code" in data
        assert "msg" in data
        assert "data" in data
