import pytest
from unittest.mock import MagicMock
from decimal import Decimal

from base.accounts.forms import UserProfileForm
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
class TestUserProfileForm:
    def test_profile_form_contains_role_field(self):
        form = UserProfileForm()
        assert "role" in form.fields

    def test_profile_form_role_has_all_choices(self):
        form = UserProfileForm()
        role_choices = form.fields["role"].choices
        assert len(role_choices) > 45
