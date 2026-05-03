from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from base.clients.models import Client
from base.jobs.models import Job, JobStatus, PaymentStatusJob, PaymentType
from base.expenses.models import Expense
from base.services.models import Service
from base.quote.models import Quote


class DashboardView(LoginRequiredMixin, View):
    template_name = "dashboard/home.html"

    def get(self, request):
        user = request.user
        is_superuser = user.is_superuser

        now = timezone.now()
        month_start = now.replace(day=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end = month_start - timedelta(days=1)

        if is_superuser:
            base_jobs = Job.objects.all()
            base_expenses = Expense.objects.all()
            base_clients = Client.objects.all()
        else:
            base_jobs = Job.objects.filter(created_by=user)
            base_expenses = Expense.objects.filter(performed_by=user)
            base_clients = Client.objects.filter(created_by=user)

        jobs_total = base_jobs.count()
        jobs_pending = base_jobs.filter(status=JobStatus.PENDING).count()
        jobs_confirmed = base_jobs.filter(status=JobStatus.CONFIRMED).count()
        jobs_completed = base_jobs.filter(status=JobStatus.COMPLETED).count()
        jobs_cancelled = base_jobs.filter(status=JobStatus.CANCELLED).count()

        jobs_this_month = base_jobs.filter(
            start_date__gte=month_start, start_date__lte=now.date()
        ).count()

        total_revenue = base_jobs.filter(
            cache__isnull=False
        ).aggregate(total=Sum("cache"))["total"] or Decimal("0")

        revenue_this_month = base_jobs.filter(
            start_date__gte=month_start, cache__isnull=False
        ).aggregate(total=Sum("cache"))["total"] or Decimal("0")

        revenue_received = base_jobs.filter(
            payment_status=PaymentStatusJob.PAID
        ).aggregate(total=Sum("cache"))["total"] or Decimal("0")

        revenue_from_partial = base_jobs.filter(
            payment_status=PaymentStatusJob.PARTIAL
        ).aggregate(total=Sum("payment_partial_value"))["total"] or Decimal("0")
        
        revenue_received = revenue_received + revenue_from_partial

        pending_full = base_jobs.filter(
            payment_status=PaymentStatusJob.PENDING,
            payment_type__in=[PaymentType.ADVANCE, PaymentType.FULL]
        ).aggregate(total=Sum("cache"))["total"] or Decimal("0")

        pending_partial = base_jobs.filter(
            payment_status=PaymentStatusJob.PARTIAL
        ).aggregate(total=Sum("payment_remaining_value"))["total"] or Decimal("0")

        revenue_pending = pending_full + pending_partial

        total_expenses = base_expenses.aggregate(total=Sum("value"))["total"] or Decimal("0")

        monthly_expenses = base_expenses.filter(
            date__gte=month_start
        ).aggregate(total=Sum("value"))["total"] or Decimal("0")

        net_profit = total_revenue - total_expenses
        monthly_balance = revenue_this_month - monthly_expenses

        if total_revenue > 0:
            profit_margin = (net_profit / total_revenue) * 100
        else:
            profit_margin = 0

        recent_jobs = (
            base_jobs.select_related("client").order_by("-created_at")[:5]
        )

        from datetime import date

        today = date.today()
        three_months_later = today + timedelta(days=90)

        upcoming_events = (
            base_jobs.filter(
                start_date__gte=today,
                start_date__lte=three_months_later,
            )
            .select_related("client")
            .order_by("start_date")
        )
        
        upcoming_events_count = upcoming_events.count()
        
        if upcoming_events_count == 0:
            upcoming_events = (
                base_jobs.select_related("client").order_by("-start_date")[:10]
            )
            upcoming_events_count = base_jobs.count()
        
        # NOVO: Jobs normais (sem visita técnica)
        upcoming_jobs = upcoming_events.filter(
            has_technical_visit=False
        ).order_by("start_date")[:10]
        
        upcoming_jobs_count = upcoming_events.filter(has_technical_visit=False).count()
        
        # NOVO: Visitas Técnicas
        upcoming_visits = upcoming_events.filter(
            has_technical_visit=True
        ).order_by("start_date")[:10]
        
        upcoming_visits_count = upcoming_events.filter(has_technical_visit=True).count()
        
        # NOVO: Tarefas pessoais pendentes (próximos 90 dias)
        from base.accounts.models import PersonalTask
        today_date = timezone.now().date()
        upcoming_tasks = PersonalTask.objects.filter(
            user=user,
            date__gte=today_date,
            date__lte=today_date + timedelta(days=90),
            is_completed=False
        ).order_by("date", "time")[:10]
        
        upcoming_tasks_count = PersonalTask.objects.filter(
            user=user,
            is_completed=False
        ).count()

        clients_total = base_clients.count()
        clients_this_month = base_clients.filter(
            created_at__gte=month_start
        ).count()

        # Tarefas pessoais para o widget do dashboard
        from base.accounts.models import PersonalTask
        today = timezone.now().date()
        today_tasks = PersonalTask.objects.filter(
            user=user,
            date=today,
            is_completed=False
        ).order_by("time")[:5]

        pending_tasks_count = PersonalTask.objects.filter(
            user=user,
            is_completed=False
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
            "company": user,
            "today_tasks": today_tasks,
            "pending_tasks_count": pending_tasks_count,
            # Novos cards
            "upcoming_jobs": upcoming_jobs,
            "upcoming_jobs_count": upcoming_jobs_count,
            "upcoming_visits": upcoming_visits,
            "upcoming_visits_count": upcoming_visits_count,
            "upcoming_tasks": upcoming_tasks,
            "upcoming_tasks_count": upcoming_tasks_count,
        }

        return render(request, self.template_name, context)


dashboard = DashboardView.as_view()


def search(request):
    from django.contrib.auth.decorators import login_required
    from functools import wraps

    if not request.user.is_authenticated:
        from django.shortcuts import redirect

        return redirect("accounts:login")

    query = request.GET.get("q", "").strip()
    user = request.user
    is_superuser = user.is_superuser

    context = {"query": query, "has_searched": bool(query)}

    if query:
        if is_superuser:
            jobs_base = Job.objects.all()
            clients_base = Client.objects.all()
            services_base = Service.objects.all()
            quotes_base = Quote.objects.all()
            expenses_base = Expense.objects.all()
        else:
            jobs_base = Job.objects.filter(created_by=user)
            clients_base = Client.objects.filter(created_by=user)
            services_base = Service.objects.filter(created_by=user)
            quotes_base = Quote.objects.filter(created_by=user)
            expenses_base = Expense.objects.filter(performed_by=user)

        jobs = (
            jobs_base
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

        clients = clients_base.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(document__icontains=query)
        )[:10]
        context["clients"] = clients
        context["clients_count"] = clients.count()

        services = services_base.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:10]
        context["services"] = services
        context["services_count"] = services.count()

        quotes = (
            quotes_base
            .filter(Q(title__icontains=query) | Q(description__icontains=query))
            .select_related("client")[:10]
        )
        context["quotes"] = quotes
        context["quotes_count"] = quotes.count()

        expenses = (
            expenses_base
            .filter(Q(description__icontains=query) | Q(category__icontains=query))
            .select_related("job")[:10]
        )
        context["expenses"] = expenses
        context["expenses_count"] = expenses.count()

        context["total_results"] = (
            context["jobs_count"]
            + context["clients_count"]
            + context["services_count"]
            + context["quotes_count"]
            + context["expenses_count"]
        )

    return render(request, "search.html", context)