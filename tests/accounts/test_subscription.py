import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from base.accounts.models import (
    Account,
    Plan,
    PlanType,
    Subscription,
    SubscriptionStatus,
    BillingPeriod,
)
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

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


@pytest.mark.django_db
class TestSubscription:
    def test_subscription_creation(self, account, plan):
        subscription = Subscription.objects.create(
            account=account,
            plan=plan,
            status=SubscriptionStatus.TRIAL,
            billing_period=BillingPeriod.MONTHLY,
            price=29.90,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )
        assert subscription.status == SubscriptionStatus.TRIAL
        assert subscription.is_active() is True

    def test_subscription_expired(self, account, plan):
        subscription = Subscription.objects.create(
            account=account,
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
            billing_period=BillingPeriod.MONTHLY,
            price=29.90,
            start_date=timezone.now().date() - timedelta(days=60),
            end_date=timezone.now().date() - timedelta(days=30),
        )
        assert subscription.is_expired() is True

    def test_subscription_days_until_expiry(self, account, plan):
        subscription = Subscription.objects.create(
            account=account,
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
            billing_period=BillingPeriod.MONTHLY,
            price=29.90,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=15),
        )
        days = subscription.days_until_expiry()
        assert days is not None
        assert days >= 14


@pytest.mark.django_db
class TestAccountLimits:
    def test_account_can_add_user_true(self, account, plan):
        plan.max_users = 5
        plan.save()
        User.objects.create_user(
            username="newuser",
            email="new@test.com",
            password="pass123",
            account=account,
        )
        assert account.can_add_user() is True

    def test_account_can_add_user_false_at_limit(self, account, plan):
        plan.max_users = 1
        plan.save()
        User.objects.create_user(
            username="newuser",
            email="new@test.com",
            password="pass123",
            account=account,
        )
        assert account.can_add_user() is False

    def test_account_has_feature(self, account, plan):
        from base.accounts.models import Feature

        feature = Feature.objects.create(key="test_feature", name="Test Feature")
        plan.features.add(feature)
        assert account.has_feature("test_feature") is True

    def test_account_has_feature_tester(self, account, plan):
        plan.type = PlanType.TESTER
        plan.save()
        assert account.has_feature("any_feature") is True
