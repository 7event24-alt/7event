from django.core.management.base import BaseCommand
from base.accounts.services.task_reminders import run_task_reminders


class Command(BaseCommand):
    help = "Envia lembretes de tarefa pessoal 1 hora antes do horario."

    def add_arguments(self, parser):
        parser.add_argument(
            "--lead-minutes",
            type=int,
            default=60,
            help="Minutos de antecedencia para disparo do lembrete (padrao: 60).",
        )
        parser.add_argument(
            "--tolerance-minutes",
            type=int,
            default=5,
            help="Tolerancia em minutos para janela do cron (padrao: 5).",
        )

    def handle(self, *args, **options):
        lead_minutes = max(1, int(options.get("lead_minutes", 60)))
        tolerance_minutes = max(0, int(options.get("tolerance_minutes", 5)))
        result = run_task_reminders(
            lead_minutes=lead_minutes,
            tolerance_minutes=tolerance_minutes,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Task reminders: "
                f"analisadas={result['checked']} "
                f"elegiveis={result['eligible']} "
                f"enviadas={result['sent']} "
                f"puladas={result['skipped']} "
                f"falhas={result['failed']}"
            )
        )
