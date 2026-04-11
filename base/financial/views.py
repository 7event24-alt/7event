from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal

from base.jobs.models import Job, PaymentStatusJob, JobStatus
from base.expenses.models import Expense


class FinancialView(LoginRequiredMixin, View):
    template_name = "financial/home.html"

    def get(self, request):
        if not request.user.account:
            return render(request, self.template_name, self.get_empty_context())

        account = request.user.account
        period = request.GET.get("period", "month")

        now = timezone.now()
        today = now.date()

        if period == "day":
            start_date = today
            end_date = today
            period_label = "Hoje"
            period_data = (
                Job.objects.filter(
                    account=account, start_date=today, cache__isnull=False
                )
                .annotate(period=TruncDay("start_date"))
                .values("period")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                Expense.objects.filter(account=account, date=today)
                .annotate(period=TruncDay("date"))
                .values("period")
                .annotate(total=Sum("value"))
            )
        elif period == "month":
            month_start = today.replace(day=1)
            if today.month == 12:
                month_end = today.replace(
                    year=today.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                month_end = today.replace(month=today.month + 1, day=1) - timedelta(
                    days=1
                )
            start_date = month_start
            end_date = month_end
            period_label = f"{now.strftime('%B').title()} {now.year}"
            period_data = (
                Job.objects.filter(
                    account=account,
                    start_date__gte=month_start,
                    start_date__lte=month_end,
                    cache__isnull=False,
                )
                .annotate(period=TruncMonth("start_date"))
                .values("period")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                Expense.objects.filter(
                    account=account, date__gte=month_start, date__lte=month_end
                )
                .annotate(period=TruncMonth("date"))
                .values("period")
                .annotate(total=Sum("value"))
            )
        elif period == "bimestral":
            # Bimestre atual (2 meses do ano civil)
            # Bimestre 1 = Jan-Fev, Bimestre 2 = Mar-Abr, etc.
            current_month = today.month

            # Calcular qual bimestre estamos
            bimestre_num = (current_month + 1) // 2

            # Primeiro mês do bimestre atual
            start_month = (bimestre_num - 1) * 2 + 1
            if start_month > 12:
                start_month -= 12

            start_date = today.replace(month=start_month, day=1)

            # Último mês do bimestre
            end_month = start_month + 1
            if end_month > 12:
                end_month -= 12
                end_year = today.year + 1
            else:
                end_year = today.year

            # Calcular último dia do mês
            if end_month == 12:
                end_date = date(end_year, 12, 31)
            else:
                # Últo dia do mês
                next_month = date(end_year, end_month + 1, 1)
                end_date = next_month - timedelta(days=1)

            period_label = f"Bimestre {bimestre_num}/{now.year}"
            period_data = (
                Job.objects.filter(
                    account=account,
                    start_date__gte=start_date,
                    start_date__lte=end_date,
                    cache__isnull=False,
                )
                .values("start_date")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                Expense.objects.filter(
                    account=account, date__gte=start_date, date__lte=end_date
                )
                .values("date")
                .annotate(total=Sum("value"))
            )
        elif period == "trimestral":
            quarter = (now.month - 1) // 3
            month_num = quarter * 3 + 1
            start_date = today.replace(month=month_num)
            if month_num + 2 > 12:
                end_date = today.replace(
                    year=today.year + 1, month=month_num - 9, day=1
                ) - timedelta(days=1)
            else:
                end_date = today.replace(month=month_num + 3, day=1) - timedelta(days=1)
            period_label = f"Trimestre {quarter + 1}/{now.year}"
            period_data = (
                Job.objects.filter(
                    account=account,
                    start_date__gte=start_date,
                    start_date__lte=end_date,
                    cache__isnull=False,
                )
                .values("start_date")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                Expense.objects.filter(
                    account=account, date__gte=start_date, date__lte=end_date
                )
                .values("date")
                .annotate(total=Sum("value"))
            )
        elif period == "annual":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
            period_label = f"Ano {now.year}"
            period_data = (
                Job.objects.filter(
                    account=account, start_date__year=now.year, cache__isnull=False
                )
                .annotate(period=TruncMonth("start_date"))
                .values("period")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                Expense.objects.filter(account=account, date__year=now.year)
                .annotate(period=TruncMonth("date"))
                .values("period")
                .annotate(total=Sum("value"))
            )
        elif period == "last_2_years":
            start_date = today.replace(year=today.year - 1, month=1, day=1)
            end_date = today
            period_label = f"Últimos 2 Anos"
            period_data = (
                Job.objects.filter(
                    account=account,
                    start_date__gte=start_date,
                    start_date__lte=end_date,
                    cache__isnull=False,
                )
                .annotate(period=TruncMonth("start_date"))
                .values("period")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                Expense.objects.filter(
                    account=account, date__gte=start_date, date__lte=end_date
                )
                .annotate(period=TruncMonth("date"))
                .values("period")
                .annotate(total=Sum("value"))
            )
        else:
            start_date = today.replace(day=1)
            end_date = today
            period_label = f"{now.strftime('%B').title()} {now.year}"
            period_data = []
            expenses_data = []

        total_revenue = sum(item["total"] for item in period_data if item.get("total"))

        revenue_received = Job.objects.filter(
            account=account,
            payment_status=PaymentStatusJob.PAID,
            start_date__gte=start_date,
            start_date__lte=end_date,
        ).aggregate(total=Sum("cache"))["total"] or Decimal("0")

        revenue_pending = Job.objects.filter(
            account=account,
            payment_status__in=[PaymentStatusJob.PENDING, PaymentStatusJob.PARTIAL],
            start_date__gte=start_date,
            start_date__lte=end_date,
        ).aggregate(total=Sum("cache"))["total"] or Decimal("0")

        total_expenses = sum(
            item["total"] for item in expenses_data if item.get("total")
        )

        net_profit = total_revenue - total_expenses

        expenses_by_category = (
            Expense.objects.filter(
                account=account, date__gte=start_date, date__lte=end_date
            )
            .values("category")
            .annotate(total=Sum("value"))
            .order_by("-total")
        )

        jobs_by_status = (
            Job.objects.filter(
                account=account, start_date__gte=start_date, start_date__lte=end_date
            )
            .values("status")
            .annotate(count=Sum("id"))
        )

        jobs_period = (
            Job.objects.filter(
                account=account, start_date__gte=start_date, start_date__lte=end_date
            )
            .select_related("client")
            .order_by("start_date")
        )

        expenses_period = (
            Expense.objects.filter(
                account=account, date__gte=start_date, date__lte=end_date
            )
            .select_related("job")
            .order_by("date")
        )

        chart_data = []
        if period in ["month", "annual", "last_2_years"]:
            period_data_list = list(period_data)
            for item in period_data_list:
                if item.get("period"):
                    chart_data.append(
                        {
                            "period": item["period"].strftime("%b/%Y")
                            if hasattr(item["period"], "strftime")
                            else str(item["period"]),
                            "revenue": float(item.get("total", 0)),
                        }
                    )

        context = {
            "total_revenue": total_revenue,
            "revenue_received": revenue_received,
            "revenue_pending": revenue_pending,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "jobs_period": jobs_period,
            "expenses_period": expenses_period,
            "period": period,
            "period_label": period_label,
            "chart_data": chart_data,
        }

        return render(request, self.template_name, context)

    def get_empty_context(self):
        return {
            "total_revenue": Decimal("0"),
            "revenue_received": Decimal("0"),
            "revenue_pending": Decimal("0"),
            "total_expenses": Decimal("0"),
            "net_profit": Decimal("0"),
            "jobs_period": [],
            "expenses_period": [],
            "period": "month",
            "period_label": "Hoje",
            "chart_data": [],
        }


financial = FinancialView.as_view()
