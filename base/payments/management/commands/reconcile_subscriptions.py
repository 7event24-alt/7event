from django.conf import settings
from django.core.management.base import BaseCommand

from base.accounts.models import Subscription, SubscriptionFinancialStatus
from base.payments.services.billing import (
    apply_preapproval_status,
    handle_stripe_subscription_updated,
)
from base.payments.services.mercadopago_client import get_preapproval
from base.payments.services.stripe_client import retrieve_subscription as stripe_retrieve_subscription


class Command(BaseCommand):
    help = "Reconcilia status de assinaturas recorrentes."

    def handle(self, *args, **options):
        subscriptions = Subscription.objects.filter(
            financial_status__in=[
                SubscriptionFinancialStatus.REGULAR,
                SubscriptionFinancialStatus.INADIMPLENTE,
                SubscriptionFinancialStatus.CANCELAMENTO_AGENDADO,
            ]
        ).filter(
            mp_subscription_id__isnull=False,
        ).exclude(mp_subscription_id="")

        stripe_subs = Subscription.objects.filter(
            financial_status__in=[
                SubscriptionFinancialStatus.REGULAR,
                SubscriptionFinancialStatus.INADIMPLENTE,
                SubscriptionFinancialStatus.CANCELAMENTO_AGENDADO,
            ]
        ).filter(
            stripe_subscription_id__isnull=False,
        ).exclude(stripe_subscription_id="")

        processed = 0
        failed = 0

        for subscription in subscriptions:
            try:
                payload = get_preapproval(subscription.mp_subscription_id)
                apply_preapproval_status(subscription, payload)
                processed += 1
            except Exception as exc:
                failed += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Falha ao reconciliar MP assinatura {subscription.id}: {exc}"
                    )
                )

        for subscription in stripe_subs:
            try:
                payload = stripe_retrieve_subscription(subscription.stripe_subscription_id)
                handle_stripe_subscription_updated(payload)
                processed += 1
            except Exception as exc:
                failed += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Falha ao reconciliar Stripe assinatura {subscription.id}: {exc}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciliacao concluida: processadas={processed}, falhas={failed}"
            )
        )
