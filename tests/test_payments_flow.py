from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from base.accounts.models import (
    BillingPeriod,
    Plan,
    PlanType,
    Subscription,
    SubscriptionFinancialStatus,
    SubscriptionStatus,
)
from base.payments.models import PaymentStatus, PaymentTransaction, PaymentWebhookEvent
from base.payments.services.billing import (
    create_or_update_recurring_subscription,
    downgrade_to_free_if_overdue,
    schedule_subscription_cancel_at_period_end,
)


User = get_user_model()


@override_settings(
    MP_ACCESS_TOKEN="APP_USR-test-token",
    MP_TEST_MODE=True,
    MP_TEST_PAYER_EMAIL="comprador_teste_123@testuser.com",
)
class PaymentsFlowTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.free_plan = Plan.objects.create(type=PlanType.FREE, name="Free", price_monthly=0, is_active=True)
        self.pro_plan = Plan.objects.create(type=PlanType.PROFESSIONAL, name="Pro", price_monthly=Decimal("99.90"), is_active=True)
        self.user = User.objects.create_user(username="bia", email="bia@example.com", password="12345678", plan=self.pro_plan)

    def _create_tx(self, status=PaymentStatus.PENDING):
        billing_month = timezone.localdate().replace(day=1)
        return PaymentTransaction.objects.create(
            user=self.user,
            plan=self.pro_plan,
            billing_period=BillingPeriod.MONTHLY,
            billing_month=billing_month,
            external_reference=f"u{self.user.id}-p{self.pro_plan.id}-{billing_month.strftime('%Y-%m')}",
            status=status,
            amount=Decimal("99.90"),
            currency="BRL",
            due_date=billing_month.replace(day=8),
            grace_limit_date=billing_month.replace(day=15),
        )

    @patch("base.payments.views.get_payment")
    def test_webhook_approved_updates_plan_and_subscription(self, mock_get_payment):
        tx = self._create_tx()
        mock_get_payment.return_value = {
            "id": 123456,
            "status": "approved",
            "external_reference": tx.external_reference,
        }

        response = self.client.post(
            "/api/v1/webhooks/mercadopago/",
            data={"id": "evt-1", "data": {"id": "123456"}},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        tx.refresh_from_db()
        self.assertEqual(tx.status, PaymentStatus.APPROVED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.plan_id, self.pro_plan.id)

        sub = Subscription.objects.get(user=self.user)
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)
        self.assertEqual(sub.plan_id, self.pro_plan.id)
        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.REGULAR)

    @patch("base.payments.views.get_payment")
    def test_webhook_duplicate_event_is_deduplicated(self, mock_get_payment):
        tx = self._create_tx(status=PaymentStatus.APPROVED)
        PaymentWebhookEvent.objects.create(event_id="evt-dup", processing_status="processed")
        mock_get_payment.return_value = {
            "id": 999,
            "status": "approved",
            "external_reference": tx.external_reference,
        }

        response = self.client.post(
            "/api/v1/webhooks/mercadopago/",
            data={"id": "evt-dup", "data": {"id": "999"}},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("deduplicated"))

    def test_cutoff_downgrades_user_to_free(self):
        tx = self._create_tx(status=PaymentStatus.PENDING)
        tx.grace_limit_date = timezone.localdate() - timedelta(days=8)
        tx.save(update_fields=["grace_limit_date", "updated_at"])

        updated = downgrade_to_free_if_overdue(today=timezone.localdate())
        self.assertEqual(updated, 1)

        self.user.refresh_from_db()
        self.assertEqual(self.user.plan_id, self.free_plan.id)
        sub = Subscription.objects.get(user=self.user)
        self.assertEqual(sub.status, SubscriptionStatus.EXPIRED)

    def test_cutoff_respects_five_day_tolerance(self):
        tx = self._create_tx(status=PaymentStatus.PENDING)
        tx.grace_limit_date = timezone.localdate() - timedelta(days=2)
        tx.save(update_fields=["grace_limit_date", "updated_at"])

        updated = downgrade_to_free_if_overdue(today=timezone.localdate())
        self.assertEqual(updated, 0)

        self.user.refresh_from_db()
        self.assertEqual(self.user.plan_id, self.pro_plan.id)

    @patch("base.payments.services.billing.create_preapproval")
    def test_create_recurring_subscription_persists_mp_id(self, mock_create_preapproval):
        mock_create_preapproval.return_value = {
            "id": "preapp-123",
            "init_point": "https://mp.local/checkout",
            "status": "authorized",
        }

        request = self.factory.get("/")
        request.user = self.user

        sub, tx, checkout_url = create_or_update_recurring_subscription(
            self.user,
            self.pro_plan,
            request,
        )

        self.assertEqual(sub.mp_subscription_id, "preapp-123")
        self.assertEqual(checkout_url, "https://mp.local/checkout")
        self.assertEqual(tx.checkout_url, "https://mp.local/checkout")

    @patch("base.payments.services.billing.update_preapproval")
    def test_cancel_subscription_marks_as_scheduled(self, mock_update_preapproval):
        mock_update_preapproval.return_value = {"id": "preapp-123", "status": "cancelled"}
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            mp_subscription_id="preapp-123",
        )

        schedule_subscription_cancel_at_period_end(sub)
        sub.refresh_from_db()

        self.assertTrue(sub.cancel_at_period_end)

    @patch("base.payments.views.get_preapproval")
    def test_webhook_preapproval_updates_subscription_status(self, mock_get_preapproval):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            mp_subscription_id="preapp-xyz",
        )
        mock_get_preapproval.return_value = {
            "id": "preapp-xyz",
            "status": "cancelled",
        }

        response = self.client.post(
            "/api/v1/webhooks/mercadopago/?topic=preapproval",
            data={"id": "evt-sub-1", "data": {"id": "preapp-xyz"}},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.status, SubscriptionStatus.CANCELLED)
