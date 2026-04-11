import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import date

from base.accounts.backends import PhoneEmailUsernameBackend
from base.accounts.permissions import CanAccessUser, IsAdminOrReadOnly, IsOwnerOrAdmin
from base.accounts.models import Account, Plan, PlanType, ProfessionalRole
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def plan(db):
    return Plan.objects.create(
        type=PlanType.BASIC,
        name="Plano Básico",
        is_active=True,
    )


@pytest.fixture
def account(db, plan):
    return Account.objects.create(
        name="Empresa Teste",
        slug="empresa-teste",
        plan=plan,
    )


@pytest.fixture
def user(db, account):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        account=account,
    )


@pytest.mark.django_db
class TestPhoneEmailBackend:
    def test_authenticate_with_email(self, account, user):
        backend = PhoneEmailUsernameBackend()
        result = backend.authenticate(
            MagicMock(), username="test@example.com", password="testpass123"
        )
        assert result == user

    def test_authenticate_with_phone(self, account, user):
        user.phone = "11999999999"
        user.save()
        backend = PhoneEmailUsernameBackend()
        result = backend.authenticate(
            MagicMock(), username="11999999999", password="testpass123"
        )
        assert result == user


@pytest.mark.django_db
class TestCanAccessUserPermission:
    def test_unauthenticated_user(self):
        permission = CanAccessUser()
        request = MagicMock()
        request.user.is_authenticated = False
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
class TestIsAdminOrReadOnly:
    def test_post_by_account_admin(self):
        permission = IsAdminOrReadOnly()
        request = MagicMock()
        request.method = "POST"
        user = MagicMock()
        user.is_account_admin = True
        user.is_superuser = True
        request.user = user
        assert permission.has_permission(request, None) is True
