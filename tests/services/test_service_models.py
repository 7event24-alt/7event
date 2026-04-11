import pytest
from decimal import Decimal

from base.services.models import Service
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
def service(db, account):
    return Service.objects.create(
        account=account,
        name="Cobertura Fotográfica",
        description="Cobertura completa de eventos",
        estimated_duration_hours=Decimal("8.00"),
        hourly_rate=Decimal("150.00"),
        typical_expenses=Decimal("200.00"),
        is_active=True,
    )


@pytest.mark.django_db
class TestServiceModel:
    def test_service_creation(self, service):
        assert service.name == "Cobertura Fotográfica"
        assert service.description == "Cobertura completa de eventos"
        assert service.estimated_duration_hours == Decimal("8.00")
        assert service.hourly_rate == Decimal("150.00")
        assert service.is_active is True

    def test_service_str(self, service):
        assert str(service) == "Cobertura Fotográfica"

    def test_service_ordering(self, db, account):
        service1 = Service.objects.create(
            account=account,
            name="Serviço Alpha",
        )
        service2 = Service.objects.create(
            account=account,
            name="Serviço Beta",
        )
        services = list(Service.objects.filter(account=account))
        assert services[0].name == "Serviço Alpha"
        assert services[1].name == "Serviço Beta"

    def test_service_estimated_total(self, service):
        expected = (Decimal("150.00") * Decimal("8.00")) + Decimal("200.00")
        assert service.estimated_total == expected

    def test_service_inactive(self, db, account):
        service = Service.objects.create(
            account=account,
            name="Serviço Inativo",
            is_active=False,
        )
        assert service.is_active is False
