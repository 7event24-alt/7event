import pytest
from unittest.mock import MagicMock
from decimal import Decimal

from base.services.views import (
    ServiceListView,
    ServiceCreateView,
    ServiceUpdateView,
    ServiceDeleteView,
)
from base.services.models import Service
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
def service(db, account):
    return Service.objects.create(
        account=account,
        name="Serviço de Teste",
        description="Descrição do serviço",
        estimated_duration_hours=Decimal("4.00"),
        hourly_rate=Decimal("100.00"),
        is_active=True,
    )


@pytest.mark.django_db
class TestServiceListView:
    def test_service_list_view_get(self, rf, user, service):
        request = rf.get("/")
        request.user = user
        view = ServiceListView()
        response = view.get(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestServiceCreateView:
    def test_service_create_view_get(self, rf, user):
        request = rf.get("/")
        request.user = user
        view = ServiceCreateView()
        response = view.get(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestServiceUpdateView:
    def test_service_update_view_get(self, rf, user, service):
        request = rf.get("/")
        request.user = user
        view = ServiceUpdateView()
        response = view.get(request, pk=service.pk)
        assert response.status_code == 200


@pytest.mark.django_db
class TestServiceDeleteView:
    def test_service_delete_post(self, rf, user, service):
        request = rf.post("/")
        request.user = user
        request._messages = MagicMock()
        view = ServiceDeleteView()
        response = view.post(request, pk=service.pk)
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.is_active is False
