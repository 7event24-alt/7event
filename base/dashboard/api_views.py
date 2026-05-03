from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from base.jobs.models import Job, PaymentType, PaymentStatusJob
from base.clients.models import Client
from base.quote.models import Quote
from base.expenses.models import Expense
from django.db.models import Sum
from decimal import Decimal


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    user = request.user
    is_superuser = user.is_superuser

    if is_superuser:
        clients_count = Client.objects.filter(is_active=True).count()
        jobs_count = Job.objects.filter(is_active=True).count()
        quotes_count = Quote.objects.filter(is_active=True).count()

        revenue_full = (
            Job.objects.filter(
                payment_status=PaymentStatusJob.PAID,
                payment_type__in=[PaymentType.ADVANCE, PaymentType.FULL]
            ).aggregate(total=Sum("cache"))["total"]
            or Decimal("0.00")
        )

        revenue_partial = (
            Job.objects.filter(
                payment_status=PaymentStatusJob.PARTIAL
            ).aggregate(total=Sum("payment_partial_value"))["total"]
            or Decimal("0.00")
        )

        expenses_total = (
            Expense.objects.filter(is_active=True).aggregate(total=Sum("value"))["total"]
            or Decimal("0.00")
        )

        pending_quotes = Quote.objects.filter(is_active=True).count()
        pending_jobs = Job.objects.filter(status=Job.JobStatus.PENDING).count()
    else:
        clients_count = Client.objects.filter(created_by=user, is_active=True).count()
        jobs_count = Job.objects.filter(created_by=user, is_active=True).count()
        quotes_count = Quote.objects.filter(created_by=user, is_active=True).count()

        revenue_full = (
            Job.objects.filter(
                created_by=user,
                payment_status=PaymentStatusJob.PAID,
                payment_type__in=[PaymentType.ADVANCE, PaymentType.FULL]
            ).aggregate(total=Sum("cache"))["total"]
            or Decimal("0.00")
        )

        revenue_partial = (
            Job.objects.filter(
                created_by=user,
                payment_status=PaymentStatusJob.PARTIAL
            ).aggregate(total=Sum("payment_partial_value"))["total"]
            or Decimal("0.00")
        )

        expenses_total = (
            Expense.objects.filter(performed_by=user, is_active=True).aggregate(total=Sum("value"))["total"]
            or Decimal("0.00")
        )

        pending_quotes = Quote.objects.filter(created_by=user, is_active=True).count()
        pending_jobs = Job.objects.filter(created_by=user, status=Job.JobStatus.PENDING).count()

    revenue = revenue_full + revenue_partial

    return Response(
        {
            "clients_count": clients_count,
            "jobs_count": jobs_count,
            "quotes_count": quotes_count,
            "revenue": float(revenue),
            "revenue_full": float(revenue_full),
            "revenue_partial": float(revenue_partial),
            "expenses": float(expenses_total),
            "pending_quotes": pending_quotes,
            "accepted_quotes": 0,
            "pending_jobs": pending_jobs,
        }
    )


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return dashboard_api(request)