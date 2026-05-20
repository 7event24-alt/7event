from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.utils import timezone

from base.accounts.models import (
    PersonalTask,
    PersonalTaskReminderDispatch,
    PersonalTaskReminderType,
)
from base.core.n8n import send_whatsapp_by_reason


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
        now_local = timezone.localtime()
        lead_minutes = max(1, int(options.get("lead_minutes", 60)))
        tolerance_minutes = max(0, int(options.get("tolerance_minutes", 5)))
        target = now_local + timedelta(minutes=lead_minutes)

        today_tasks = PersonalTask.objects.select_related("user").filter(
            is_completed=False,
            date=target.date(),
            time__isnull=False,
        )

        checked = 0
        eligible = 0
        sent = 0
        skipped = 0
        failed = 0

        for task in today_tasks:
            checked += 1

            task_dt = timezone.make_aware(
                datetime.combine(task.date, task.time),
                timezone.get_current_timezone(),
            )
            diff_minutes = (task_dt - now_local).total_seconds() / 60

            min_window = lead_minutes - tolerance_minutes
            max_window = lead_minutes + tolerance_minutes
            if diff_minutes < min_window or diff_minutes > max_window:
                continue
            eligible += 1

            if not task.user.phone:
                skipped += 1
                continue

            try:
                PersonalTaskReminderDispatch.objects.create(
                    task=task,
                    reminder_type=PersonalTaskReminderType.ONE_HOUR_BEFORE,
                )
            except IntegrityError:
                # Ja enviado anteriormente
                skipped += 1
                continue

            ok, _ = send_whatsapp_by_reason(
                phone=task.user.phone,
                reason="task_reminder_1h",
                nome=(task.user.first_name or task.user.full_name or task.user.username or ""),
                titulo=task.title,
                data=task.date.strftime("%d/%m/%Y"),
                hora=task.time.strftime("%H:%M"),
            )

            if ok:
                sent += 1
            else:
                failed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Task reminders: analisadas={checked} elegiveis={eligible} enviadas={sent} puladas={skipped} falhas={failed}"
            )
        )
