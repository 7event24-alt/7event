from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal

from base.jobs.models import Job, PaymentStatusJob, JobStatus, PaymentType, JobStaff
from base.expenses.models import Expense, ExpenseCategory


class FinancialView(LoginRequiredMixin, View):
    template_name = "financial/home.html"

    def get(self, request):
        user = request.user
        is_superuser = user.is_superuser
        period = request.GET.get("period", "month")

        now = timezone.now()
        today = now.date()

        if is_superuser:
            base_jobs = Job.objects.filter(is_active=True)
            base_expenses = Expense.objects.all()
        else:
            # Include jobs created by user OR where user is a staff member
            base_jobs = Job.objects.filter(
                Q(created_by=user) | Q(job_staff__professional=user),
                is_active=True,
            ).distinct()
            # Include expenses where:
            # 1. performed_by=user (user created the expense)
            # 2. expense.job where user is creator OR staff member
            base_expenses = Expense.objects.filter(
                Q(performed_by=user) |
                Q(job__created_by=user) |
                Q(job__job_staff__professional=user)
            ).filter(is_active=True).distinct()
        
        # Calculate revenue including staff cache values
        def get_jobs_with_staff_info(user):
            """Get jobs with annotation for revenue calculation"""
            # For jobs created by user: use job.cache
            created_jobs = Q(created_by=user)
            # For jobs where user is staff: use job_staff__cache_value
            staff_jobs = Q(job_staff__professional=user)
            
            return Job.objects.filter(
                created_jobs | staff_jobs,
                is_active=True,
            ).distinct().annotate(
                # This will be used in calculation
                is_creator=models.Case(
                    models.When(created_by=user, then=models.Value(True)),
                    default=models.Value(False),
                    output_field=models.BooleanField()
                )
            )
        
        # Get all relevant jobs for revenue calculation
        all_relevant_jobs = Job.objects.filter(
            Q(created_by=user) | Q(job_staff__professional=user),
            is_active=True,
        ).distinct().select_related('created_by').prefetch_related('job_staff')
        
        # Calculate total revenue including staff cache values
        def calculate_total_revenue(jobs, user):
            total = Decimal('0')
            for job in jobs:
                if job.created_by == user:
                    # Job creator: use job.cache
                    total += job.cache or Decimal('0')
                else:
                    # Staff member: use job_staff.cache_value
                    staff_record = job.job_staff.filter(professional=user).first()
                    if staff_record:
                        total += staff_record.cache_value or Decimal('0')
            return total

        if period == "day":
            start_date = today
            end_date = today
            period_label = "Hoje"
            period_data = (
                base_jobs.filter(
                    start_date=today, cache__isnull=False
                )
                .annotate(period=TruncDay("start_date"))
                .values("period")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                base_expenses.filter(date=today)
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
                base_jobs.filter(
                    start_date__gte=month_start,
                    start_date__lte=month_end,
                    cache__isnull=False,
                )
                .annotate(period=TruncMonth("start_date"))
                .values("period")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                base_expenses.filter(
                    date__gte=month_start, date__lte=month_end
                )
                .annotate(period=TruncMonth("date"))
                .values("period")
                .annotate(total=Sum("value"))
            )
        elif period == "bimestral":
            current_month = today.month
            bimestre_num = (current_month + 1) // 2
            start_month = (bimestre_num - 1) * 2 + 1
            if start_month > 12:
                start_month -= 12

            start_date = today.replace(month=start_month, day=1)

            end_month = start_month + 1
            if end_month > 12:
                end_month -= 12
                end_year = today.year + 1
            else:
                end_year = today.year

            if end_month == 12:
                end_date = date(end_year, 12, 31)
            else:
                next_month = date(end_year, end_month + 1, 1)
                end_date = next_month - timedelta(days=1)

            period_label = f"Bimestre {bimestre_num}/{now.year}"
            period_data = (
                base_jobs.filter(
                    start_date__gte=start_date,
                    start_date__lte=end_date,
                    cache__isnull=False,
                )
                .values("start_date")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                base_expenses.filter(
                    date__gte=start_date, date__lte=end_date
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
                base_jobs.filter(
                    start_date__gte=start_date,
                    start_date__lte=end_date,
                    cache__isnull=False,
                )
                .values("start_date")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                base_expenses.filter(
                    date__gte=start_date, date__lte=end_date
                )
                .values("date")
                .annotate(total=Sum("value"))
            )
        elif period == "annual":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
            period_label = f"Ano {now.year}"
            period_data = (
                base_jobs.filter(
                    start_date__year=now.year, cache__isnull=False
                )
                .annotate(period=TruncMonth("start_date"))
                .values("period")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                base_expenses.filter(date__year=now.year)
                .annotate(period=TruncMonth("date"))
                .values("period")
                .annotate(total=Sum("value"))
            )
        elif period == "last_2_years":
            start_date = today.replace(year=today.year - 1, month=1, day=1)
            end_date = today
            period_label = f"Últimos 2 Anos"
            period_data = (
                base_jobs.filter(
                    start_date__gte=start_date,
                    start_date__lte=end_date,
                    cache__isnull=False,
                )
                .annotate(period=TruncMonth("start_date"))
                .values("period")
                .annotate(total=Sum("cache"))
            )
            expenses_data = (
                base_expenses.filter(
                    date__gte=start_date, date__lte=end_date
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
        
        # Get all relevant jobs for this user (creator or staff)
        relevant_jobs = Job.objects.filter(
            Q(created_by=user) | Q(job_staff__professional=user),
            is_active=True,
        ).distinct().select_related('created_by').prefetch_related('job_staff')
        
        # Calculate revenue including staff cache values
        total_revenue = Decimal('0')
        revenue_received = Decimal('0')
        revenue_pending = Decimal('0')
        
        for job in relevant_jobs:
            # Determine revenue for this job
            if job.created_by == user:
                # User is creator: use job.cache
                job_revenue = job.cache or Decimal('0')
            else:
                # User is staff member: use staff record cache_value
                staff_record = job.job_staff.filter(professional=user).first()
                job_revenue = staff_record.cache_value if staff_record else Decimal('0')
            
            total_revenue += job_revenue
            
            # Check payment status
            if job.payment_status == PaymentStatusJob.PAID:
                revenue_received += job_revenue
            elif job.payment_status == PaymentStatusJob.PARTIAL:
                revenue_received += job.payment_partial_value or Decimal('0')
                revenue_pending += job.payment_remaining_value or Decimal('0')
            else:
                revenue_pending += job_revenue

        total_expenses = sum(
            item["total"] for item in expenses_data if item.get("total")
        )

        net_profit = total_revenue - total_expenses

        expenses_by_category = (
            base_expenses.filter(
                date__gte=start_date, date__lte=end_date
            )
            .values("category")
            .annotate(total=Sum("value"))
            .order_by("-total")
        )
        
        # Add category labels
        category_dict = dict(ExpenseCategory.choices)
        for item in expenses_by_category:
            item['category_label'] = category_dict.get(item['category'], item['category'])

        jobs_by_status = (
            base_jobs.filter(
                start_date__gte=start_date, start_date__lte=end_date
            )
            .values("status")
            .annotate(count=Sum("id"))
        )

        jobs_period = (
            base_jobs.filter(
                start_date__gte=start_date, start_date__lte=end_date
            )
            .select_related("client")
            .order_by("start_date")
        )

        expenses_period = (
            base_expenses.filter(
                date__gte=start_date, date__lte=end_date
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
            "expenses_by_category": expenses_by_category,
            "period": period,
            "period_label": period_label,
            "chart_data": chart_data,
        }

        return render(request, self.template_name, context)


financial = FinancialView.as_view()
