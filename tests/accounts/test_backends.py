import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import date

from base.accounts.backends import PhoneEmailUsernameBackend
from base.accounts.models import Account, Plan, PlanType
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
class TestPhoneEmailUsernameBackend:
    def test_authenticate_invalid_password(self, account, user):
        backend = PhoneEmailUsernameBackend()
        result = backend.authenticate(
            MagicMock(), username="testuser", password="wrongpassword"
        )
        assert result is None

    def test_authenticate_nonexistent_user(self, account):
        backend = PhoneEmailUsernameBackend()
        result = backend.authenticate(
            MagicMock(), username="nonexistent", password="password"
        )
        assert result is None

    def test_get_user_by_id(self, account, user):
        backend = PhoneEmailUsernameBackend()
        result = backend.get_user(user.pk)
        assert result == user

    def test_get_user_nonexistent_id(self, account):
        backend = PhoneEmailUsernameBackend()
        result = backend.get_user(99999)
        assert result is None
