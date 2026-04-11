from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from base.clients.models import Client
from base.jobs.models import Job, JobStatus, PaymentStatusJob
from base.expenses.models import Expense
from base.services.models import Service
from base.quote.models import Quote


class DashboardView(LoginRequiredMixin, View):
    template_name = "dashboard/home.html"

    def get(self, request):
        company = request.user.account
        if not company:
            return render(
                request,
                self.template_name,
                {"error": "Você precisa estar associado a uma empresa."},
            )

        now = timezone.now()
        month_start = now.replace(day=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end = month_start - timedelta(days=1)

        # Jobs counts by status
        jobs_total = Job.objects.filter(account=company).count()
        jobs_pending = Job.objects.filter(
            account=company, status=JobStatus.PENDING
        ).count()
        jobs_confirmed = Job.objects.filter(
            account=company, status=JobStatus.CONFIRMED
        ).count()
        jobs_completed = Job.objects.filter(
            account=company, status=JobStatus.COMPLETED
        ).count()
        jobs_cancelled = Job.objects.filter(
            account=company, status=JobStatus.CANCELLED
        ).count()

        # Jobs this month
        jobs_this_month = Job.objects.filter(
            account=company, start_date__gte=month_start, start_date__lte=now.date()
        ).count()

        # Revenue metrics
        total_revenue = Job.objects.filter(
            account=company, cache__isnull=False
        ).aggregate(total=Sum("cache"))["total"] or Decimal("0")

        revenue_this_month = Job.objects.filter(
            account=company, start_date__gte=month_start, cache__isnull=False
        ).aggregate(total=Sum("cache"))["total"] or Decimal("0")

        revenue_received = Job.objects.filter(
            account=company, payment_status=PaymentStatusJob.PAID
        ).aggregate(total=Sum("cache"))["total"] or Decimal("0")

        revenue_pending = Job.objects.filter(
            account=company,
            payment_status__in=[PaymentStatusJob.PENDING, PaymentStatusJob.PARTIAL],
        ).aggregate(total=Sum("cache"))["total"] or Decimal("0")

        # Expenses
        total_expenses = Expense.objects.filter(account=company).aggregate(
            total=Sum("value")
        )["total"] or Decimal("0")

        monthly_expenses = Expense.objects.filter(
            account=company, date__gte=month_start
        ).aggregate(total=Sum("value"))["total"] or Decimal("0")

        net_profit = total_revenue - total_expenses
        monthly_balance = revenue_this_month - monthly_expenses

        if total_revenue > 0:
            profit_margin = (net_profit / total_revenue) * 100
        else:
            profit_margin = 0

        # Recent jobs
        recent_jobs = (
            Job.objects.filter(account=company)
            .select_related("client")
            .order_by("-created_at")[:5]
        )

        # Upcoming events (today to next 3 months)
        from datetime import date

        today = date.today()
        three_months_later = today + timedelta(days=90)

        upcoming_events = (
            Job.objects.filter(
                account=company,
                start_date__gte=today,
                start_date__lte=three_months_later,
            )
            .select_related("client")
            .order_by("start_date")
        )

        upcoming_events_count = upcoming_events.count()

        # If no future events, show recent past events
        if upcoming_events_count == 0:
            upcoming_events = (
                Job.objects.filter(account=company)
                .select_related("client")
                .order_by("-start_date")[:10]
            )
            upcoming_events_count = Job.objects.filter(account=company).count()

        # Clients
        clients_total = Client.objects.filter(account=company).count()
        clients_this_month = Client.objects.filter(
            account=company, created_at__gte=month_start
        ).count()

        context = {
            "total_revenue": total_revenue,
            "revenue_this_month": revenue_this_month,
            "total_expenses": total_expenses,
            "monthly_expenses": monthly_expenses,
            "net_profit": net_profit,
            "monthly_balance": monthly_balance,
            "profit_margin": profit_margin,
            "jobs_this_month": jobs_this_month,
            "jobs_total": jobs_total,
            "jobs_pending": jobs_pending,
            "jobs_confirmed": jobs_confirmed,
            "jobs_completed": jobs_completed,
            "jobs_cancelled": jobs_cancelled,
            "recent_jobs": recent_jobs,
            "upcoming_events": upcoming_events,
            "upcoming_events_count": upcoming_events_count,
            "revenue_received": revenue_received,
            "revenue_pending": revenue_pending,
            "clients_total": clients_total,
            "clients_this_month": clients_this_month,
            "company": company,
        }

        return render(request, self.template_name, context)


dashboard = DashboardView.as_view()


def search(request):
    from django.contrib.auth.decorators import login_required
    from functools import wraps

    # Login required decorator equivalent for function view
    if not request.user.is_authenticated:
        from django.shortcuts import redirect

        return redirect("accounts:login")

    query = request.GET.get("q", "").strip()
    account = request.user.account

    if not account:
        return render(
            request, "search.html", {"query": query, "error": "Conta não encontrada"}
        )

    context = {"query": query, "has_searched": bool(query)}

    if query:
        # Buscar em Jobs
        jobs = (
            Job.objects.filter(account=account)
            .filter(
                Q(title__icontains=query)
                | Q(location__icontains=query)
                | Q(description__icontains=query)
                | Q(client__name__icontains=query)
            )
            .select_related("client")[:10]
        )
        context["jobs"] = jobs
        context["jobs_count"] = jobs.count()

        # Buscar em Clients
        clients = Client.objects.filter(account=account).filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(document__icontains=query)
        )[:10]
        context["clients"] = clients
        context["clients_count"] = clients.count()

        # Buscar em Services
        services = Service.objects.filter(account=account).filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:10]
        context["services"] = services
        context["services_count"] = services.count()

        # Buscar em Quotes
        quotes = (
            Quote.objects.filter(account=account)
            .filter(Q(title__icontains=query) | Q(description__icontains=query))
            .select_related("client")[:10]
        )
        context["quotes"] = quotes
        context["quotes_count"] = quotes.count()

        # Buscar em Expenses
        expenses = (
            Expense.objects.filter(account=account)
            .filter(Q(description__icontains=query) | Q(category__icontains=query))
            .select_related("job")[:10]
        )
        context["expenses"] = expenses
        context["expenses_count"] = expenses.count()

        # Total de resultados
        context["total_results"] = (
            context["jobs_count"]
            + context["clients_count"]
            + context["services_count"]
            + context["quotes_count"]
            + context["expenses_count"]
        )

    return render(request, "search.html", context)
