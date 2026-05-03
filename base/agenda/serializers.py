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
    status_color = serializers.SerializerMethodField()
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
            "status_color",
            "textColor",
            "event_type",
        ]

    def get_status_color(self, obj):
        colors = {
            "pending": "#f59e0b",
            "confirmed": "#10b981",
            "completed": "#6366f1",
            "cancelled": "#ef4444",
        }
        return colors.get(obj.status, "#1e3a5f")

    def get_textColor(self, obj):
        return "#ffffff"

    def get_start(self, obj):
        if obj.start_date:
            date_str = str(obj.start_date)
            if obj.start_time:
                time_str = str(obj.start_time)
                if len(time_str) == 5:
                    return f"{date_str}T{time_str}:00"
                return f"{date_str}T{time_str}"
            return date_str
        return None

    def get_end(self, obj):
        if obj.end_date:
            date_str = str(obj.end_date)
            if obj.end_time:
                time_str = str(obj.end_time)
                if len(time_str) == 5:
                    return f"{date_str}T{time_str}:00"
                return f"{date_str}T{time_str}"
            return date_str
        return None


class AgendaEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_superuser = user.is_superuser

        # Jobs (código existente)
        if is_superuser:
            jobs = Job.objects.filter(is_active=True).select_related("client")
        else:
            jobs = Job.objects.filter(created_by=user, is_active=True).select_related("client")

        jobs = jobs.order_by("start_date")
        job_serializer = AgendaEventSerializer(jobs, many=True)
        job_events = job_serializer.data

        # PersonalTasks do usuário
        try:
            from base.accounts.models import PersonalTask
            from datetime import datetime
            from calendar import monthrange
            from django.utils import timezone

            year = int(request.query_params.get("year", timezone.now().year))
            month = int(request.query_params.get("month", timezone.now().month))
            first_day = datetime(year, month, 1)
            last_day = datetime(year, month, monthrange(year, month)[1])

            tasks = PersonalTask.objects.filter(
                user=user,
                date__gte=first_day.date(),
                date__lte=last_day.date()
            ).order_by("time")

            task_events = []
            for task in tasks:
                start_dt = f"{task.date}T{task.time.strftime('%H:%M:%S') if task.time else '00:00:00'}"
                task_events.append({
                    "id": f"task_{task.id}",
                    "title": task.title,
                    "start": start_dt,
                    "end": start_dt,  # FullCalendar exige end
                    "backgroundColor": "#bfdbfe",  # bg-blue-200
                    "borderColor": "#93c5fd",     # border blue-300
                    "textColor": "#1e40af",        # text-blue-800
                    "extendedProps": {
                        "type": "task",
                        "is_completed": task.is_completed
                    }
                })

            # Unificar eventos
            all_events = job_events + task_events
            return Response(all_events)

        except Exception as e:
            # Se der erro, retorna apenas jobs (compatibilidade)
            return Response(job_events)


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

        job_serializer = AgendaEventSerializer(jobs, many=True)
        job_events = job_serializer.data

        # PersonalTasks do usuário
        try:
            from base.accounts.models import PersonalTask

            tasks = PersonalTask.objects.filter(
                user=user,
                date__gte=first_day.date(),
                date__lte=last_day.date()
            ).order_by("time")

            task_events = []
            for task in tasks:
                start_dt = f"{task.date}T{task.time.strftime('%H:%M:%S') if task.time else '00:00:00'}"
                task_events.append({
                    "id": f"task_{task.id}",
                    "title": task.title,
                    "start": start_dt,
                    "end": start_dt,
                    "backgroundColor": "#bfdbfe",  # bg-blue-200
                    "borderColor": "#93c5fd",     # border blue-300
                    "textColor": "#1e40af",        # text-blue-800
                    "extendedProps": {
                        "type": "task",
                        "is_completed": task.is_completed
                    }
                })

            all_events = job_events + task_events
            return Response(all_events)

        except Exception as e:
            # Se der erro, retorna apenas jobs
            return Response(job_events)