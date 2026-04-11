import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date

from base.jobs.models import Job, EventType, JobStatus, PaymentType, PaymentStatusJob
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
        event_type=EventType.SHOWS_FESTIVAIS,
        start_date=date(2025, 6, 15),
        end_date=date(2025, 6, 16),
        status=JobStatus.CONFIRMED,
        cache=Decimal("10000.00"),
        payment_status=PaymentStatusJob.PAID,
    )


@pytest.mark.django_db
class TestJobModel:
    def test_job_net_profit_with_expenses(self, job, account):
        from base.expenses.models import Expense, ExpenseCategory

        Expense.objects.create(
            account=account,
            job=job,
            category=ExpenseCategory.TRANSPORT,
            value=Decimal("500.00"),
            date=date(2025, 6, 15),
        )
        Expense.objects.create(
            account=account,
            job=job,
            category=ExpenseCategory.FOOD,
            value=Decimal("300.00"),
            date=date(2025, 6, 15),
        )
        assert job.net_profit == Decimal("9200.00")

    def test_job_is_past_event(self, job):
        job.start_date = date(2020, 1, 1)
        job.save()
        assert job.is_past_event is True


@pytest.mark.django_db
class TestJobStatus:
    def test_all_statuses(self):
        assert JobStatus.PENDING.label == "Pendente"
        assert JobStatus.CONFIRMED.label == "Confirmado"
        assert JobStatus.COMPLETED.label == "Concluído"
        assert JobStatus.CANCELLED.label == "Cancelado"


@pytest.mark.django_db
class TestPaymentType:
    def test_all_payment_types(self):
        assert PaymentType.ADVANCE.label == "Pagamento Antecipado"
        assert PaymentType.FULL.label == "Pagamento Total"
        assert PaymentType.PARTIAL.label == "Pagamento Parcial"
