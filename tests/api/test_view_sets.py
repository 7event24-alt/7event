import pytest

from base.expenses.api_views import ExpenseViewSet
from base.jobs.api_views import JobViewSet
from base.clients.api_views import ClientViewSet
from base.accounts.models import Account, Plan, PlanType
from base.clients.models import Client
from base.jobs.models import Job, EventType, JobStatus
from base.expenses.models import Expense, ExpenseCategory


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
        title="Evento Teste",
        event_type=EventType.CORPORATIVO,
        start_date="2025-06-15",
        status=JobStatus.PENDING,
    )


@pytest.fixture
def expense(db, account, job):
    return Expense.objects.create(
        account=account,
        job=job,
        category=ExpenseCategory.TRANSPORT,
        value=100.00,
        date="2025-06-15",
    )


@pytest.mark.django_db
class TestExpenseAPI:
    def test_expense_api_list(self, rf, expense):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            account=expense.account,
        )
        request = rf.get("/")
        request.user = user
        view = ExpenseViewSet.as_view({"get": "list"})
        response = view(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestClientViewSet:
    def test_client_viewset_get_queryset(self, rf, client):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            account=client.account,
        )
        request = rf.get("/")
        request.user = user
        view = ClientViewSet()
        view.request = request
        qs = view.get_queryset()
        assert qs.count() == 1
        assert qs.first().name == "Cliente Teste"
