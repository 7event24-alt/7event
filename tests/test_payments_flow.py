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
    create_or_update_recurring_subscription_stripe,
    downgrade_to_free_if_overdue,
    handle_stripe_checkout_completed,
    handle_stripe_invoice_paid,
    handle_stripe_invoice_payment_failed,
    handle_stripe_subscription_updated,
    map_stripe_subscription_status,
    resume_scheduled_subscription,
    resume_scheduled_subscription_stripe,
    schedule_subscription_cancel_at_period_end,
    schedule_subscription_cancel_at_period_end_stripe,
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

    def test_cancel_subscription_marks_as_scheduled(self):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            mp_subscription_id="preapp-123",
        )

        schedule_subscription_cancel_at_period_end(sub)
        sub.refresh_from_db()

        self.assertTrue(sub.cancel_at_period_end)

    @patch("base.payments.services.billing.update_preapproval")
    def test_resume_subscription_unsets_scheduled_cancel(self, mock_update_preapproval):
        mock_update_preapproval.return_value = {"id": "preapp-123", "status": "authorized"}
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            financial_status=SubscriptionFinancialStatus.CANCELAMENTO_AGENDADO,
            cancel_at_period_end=True,
            mp_subscription_id="preapp-123",
        )

        resume_scheduled_subscription(sub)
        sub.refresh_from_db()

        self.assertFalse(sub.cancel_at_period_end)
        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.REGULAR)

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


@override_settings(
    STRIPE_API_KEY="sk_test_fake",
    STRIPE_PUBLISHABLE_KEY="pk_test_fake",
    STRIPE_TEST_MODE=True,
)
class StripePaymentsFlowTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.free_plan = Plan.objects.create(type=PlanType.FREE, name="Free", price_monthly=0, is_active=True)
        self.pro_plan = Plan.objects.create(type=PlanType.PROFESSIONAL, name="Pro", price_monthly=Decimal("99.90"), is_active=True)
        self.user = User.objects.create_user(username="stripe_user", email="stripe@example.com", password="12345678", plan=self.pro_plan)

    def test_map_stripe_subscription_status(self):
        self.assertEqual(map_stripe_subscription_status("active"), SubscriptionFinancialStatus.REGULAR)
        self.assertEqual(map_stripe_subscription_status("trialing"), SubscriptionFinancialStatus.REGULAR)
        self.assertEqual(map_stripe_subscription_status("past_due"), SubscriptionFinancialStatus.INADIMPLENTE)
        self.assertEqual(map_stripe_subscription_status("incomplete"), SubscriptionFinancialStatus.INADIMPLENTE)
        self.assertEqual(map_stripe_subscription_status("canceled"), SubscriptionFinancialStatus.CANCELADO)
        self.assertEqual(map_stripe_subscription_status("incomplete_expired"), SubscriptionFinancialStatus.CANCELADO)
        self.assertEqual(map_stripe_subscription_status("unpaid"), SubscriptionFinancialStatus.SUSPENSO)

    @patch("base.payments.services.billing.create_checkout_session")
    def test_create_recurring_subscription_stripe_creates_session(self, mock_create_session):
        mock_session = type("Session", (), {"id": "cs_test_123", "customer": "cus_test_456", "url": "https://checkout.stripe.com/test"})()
        mock_create_session.return_value = mock_session

        request = self.factory.get("/")
        request.user = self.user

        sub, tx, checkout_url = create_or_update_recurring_subscription_stripe(
            self.user, self.pro_plan, request,
        )

        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.PENDING)
        self.assertEqual(sub.status, SubscriptionStatus.PENDING)
        self.assertEqual(sub.plan_id, self.pro_plan.id)
        self.assertEqual(checkout_url, "https://checkout.stripe.com/test")
        self.assertEqual(tx.checkout_url, "https://checkout.stripe.com/test")
        self.assertEqual(tx.provider_preference_id, "cs_test_123")

    @patch("base.payments.services.billing.create_checkout_session")
    def test_create_recurring_subscription_stripe_updates_existing(self, mock_create_session):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            financial_status=SubscriptionFinancialStatus.REGULAR,
        )
        mock_session = type("Session", (), {"id": "cs_test_456", "customer": "cus_test_789", "url": "https://checkout.stripe.com/updated"})()
        mock_create_session.return_value = mock_session

        request = self.factory.get("/")
        request.user = self.user

        create_or_update_recurring_subscription_stripe(self.user, self.pro_plan, request)
        sub.refresh_from_db()

        self.assertEqual(sub.stripe_customer_id, "cus_test_789")
        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.PENDING)

    def test_handle_stripe_checkout_completed_activates_subscription(self):
        session = {
            "id": "cs_test_completed",
            "customer": "cus_test_completed",
            "subscription": "sub_test_completed",
            "metadata": {"user_id": str(self.user.id), "plan_id": str(self.pro_plan.id)},
        }

        handle_stripe_checkout_completed(session)
        sub = Subscription.objects.get(user=self.user)

        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.REGULAR)
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)
        self.assertEqual(sub.stripe_subscription_id, "sub_test_completed")
        self.assertEqual(sub.stripe_customer_id, "cus_test_completed")
        self.user.refresh_from_db()
        self.assertEqual(self.user.plan_id, self.pro_plan.id)

    def test_handle_stripe_checkout_completed_ignores_missing_metadata(self):
        session = {
            "id": "cs_test_no_meta",
            "customer": None,
            "subscription": None,
            "metadata": {},
        }
        handle_stripe_checkout_completed(session)
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

    def test_handle_stripe_invoice_paid_marks_regular(self):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_inv_paid",
            financial_status=SubscriptionFinancialStatus.INADIMPLENTE,
            past_due_since=timezone.localdate() - timedelta(days=3),
        )

        handle_stripe_invoice_paid({"subscription": "sub_inv_paid"})
        sub.refresh_from_db()

        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.REGULAR)
        self.assertIsNone(sub.past_due_since)

    def test_handle_stripe_invoice_payment_failed_marks_inadimplente(self):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_inv_fail",
            financial_status=SubscriptionFinancialStatus.REGULAR,
        )

        handle_stripe_invoice_payment_failed({"subscription": "sub_inv_fail"})
        sub.refresh_from_db()

        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.INADIMPLENTE)
        self.assertIsNotNone(sub.past_due_since)

    def test_handle_stripe_invoice_payment_failed_skips_if_already_inadimplente(self):
        past_since = timezone.localdate() - timedelta(days=2)
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_inv_fail_dup",
            financial_status=SubscriptionFinancialStatus.INADIMPLENTE,
            past_due_since=past_since,
        )

        handle_stripe_invoice_payment_failed({"subscription": "sub_inv_fail_dup"})
        sub.refresh_from_db()

        self.assertEqual(sub.past_due_since, past_since)

    def test_handle_stripe_subscription_updated_canceled(self):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_upd_cancel",
            financial_status=SubscriptionFinancialStatus.REGULAR,
        )

        handle_stripe_subscription_updated({
            "id": "sub_upd_cancel",
            "status": "canceled",
            "cancel_at_period_end": False,
        })
        sub.refresh_from_db()

        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.CANCELADO)
        self.assertEqual(sub.status, SubscriptionStatus.CANCELLED)
        self.assertIsNotNone(sub.cancelled_at)

    def test_handle_stripe_subscription_updated_inadimplente(self):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_upd_past_due",
            financial_status=SubscriptionFinancialStatus.REGULAR,
        )

        handle_stripe_subscription_updated({
            "id": "sub_upd_past_due",
            "status": "past_due",
            "cancel_at_period_end": False,
        })
        sub.refresh_from_db()

        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.INADIMPLENTE)
        self.assertIsNotNone(sub.past_due_since)

    def test_schedule_cancel_at_period_end_stripe(self):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            financial_status=SubscriptionFinancialStatus.REGULAR,
            stripe_subscription_id="sub_cancel_stripe",
        )

        schedule_subscription_cancel_at_period_end_stripe(sub)
        sub.refresh_from_db()

        self.assertTrue(sub.cancel_at_period_end)
        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.CANCELAMENTO_AGENDADO)

    def test_resume_scheduled_subscription_stripe(self):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            financial_status=SubscriptionFinancialStatus.CANCELAMENTO_AGENDADO,
            cancel_at_period_end=True,
            stripe_subscription_id="sub_resume_stripe",
        )

        resume_scheduled_subscription_stripe(sub)
        sub.refresh_from_db()

        self.assertFalse(sub.cancel_at_period_end)
        self.assertEqual(sub.financial_status, SubscriptionFinancialStatus.REGULAR)

    @patch("base.payments.services.billing.stripe_cancel_at_period_end")
    def test_schedule_cancel_calls_stripe_client(self, mock_stripe_cancel):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id="sub_cancel_client",
        )

        schedule_subscription_cancel_at_period_end_stripe(sub)
        mock_stripe_cancel.assert_called_once_with("sub_cancel_client")

    @patch("base.payments.services.billing.stripe_resume_cancel")
    def test_resume_calls_stripe_client(self, mock_stripe_resume):
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=SubscriptionStatus.ACTIVE,
            financial_status=SubscriptionFinancialStatus.CANCELAMENTO_AGENDADO,
            cancel_at_period_end=True,
            stripe_subscription_id="sub_resume_client",
        )

        resume_scheduled_subscription_stripe(sub)
        mock_stripe_resume.assert_called_once_with("sub_resume_client")
