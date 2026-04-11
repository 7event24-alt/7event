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


@pytest.mark.django_db
class TestServiceModel:
    def test_service_estimated_total_zero_rate(self, account):
        service = Service.objects.create(
            account=account,
            name="Serviço Barato",
            hourly_rate=Decimal("0"),
            estimated_duration_hours=Decimal("10"),
        )
        assert service.estimated_total == Decimal("0")

    def test_service_estimated_total_with_expenses(self, account):
        service = Service.objects.create(
            account=account,
            name="Serviço Completo",
            hourly_rate=Decimal("100"),
            estimated_duration_hours=Decimal("8"),
            typical_expenses=Decimal("500"),
        )
        expected = (Decimal("100") * Decimal("8")) + Decimal("500")
        assert service.estimated_total == expected

    def test_service_inactive_still_exists(self, account):
        service = Service.objects.create(
            account=account,
            name="Serviço Inativo",
            is_active=False,
        )
        assert Service.objects.filter(pk=service.pk).exists() is True

    def test_service_str(self, account):
        service = Service.objects.create(
            account=account,
            name="Serviço de Fotografia",
        )
        assert str(service) == "Serviço de Fotografia"
