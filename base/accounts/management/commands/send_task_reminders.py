from django.core.management.base import BaseCommand
from base.accounts.services.reminders import run_system_reminders


class Command(BaseCommand):
    help = "Envia lembretes de tarefas, eventos pessoais e trabalhos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--task-lead-minutes",
            type=int,
            default=60,
            help="Minutos de antecedencia para tarefas com horario (padrao: 60).",
        )
        parser.add_argument(
            "--event-lead-minutes",
            type=int,
            default=1440,
            help="Minutos de antecedencia para eventos pessoais com horario (padrao: 1440).",
        )
        parser.add_argument(
            "--job-lead-minutes",
            type=int,
            default=1440,
            help="Minutos de antecedencia para trabalhos com horario (padrao: 1440).",
        )
        parser.add_argument(
            "--time-tolerance-minutes",
            type=int,
            default=5,
            help="Tolerancia para lembretes com horario definido (padrao: 5).",
        )
        parser.add_argument(
            "--slot-tolerance-minutes",
            type=int,
            default=10,
            help="Tolerancia para slots 10h/16h sem horario (padrao: 10).",
        )

    def handle(self, *args, **options):
        result = run_system_reminders(
            task_lead_minutes=max(1, int(options.get("task_lead_minutes", 60))),
            event_lead_minutes=max(1, int(options.get("event_lead_minutes", 1440))),
            job_lead_minutes=max(1, int(options.get("job_lead_minutes", 1440))),
            time_tolerance_minutes=max(0, int(options.get("time_tolerance_minutes", 5))),
            slot_tolerance_minutes=max(0, int(options.get("slot_tolerance_minutes", 10))),
        )

        self.stdout.write(
            self.style.SUCCESS(
                "System reminders: "
                f"tasks(enviadas={result['tasks']['sent']},falhas={result['tasks']['failed']}) "
                f"events(enviadas={result['events']['sent']},falhas={result['events']['failed']}) "
                f"jobs(enviadas={result['jobs']['sent']},falhas={result['jobs']['failed']}) "
                f"total(enviadas={result['total']['sent']},falhas={result['total']['failed']})"
            )
        )
