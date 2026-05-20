from datetime import datetime, timedelta

from django.db import IntegrityError
from django.utils import timezone

from base.accounts.models import (
    PersonalTask,
    PersonalTaskReminderDispatch,
    PersonalTaskReminderType,
)
from base.core.n8n import send_whatsapp_by_reason


def run_task_reminders(lead_minutes=60, tolerance_minutes=5):
    now_local = timezone.localtime()
    lead_minutes = max(1, int(lead_minutes))
    tolerance_minutes = max(0, int(tolerance_minutes))
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

    return {
        "checked": checked,
        "eligible": eligible,
        "sent": sent,
        "skipped": skipped,
        "failed": failed,
        "lead_minutes": lead_minutes,
        "tolerance_minutes": tolerance_minutes,
    }
