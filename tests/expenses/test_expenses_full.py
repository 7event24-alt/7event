import pytest
from unittest.mock import MagicMock
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


@pytest.mark.django_db
class TestExpenseModel:
    def test_expense_str(self, account, job):
        expense = Expense.objects.create(
            account=account,
            job=job,
            category=ExpenseCategory.FOOD,
            value=Decimal("100.00"),
            date=date(2025, 6, 15),
            description="Almoço",
        )
        assert "food" in str(expense).lower()

    def test_expense_with_description(self, account, job):
        expense = Expense.objects.create(
            account=account,
            job=job,
            category=ExpenseCategory.EQUIPMENT,
            value=Decimal("500.00"),
            date=date(2025, 6, 15),
            description="Aluguel de equipamento",
        )
        assert expense.description == "Aluguel de equipamento"


@pytest.mark.django_db
class TestExpenseCategory:
    def test_all_categories(self):
        assert ExpenseCategory.EQUIPMENT.label == "Equipamento"
        assert ExpenseCategory.TRANSPORT.label == "Transporte"
        assert ExpenseCategory.FOOD.label == "Alimentação"
        assert ExpenseCategory.ACCOMMODATION.label == "Hospedagem"
        assert ExpenseCategory.MARKETING.label == "Marketing"
        assert ExpenseCategory.FEE.label == "Taxa/Imposto"
        assert ExpenseCategory.OTHER.label == "Outro"
