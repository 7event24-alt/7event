from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
from calendar import monthrange, Calendar

from base.jobs.models import Job, JobStatus


class AgendaView(LoginRequiredMixin, View):
    template_name = "agenda/home.html"

    def get(self, request):
        if not request.user.account:
            return render(request, self.template_name, self.get_context_data())

        now = timezone.now()
        year = int(request.GET.get("year") or now.year)
        month = int(request.GET.get("month") or now.month)

        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1

        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, monthrange(year, month)[1])

        status_filter = request.GET.get("status", "")

        jobs = (
            Job.objects.filter(
                account=request.user.account,
                start_date__gte=first_day.date(),
                start_date__lte=last_day.date(),
            )
            .select_related("client")
            .order_by("start_date", "start_time")
        )

        if status_filter:
            jobs = jobs.filter(status=status_filter)

        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1

        month_names = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro",
        }
        month_name = month_names[month]

        cal = Calendar()
        weeks = cal.monthdayscalendar(year, month)

        calendar_weeks = []
        for week in weeks:
            week_data = []
            for day_num in week:
                if day_num == 0:
                    week_data.append({"day": "", "is_current_month": False, "jobs": []})
                else:
                    current_date = datetime(year, month, day_num).date()
                    day_jobs = [
                        {
                            "id": job.id,
                            "title": job.title,
                            "start_time": job.start_time.strftime("%H:%M")
                            if job.start_time
                            else "",
                            "status_color": self.get_status_color(job.status),
                        }
                        for job in jobs.filter(start_date=current_date)
                    ]
                    week_data.append(
                        {
                            "day": day_num,
                            "date": current_date,
                            "is_current_month": True,
                            "is_today": current_date == timezone.now().date(),
                            "jobs": day_jobs,
                        }
                    )
            calendar_weeks.append(week_data)

        upcoming_jobs = (
            Job.objects.filter(
                account=request.user.account,
                start_date__gte=now.date(),
                status__in=[JobStatus.PENDING, JobStatus.CONFIRMED],
            )
            .select_related("client")
            .order_by("start_date")[:10]
        )
        for job in upcoming_jobs:
            job.status_color = self.get_status_color(job.status)

        context = {
            "year": year,
            "month": month,
            "month_name": month_name,
            "prev_month": prev_month,
            "prev_year": prev_year,
            "next_month": next_month,
            "next_year": next_year,
            "calendar_weeks": calendar_weeks,
            "jobs": jobs,
            "upcoming_jobs": upcoming_jobs,
            "status_filter": status_filter,
        }

        return render(request, self.template_name, context)

    def get_status_color(self, status):
        colors = {
            JobStatus.PENDING: "#f59e0b",
            JobStatus.CONFIRMED: "#10b981",
            JobStatus.COMPLETED: "#6366f1",
            JobStatus.CANCELLED: "#ef4444",
        }
        return colors.get(status, "#1e3a5f")

    def get_context_data(self):
        return {
            "year": timezone.now().year,
            "month": timezone.now().month,
            "month_name": "Mês",
            "calendar_weeks": [],
            "jobs": [],
            "upcoming_jobs": [],
        }


agenda = AgendaView.as_view()


class DayDetailView(LoginRequiredMixin, View):
    template_name = "agenda/day_detail.html"

    def get(self, request, year, month, day):
        if not request.user.account:
            return render(request, self.template_name, {"error": "Sem conta"})

        try:
            selected_date = datetime(int(year), int(month), int(day)).date()
        except ValueError:
            selected_date = timezone.now().date()

        jobs = (
            Job.objects.filter(
                account=request.user.account,
                start_date=selected_date,
            )
            .select_related("client")
            .order_by("start_time")
        )

        month_names = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro",
        }
        month_name = month_names.get(selected_date.month, "")

        prev_day = selected_date - timedelta(days=1)
        next_day = selected_date + timedelta(days=1)

        total_cache = sum(job.cache or 0 for job in jobs)

        context = {
            "selected_date": selected_date,
            "day": selected_date.day,
            "month": selected_date.month,
            "year": selected_date.year,
            "month_name": month_name,
            "jobs": jobs,
            "jobs_count": jobs.count(),
            "total_cache": total_cache,
            "prev_day": prev_day,
            "next_day": next_day,
        }

        return render(request, self.template_name, context)


day_detail = DayDetailView.as_view()
