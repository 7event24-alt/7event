import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse

from base.clients.views import ClientListView, ClientCreateView, ClientUpdateView
from base.clients.models import Client
from base.accounts.models import Account, Plan, PlanType


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
    from django.contrib.auth import get_user_model

    User = get_user_model()
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
class TestClientListView:
    def test_client_list_view_requires_login(self, client, rf):
        request = rf.get("/")
        request.user = MagicMock()
        request.user.account = None
        view = ClientListView()
        response = view.dispatch(request)
        assert response.status_code == 403

    def test_client_list_view_with_query(self, rf, user, client):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(username="testuser")

        request = rf.get("/", {"q": "Teste"})
        request.user = user
        view = ClientListView()
        response = view.get(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestClientCreateView:
    def test_client_create_view_get(self, rf, user):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(username="testuser")

        request = rf.get("/")
        request.user = user
        view = ClientCreateView()
        response = view.get(request)
        assert response.status_code == 200

    def test_client_create_view_post_valid(self, rf, user, account):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(username="testuser")

        request = rf.post(
            "/",
            {"name": "Novo Cliente", "email": "novo@teste.com", "phone": "11988888888"},
        )
        request.user = user
        request._messages = MagicMock()
        view = ClientCreateView()
        response = view.post(request)
        assert response.status_code == 302
        assert Client.objects.filter(name="Novo Cliente").exists()


@pytest.mark.django_db
class TestClientUpdateView:
    def test_client_update_view_get(self, rf, user, client):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(username="testuser")

        request = rf.get("/")
        request.user = user
        view = ClientUpdateView()
        response = view.get(request, pk=client.pk)
        assert response.status_code == 200

    def test_client_update_view_post_valid(self, rf, user, client):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(username="testuser")

        request = rf.post(
            "/",
            {
                "name": "Cliente Atualizado",
                "email": "atualizado@teste.com",
                "phone": "11988888888",
            },
        )
        request.user = user
        request._messages = MagicMock()
        view = ClientUpdateView()
        response = view.post(request, pk=client.pk)
        assert response.status_code == 302
        client.refresh_from_db()
        assert client.name == "Cliente Atualizado"
