import pytest
from unittest.mock import MagicMock
from decimal import Decimal

from base.clients.views import (
    ClientListView,
    ClientCreateView,
    ClientQuickCreateView,
    ClientDetailView,
    ClientDeleteView,
)
from base.clients.models import Client
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


@pytest.fixture
def client(db, account):
    return Client.objects.create(
        account=account,
        name="Cliente Teste",
        email="cliente@teste.com",
        phone="11999999999",
    )


@pytest.mark.django_db
class TestClientViews:
    def test_client_list_with_search(self, rf, user, client):
        request = rf.get("/", {"q": "Teste"})
        request.user = user
        view = ClientListView()
        response = view.get(request)
        assert response.status_code == 200

    def test_client_quick_create(self, rf, user, account):
        request = rf.post(
            "/",
            {
                "name": "Quick Client",
                "email": "quick@teste.com",
                "phone": "11988888888",
            },
        )
        request.user = user
        view = ClientQuickCreateView()
        response = view.post(request)
        assert response.status_code == 200

    def test_client_delete_view(self, rf, user, client):
        request = rf.post("/")
        request.user = user
        request._messages = MagicMock()
        view = ClientDeleteView()
        response = view.post(request, pk=client.pk)
        assert response.status_code == 302
        assert not Client.objects.filter(pk=client.pk).exists()
