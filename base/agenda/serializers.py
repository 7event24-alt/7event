from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
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
        company = request.user.account
        user = request.user
        is_superuser = user.is_superuser

        jobs = Job.objects.filter(account=company).select_related("client")

        if not is_superuser:
            from django.db.models import Q

            jobs = jobs.filter(Q(user=user) | Q(workers=user))

        user_filter = request.GET.get("user", "")
        if is_superuser and user_filter:
            jobs = jobs.filter(user_id=user_filter)

        jobs = jobs.order_by("start_date")
        serializer = AgendaEventSerializer(jobs, many=True)
        return Response(serializer.data)


class AgendaViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))

        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, monthrange(year, month)[1])

        jobs = Job.objects.filter(
            user=user, start_date__gte=first_day.date(), start_date__lte=last_day.date()
        ).select_related("client")

        serializer = AgendaEventSerializer(jobs, many=True)
        return Response(serializer.data)


class AdminMetricsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    blocked_users = serializers.IntegerField()
    trial_users = serializers.IntegerField()
    monthly_users = serializers.IntegerField()
    annual_users = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    inadimplente_users = serializers.IntegerField()
    total_clients = serializers.IntegerField()
    total_jobs = serializers.IntegerField()
    total_expenses = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
