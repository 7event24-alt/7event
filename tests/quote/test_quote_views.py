import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import date

from base.quote.views import (
    QuoteListView,
    QuoteCreateView,
    QuoteUpdateView,
    QuoteDetailView,
    QuoteDeleteView,
)
from base.quote.models import Quote, QuoteService, QuoteExpense
from base.services.models import Service
from base.clients.models import Client
from base.accounts.models import Account, Plan, PlanType
from django.contrib.auth import get_user_model
from base.jobs.models import EventType

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


@pytest.fixture
def service(db, account):
    return Service.objects.create(
        account=account,
        name="Serviço de Teste",
        estimated_duration_hours=Decimal("4.00"),
        hourly_rate=Decimal("100.00"),
        is_active=True,
    )


@pytest.fixture
def quote(db, account, client):
    return Quote.objects.create(
        account=account,
        client=client,
        title="Orçamento Teste",
        hourly_rate=Decimal("150.00"),
        work_hours=Decimal("8.00"),
    )


@pytest.mark.django_db
class TestQuoteListView:
    def test_quote_list_view_get(self, rf, user, quote):
        request = rf.get("/")
        request.user = user
        view = QuoteListView()
        response = view.get(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestQuoteCreateView:
    def test_quote_create_view_get(self, rf, user):
        request = rf.get("/")
        request.user = user
        view = QuoteCreateView()
        response = view.get(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestQuoteUpdateView:
    def test_quote_update_view_get(self, rf, user, quote):
        request = rf.get("/")
        request.user = user
        view = QuoteUpdateView()
        response = view.get(request, pk=quote.pk)
        assert response.status_code == 200


@pytest.mark.django_db
class TestQuoteDeleteView:
    def test_quote_delete_post(self, rf, user, quote):
        request = rf.post("/")
        request.user = user
        request._messages = MagicMock()
        view = QuoteDeleteView()
        response = view.post(request, pk=quote.pk)
        assert response.status_code == 302
        assert not Quote.objects.filter(pk=quote.pk).exists()
