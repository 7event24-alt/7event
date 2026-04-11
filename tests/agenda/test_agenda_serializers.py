import pytest
from decimal import Decimal
from datetime import date, time

from base.agenda.serializers import AgendaEventSerializer, AdminMetricsSerializer
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
        title="Evento Agenda",
        event_type=EventType.CORPORATIVO,
        start_date=date(2025, 6, 15),
        end_date=date(2025, 6, 16),
        start_time=time(14, 0),
        end_time=time(22, 0),
        status=JobStatus.CONFIRMED,
        cache=Decimal("5000.00"),
    )


@pytest.mark.django_db
class TestAgendaEventSerializer:
    def test_agenda_event_serializer_fields(self, job, client):
        serializer = AgendaEventSerializer(job)
        assert serializer.data["title"] == "Evento Agenda"
        assert "start" in serializer.data
        assert "end" in serializer.data
