import pytest
from django import forms

from base.accounts.forms import RegisterForm, AccountAdminForm, UserProfileForm
from base.accounts.models import Account, Plan, PlanType, ProfessionalRole


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


@pytest.mark.django_db
class TestRegisterForm:
    def test_register_form_fields(self):
        form = RegisterForm()
        assert "first_name" in form.fields
        assert "last_name" in form.fields
        assert "email" in form.fields
        assert "username" in form.fields
        assert "phone" in form.fields
        assert "role" in form.fields

    def test_register_form_role_choices(self):
        form = RegisterForm()
        role_choices = form.fields["role"].choices
        assert len(role_choices) > 1
        assert ("", "Selecione uma função") in role_choices
        assert ProfessionalRole.DIRETOR_EVENTO in [c[0] for c in role_choices]

    def test_register_form_widget_classes(self):
        form = RegisterForm()
        assert form.fields["first_name"].widget.attrs["class"] == "input"
        assert isinstance(form.fields["role"].widget, forms.Select)


@pytest.mark.django_db
class TestAccountAdminForm:
    def test_account_admin_form_fields(self):
        form = AccountAdminForm()
        assert "name" in form.fields
        assert "slug" in form.fields
        assert "cnpj" in form.fields
        assert "phone" in form.fields
        assert "email" in form.fields
        assert "address" in form.fields
        assert "account_type" in form.fields


@pytest.mark.django_db
class TestUserProfileForm:
    def test_user_profile_form_fields(self):
        form = UserProfileForm()
        assert "first_name" in form.fields
        assert "last_name" in form.fields
        assert "email" in form.fields
        assert "phone" in form.fields
        assert "role" in form.fields

    def test_user_profile_form_role_choices(self):
        form = UserProfileForm()
        role_choices = form.fields["role"].choices
        assert len(role_choices) > 1
        assert ("", "Selecione uma função") in role_choices
