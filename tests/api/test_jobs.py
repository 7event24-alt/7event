import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date

from base.jobs.models import Job, EventType, JobStatus, PaymentStatusJob
from base.clients.models import Client
from base.accounts.models import Account, Plan, PlanType

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def account(db):
    plan = Plan.objects.create(
        type=PlanType.BASIC,
        name="Test Plan",
        max_users=5,
        max_clients=100,
        max_jobs=100,
        max_expenses=100,
        max_agenda_events=100,
        price_monthly=29.90,
        is_active=True,
    )
    return Account.objects.create(name="Test Company", slug="test-company", plan=plan)


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
        name="Test Client",
        email="client@example.com",
        phone="11999999999",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestJobAPI:
    def test_list_jobs_unauthenticated(self, api_client):
        url = reverse("jobs:job-api-list")
        response = api_client.get(url)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_create_job(self, authenticated_client, account, client):
        url = reverse("jobs:job-api-list")
        data = {
            "account": account.id,
            "client": client.id,
            "title": "New Job",
            "event_type": EventType.CORPORATIVO,
            "start_date": "2025-07-01",
            "status": JobStatus.PENDING,
            "cache": "3000.00",
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Job"
