import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date

from base.accounts.views import RegisterView, ProfileView, CustomPasswordChangeView
from base.accounts.forms import RegisterForm, UserProfileForm
from base.accounts.models import Account, Plan, PlanType, ProfessionalRole
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordChangeView

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
        first_name="João",
        last_name="Silva",
        role=ProfessionalRole.DIRETOR_EVENTO,
    )


@pytest.mark.django_db
class TestRegisterView:
    def test_register_view_get(self, rf):
        request = rf.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        view = RegisterView()
        response = view.get(request)
        assert response.status_code == 200

    def test_register_view_authenticated_redirect(self, rf, user):
        request = rf.get("/")
        request.user = user
        view = RegisterView()
        response = view.get(request)
        assert response.status_code == 302


@pytest.mark.django_db
class TestProfileView:
    def test_profile_view_get(self, rf, user):
        request = rf.get("/")
        request.user = user
        view = ProfileView()
        response = view.get(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestCustomPasswordChangeView:
    def test_password_change_view_attributes(self):
        view = CustomPasswordChangeView()
        assert hasattr(view, "success_url")
        assert hasattr(view, "form_class")
