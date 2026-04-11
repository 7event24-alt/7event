from rest_framework import serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import viewsets
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth import get_user_model

from base.clients.models import Client
from base.jobs.models import Job
from base.expenses.models import Expense

User = get_user_model()


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


class AdminPanelViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request):
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        blocked_users = User.objects.filter(is_blocked=True).count()

        trial_users = User.objects.filter(plan="trial").count()
        monthly_users = User.objects.filter(plan="monthly").count()
        annual_users = User.objects.filter(plan="annual").count()

        pending_payments = User.objects.filter(payment_status="pending").count()
        inadimplente_users = User.objects.filter(payment_status="inadimplente").count()

        total_clients = Client.objects.count()
        total_jobs = Job.objects.count()
        total_expenses = Expense.objects.count()
        total_revenue = Job.objects.aggregate(total=Sum("cache"))["total"] or 0

        serializer = AdminMetricsSerializer(
            {
                "total_users": total_users,
                "active_users": active_users,
                "blocked_users": blocked_users,
                "trial_users": trial_users,
                "monthly_users": monthly_users,
                "annual_users": annual_users,
                "pending_payments": pending_payments,
                "inadimplente_users": inadimplente_users,
                "total_clients": total_clients,
                "total_jobs": total_jobs,
                "total_expenses": total_expenses,
                "total_revenue": total_revenue,
            }
        )
        return Response(serializer.data)
