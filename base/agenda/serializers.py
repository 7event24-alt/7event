from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from django.utils import timezone
from datetime import datetime
from calendar import monthrange

from base.jobs.models import Job


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
        if obj.start_date:
            return str(obj.start_date)
        return None
    
    def get_end(self, obj):
        if obj.end_date:
            return str(obj.end_date)
        return None

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
            all_events.append(job_event)

            # Se tem visita técnica, gerar evento separado (apenas data, sem hora)
            if job.has_technical_visit and job.technical_visit_date:
                visit_date = str(job.technical_visit_date)

                all_events.append({
                    "id": f"visit_{job.id}",
                    "title": f"VT: {job.title}",
                    "start": visit_date,
                    "end": visit_date,
                    "backgroundColor": "#fbbf24",  # yellow-400 (amarelinho)
                    "borderColor": "#f59e0b",      # yellow-500
                    "textColor": "#ffffff",
                    "extendedProps": {
                        "type": "technical_visit",
                        "job_id": job.id
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
                date__lte=last_day.date()
            ).order_by("time")

            for task in tasks:
                start_dt = f"{task.date}T{task.time.strftime('%H:%M:%S') if task.time else '00:00:00'}"
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
                        "is_completed": task.is_completed
                    }
                })

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
            all_events.append(job_event)

            # Se tem visita técnica, gerar evento separado (apenas data, sem hora)
            if job.has_technical_visit and job.technical_visit_date:
                visit_date = str(job.technical_visit_date)

                all_events.append({
                    "id": f"visit_{job.id}",
                    "title": f"VT: {job.title}",
                    "start": visit_date,
                    "end": visit_date,
                    "backgroundColor": "#fbbf24",  # yellow-400 (amarelinho)
                    "borderColor": "#f59e0b",      # yellow-500
                    "textColor": "#ffffff",
                    "extendedProps": {
                        "type": "technical_visit",
                        "job_id": job.id
                    }
                })

        # PersonalTasks do usuário
        try:
            from base.accounts.models import PersonalTask

            tasks = PersonalTask.objects.filter(
                user=user,
                date__gte=first_day.date(),
                date__lte=last_day.date()
            ).order_by("time")

            for task in tasks:
                start_dt = f"{task.date}T{task.time.strftime('%H:%M:%S') if task.time else '00:00:00'}"
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
                        "is_completed": task.is_completed
                    }
                })

        except Exception as e:
            pass

        return Response(all_events)
