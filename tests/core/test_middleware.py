import pytest
from unittest.mock import MagicMock, patch
from django.urls import reverse

from base.core.middleware import BlockedUserMiddleware, AdminAccessMiddleware


@pytest.mark.django_db
class TestBlockedUserMiddleware:
    def test_authenticated_active_user(self):
        middleware = BlockedUserMiddleware(lambda req: None)
        user = MagicMock()
        user.is_authenticated = True
        user.is_active = True
        user.is_blocked = False

        request = MagicMock()
        request.user = user

        result = middleware.process_request(request)
        assert result is None

    def test_authenticated_inactive_user(self):
        middleware = BlockedUserMiddleware(lambda req: None)
        user = MagicMock()
        user.is_authenticated = True
        user.is_active = False
        user.is_blocked = False

        request = MagicMock()
        request.user = user

        result = middleware.process_request(request)
        assert result is not None
        assert result.url == "/accounts/login/"

    def test_authenticated_blocked_user(self):
        middleware = BlockedUserMiddleware(lambda req: None)
        user = MagicMock()
        user.is_authenticated = True
        user.is_active = True
        user.is_blocked = True

        request = MagicMock()
        request.user = user

        result = middleware.process_request(request)
        assert result is not None
        assert result.url == "/accounts/login/"

    def test_unauthenticated_user(self):
        middleware = BlockedUserMiddleware(lambda req: None)
        user = MagicMock()
        user.is_authenticated = False

        request = MagicMock()
        request.user = user

        result = middleware.process_request(request)
        assert result is None


@pytest.mark.django_db
class TestAdminAccessMiddleware:
    def test_admin_path_unauthenticated(self):
        middleware = AdminAccessMiddleware(lambda req: None)

        request = MagicMock()
        request.path = "/admin/"
        request.user.is_authenticated = False

        result = middleware.process_request(request)
        assert result is not None
        assert "/accounts/login/" in result.url

    def test_admin_path_non_superuser(self):
        middleware = AdminAccessMiddleware(lambda req: None)

        request = MagicMock()
        request.path = "/admin/"
        request.user.is_authenticated = True
        request.user.is_superuser = False

        result = middleware.process_request(request)
        assert result is not None

    def test_admin_path_superuser(self):
        middleware = AdminAccessMiddleware(lambda req: None)

        request = MagicMock()
        request.path = "/admin/"
        request.user.is_authenticated = True
        request.user.is_superuser = True

        result = middleware.process_request(request)
        assert result is None

    def test_non_admin_path(self):
        middleware = AdminAccessMiddleware(lambda req: None)

        request = MagicMock()
        request.path = "/dashboard/"
        request.user.is_authenticated = True

        result = middleware.process_request(request)
        assert result is None
