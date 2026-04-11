from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from base.jobs.models import Job, JobStatus, PaymentStatusJob
from base.expenses.models import Expense, ExpenseCategory


class FinancialSummarySerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_received = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_pending = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=12, decimal_places=2)


class MonthlyRevenueSerializer(serializers.Serializer):
    month = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class ExpenseByCategorySerializer(serializers.Serializer):
    category = serializers.CharField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)


class JobsByStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class FinancialViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user

        total_revenue = (
            Job.objects.filter(user=user, cache__isnull=False).aggregate(
                total=Sum("cache")
            )["total"]
            or 0
        )

        revenue_received = (
            Job.objects.filter(
                user=user, payment_status=PaymentStatusJob.PAID
            ).aggregate(total=Sum("cache"))["total"]
            or 0
        )

        revenue_pending = (
            Job.objects.filter(
                user=user,
                payment_status__in=[PaymentStatusJob.PENDING, PaymentStatusJob.PARTIAL],
            ).aggregate(total=Sum("cache"))["total"]
            or 0
        )

        total_expenses = (
            Expense.objects.filter(user=user).aggregate(total=Sum("value"))["total"]
            or 0
        )

        net_profit = total_revenue - total_expenses

        serializer = FinancialSummarySerializer(
            {
                "total_revenue": total_revenue,
                "revenue_received": revenue_received,
                "revenue_pending": revenue_pending,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
            }
        )
        return Response(serializer.data)
