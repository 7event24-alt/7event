from django.core.management.base import BaseCommand

from base.payments.services.billing import downgrade_to_free_if_overdue


class Command(BaseCommand):
    help = "Aplica downgrade para plano FREE quando a cobranca passou do corte sem aprovacao."

    def handle(self, *args, **options):
        updated = downgrade_to_free_if_overdue()
        self.stdout.write(self.style.SUCCESS(f"Downgrades aplicados: {updated}"))
