from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange

from base.jobs.models import Job
from base.accounts.models import PersonalAgendaEvent, PersonalAgendaStatus


def _last_day_of_month(year, month):
    return monthrange(year, month)[1]


def _add_months(base_date, months_to_add):
    month_index = base_date.month - 1 + months_to_add
    year = base_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base_date.day, _last_day_of_month(year, month))
    return base_date.replace(year=year, month=month, day=day)


def _iter_occurrence_dates(event, range_start, range_end):
    recurrence_end = event.recurrence_until or range_end
    effective_end = min(recurrence_end, range_end)
    if event.date > effective_end:
        return

    if event.recurrence == "none":
        if range_start <= event.date <= effective_end:
            yield event.date
        return

    current = event.date
    while current <= effective_end:
        if current >= range_start:
            yield current

        if event.recurrence == "daily":
            current += timedelta(days=1)
        elif event.recurrence == "weekly":
            current += timedelta(days=7)
        elif event.recurrence == "monthly":
            current = _add_months(current, 1)
        elif event.recurrence == "yearly":
            current = _add_months(current, 12)
        else:
            break


class AgendaEventSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    textColor = serializers.SerializerMethodField()
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "client_name",
            "start",
            "end",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "location",
            "status",
            "textColor",
        ]

    def get_start(self, obj):
        if not obj.start_date:
            return None
        if obj.start_time:
            return f"{obj.start_date.isoformat()}T{obj.start_time.strftime('%H:%M:%S')}"
        return obj.start_date.isoformat()

    def get_end(self, obj):
        if not obj.end_date:
            return None
        if obj.end_time:
            return f"{obj.end_date.isoformat()}T{obj.end_time.strftime('%H:%M:%S')}"
        return (obj.end_date + timedelta(days=1)).isoformat()

    def get_textColor(self, obj):
        return "#ffffff"


class AgendaEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_superuser = user.is_superuser

        # Jobs
        if is_superuser:
            jobs = Job.objects.filter(is_active=True).select_related("client")
        else:
            jobs = Job.objects.filter(created_by=user, is_active=True).select_related("client")

        jobs = jobs.order_by("start_date")

        all_events = []

        # Gerar eventos para cada job
        for job in jobs:
            # Evento do Job normal
            job_serializer = AgendaEventSerializer(job)
            job_event = job_serializer.data
            job_event["backgroundColor"] = "#1e3a5f"  # blue-900
            job_event["borderColor"] = "#1e3a5f"
            job_event["extendedProps"] = {
                "type": "job",
                "filter_status": job.status,
                "status": job.status,
            }
            all_events.append(job_event)

            # Se tem visita técnica, gerar evento separado
            if job.has_technical_visit and job.technical_visit_date:
                visit_start = str(job.technical_visit_date)
                if job.technical_visit_time:
                    visit_start = f"{job.technical_visit_date.isoformat()}T{job.technical_visit_time.strftime('%H:%M:%S')}"

                all_events.append({
                    "id": f"visit_{job.id}",
                    "title": f"VT: {job.title}",
                    "start": visit_start,
                    "end": visit_start,
                    "backgroundColor": "#fbbf24",  # yellow-400 (amarelinho)
                    "borderColor": "#f59e0b",      # yellow-500
                    "textColor": "#ffffff",
                    "extendedProps": {
                        "type": "technical_visit",
                        "job_id": job.id,
                        "filter_status": job.status,
                        "status": job.status,
                    }
                })

        # PersonalTasks do usuário
        try:
            from base.accounts.models import PersonalTask

            year = int(request.query_params.get("year", timezone.now().year))
            month = int(request.query_params.get("month", timezone.now().month))
            first_day = datetime(year, month, 1)
            last_day = datetime(year, month, monthrange(year, month)[1])

            tasks = PersonalTask.objects.filter(
                user=user,
                date__gte=first_day.date(),
                date__lte=last_day.date(),
                is_completed=False,
            ).order_by("time")

            for task in tasks:
                if task.time:
                    start_dt = f"{task.date}T{task.time.strftime('%H:%M:%S')}"
                else:
                    start_dt = str(task.date)
                all_events.append({
                    "id": f"task_{task.id}",
                    "title": task.title,
                    "start": start_dt,
                    "end": start_dt,
                    "backgroundColor": "#60a5fa",  # blue-400 (baby blue)
                    "borderColor": "#3b82f6",     # blue-500
                    "textColor": "#ffffff",
                    "extendedProps": {
                        "type": "task",
                        "is_completed": task.is_completed,
                        "filter_status": "completed" if task.is_completed else "pending",
                    }
                })

            personal_agenda_events = PersonalAgendaEvent.objects.filter(
                user=user,
                status=PersonalAgendaStatus.PENDING,
            ).order_by("date", "start_time")

            for personal_event in personal_agenda_events:
                for occurrence_date in _iter_occurrence_dates(personal_event, first_day.date(), last_day.date()):
                    is_all_day = (
                        personal_event.start_time.strftime('%H:%M') == '00:00'
                        and personal_event.end_time.strftime('%H:%M') == '23:59'
                    )
                    start_dt = str(occurrence_date) if is_all_day else f"{occurrence_date}T{personal_event.start_time.strftime('%H:%M:%S')}"
                    end_dt = str(occurrence_date + timedelta(days=1)) if is_all_day else f"{occurrence_date}T{personal_event.end_time.strftime('%H:%M:%S')}"
                    payload = {
                        "id": f"personal_agenda_{personal_event.id}_{occurrence_date}",
                        "title": personal_event.title,
                        "start": start_dt,
                        "end": end_dt,
                        "backgroundColor": "#8b5cf6",
                        "borderColor": "#7c3aed",
                        "textColor": "#ffffff",
                        "extendedProps": {
                            "type": "personal_agenda",
                            "status": personal_event.status,
                            "filter_status": personal_event.status,
                        }
                    }
                    if is_all_day:
                        payload["allDay"] = True
                    all_events.append(payload)

        except Exception as e:
            pass

        return Response(all_events)


class AgendaViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user
        is_superuser = user.is_superuser
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))

        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, monthrange(year, month)[1])

        if is_superuser:
            jobs = Job.objects.filter(
                is_active=True,
                start_date__gte=first_day.date(),
                start_date__lte=last_day.date()
            ).select_related("client")
        else:
            jobs = Job.objects.filter(
                created_by=user,
                is_active=True,
                start_date__gte=first_day.date(),
                start_date__lte=last_day.date()
            ).select_related("client")

        all_events = []

        for job in jobs:
            # Evento do Job normal
            job_serializer = AgendaEventSerializer(job)
            job_event = job_serializer.data
            job_event["backgroundColor"] = "#1e3a5f"  # blue-900
            job_event["borderColor"] = "#1e3a5f"
            job_event["extendedProps"] = {
                "type": "job",
                "filter_status": job.status,
                "status": job.status,
            }
            all_events.append(job_event)

            # Se tem visita técnica, gerar evento separado
            if job.has_technical_visit and job.technical_visit_date:
                visit_start = str(job.technical_visit_date)
                if job.technical_visit_time:
                    visit_start = f"{job.technical_visit_date.isoformat()}T{job.technical_visit_time.strftime('%H:%M:%S')}"

                all_events.append({
                    "id": f"visit_{job.id}",
                    "title": f"VT: {job.title}",
                    "start": visit_start,
                    "end": visit_start,
                    "backgroundColor": "#fbbf24",  # yellow-400 (amarelinho)
                    "borderColor": "#f59e0b",      # yellow-500
                    "textColor": "#ffffff",
                    "extendedProps": {
                        "type": "technical_visit",
                        "job_id": job.id,
                        "filter_status": job.status,
                        "status": job.status,
                    }
                })

        # PersonalTasks do usuário
        try:
            from base.accounts.models import PersonalTask

            tasks = PersonalTask.objects.filter(
                user=user,
                date__gte=first_day.date(),
                date__lte=last_day.date(),
                is_completed=False,
            ).order_by("time")

            for task in tasks:
                if task.time:
                    start_dt = f"{task.date}T{task.time.strftime('%H:%M:%S')}"
                else:
                    start_dt = str(task.date)
                all_events.append({
                    "id": f"task_{task.id}",
                    "title": task.title,
                    "start": start_dt,
                    "end": start_dt,
                    "backgroundColor": "#60a5fa",  # blue-400 (baby blue)
                    "borderColor": "#3b82f6",     # blue-500
                    "textColor": "#ffffff",
                    "extendedProps": {
                        "type": "task",
                        "is_completed": task.is_completed,
                        "filter_status": "completed" if task.is_completed else "pending",
                    }
                })

            personal_agenda_events = PersonalAgendaEvent.objects.filter(
                user=user,
                status=PersonalAgendaStatus.PENDING,
            ).order_by("date", "start_time")

            for personal_event in personal_agenda_events:
                for occurrence_date in _iter_occurrence_dates(personal_event, first_day.date(), last_day.date()):
                    is_all_day = (
                        personal_event.start_time.strftime('%H:%M') == '00:00'
                        and personal_event.end_time.strftime('%H:%M') == '23:59'
                    )
                    start_dt = str(occurrence_date) if is_all_day else f"{occurrence_date}T{personal_event.start_time.strftime('%H:%M:%S')}"
                    end_dt = str(occurrence_date + timedelta(days=1)) if is_all_day else f"{occurrence_date}T{personal_event.end_time.strftime('%H:%M:%S')}"
                    payload = {
                        "id": f"personal_agenda_{personal_event.id}_{occurrence_date}",
                        "title": personal_event.title,
                        "start": start_dt,
                        "end": end_dt,
                        "backgroundColor": "#8b5cf6",
                        "borderColor": "#7c3aed",
                        "textColor": "#ffffff",
                        "extendedProps": {
                            "type": "personal_agenda",
                            "status": personal_event.status,
                            "filter_status": personal_event.status,
                        }
                    }
                    if is_all_day:
                        payload["allDay"] = True
                    all_events.append(payload)

        except Exception as e:
            pass

        return Response(all_events)
