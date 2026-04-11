import pytest
from django.contrib.auth import get_user_model

from base.accounts.models import (
    Account,
    Plan,
    PlanType,
    Subscription,
    SubscriptionStatus,
    BillingPeriod,
    Feature,
    AccountType,
    ProfessionalRole,
)

User = get_user_model()


@pytest.fixture
def plan(db):
    return Plan.objects.create(
        type=PlanType.BASIC,
        name="Plano Básico",
        max_users=5,
        max_clients=100,
        max_jobs=100,
        max_expenses=100,
        max_agenda_events=100,
        price_monthly=29.90,
        price_quarterly=89.90,
        price_semester=179.90,
        is_active=True,
    )


@pytest.fixture
def account(db, plan):
    return Account.objects.create(
        name="Empresa Teste",
        slug="empresa-teste",
        account_type=AccountType.COMPANY,
        cnpj="12345678000100",
        phone="11999999999",
        email="teste@empresa.com",
        plan=plan,
        is_active=True,
    )


@pytest.fixture
def user(db, account):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="João",
        last_name="Silva",
        account=account,
        phone="11988888888",
        role=ProfessionalRole.DIRETOR_EVENTO,
    )


@pytest.fixture
def admin_user(db, account):
    return User.objects.create_user(
        username="adminuser",
        email="admin@example.com",
        password="testpass123",
        account=account,
        is_account_admin=True,
    )


@pytest.mark.django_db
class TestAccountModel:
    def test_account_creation(self, account):
        assert account.name == "Empresa Teste"
        assert account.slug == "empresa-teste"
        assert account.account_type == AccountType.COMPANY
        assert account.is_active is True

    def test_account_str(self, account):
        assert str(account) == "Empresa Teste"

    def test_account_user_count(self, account, user):
        assert account.user_count == 1

    def test_account_is_at_user_limit(self, db, account, plan):
        user = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass123",
            account=account,
        )
        plan.max_users = 1
        plan.save()
        assert account.is_at_user_limit is True

    def test_account_can_access(self, account):
        assert account.can_access is True

    def test_account_blocked(self, account):
        account.is_blocked = True
        account.save()
        assert account.can_access is False


@pytest.mark.django_db
class TestPlanModel:
    def test_plan_creation(self, plan):
        assert plan.name == "Plano Básico"
        assert plan.type == PlanType.BASIC
        assert plan.is_active is True

    def test_plan_with_default(self, db):
        plan = Plan.objects.create(
            type=PlanType.BASIC,
            name="Plano Básico",
            is_active=True,
        )
        assert Plan.get_default() is not None

    def test_plan_with_tester(self, db):
        plan = Plan.objects.create(
            type=PlanType.TESTER,
            name="Plano Tester",
            is_active=True,
        )
        assert Plan.get_tester() is not None


@pytest.mark.django_db
class TestFeatureModel:
    def test_feature_creation(self, db):
        feature = Feature.objects.create(
            key="test_feature",
            name="Feature de Teste",
            description="Uma feature para testes",
            is_premium=False,
        )
        assert feature.name == "Feature de Teste"
        assert str(feature) == "Feature de Teste"


@pytest.mark.django_db
class TestSubscriptionModel:
    def test_subscription_creation(self, account, plan):
        from django.utils import timezone
        from datetime import timedelta

        subscription = Subscription.objects.create(
            account=account,
            plan=plan,
            status=SubscriptionStatus.TRIAL,
            billing_period=BillingPeriod.MONTHLY,
            price=29.90,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )
        assert subscription.account == account
        assert subscription.status == SubscriptionStatus.TRIAL
        assert subscription.is_active() is True


@pytest.mark.django_db
class TestUserModel:
    def test_user_creation(self, user):
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "João"
        assert user.last_name == "Silva"
        assert user.account is not None
        assert user.role == ProfessionalRole.DIRETOR_EVENTO

    def test_user_str(self, user):
        assert str(user) == "João Silva"

    def test_user_full_name(self, user):
        assert user.full_name == "João Silva"

    def test_user_is_account_owner(self, admin_user):
        assert admin_user.is_account_owner is True

    def test_user_company(self, user):
        assert user.company == user.account

    def test_user_can_access(self, user):
        assert user.can_access is True

    def test_user_blocked(self, user):
        user.is_blocked = True
        user.save()
        assert user.can_access is False


@pytest.mark.django_db
class TestProfessionalRole:
    def test_professional_role_choices(self):
        assert len(ProfessionalRole.choices) >= 47
        assert (
            ProfessionalRole.DIRETOR_EVENTO.label == "Diretor de Evento / Event Manager"
        )
        assert ProfessionalRole.CONVIDADO.label == "Convidado"
