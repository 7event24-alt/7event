from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone

from .models import Job, EventType, JobStatus, PaymentType, PaymentStatusJob
from base.clients.models import Client


class CompanyRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.account:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Você precisa estar associado a uma empresa.")
        return super().dispatch(request, *args, **kwargs)


class JobListView(CompanyRequiredMixin, View):
    template_name = "jobs/list.html"

    def get(self, request):
        company = request.user.account
        user = request.user

        # Admin vê todos, worker só vê jobs associados
        if user.is_account_admin:
            jobs = Job.objects.filter(account=company)
        else:
            jobs = Job.objects.filter(
                account=company,
            ).filter(Q(user=user) | Q(workers=user))

        jobs = jobs.select_related("client", "user").order_by("-start_date")

        query = request.GET.get("q", "")
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query)
                | Q(client__name__icontains=query)
                | Q(location__icontains=query)
            )

        status_filter = request.GET.get("status", "")
        if status_filter:
            jobs = jobs.filter(status=status_filter)

        payment_filter = request.GET.get("payment_status", "")
        if payment_filter:
            jobs = jobs.filter(payment_status=payment_filter)

        user_filter = request.GET.get("user", "")
        if user_filter:
            jobs = jobs.filter(user_id=user_filter)

        # Get all users of the company for filter (superuser only)
        users = []
        is_superuser = request.user.is_superuser
        if is_superuser:
            users = company.users.all()

        return render(
            request,
            self.template_name,
            {
                "jobs": jobs,
                "query": query,
                "status_filter": status_filter,
                "payment_filter": payment_filter,
                "user_filter": user_filter,
                "event_types": EventType.choices,
                "job_statuses": JobStatus.choices,
                "payment_statuses": PaymentStatusJob.choices,
                "users": users,
                "is_superuser": is_superuser,
            },
        )


class JobCreateView(CompanyRequiredMixin, View):
    template_name = "jobs/form.html"

    def get(self, request):
        from .forms import JobForm
        from datetime import datetime

        form = JobForm(user=request.user)
        initial_date = request.GET.get("date")
        if initial_date:
            try:
                dt = datetime.strptime(initial_date, "%Y-%m-%d")
                form.fields["start_date"].initial = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        from base.accounts.models import User

        available_workers = User.objects.filter(account=request.user.account).exclude(
            id=request.user.id
        )

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "initial_date": initial_date,
                "available_workers": available_workers,
                "selected_workers": [],
            },
        )

    def post(self, request):
        from .forms import JobForm

        form = JobForm(request.POST, user=request.user)
        if form.is_valid():
            job = form.save(commit=False)
            job.account = request.user.account
            job.user = request.user
            job.save()
            form.save_m2m()

            # Get selected workers from POST
            worker_ids = request.POST.getlist("workers")
            if worker_ids:
                from base.accounts.models import User

                workers = User.objects.filter(
                    id__in=worker_ids, account=request.user.account
                )
                job.workers.set(workers)

            # Criar notificação
            if request.user.account.notify_on_job_created:
                from base.accounts.models import Notification, NotificationType

                Notification.objects.create(
                    user=request.user,
                    title="Novo trabalho criado",
                    message=f"Trabalho '{job.title}' foi criado com sucesso",
                    action_url=f"/trabalhos/{job.pk}/",
                    notification_type=NotificationType.JOB,
                )

                # Enviar email de notificação (opcional)
                try:
                    from base.core.emails import send_new_job_notification

                    send_new_job_notification(request.user, job)
                except Exception as e:
                    print(f"Erro ao enviar email: {e}")

            messages.success(request, "Trabalho criado com sucesso!")
            return redirect("jobs:detail", pk=job.pk)

        from base.accounts.models import User

        available_workers = User.objects.filter(account=request.user.account).exclude(
            id=request.user.id
        )
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "available_workers": available_workers,
                "selected_workers": [],
            },
        )


class JobUpdateView(CompanyRequiredMixin, View):
    template_name = "jobs/form.html"

    def get(self, request, pk):
        from .forms import JobForm

        job = get_object_or_404(Job, pk=pk, account=request.user.account)
        form = JobForm(instance=job, user=request.user)

        from base.accounts.models import User

        available_workers = User.objects.filter(account=request.user.account).exclude(
            id=request.user.id
        )
        selected_workers = list(job.workers.all())

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": job,
                "available_workers": available_workers,
                "selected_workers": selected_workers,
            },
        )

    def post(self, request, pk):
        from .forms import JobForm

        job = get_object_or_404(Job, pk=pk, account=request.user.account)
        form = JobForm(request.POST, instance=job, user=request.user)
        if form.is_valid():
            form.save()

            worker_ids = request.POST.getlist("workers")
            from base.accounts.models import User

            if worker_ids:
                workers = User.objects.filter(
                    id__in=worker_ids, account=request.user.account
                )
                job.workers.set(workers)
            else:
                job.workers.clear()

            messages.success(request, "Trabalho atualizado com sucesso!")
            return redirect("jobs:detail", pk=job.pk)
        clients = Client.objects.filter(account=request.user.account)
        available_workers = User.objects.filter(account=request.user.account).exclude(
            id=request.user.id
        )
        selected_workers = list(job.workers.all())
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": job,
                "clients": clients,
                "available_workers": available_workers,
                "selected_workers": selected_workers,
            },
        )


class JobDetailView(CompanyRequiredMixin, View):
    template_name = "jobs/detail.html"

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk, account=request.user.account)
        expenses = job.expenses.all()
        total_expenses = sum(e.value for e in expenses)
        net_profit = (job.cache or 0) - total_expenses

        return render(
            request,
            self.template_name,
            {
                "job": job,
                "expenses": expenses,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
            },
        )


class JobConfirmView(CompanyRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, account=request.user.account)
        job.status = JobStatus.CONFIRMED
        job.save()
        messages.success(request, "Trabalho confirmado com sucesso!")
        return redirect("jobs:detail", pk=job.pk)


class JobCompleteView(CompanyRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, account=request.user.account)
        job.status = JobStatus.COMPLETED
        job.save()
        messages.success(request, "Trabalho marcado como concluído!")
        return redirect("jobs:detail", pk=job.pk)


class JobCancelView(CompanyRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, account=request.user.account)
        job.status = JobStatus.CANCELLED
        job.save()
        messages.success(request, "Trabalho cancelado!")
        return redirect("jobs:detail", pk=job.pk)


class JobApproveView(CompanyRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, account=request.user.account)
        if not request.user.is_account_admin:
            messages.error(request, "Apenas administradores podem aprovar trabalhos.")
            return redirect("jobs:detail", pk=job.pk)
        job.approved_by = request.user
        job.approved_at = timezone.now()
        job.save()
        messages.success(request, "Trabalho aprovado com sucesso!")
        return redirect("jobs:detail", pk=job.pk)


class JobDeleteView(CompanyRequiredMixin, View):
    template_name = "jobs/confirm_delete.html"

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk, account=request.user.account)
        return render(request, self.template_name, {"job": job})

    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, account=request.user.account)
        job.delete()
        messages.success(request, "Trabalho excluído com sucesso!")
        return redirect("jobs:list")


class ClientQuickCreateView(CompanyRequiredMixin, View):
    template_name = "clients/quick_form.html"

    def post(self, request):
        from base.clients.forms import ClientForm

        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.account = request.user.account
            client.save()
            return render(
                request, self.template_name, {"success": True, "client": client}
            )
        return render(request, self.template_name, {"form": form, "error": True})
