import pytest
from decimal import Decimal
from datetime import date

from base.quote.models import Quote, QuoteService, QuoteExpense
from base.services.models import Service
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
def client(db, account):
    return Client.objects.create(
        account=account,
        name="Cliente Teste",
        phone="11999999999",
    )


@pytest.fixture
def service(db, account):
    return Service.objects.create(
        account=account,
        name="Serviço de Video",
        hourly_rate=Decimal("200.00"),
        estimated_duration_hours=Decimal("4.00"),
        typical_expenses=Decimal("100.00"),
    )


@pytest.fixture
def quote(db, account, client):
    return Quote.objects.create(
        account=account,
        client=client,
        title="Orçamento Video",
        hourly_rate=Decimal("200.00"),
        work_hours=Decimal("8.00"),
        labor_cost=Decimal("1600.00"),
    )


@pytest.mark.django_db
class TestQuoteModel:
    def test_quote_with_services(self, quote, service):
        QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=2,
        )
        assert quote.services.count() == 1

    def test_quote_with_expenses(self, quote):
        QuoteExpense.objects.create(
            quote=quote,
            description="Transporte",
            quantity=Decimal("2"),
            unit_price=Decimal("100.00"),
        )
        assert quote.expenses.count() == 1

    def test_quote_calculate_with_services_and_expenses(self, quote, service):
        QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=1,
        )
        QuoteExpense.objects.create(
            quote=quote,
            description="Transporte",
            quantity=Decimal("1"),
            unit_price=Decimal("200.00"),
        )
        total = quote.calculate()
        assert total > Decimal("0")


@pytest.mark.django_db
class TestQuoteServiceModel:
    def test_quote_service_unit_price_default(self, quote, service):
        qs = QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=1,
        )
        expected = service.hourly_rate * service.estimated_duration_hours
        assert qs.unit_price == expected

    def test_quote_service_unit_price_custom(self, quote, service):
        qs = QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=1,
            custom_price=Decimal("1000.00"),
        )
        assert qs.unit_price == Decimal("1000.00")

    def test_quote_service_total_multiple(self, quote, service):
        qs = QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=3,
        )
        assert qs.total == qs.unit_price * 3

    def test_quote_service_str(self, quote, service):
        qs = QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=2,
        )
        assert "Video" in str(qs)


@pytest.mark.django_db
class TestQuoteExpenseModel:
    def test_quote_expense_updates_quote_total(self, quote):
        QuoteExpense.objects.create(
            quote=quote,
            description="Equipamento",
            quantity=Decimal("1"),
            unit_price=Decimal("500.00"),
        )
        quote.refresh_from_db()
        assert quote.expenses_cost == Decimal("500.00")

    def test_quote_expense_str(self, quote):
        expense = QuoteExpense.objects.create(
            quote=quote,
            description="Transporte",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
        )
        assert str(expense) == "Transporte"
