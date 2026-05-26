from django.core.management.base import BaseCommand

from base.accounts.models import Subscription, SubscriptionFinancialStatus
from base.payments.services.billing import apply_preapproval_status
from base.payments.services.mercadopago_client import get_preapproval


class Command(BaseCommand):
    help = "Reconcilia status de assinaturas recorrentes no Mercado Pago."

    def handle(self, *args, **options):
        subscriptions = Subscription.objects.filter(
            mp_subscription_id__isnull=False,
        ).exclude(mp_subscription_id="").filter(
            financial_status__in=[
                SubscriptionFinancialStatus.REGULAR,
                SubscriptionFinancialStatus.INADIMPLENTE,
                SubscriptionFinancialStatus.CANCELAMENTO_AGENDADO,
            ]
        )

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
                        f"Falha ao reconciliar assinatura {subscription.id}: {exc}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciliacao concluida: processadas={processed}, falhas={failed}"
            )
        )
