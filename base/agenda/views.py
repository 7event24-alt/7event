from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
from calendar import monthrange, Calendar

from base.jobs.models import Job, JobStatus, JobStaff
from base.accounts.models import PersonalTask


class AgendaView(LoginRequiredMixin, View):
    template_name = "agenda/home.html"

    def get(self, request):
        user = request.user
        is_superuser = user.is_superuser

        if is_superuser:
            base_jobs = Job.objects.filter(is_active=True)
        else:
            # Mostrar trabalhos criados pelo user OU onde ele é staff
            base_jobs = Job.objects.filter(
                models.Q(created_by=user) | models.Q(job_staff__professional=user),
                is_active=True,
            ).distinct()

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
        user_filter = request.GET.get("user", "")

        jobs = (
            base_jobs.filter(
                start_date__gte=first_day.date(),
                start_date__lte=last_day.date(),
            )
            .select_related("client")
            .order_by("start_date", "start_time")
        )

        if status_filter:
            jobs = jobs.filter(status=status_filter)

        if user_filter:
            jobs = jobs.filter(user_id=user_filter)

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

        today = now.date()
        current_month_end = today.replace(day=monthrange(today.year, today.month)[1])

        upcoming_jobs = base_jobs.filter(
            start_date__gte=today,
            start_date__lte=current_month_end,
            status__in=[JobStatus.PENDING, JobStatus.CONFIRMED],
        )
        if user_filter and is_superuser:
            upcoming_jobs = upcoming_jobs.filter(user_id=user_filter)

        upcoming_jobs = upcoming_jobs.select_related("client").order_by("start_date")[
            :10
        ]

        for job in upcoming_jobs:
            job.status_color = self.get_status_color(job.status)

        upcoming_visits = base_jobs.filter(
            has_technical_visit=True,
            technical_visit_date__gte=today,
            technical_visit_date__lte=current_month_end,
            status__in=[JobStatus.PENDING, JobStatus.CONFIRMED],
        )
        if user_filter and is_superuser:
            upcoming_visits = upcoming_visits.filter(user_id=user_filter)
        upcoming_visits = upcoming_visits.select_related("client").order_by("technical_visit_date")[:10]

        upcoming_tasks = PersonalTask.objects.filter(
            user=user,
            date__gte=today,
            date__lte=current_month_end,
            is_completed=False,
        ).order_by("date", "time")[:10]

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
            "upcoming_visits": upcoming_visits,
            "upcoming_tasks": upcoming_tasks,
            "status_filter": status_filter,
            "user_filter": user_filter,
            "is_superuser": is_superuser,
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


agenda = AgendaView.as_view()


class DayDetailView(LoginRequiredMixin, View):
    template_name = "agenda/day_detail.html"

    def get(self, request, year, month, day):
        user = request.user
        is_superuser = user.is_superuser

        try:
            selected_date = datetime(int(year), int(month), int(day)).date()
        except ValueError:
            selected_date = timezone.now().date()

        # Jobs normais (na data do evento)
        if is_superuser:
            jobs = Job.objects.filter(start_date=selected_date, is_active=True)
        else:
            jobs = Job.objects.filter(
                models.Q(created_by=user) | models.Q(job_staff__professional=user),
                start_date=selected_date,
                is_active=True,
            ).distinct()

        jobs = jobs.select_related("client").order_by("start_time")

        # Visitas Técnicas (na data da visita técnica)
        if is_superuser:
            visits = Job.objects.filter(
                is_active=True,
                has_technical_visit=True,
                technical_visit_date=selected_date
            ).select_related("client")
        else:
            visits = Job.objects.filter(
                (models.Q(created_by=user) | models.Q(job_staff__professional=user)) &
                models.Q(is_active=True, has_technical_visit=True, technical_visit_date=selected_date)
            ).select_related("client").distinct()

        # Tarefas Pessoais
        from base.accounts.models import PersonalTask
        tasks = PersonalTask.objects.filter(
            user=user,
            date=selected_date
        ).order_by("time")

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
            "visits": visits,
            "visits_count": visits.count(),
            "tasks": tasks,
            "tasks_count": tasks.count(),
            "total_cache": total_cache,
            "prev_day": prev_day,
            "next_day": next_day,
        }

        return render(request, self.template_name, context)


day_detail = DayDetailView.as_view()
