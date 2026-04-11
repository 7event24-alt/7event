import pytest
from django.contrib.auth import get_user_model

from base.clients.models import Client
from base.accounts.models import Account, Plan, PlanType

User = get_user_model()


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
    return Account.objects.create(name="Test Account", slug="test-account", plan=plan)


@pytest.fixture
def user(db, account):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        account=account,
    )


@pytest.fixture
def client(db, user, account):
    return Client.objects.create(
        account=account,
        name="Test Client",
        email="client@example.com",
        phone="11999999999",
    )


@pytest.mark.django_db
class TestClientModel:
    def test_client_creation(self, client):
        assert client.name == "Test Client"
        assert client.email == "client@example.com"
        assert client.phone == "11999999999"
        assert client.account is not None

    def test_client_str(self, client):
        assert str(client) == "Test Client"

    def test_client_address(self, client):
        client.address = "Test Address, 123"
        client.save()
        assert client.address == "Test Address, 123"

    def test_client_notes(self, client):
        client.notes = "Test notes"
        client.save()
        assert client.notes == "Test notes"

    def test_client_document(self, account):
        client = Client.objects.create(
            account=account,
            name="Doc Client",
            phone="11999999999",
            document="12345678000100",
        )
        assert client.document == "12345678000100"

    def test_client_ordering(self, account):
        client1 = Client.objects.create(
            account=account,
            name="Alpha Client",
            phone="11999999999",
            email="alpha@test.com",
        )
        client2 = Client.objects.create(
            account=account,
            name="Beta Client",
            phone="11999999998",
            email="beta@test.com",
        )
        clients = Client.objects.filter(account=account)
        assert clients.first().name == "Alpha Client"
