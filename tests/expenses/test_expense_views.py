import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import date

from base.expenses.views import (
    ExpenseListView,
    ExpenseCreateView,
    ExpenseUpdateView,
    ExpenseDeleteView,
    ExpenseForm,
)
from base.expenses.models import Expense, ExpenseCategory
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
class TestExpenseListView:
    def test_expense_list_view_get(self, rf, user, expense):
        request = rf.get("/")
        request.user = user
        view = ExpenseListView()
        response = view.get(request)
        assert response.status_code == 200

    def test_expense_list_view_with_category_filter(self, rf, user, expense):
        request = rf.get("/", {"category": ExpenseCategory.TRANSPORT})
        request.user = user
        view = ExpenseListView()
        response = view.get(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestExpenseCreateView:
    def test_expense_create_view_get(self, rf, user):
        request = rf.get("/")
        request.user = user
        view = ExpenseCreateView()
        response = view.get(request)
        assert response.status_code == 200

    def test_expense_create_view_post_valid(self, rf, user, job):
        request = rf.post(
            "/",
            {
                "job": job.id,
                "category": ExpenseCategory.FOOD,
                "value": "200.00",
                "date": "2025-06-15",
                "description": "Alimentação",
            },
        )
        request.user = user
        request._messages = MagicMock()
        view = ExpenseCreateView()
        response = view.post(request)
        assert response.status_code == 302
        assert Expense.objects.filter(category=ExpenseCategory.FOOD).exists()


@pytest.mark.django_db
class TestExpenseUpdateView:
    def test_expense_update_view_get(self, rf, user, expense):
        request = rf.get("/")
        request.user = user
        view = ExpenseUpdateView()
        response = view.get(request, pk=expense.pk)
        assert response.status_code == 200


@pytest.mark.django_db
class TestExpenseDeleteView:
    def test_expense_delete_post(self, rf, user, expense):
        request = rf.post("/")
        request.user = user
        request._messages = MagicMock()
        view = ExpenseDeleteView()
        response = view.post(request, pk=expense.pk)
        assert response.status_code == 302
        assert not Expense.objects.filter(pk=expense.pk).exists()


@pytest.mark.django_db
class TestExpenseForm:
    def test_expense_form_fields(self):
        form = ExpenseForm()
        assert "job" in form.fields
        assert "category" in form.fields
        assert "value" in form.fields
        assert "date" in form.fields
        assert "description" in form.fields

    def test_expense_form_widget_classes(self):
        form = ExpenseForm()
        assert form.fields["category"].widget.attrs["class"] == "input"
        assert form.fields["value"].widget.attrs["class"] == "input"
