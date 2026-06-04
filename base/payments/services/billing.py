import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from base.accounts.models import (
    BillingPeriod,
    Plan,
    PlanType,
    Subscription,
    SubscriptionFinancialStatus,
    SubscriptionStatus,
)
from base.payments.models import PaymentStatus, PaymentTransaction
from base.core.n8n import send_whatsapp_by_reason

from .mercadopago_client import create_preapproval, create_preference, update_preapproval


def _notify_subscription_event(user, reason, **context):
    if not user:
        return

    if user.phone:
        send_whatsapp_by_reason(
            phone=user.phone,
            reason=reason,
            user=user,
            **context,
        )

    if getattr(user, "notify_via_email", True) and user.email:
        subject_map = {
            "subscription_activated": "Sua assinatura foi ativada",
            "subscription_overdue": "Assinatura com inadimplência",
            "plan_downgraded_cutoff": "Plano ajustado por inadimplência",
            "payment_approved": "Pagamento aprovado",
        }
        template_map = {
            "subscription_activated": "emails/subscription_activated.html",
            "subscription_overdue": "emails/subscription_overdue.html",
            "plan_downgraded_cutoff": "emails/plan_downgraded_cutoff.html",
            "payment_approved": "emails/payment_approved.html",
        }

        template_name = template_map.get(reason)
        if not template_name:
            return

        email_context = {
            "user": user,
            "nome": context.get("nome") or user.first_name or user.username,
            "plano": context.get("plano") or "",
            "plan_url": (settings.APP_PUBLIC_URL or "https://7event.com.br").rstrip("/") + "/app/planos/",
        }

        try:
            html_body = render_to_string(template_name, email_context)
            text_body = strip_tags(html_body)
            message = EmailMultiAlternatives(
                subject=subject_map.get(reason, "Atualização de assinatura"),
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            message.attach_alternative(html_body, "text/html")
            message.send(fail_silently=True)
        except Exception:
            pass


def month_start(ref_date=None):
    current = ref_date or timezone.localdate()
    return current.replace(day=1)


def build_external_reference(user_id, plan_id, billing_month):
    return f"u{user_id}-p{plan_id}-{billing_month.strftime('%Y-%m')}"


def _month_day_safe(year, month, day):
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def _build_mp_payer_payload(user):
    payer = {}

    first_name = (user.first_name or "").strip()
    last_name = (user.last_name or "").strip()
    if first_name:
        payer["name"] = first_name
    if last_name:
        payer["surname"] = last_name

    cpf = "".join(c for c in str(getattr(user, "cpf", "") or "") if c.isdigit())
    if len(cpf) == 11:
        payer["identification"] = {
            "type": "CPF",
            "number": cpf,
        }

    phone = "".join(c for c in str(getattr(user, "phone", "") or "") if c.isdigit())
    if phone.startswith("55") and len(phone) in (12, 13):
        payer["phone"] = {
            "area_code": phone[2:4],
            "number": phone[4:],
        }

    return payer


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


def ensure_checkout_for_transaction(transaction_obj, request, force_new=False):
    if transaction_obj.checkout_url and not force_new:
        return transaction_obj

    if force_new:
        transaction_obj.provider_preference_id = ""
        transaction_obj.checkout_url = ""

    base_url = settings.APP_PUBLIC_URL or request.build_absolute_uri("/").rstrip("/")
    if base_url.startswith("http://"):
        base_url = "https://" + base_url[len("http://") :]

    success_url = f"{base_url}{reverse('plans:payment_success')}"
    failure_url = f"{base_url}{reverse('plans:payment_failure')}"
    pending_url = f"{base_url}{reverse('plans:payment_pending')}"
    notification_url = (settings.MP_NOTIFICATION_URL or "").strip() or f"{base_url}{reverse('payments:webhook_mercadopago')}"

    preference_payload = {
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
        "payer": _build_mp_payer_payload(transaction_obj.user),
        "payment_methods": {
            # Mantem checkout aberto para cartao/PIX/boleto sem forcar wallet login.
            "excluded_payment_types": [],
            "excluded_payment_methods": [],
            "installments": 12,
            "default_installments": 1,
        },
    }

    preference = create_preference(preference_payload)

    transaction_obj.provider_preference_id = preference.get("id", "")
    transaction_obj.checkout_url = preference.get("init_point", "")
    transaction_obj.raw_payload = {
        "preference_request": preference_payload,
        "preference_response": preference,
    }
    transaction_obj.save(update_fields=["provider_preference_id", "checkout_url", "raw_payload", "updated_at"])
    return transaction_obj


def _mp_base_url(request):
    base_url = settings.APP_PUBLIC_URL or request.build_absolute_uri("/").rstrip("/")
    if base_url.startswith("http://"):
        base_url = "https://" + base_url[len("http://") :]
    return base_url


def _build_preapproval_payload(user, plan, request):
    base_url = _mp_base_url(request)
    amount = Decimal(plan.price_monthly)
    user_email = (user.email or "").strip()
    payer_email = user_email

    test_mode = bool(getattr(settings, "MP_TEST_MODE", False))
    fallback_test_email = (getattr(settings, "MP_TEST_PAYER_EMAIL", "") or "").strip()
    if test_mode and fallback_test_email:
        payer_email = fallback_test_email
    elif test_mode and not fallback_test_email and "test" not in user_email.lower():
        raise ValueError(
            "Modo de teste ativo no Mercado Pago, mas nao foi definido MP_TEST_PAYER_EMAIL. "
            "Configure um comprador de teste ou acesse com usuario tester."
        )

    return {
        "reason": f"Assinatura {plan.name} - 7event",
        "external_reference": f"sub-u{user.id}-p{plan.id}",
        "payer_email": payer_email,
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": float(amount),
            "currency_id": settings.MP_CURRENCY,
        },
        "notification_url": (settings.MP_NOTIFICATION_URL or "").strip()
        or f"{base_url}{reverse('payments:webhook_mercadopago')}",
        "back_url": f"{base_url}{reverse('plans:payment_success')}",
        "metadata": {
            "user_id": user.id,
            "plan_id": plan.id,
            "billing_period": BillingPeriod.MONTHLY,
        },
    }


@transaction.atomic
def create_or_update_recurring_subscription(user, plan, request):
    subscription, _ = Subscription.objects.select_for_update().get_or_create(user=user)
    preapproval_payload = _build_preapproval_payload(user, plan, request)
    response = create_preapproval(preapproval_payload)

    mp_subscription_id = str(response.get("id") or "").strip()
    init_point = (response.get("init_point") or response.get("sandbox_init_point") or "").strip()
    now = timezone.localdate()

    subscription.plan = plan
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.billing_period = BillingPeriod.MONTHLY
    subscription.price = Decimal(plan.price_monthly)
    subscription.mp_subscription_id = mp_subscription_id
    subscription.financial_status = SubscriptionFinancialStatus.REGULAR
    subscription.billing_anchor_date = subscription.billing_anchor_date or now
    subscription.current_period_start = now
    subscription.current_period_end = subscription.current_period_end or _month_day_safe(
        now.year,
        now.month,
        min(now.day, settings.MP_BILLING_CUTOFF_DAY),
    )
    subscription.next_billing_date = _month_day_safe(
        now.year + (1 if now.month == 12 else 0),
        1 if now.month == 12 else now.month + 1,
        min(now.day, settings.MP_BILLING_DUE_DAY),
    )
    subscription.cancel_at_period_end = False
    subscription.cancelled_at = None
    subscription.past_due_since = None
    subscription.payment_status = PaymentStatus.PENDING
    subscription.save()

    tx = get_or_create_monthly_transaction(user, plan, billing_period=BillingPeriod.MONTHLY)
    tx.raw_payload = {
        "preapproval_request": preapproval_payload,
        "preapproval_response": response,
    }
    tx.checkout_url = init_point
    tx.save(update_fields=["raw_payload", "checkout_url", "updated_at"])

    return subscription, tx, init_point


@transaction.atomic
def schedule_subscription_cancel_at_period_end(subscription):
    # Regra de negocio: cancelamento deve ocorrer ao fim do ciclo pago.
    # Aqui apenas agenda internamente; a cobranca pode ser retomada sem gerar nova assinatura.
    subscription.cancel_at_period_end = True
    subscription.financial_status = SubscriptionFinancialStatus.CANCELAMENTO_AGENDADO
    subscription.cancelled_at = None
    subscription.save(
        update_fields=["cancel_at_period_end", "financial_status", "cancelled_at", "updated_at"]
    )
    return subscription


def map_mp_subscription_status(mp_status):
    status = (mp_status or "").strip().lower()
    if status in {"authorized", "active"}:
        return SubscriptionFinancialStatus.REGULAR
    if status in {"paused", "pending", "payment_required"}:
        return SubscriptionFinancialStatus.INADIMPLENTE
    if status in {"cancelled", "canceled"}:
        return SubscriptionFinancialStatus.CANCELADO
    return SubscriptionFinancialStatus.INADIMPLENTE


@transaction.atomic
def resume_scheduled_subscription(subscription):
    subscription.cancel_at_period_end = False
    if subscription.financial_status == SubscriptionFinancialStatus.CANCELAMENTO_AGENDADO:
        subscription.financial_status = SubscriptionFinancialStatus.REGULAR
    subscription.cancelled_at = None

    # Quando houver assinatura MP existente, tenta reautorizar para manter a mesma cobranca.
    if subscription.mp_subscription_id:
        try:
            update_preapproval(subscription.mp_subscription_id, {"status": "authorized"})
        except Exception:
            # Mantem retomada interna; reconciliacao ajusta eventual divergencia externa.
            pass

    subscription.save(
        update_fields=["cancel_at_period_end", "financial_status", "cancelled_at", "updated_at"]
    )
    return subscription


@transaction.atomic
def apply_preapproval_status(subscription, preapproval_payload):
    previous = subscription.financial_status
    mapped = map_mp_subscription_status(preapproval_payload.get("status"))
    subscription.financial_status = mapped

    if mapped == SubscriptionFinancialStatus.REGULAR:
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.payment_status = PaymentStatus.APPROVED
        subscription.last_payment_date = timezone.localdate()
        subscription.past_due_since = None
        if subscription.plan_id and subscription.user and subscription.user.plan_id != subscription.plan_id:
            subscription.user.plan_id = subscription.plan_id
            subscription.user.save(update_fields=["plan", "updated_at"])
    elif mapped == SubscriptionFinancialStatus.CANCELADO:
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.payment_status = PaymentStatus.CANCELLED
        subscription.cancelled_at = timezone.now()
    else:
        subscription.payment_status = PaymentStatus.PENDING
        if not subscription.past_due_since:
            subscription.past_due_since = timezone.localdate()
            if subscription.user:
                _notify_subscription_event(
                    user=subscription.user,
                    reason="subscription_overdue",
                    nome=(
                        subscription.user.first_name
                        or subscription.user.full_name
                        or subscription.user.username
                        or ""
                    ),
                    plano=(subscription.plan.name if subscription.plan else ""),
                )

    if previous == SubscriptionFinancialStatus.CANCELAMENTO_AGENDADO and mapped == SubscriptionFinancialStatus.CANCELADO:
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = timezone.now()

    subscription.save()

    if (
        mapped == SubscriptionFinancialStatus.REGULAR
        and previous != SubscriptionFinancialStatus.REGULAR
        and subscription.user
    ):
        _notify_subscription_event(
            user=subscription.user,
            reason="subscription_activated",
            nome=(
                subscription.user.first_name
                or subscription.user.full_name
                or subscription.user.username
                or ""
            ),
            plano=(subscription.plan.name if subscription.plan else ""),
        )

    return subscription


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
    subscription.financial_status = SubscriptionFinancialStatus.REGULAR
    subscription.current_period_start = tx.billing_month
    subscription.current_period_end = subscription.end_date
    subscription.billing_anchor_date = subscription.billing_anchor_date or tx.billing_month
    subscription.past_due_since = None
    subscription.cancel_at_period_end = False
    subscription.save()

    tx.user.plan = tx.plan
    tx.user.save(update_fields=["plan", "updated_at"])

    _notify_subscription_event(
        user=tx.user,
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

    subscription, _ = Subscription.objects.get_or_create(user=tx.user)
    subscription.payment_status = tx.status
    if subscription.financial_status == SubscriptionFinancialStatus.REGULAR:
        subscription.financial_status = SubscriptionFinancialStatus.INADIMPLENTE
    if not subscription.past_due_since:
        subscription.past_due_since = timezone.localdate()
    subscription.save(update_fields=["payment_status", "financial_status", "past_due_since", "updated_at"])
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
        if not subscription.past_due_since:
            subscription.past_due_since = tx.grace_limit_date

        tolerance_days = int(getattr(settings, "SUBSCRIPTIONS_PAST_DUE_TOLERANCE_DAYS", 5) or 5)
        tolerance_deadline = subscription.past_due_since + timedelta(days=tolerance_days)
        if check_date <= tolerance_deadline:
            if subscription.financial_status != SubscriptionFinancialStatus.INADIMPLENTE:
                subscription.financial_status = SubscriptionFinancialStatus.INADIMPLENTE
                subscription.save(update_fields=["financial_status", "past_due_since", "updated_at"])
            continue

        subscription.status = SubscriptionStatus.EXPIRED
        subscription.payment_status = tx.status
        subscription.plan = free_plan
        subscription.financial_status = SubscriptionFinancialStatus.SUSPENSO
        subscription.save()

        if user.plan_id != free_plan.id:
            user.plan = free_plan
            user.save(update_fields=["plan", "updated_at"])
            updated += 1

        _notify_subscription_event(
            user=user,
            reason="plan_downgraded_cutoff",
            nome=(user.first_name or user.full_name or user.username or ""),
        )
    return updated
