import pytest
from decimal import Decimal

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
        name="Cobertura Fotográfica",
        estimated_duration_hours=Decimal("8.00"),
        hourly_rate=Decimal("150.00"),
        typical_expenses=Decimal("200.00"),
    )


@pytest.fixture
def quote(db, account, client):
    return Quote.objects.create(
        account=account,
        client=client,
        title="Orçamento Evento",
        description="Orçamento para evento corporativo",
        hourly_rate=Decimal("150.00"),
        work_hours=Decimal("8.00"),
        labor_cost=Decimal("1200.00"),
    )


@pytest.mark.django_db
class TestQuoteModel:
    def test_quote_creation(self, quote):
        assert quote.title == "Orçamento Evento"
        assert quote.hourly_rate == Decimal("150.00")
        assert quote.work_hours == Decimal("8.00")
        assert quote.is_sent is False
        assert quote.is_accepted is False

    def test_quote_str(self, quote):
        assert str(quote) == "Orçamento Evento"

    def test_quote_calculate(self, quote, service, db):
        QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=1,
        )
        assert quote.calculate() > 0

    def test_quote_ordering(self, db, account, client):
        quote1 = Quote.objects.create(
            account=account,
            client=client,
            title="Orçamento Alpha",
            hourly_rate=Decimal("100.00"),
            work_hours=Decimal("1.00"),
        )
        quote2 = Quote.objects.create(
            account=account,
            client=client,
            title="Orçamento Beta",
            hourly_rate=Decimal("100.00"),
            work_hours=Decimal("1.00"),
        )
        quotes = list(Quote.objects.filter(account=account))
        assert quotes[0] == quote2
        assert quotes[1] == quote1


@pytest.mark.django_db
class TestQuoteServiceModel:
    def test_quote_service_creation(self, quote, service):
        quote_service = QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=2,
        )
        assert quote_service.quantity == 2

    def test_quote_service_str(self, quote, service):
        quote_service = QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=1,
        )
        assert str(quote_service) == "Cobertura Fotográfica x1"

    def test_quote_service_unit_price(self, quote, service):
        quote_service = QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=1,
        )
        expected = service.hourly_rate * service.estimated_duration_hours
        assert quote_service.unit_price == expected

    def test_quote_service_custom_price(self, quote, service):
        quote_service = QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=1,
            custom_price=Decimal("500.00"),
        )
        assert quote_service.unit_price == Decimal("500.00")

    def test_quote_service_total(self, quote, service):
        quote_service = QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=3,
        )
        assert quote_service.total == quote_service.unit_price * 3


@pytest.mark.django_db
class TestQuoteExpenseModel:
    def test_quote_expense_creation(self, quote):
        expense = QuoteExpense.objects.create(
            quote=quote,
            description="Transporte",
            quantity=Decimal("2"),
            unit_price=Decimal("100.00"),
        )
        assert expense.description == "Transporte"

    def test_quote_expense_str(self, quote):
        expense = QuoteExpense.objects.create(
            quote=quote,
            description="Transporte",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
        )
        assert str(expense) == "Transporte"

    def test_quote_expense_total(self, quote):
        expense = QuoteExpense.objects.create(
            quote=quote,
            description="Transporte",
            quantity=Decimal("2"),
            unit_price=Decimal("100.00"),
        )
        assert expense.total == Decimal("200.00")

    def test_quote_expense_updates_quote(self, quote):
        QuoteExpense.objects.create(
            quote=quote,
            description="Transporte",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
        )
        quote.refresh_from_db()
        assert quote.expenses_cost == Decimal("100.00")
