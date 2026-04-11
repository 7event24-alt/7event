import pytest
from decimal import Decimal
from datetime import date, time

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
        email="cliente@teste.com",
        phone="11999999999",
    )


@pytest.fixture
def job(db, account, client):
    return Job.objects.create(
        account=account,
        client=client,
        title="Evento Corporativo",
        event_type=EventType.CORPORATIVO,
        start_date=date(2025, 6, 15),
        end_date=date(2025, 6, 16),
        start_time=time(14, 0),
        end_time=time(22, 0),
        location="Centro de Convenções",
        description="Evento de lançamento de produto",
        cache=Decimal("5000.00"),
        payment_type=PaymentType.FULL,
        status=JobStatus.PENDING,
        payment_status=PaymentStatusJob.PENDING,
    )


@pytest.mark.django_db
class TestJobModel:
    def test_job_creation(self, job):
        assert job.title == "Evento Corporativo"
        assert job.event_type == EventType.CORPORATIVO
        assert job.cache == Decimal("5000.00")
        assert job.status == JobStatus.PENDING

    def test_job_str(self, job):
        assert str(job) == "Evento Corporativo - Cliente Teste"

    def test_job_is_single_day(self, job):
        assert job.is_single_day is False

    def test_job_duration_days(self, job):
        assert job.duration_days == 2

    def test_job_single_day(self, db, account, client):
        single_job = Job.objects.create(
            account=account,
            client=client,
            title="Evento Único",
            event_type=EventType.EVENTOS,
            start_date=date(2025, 6, 15),
            end_date=date(2025, 6, 15),
        )
        assert single_job.is_single_day is True
        assert single_job.duration_days == 1

    def test_job_total_expenses(self, job, account):
        from base.expenses.models import Expense, ExpenseCategory

        Expense.objects.create(
            account=account,
            job=job,
            category=ExpenseCategory.TRANSPORT,
            description="Transporte ida",
            value=Decimal("200.00"),
            date=date(2025, 6, 15),
        )
        Expense.objects.create(
            account=account,
            job=job,
            category=ExpenseCategory.TRANSPORT,
            description="Transporte volta",
            value=Decimal("200.00"),
            date=date(2025, 6, 15),
        )
        assert job.total_expenses == Decimal("400.00")

    def test_job_net_profit(self, job):
        assert job.net_profit == Decimal("5000.00")


@pytest.mark.django_db
class TestEventType:
    def test_event_type_choices(self):
        assert len(EventType.choices) == 15
        assert EventType.CORPORATIVO.label == "Corporativo"
        assert EventType.LIVES.label == "Lives / Transmissões ao Vivo"
        assert EventType.CAMPANHA_PUBLICITARIA.label == "Campanha Publicitária"


@pytest.mark.django_db
class TestJobStatus:
    def test_job_status_choices(self):
        assert JobStatus.PENDING.label == "Pendente"
        assert JobStatus.CONFIRMED.label == "Confirmado"
        assert JobStatus.COMPLETED.label == "Concluído"
        assert JobStatus.CANCELLED.label == "Cancelado"


@pytest.mark.django_db
class TestPaymentType:
    def test_payment_type_choices(self):
        assert PaymentType.ADVANCE.label == "Pagamento Antecipado"
        assert PaymentType.FULL.label == "Pagamento Total"
        assert PaymentType.PARTIAL.label == "Pagamento Parcial"


@pytest.mark.django_db
class TestPaymentStatusJob:
    def test_payment_status_choices(self):
        assert PaymentStatusJob.PENDING.label == "Pendente"
        assert PaymentStatusJob.PARTIAL.label == "Parcial"
        assert PaymentStatusJob.PAID.label == "Pago"
