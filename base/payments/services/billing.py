import calendar
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from base.accounts.models import BillingPeriod, Plan, PlanType, Subscription, SubscriptionStatus
from base.payments.models import PaymentStatus, PaymentTransaction
from base.core.n8n import send_whatsapp_by_reason

from .mercadopago_client import create_preference


def month_start(ref_date=None):
    current = ref_date or timezone.localdate()
    return current.replace(day=1)


def build_external_reference(user_id, plan_id, billing_month):
    return f"u{user_id}-p{plan_id}-{billing_month.strftime('%Y-%m')}"


def _month_day_safe(year, month, day):
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def get_or_create_monthly_transaction(user, plan, billing_period=BillingPeriod.MONTHLY):
    billing_month = month_start()
    reference = build_external_reference(user.id, plan.id, billing_month)
    due_date = _month_day_safe(billing_month.year, billing_month.month, settings.MP_BILLING_DUE_DAY)
    grace_limit_date = _month_day_safe(
        billing_month.year,
        billing_month.month,
        settings.MP_BILLING_CUTOFF_DAY,
    )

    tx, created = PaymentTransaction.objects.get_or_create(
        external_reference=reference,
        defaults={
            "user": user,
            "plan": plan,
            "billing_period": billing_period,
            "billing_month": billing_month,
            "amount": Decimal(plan.price_monthly),
            "currency": settings.MP_CURRENCY,
            "due_date": due_date,
            "grace_limit_date": grace_limit_date,
        },
    )

    # Se a cobranca do mes ja existir e ainda nao tiver sido aprovada,
    # sincroniza valores/plano para refletir mudancas recentes no cadastro do plano.
    if not created and tx.status != PaymentStatus.APPROVED:
        updated_fields = []
        current_amount = Decimal(plan.price_monthly)

        if tx.plan_id != plan.id:
            tx.plan = plan
            updated_fields.append("plan")

        if tx.amount != current_amount:
            tx.amount = current_amount
            # Forca regeneracao de checkout com valor atualizado
            tx.provider_preference_id = ""
            tx.provider_payment_id = ""
            tx.checkout_url = ""
            updated_fields.extend(["amount", "provider_preference_id", "provider_payment_id", "checkout_url"])

        if tx.due_date != due_date:
            tx.due_date = due_date
            updated_fields.append("due_date")

        if tx.grace_limit_date != grace_limit_date:
            tx.grace_limit_date = grace_limit_date
            updated_fields.append("grace_limit_date")

        if updated_fields:
            updated_fields.append("updated_at")
            tx.save(update_fields=updated_fields)

    return tx


def ensure_checkout_for_transaction(transaction_obj, request):
    if transaction_obj.checkout_url:
        return transaction_obj

    base_url = settings.APP_PUBLIC_URL or request.build_absolute_uri("/").rstrip("/")
    if base_url.startswith("http://"):
        base_url = "https://" + base_url[len("http://") :]

    success_url = f"{base_url}{reverse('plans:payment_success')}"
    failure_url = f"{base_url}{reverse('plans:payment_failure')}"
    pending_url = f"{base_url}{reverse('plans:payment_pending')}"
    notification_url = (settings.MP_NOTIFICATION_URL or "").strip() or f"{base_url}{reverse('payments:webhook_mercadopago')}"

    preference = create_preference(
        {
            "items": [
                {
                    "title": f"Plano {transaction_obj.plan.name} - {transaction_obj.billing_month.strftime('%m/%Y')}",
                    "quantity": 1,
                    "currency_id": transaction_obj.currency,
                    "unit_price": float(transaction_obj.amount),
                }
            ],
            "external_reference": transaction_obj.external_reference,
            "notification_url": notification_url,
            "metadata": {
                "user_id": transaction_obj.user_id,
                "plan_id": transaction_obj.plan_id,
                "billing_month": transaction_obj.billing_month.strftime("%Y-%m"),
            },
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url,
            },
            "auto_return": "approved",
            "payment_methods": {
                # Mantem checkout aberto para cartao/PIX/boleto sem forcar wallet login.
                "excluded_payment_types": [],
                "excluded_payment_methods": [],
                "installments": 12,
                "default_installments": 1,
            },
        }
    )

    transaction_obj.provider_preference_id = preference.get("id", "")
    transaction_obj.checkout_url = preference.get("init_point", "")
    transaction_obj.raw_payload = preference
    transaction_obj.save(update_fields=["provider_preference_id", "checkout_url", "raw_payload", "updated_at"])
    return transaction_obj


@transaction.atomic
def apply_approved_payment(transaction_obj, payment_payload):
    tx = PaymentTransaction.objects.select_for_update().get(pk=transaction_obj.pk)
    if tx.status == PaymentStatus.APPROVED:
        return tx

    tx.status = PaymentStatus.APPROVED
    tx.provider_payment_id = str(payment_payload.get("id") or tx.provider_payment_id)
    tx.raw_payload = payment_payload
    tx.paid_at = timezone.now()
    tx.save(
        update_fields=["status", "provider_payment_id", "raw_payload", "paid_at", "updated_at"]
    )

    subscription, _ = Subscription.objects.select_for_update().get_or_create(user=tx.user)
    subscription.plan = tx.plan
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.billing_period = tx.billing_period
    subscription.price = tx.amount
    subscription.payment_status = PaymentStatus.APPROVED
    subscription.last_payment_date = timezone.localdate()
    subscription.start_date = tx.billing_month
    subscription.end_date = _month_day_safe(tx.billing_month.year, tx.billing_month.month, settings.MP_BILLING_CUTOFF_DAY)
    subscription.next_billing_date = _month_day_safe(
        tx.billing_month.year + (1 if tx.billing_month.month == 12 else 0),
        1 if tx.billing_month.month == 12 else tx.billing_month.month + 1,
        settings.MP_BILLING_DUE_DAY,
    )
    subscription.save()

    tx.user.plan = tx.plan
    tx.user.save(update_fields=["plan", "updated_at"])

    if tx.user.phone:
        send_whatsapp_by_reason(
            phone=tx.user.phone,
            reason="payment_approved",
            nome=(tx.user.first_name or tx.user.full_name or tx.user.username or ""),
            plano=(tx.plan.name if tx.plan else ""),
        )
    return tx


@transaction.atomic
def apply_non_approved_status(transaction_obj, payment_payload):
    tx = PaymentTransaction.objects.select_for_update().get(pk=transaction_obj.pk)
    if tx.status == PaymentStatus.APPROVED:
        return tx

    status = payment_payload.get("status")
    if status == PaymentStatus.REJECTED:
        tx.status = PaymentStatus.REJECTED
    elif status == PaymentStatus.CANCELLED:
        tx.status = PaymentStatus.CANCELLED
    else:
        tx.status = PaymentStatus.PENDING

    tx.provider_payment_id = str(payment_payload.get("id") or tx.provider_payment_id)
    tx.raw_payload = payment_payload
    tx.save(update_fields=["status", "provider_payment_id", "raw_payload", "updated_at"])
    return tx


@transaction.atomic
def downgrade_to_free_if_overdue(today=None):
    check_date = today or timezone.localdate()
    free_plan = Plan.objects.filter(type=PlanType.FREE, is_active=True).first()
    if not free_plan:
        return 0

    overdue_transactions = (
        PaymentTransaction.objects.select_for_update()
        .filter(grace_limit_date__lt=check_date)
        .exclude(status=PaymentStatus.APPROVED)
    )

    updated = 0
    for tx in overdue_transactions:
        user = tx.user
        subscription, _ = Subscription.objects.get_or_create(user=user)
        subscription.status = SubscriptionStatus.EXPIRED
        subscription.payment_status = tx.status
        subscription.plan = free_plan
        subscription.save()

        if user.plan_id != free_plan.id:
            user.plan = free_plan
            user.save(update_fields=["plan", "updated_at"])
            updated += 1

        if user.phone:
            send_whatsapp_by_reason(
                phone=user.phone,
                reason="plan_downgraded_cutoff",
                nome=(user.first_name or user.full_name or user.username or ""),
            )
    return updated
