import pytest
from decimal import Decimal
from datetime import date

from base.clients.forms import ClientForm
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
def client(db, account):
    return Client.objects.create(
        account=account,
        name="Cliente Teste",
        email="cliente@teste.com",
        phone="11999999999",
        address="Rua Teste, 123",
        notes="Notas de teste",
    )


@pytest.mark.django_db
class TestClientForm:
    def test_client_form_with_valid_data(self):
        data = {
            "name": "Novo Cliente",
            "email": "novo@teste.com",
            "phone": "11988888888",
            "document": "12345678901",
            "address": "Nova Rua, 100",
            "notes": "Novas notas",
        }
        form = ClientForm(data=data)
        assert form.is_valid()

    def test_client_form_with_invalid_email(self):
        data = {
            "name": "Cliente",
            "email": "not-an-email",
            "phone": "11988888888",
        }
        form = ClientForm(data=data)
        assert not form.is_valid()
        assert "email" in form.errors

    def test_client_form_missing_required_phone(self):
        data = {
            "name": "Cliente",
            "email": "cliente@teste.com",
        }
        form = ClientForm(data=data)
        assert not form.is_valid()
        assert "phone" in form.errors


@pytest.mark.django_db
class TestClientModel:
    def test_client_with_document(self, account):
        client = Client.objects.create(
            account=account,
            name="Cliente CNPJ",
            email="cnpj@teste.com",
            phone="11999999999",
            document="12345678000100",
        )
        assert client.document == "12345678000100"

    def test_client_full_address(self, client):
        assert client.address == "Rua Teste, 123"

    def test_client_notes(self, client):
        assert client.notes == "Notas de teste"
