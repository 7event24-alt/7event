import pytest
from unittest.mock import MagicMock
from decimal import Decimal

from base.dashboard.views import DashboardView
from base.jobs.models import Job, EventType, JobStatus
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
        phone="11999999999",
    )


@pytest.fixture
def job(db, account, client):
    return Job.objects.create(
        account=account,
        client=client,
        title="Evento Dashboard",
        event_type=EventType.CORPORATIVO,
        start_date="2025-06-15",
        status=JobStatus.CONFIRMED,
        cache=Decimal("5000.00"),
    )


@pytest.mark.django_db
class TestDashboardView:
    def test_dashboard_view_get(self, rf, user, job, client):
        request = rf.get("/")
        request.user = user
        view = DashboardView()
        response = view.get(request)
        assert response.status_code == 200

    def test_dashboard_view_without_account(self, rf, user):
        user.account = None
        user.save()
        request = rf.get("/")
        request.user = user
        view = DashboardView()
        response = view.get(request)
        assert response.status_code == 200
