from datetime import datetime, timedelta

from django.db import IntegrityError
from django.utils import timezone

from base.accounts.models import (
    PersonalAgendaEvent,
    PersonalAgendaStatus,
    PersonalTask,
    SystemReminderDispatch,
    SystemReminderEntityType,
)
from base.core.n8n import send_whatsapp_by_reason
from base.jobs.models import Job, JobStatus


def _event_time_or_default(value):
    return value.strftime("%H:%M") if value else "Não Definido"


def _event_location_or_default(value):
    return value if value else "Não Definido"


def _user_name(user):
    return user.first_name or user.full_name or user.username or ""


def _dispatch_once(entity_type, entity_id, reminder_type, slot_date, slot_label):
    try:
        SystemReminderDispatch.objects.create(
            entity_type=entity_type,
            entity_id=entity_id,
            reminder_type=reminder_type,
            slot_date=slot_date,
            slot_label=slot_label,
        )
        return True
    except IntegrityError:
        return False


def _within_window(diff_minutes, lead, tolerance):
    return (lead - tolerance) <= diff_minutes <= (lead + tolerance)


def _check_slot(now_local, target_date, slot_hour, slot_tolerance_minutes):
    slot_dt = timezone.make_aware(
        datetime.combine(target_date, datetime.min.time()).replace(hour=slot_hour),
        timezone.get_current_timezone(),
    )
    diff = (slot_dt - now_local).total_seconds() / 60
    return abs(diff) <= slot_tolerance_minutes


def run_system_reminders(
    task_lead_minutes=60,
    event_lead_minutes=1440,
    job_lead_minutes=1440,
    time_tolerance_minutes=5,
    slot_tolerance_minutes=10,
):
    now_local = timezone.localtime()

    result = {
        "tasks": {"checked": 0, "eligible": 0, "sent": 0, "skipped": 0, "failed": 0},
        "events": {"checked": 0, "eligible": 0, "sent": 0, "skipped": 0, "failed": 0},
        "jobs": {"checked": 0, "eligible": 0, "sent": 0, "skipped": 0, "failed": 0},
    }

    # Tasks: 1h antes com horario; sem horario no proprio dia as 10h/16h
    task_target = (now_local + timedelta(minutes=max(1, int(task_lead_minutes)))).date()
    tasks = PersonalTask.objects.select_related("user").filter(is_completed=False, date=task_target)
    for task in tasks:
        result["tasks"]["checked"] += 1
        user = task.user
        if not user.phone:
            result["tasks"]["skipped"] += 1
            continue

        reminder_type = "task_1h_before" if task.time else "task_no_time_day_slot"
        slot_label = "exact"
        eligible = False

        if task.time:
            task_dt = timezone.make_aware(
                datetime.combine(task.date, task.time),
                timezone.get_current_timezone(),
            )
            diff = (task_dt - now_local).total_seconds() / 60
            eligible = _within_window(diff, max(1, int(task_lead_minutes)), max(0, int(time_tolerance_minutes)))
        else:
            if _check_slot(now_local, task.date, 10, max(0, int(slot_tolerance_minutes))):
                eligible = True
                slot_label = "morning"
            elif _check_slot(now_local, task.date, 16, max(0, int(slot_tolerance_minutes))):
                if SystemReminderDispatch.objects.filter(
                    entity_type=SystemReminderEntityType.TASK,
                    entity_id=task.id,
                    reminder_type=reminder_type,
                    slot_date=task.date,
                    slot_label="morning",
                ).exists():
                    result["tasks"]["skipped"] += 1
                    continue
                eligible = True
                slot_label = "afternoon"

        if not eligible:
            continue
        result["tasks"]["eligible"] += 1

        if not _dispatch_once(SystemReminderEntityType.TASK, task.id, reminder_type, task.date, slot_label):
            result["tasks"]["skipped"] += 1
            continue

        ok, _ = send_whatsapp_by_reason(
            phone=user.phone,
            reason="task_reminder_1h",
            user=user,
            nome=_user_name(user),
            titulo=task.title,
            data=task.date.strftime("%d/%m/%Y"),
            hora=_event_time_or_default(task.time),
            local="Não Definido",
        )
        result["tasks"]["sent" if ok else "failed"] += 1

    # Personal agenda events: 1 dia antes; sem horario usa 10h/16h no dia anterior
    event_target = (now_local + timedelta(minutes=max(1, int(event_lead_minutes)))).date()
    events = PersonalAgendaEvent.objects.select_related("user").filter(
        status=PersonalAgendaStatus.PENDING,
        date=event_target,
    )
    for event in events:
        result["events"]["checked"] += 1
        user = event.user
        if not user.phone:
            result["events"]["skipped"] += 1
            continue

        has_time = bool(event.start_time)
        reminder_type = "event_1d_before" if has_time else "event_no_time_day_before_slot"
        reminder_date = event.date - timedelta(days=1)
        slot_label = "exact"
        eligible = False

        if has_time:
            event_dt = timezone.make_aware(
                datetime.combine(event.date, event.start_time),
                timezone.get_current_timezone(),
            )
            diff = (event_dt - now_local).total_seconds() / 60
            eligible = _within_window(diff, max(1, int(event_lead_minutes)), max(0, int(time_tolerance_minutes)))
        else:
            if now_local.date() != reminder_date:
                continue
            if _check_slot(now_local, reminder_date, 10, max(0, int(slot_tolerance_minutes))):
                eligible = True
                slot_label = "morning"
            elif _check_slot(now_local, reminder_date, 16, max(0, int(slot_tolerance_minutes))):
                if SystemReminderDispatch.objects.filter(
                    entity_type=SystemReminderEntityType.AGENDA_EVENT,
                    entity_id=event.id,
                    reminder_type=reminder_type,
                    slot_date=reminder_date,
                    slot_label="morning",
                ).exists():
                    result["events"]["skipped"] += 1
                    continue
                eligible = True
                slot_label = "afternoon"

        if not eligible:
            continue
        result["events"]["eligible"] += 1

        if not _dispatch_once(SystemReminderEntityType.AGENDA_EVENT, event.id, reminder_type, reminder_date, slot_label):
            result["events"]["skipped"] += 1
            continue

        ok, _ = send_whatsapp_by_reason(
            phone=user.phone,
            reason="event_reminder_1d",
            user=user,
            nome=_user_name(user),
            titulo=event.title,
            data=event.date.strftime("%d/%m/%Y"),
            hora=_event_time_or_default(event.start_time),
            local=_event_location_or_default(event.location),
        )
        result["events"]["sent" if ok else "failed"] += 1

    # Jobs: 1 dia antes; sem horario usa 10h/16h no dia anterior
    job_target = (now_local + timedelta(minutes=max(1, int(job_lead_minutes)))).date()
    jobs = Job.objects.select_related("created_by", "client").filter(
        is_active=True,
        start_date=job_target,
    ).exclude(status__in=[JobStatus.CANCELLED, JobStatus.COMPLETED])

    for job in jobs:
        result["jobs"]["checked"] += 1
        user = job.created_by
        if not user or not user.phone:
            result["jobs"]["skipped"] += 1
            continue

        has_time = bool(job.start_time)
        reminder_type = "job_1d_before" if has_time else "job_no_time_day_before_slot"
        reminder_date = job.start_date - timedelta(days=1)
        slot_label = "exact"
        eligible = False

        if has_time:
            job_dt = timezone.make_aware(
                datetime.combine(job.start_date, job.start_time),
                timezone.get_current_timezone(),
            )
            diff = (job_dt - now_local).total_seconds() / 60
            eligible = _within_window(diff, max(1, int(job_lead_minutes)), max(0, int(time_tolerance_minutes)))
        else:
            if now_local.date() != reminder_date:
                continue
            if _check_slot(now_local, reminder_date, 10, max(0, int(slot_tolerance_minutes))):
                eligible = True
                slot_label = "morning"
            elif _check_slot(now_local, reminder_date, 16, max(0, int(slot_tolerance_minutes))):
                if SystemReminderDispatch.objects.filter(
                    entity_type=SystemReminderEntityType.JOB,
                    entity_id=job.id,
                    reminder_type=reminder_type,
                    slot_date=reminder_date,
                    slot_label="morning",
                ).exists():
                    result["jobs"]["skipped"] += 1
                    continue
                eligible = True
                slot_label = "afternoon"

        if not eligible:
            continue
        result["jobs"]["eligible"] += 1

        if not _dispatch_once(SystemReminderEntityType.JOB, job.id, reminder_type, reminder_date, slot_label):
            result["jobs"]["skipped"] += 1
            continue

        ok, _ = send_whatsapp_by_reason(
            phone=user.phone,
            reason="job_reminder_1d",
            user=user,
            nome=_user_name(user),
            titulo=job.title,
            data=job.start_date.strftime("%d/%m/%Y"),
            hora=_event_time_or_default(job.start_time),
            local=_event_location_or_default(job.location),
        )
        result["jobs"]["sent" if ok else "failed"] += 1

    result["total"] = {
        "sent": result["tasks"]["sent"] + result["events"]["sent"] + result["jobs"]["sent"],
        "failed": result["tasks"]["failed"] + result["events"]["failed"] + result["jobs"]["failed"],
    }
    return result
