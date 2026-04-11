import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import date, time

from base.jobs.views import (
    JobListView,
    JobCreateView,
    JobUpdateView,
    JobDetailView,
    JobConfirmView,
    JobCompleteView,
    JobCancelView,
)
from base.jobs.models import Job, EventType, JobStatus, PaymentType, PaymentStatusJob
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
        start_date=date(2025, 6, 15),
        end_date=date(2025, 6, 16),
        start_time=time(14, 0),
        end_time=time(22, 0),
        location="Local Teste",
        description="Descrição do evento",
        cache=Decimal("5000.00"),
        status=JobStatus.PENDING,
        payment_status=PaymentStatusJob.PENDING,
    )


@pytest.mark.django_db
class TestJobListView:
    def test_job_list_view_get(self, rf, user, job):
        request = rf.get("/")
        request.user = user
        view = JobListView()
        response = view.get(request)
        assert response.status_code == 200

    def test_job_list_view_with_query(self, rf, user, job):
        request = rf.get("/", {"q": "Evento"})
        request.user = user
        view = JobListView()
        response = view.get(request)
        assert response.status_code == 200

    def test_job_list_view_with_status_filter(self, rf, user, job):
        request = rf.get("/", {"status": JobStatus.PENDING})
        request.user = user
        view = JobListView()
        response = view.get(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestJobCreateView:
    def test_job_create_view_get(self, rf, user):
        request = rf.get("/")
        request.user = user
        view = JobCreateView()
        response = view.get(request)
        assert response.status_code == 200

    def test_job_create_view_post_valid(self, rf, user, client):
        request = rf.post(
            "/",
            {
                "client": client.id,
                "title": "Novo Trabalho",
                "event_type": EventType.CORPORATIVO,
                "start_date": "2025-07-01",
                "location": "Novo Local",
                "cache": "3000.00",
                "status": JobStatus.PENDING,
                "payment_status": PaymentStatusJob.PENDING,
            },
        )
        request.user = user
        request._messages = MagicMock()
        view = JobCreateView()
        response = view.post(request)
        assert response.status_code == 302
        assert Job.objects.filter(title="Novo Trabalho").exists()


@pytest.mark.django_db
class TestJobUpdateView:
    def test_job_update_view_get(self, rf, user, job):
        request = rf.get("/")
        request.user = user
        view = JobUpdateView()
        response = view.get(request, pk=job.pk)
        assert response.status_code == 200

    def test_job_update_view_post_valid(self, rf, user, job):
        request = rf.post(
            "/",
            {
                "client": job.client.id,
                "title": "Trabalho Atualizado",
                "event_type": EventType.CORPORATIVO,
                "start_date": "2025-07-01",
                "cache": "4000.00",
                "status": JobStatus.CONFIRMED,
                "payment_status": PaymentStatusJob.PENDING,
            },
        )
        request.user = user
        request._messages = MagicMock()
        view = JobUpdateView()
        response = view.post(request, pk=job.pk)
        assert response.status_code == 302
        job.refresh_from_db()
        assert job.title == "Trabalho Atualizado"


@pytest.mark.django_db
class TestJobDetailView:
    def test_job_detail_view(self, rf, user, job):
        request = rf.get("/")
        request.user = user
        view = JobDetailView()
        response = view.get(request, pk=job.pk)
        assert response.status_code == 200


@pytest.mark.django_db
class TestJobConfirmView:
    def test_job_confirm_post(self, rf, user, job):
        request = rf.post("/")
        request.user = user
        request._messages = MagicMock()
        view = JobConfirmView()
        response = view.post(request, pk=job.pk)
        assert response.status_code == 302
        job.refresh_from_db()
        assert job.status == JobStatus.CONFIRMED


@pytest.mark.django_db
class TestJobCompleteView:
    def test_job_complete_post(self, rf, user, job):
        request = rf.post("/")
        request.user = user
        request._messages = MagicMock()
        view = JobCompleteView()
        response = view.post(request, pk=job.pk)
        assert response.status_code == 302
        job.refresh_from_db()
        assert job.status == JobStatus.COMPLETED


@pytest.mark.django_db
class TestJobCancelView:
    def test_job_cancel_post(self, rf, user, job):
        request = rf.post("/")
        request.user = user
        request._messages = MagicMock()
        view = JobCancelView()
        response = view.post(request, pk=job.pk)
        assert response.status_code == 302
        job.refresh_from_db()
        assert job.status == JobStatus.CANCELLED
