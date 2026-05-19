from django.core.management.base import BaseCommand

from base.accounts.models import PlanType, User
from base.payments.services.billing import get_or_create_monthly_transaction


class Command(BaseCommand):
    help = "Gera cobrancas mensais para usuarios em planos pagos."

    def handle(self, *args, **options):
        users = User.objects.select_related("plan").filter(is_active=True).exclude(plan__type=PlanType.FREE)
        created_or_found = 0
        for user in users:
            if not user.plan:
                continue
            get_or_create_monthly_transaction(user, user.plan)
            created_or_found += 1

        self.stdout.write(self.style.SUCCESS(f"Cobrancas verificadas: {created_or_found}"))
