from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from base.jobs.models import Job
from base.clients.models import Client
from base.quote.models import Quote
from base.expenses.models import Expense


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    if not request.user.account:
        return Response({"error": "Usuário não possui conta associada"}, status=400)

    account = request.user.account

    clients_count = Client.objects.filter(account=account).count()
    jobs_count = Job.objects.filter(account=account).count()
    quotes_count = Quote.objects.filter(account=account).count()

    from django.db.models import Sum

    revenue = (
        Job.objects.filter(account=account, status=Job.JobStatus.COMPLETED).aggregate(
            total=Sum("cache")
        )["total"]
        or 0
    )

    expenses_total = (
        Expense.objects.filter(account=account).aggregate(total=Sum("value"))["total"]
        or 0
    )

    pending_quotes = Quote.objects.filter(
        account=account, status=Quote.QuoteStatus.DRAFT
    ).count()

    accepted_quotes = Quote.objects.filter(
        account=account, status=Quote.QuoteStatus.ACCEPTED
    ).count()

    pending_jobs = Job.objects.filter(
        account=account, status=Job.JobStatus.PENDING
    ).count()

    return Response(
        {
            "clients_count": clients_count,
            "jobs_count": jobs_count,
            "quotes_count": quotes_count,
            "revenue": float(revenue),
            "expenses": float(expenses_total),
            "pending_quotes": pending_quotes,
            "accepted_quotes": accepted_quotes,
            "pending_jobs": pending_jobs,
        }
    )


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return dashboard_api(request)
