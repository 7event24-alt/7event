import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from base.accounts.views import ProfileView
from base.accounts.models import Account, Plan, PlanType, ProfessionalRole
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin

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
        role=ProfessionalRole.LIGHTING_DESIGNER,
    )


@pytest.mark.django_db
class TestProfileView:
    def test_profile_view_get(self, rf, user):
        request = rf.get("/")
        request.user = user
        view = ProfileView()
        response = view.get(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestProfessionalRole:
    def test_all_roles_exist(self):
        assert (
            ProfessionalRole.DIRETOR_EVENTO.label == "Diretor de Evento / Event Manager"
        )
        assert ProfessionalRole.TECNICO_SOM.label == "Técnico de Som (PA)"
        assert ProfessionalRole.FOTOGRAFO.label == "Fotógrafo"
        assert ProfessionalRole.CONVIDADO.label == "Convidado"
