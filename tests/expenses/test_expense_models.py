import pytest
from decimal import Decimal
from datetime import date

from base.expenses.models import Expense, ExpenseCategory
from base.jobs.models import Job, EventType, JobStatus
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
def job(db, account, client):
    return Job.objects.create(
        account=account,
        client=client,
        title="Evento Teste",
        event_type=EventType.CORPORATIVO,
        start_date=date(2025, 6, 15),
        status=JobStatus.PENDING,
    )


@pytest.fixture
def expense(db, account, job):
    return Expense.objects.create(
        account=account,
        job=job,
        category=ExpenseCategory.TRANSPORT,
        value=Decimal("150.00"),
        date=date(2025, 6, 15),
        description="Transporte para evento",
    )


@pytest.mark.django_db
class TestExpenseModel:
    def test_expense_creation(self, expense):
        assert expense.category == ExpenseCategory.TRANSPORT
        assert expense.value == Decimal("150.00")
        assert expense.description == "Transporte para evento"

    def test_expense_str(self, expense):
        assert str(expense) == "transport - R$ 150.00"

    def test_expense_ordering(self, db, account, job):
        expense1 = Expense.objects.create(
            account=account,
            job=job,
            category=ExpenseCategory.FOOD,
            value=Decimal("50.00"),
            date=date(2025, 6, 10),
        )
        expense2 = Expense.objects.create(
            account=account,
            job=job,
            category=ExpenseCategory.TRANSPORT,
            value=Decimal("100.00"),
            date=date(2025, 6, 20),
        )
        expenses = list(Expense.objects.filter(account=account))
        assert expenses[0] == expense2
        assert expenses[1] == expense1


@pytest.mark.django_db
class TestExpenseCategory:
    def test_expense_category_choices(self):
        assert ExpenseCategory.EQUIPMENT.label == "Equipamento"
        assert ExpenseCategory.TRANSPORT.label == "Transporte"
        assert ExpenseCategory.FOOD.label == "Alimentação"
        assert ExpenseCategory.ACCOMMODATION.label == "Hospedagem"
        assert ExpenseCategory.MARKETING.label == "Marketing"
        assert ExpenseCategory.FEE.label == "Taxa/Imposto"
        assert ExpenseCategory.OTHER.label == "Outro"
