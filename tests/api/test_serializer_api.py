import pytest
from decimal import Decimal
from datetime import date

from base.expenses.serializers import ExpenseSerializer
from base.jobs.serializers import JobSerializer
from base.clients.serializers import ClientSerializer


@pytest.mark.django_db
class TestExpenseSerializer:
    def test_expense_serializer_fields(self):
        from base.expenses.models import Expense

        expense = Expense(
            account_id=1,
            job_id=1,
            category="transport",
            value=Decimal("150.00"),
            date=date(2025, 6, 15),
            description="Teste",
        )
        serializer = ExpenseSerializer(expense)
        assert "id" in serializer.data
        assert serializer.data["value"] == "150.00"
        assert serializer.data["category"] == "transport"


@pytest.mark.django_db
class TestClientSerializer:
    def test_client_serializer_fields(self, db):
        from base.clients.models import Client
        from base.accounts.models import Account, Plan, PlanType

        plan = Plan.objects.create(type=PlanType.BASIC, name="Test", is_active=True)
        account = Account.objects.create(name="Test", slug="test", plan=plan)
        client = Client.objects.create(
            account=account,
            name="Test Client",
            email="test@test.com",
            phone="11999999999",
        )

        serializer = ClientSerializer(client)
        assert serializer.data["name"] == "Test Client"
        assert serializer.data["email"] == "test@test.com"


@pytest.mark.django_db
class TestJobSerializer:
    def test_job_serializer_fields(self, db):
        from base.jobs.models import Job, EventType, JobStatus
        from base.accounts.models import Account, Plan, PlanType
        from base.clients.models import Client

        plan = Plan.objects.create(type=PlanType.BASIC, name="Test", is_active=True)
        account = Account.objects.create(name="Test", slug="test", plan=plan)
        client = Client.objects.create(
            account=account, name="Client", phone="11999999999"
        )
        job = Job.objects.create(
            account=account,
            client=client,
            title="Test Job",
            event_type=EventType.CORPORATIVO,
            status=JobStatus.PENDING,
            start_date=date(2025, 6, 15),
        )

        serializer = JobSerializer(job)
        assert serializer.data["title"] == "Test Job"
        assert serializer.data["event_type"] == "corporativo"
