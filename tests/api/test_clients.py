import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from base.clients.models import Client
from base.accounts.models import Account, Plan, PlanType

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def account(db):
    plan = Plan.objects.create(
        type=PlanType.BASIC,
        name="Test Plan",
        max_users=5,
        max_clients=100,
        max_jobs=100,
        max_expenses=100,
        max_agenda_events=100,
        price_monthly=29.90,
        is_active=True,
    )
    return Account.objects.create(name="Test Company", slug="test-company", plan=plan)


@pytest.fixture
def user(db, account):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        account=account,
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def client(db, user, account):
    return Client.objects.create(
        account=account,
        name="Test Client",
        email="client@example.com",
        phone="11999999999",
    )


@pytest.mark.django_db
class TestClientAPI:
    def test_list_clients_unauthenticated(self, api_client):
        url = reverse("clients:client-api-list")
        response = api_client.get(url)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_list_clients_authenticated(self, authenticated_client, client):
        url = reverse("clients:client-api-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_create_client(self, authenticated_client, account):
        url = reverse("clients:client-api-list")
        data = {
            "name": "New Client",
            "email": "new@example.com",
            "phone": "11988888888",
            "account": account.id,
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Client"

    def test_update_client(self, authenticated_client, client):
        url = reverse("clients:client-api-detail", args=[client.pk])
        data = {"name": "Updated Client"}
        response = authenticated_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Client"

    def test_delete_client(self, authenticated_client, client):
        url = reverse("clients:client-api-detail", args=[client.pk])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_client_isolation(self, api_client, db):
        plan = Plan.objects.create(
            type=PlanType.BASIC,
            name="Plan 1",
            max_users=5,
            max_clients=100,
            max_jobs=100,
            max_expenses=100,
            max_agenda_events=100,
            price_monthly=29.90,
            is_active=True,
        )
        account1 = Account.objects.create(name="Account 1", slug="account-1", plan=plan)
        account2 = Account.objects.create(name="Account 2", slug="account-2", plan=plan)

        user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass123",
            account=account1,
        )
        user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="pass123",
            account=account2,
        )

        client1 = Client.objects.create(
            account=account1, name="My Client", phone="11999999999"
        )
        client2 = Client.objects.create(
            account=account2, name="Other Client", phone="11999999998"
        )

        api_client.force_authenticate(user=user1)
        url = reverse("clients:client-api-list")
        response = api_client.get(url)

        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "My Client"
