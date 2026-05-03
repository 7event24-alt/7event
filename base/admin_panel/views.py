from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.contrib import messages

from base.accounts.models import Plan, Subscription, SubscriptionStatus, User
from base.jobs.models import Job
from base.clients.models import Client
from base.expenses.models import Expense

User = get_user_model()


class UserListView(LoginRequiredMixin, View):
    template_name = "admin_panel/users.html"

    def get(self, request):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        users = User.objects.order_by("-created_at")
        search = request.GET.get("q", "")
        status_filter = request.GET.get("status", "")

        if search:
            users = users.filter(
                username__icontains=search
            ) | users.filter(first_name__icontains=search
            ) | users.filter(last_name__icontains=search
            ) | users.filter(email__icontains=search)

        if status_filter == "active":
            users = users.filter(is_blocked=False)
        elif status_filter == "blocked":
            users = users.filter(is_blocked=True)

        context = {
            "users": users,
            "search": search,
            "status_filter": status_filter,
        }
        return render(request, self.template_name, context)


class UserDetailView(LoginRequiredMixin, View):
    template_name = "admin_panel/user_detail.html"

    def get(self, request, pk):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        user = get_object_or_404(User, pk=pk)
        jobs = Job.objects.filter(created_by=user).select_related("client")[:10]
        clients = Client.objects.filter(created_by=user).order_by("-created_at")[:10]
        expenses = Expense.objects.filter(performed_by=user).select_related("job")[:10]

        total_jobs = Job.objects.filter(created_by=user).count()
        total_clients = Client.objects.filter(created_by=user).count()
        total_expenses = Expense.objects.filter(performed_by=user).count()

        context = {
            "user_obj": user,
            "jobs": jobs,
            "clients": clients,
            "expenses": expenses,
            "total_jobs": total_jobs,
            "total_clients": total_clients,
            "total_expenses": total_expenses,
        }
        return render(request, self.template_name, context)


class AdminPanelView(LoginRequiredMixin, View):
    template_name = "admin_panel/home.html"

    def get(self, request):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        users = User.objects.annotate(
            job_count=Count("jobs_created"),
            client_count=Count("clients_created"),
        ).order_by("-created_at")

        search = request.GET.get("q", "")
        if search:
            users = users.filter(username__icontains=search) | users.filter(email__icontains=search)

        context = {
            "users": users,
            "search": search,
            "plan_types": Plan.get_type_choices() if hasattr(Plan, 'get_type_choices') else [],
            "payment_statuses": SubscriptionStatus.choices,
        }
        return render(request, self.template_name, context)


class PlanListView(LoginRequiredMixin, View):
    template_name = "admin_panel/plans.html"

    def get(self, request):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        plans = Plan.objects.all().order_by("price_monthly")
        return render(request, self.template_name, {"plans": plans})


class PlanCreateView(LoginRequiredMixin, View):
    template_name = "admin_panel/plan_form.html"

    def get(self, request):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        from base.accounts.models import Plan as PlanModel
        from django import forms

        class PlanForm(forms.ModelForm):
            class Meta:
                model = PlanModel
                fields = [
                    "type", "name", "description", "max_users", "max_clients",
                    "max_jobs", "max_expenses", "max_agenda_events",
                    "can_associate_professionals", "job_creation_limit",
                    "price_monthly", "price_quarterly", "price_semester", "is_active",
                ]

        form = PlanForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        from base.accounts.models import Plan as PlanModel
        from django import forms

        class PlanForm(forms.ModelForm):
            class Meta:
                model = PlanModel
                fields = [
                    "type", "name", "description", "max_users", "max_clients",
                    "max_jobs", "max_expenses", "max_agenda_events",
                    "can_associate_professionals", "job_creation_limit",
                    "price_monthly", "price_quarterly", "price_semester", "is_active",
                ]

        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plano criado com sucesso!")
            return redirect("admin_panel:plan_list")
        return render(request, self.template_name, {"form": form})


class PlanEditView(LoginRequiredMixin, View):
    template_name = "admin_panel/plan_form.html"

    def get(self, request, pk):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        plan = get_object_or_404(Plan, pk=pk)
        from base.accounts.models import Plan as PlanModel
        from django import forms

        class PlanForm(forms.ModelForm):
            class Meta:
                model = PlanModel
                fields = [
                    "type", "name", "description", "max_users", "max_clients",
                    "max_jobs", "max_expenses", "max_agenda_events",
                    "can_associate_professionals", "job_creation_limit",
                    "price_monthly", "price_quarterly", "price_semester",
                    "payment_link", "is_visible", "is_active", "highlight",
                ]

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for field in self.fields.values():
                    field.widget.attrs.update(
                        {"class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"}
                    )

        form = PlanForm(instance=plan)
        return render(request, self.template_name, {"form": form, "object": plan})

    def post(self, request, pk):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        plan = get_object_or_404(Plan, pk=pk)
        from base.accounts.models import Plan as PlanModel
        from django import forms

        class PlanForm(forms.ModelForm):
            class Meta:
                model = PlanModel
                fields = [
                    "type", "name", "description", "max_users", "max_clients",
                    "max_jobs", "max_expenses", "max_agenda_events",
                    "can_associate_professionals", "job_creation_limit",
                    "price_monthly", "price_quarterly", "price_semester",
                    "payment_link", "is_visible", "is_active", "highlight",
                ]

        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Plano atualizado com sucesso!")
            return redirect("admin_panel:plan_list")
        return render(request, self.template_name, {"form": form, "object": plan})


class PlanDeleteView(LoginRequiredMixin, View):
    template_name = "admin_panel/plan_confirm_delete.html"

    def get(self, request, pk):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        plan = get_object_or_404(Plan, pk=pk)
        return render(request, self.template_name, {"plan": plan})

    def post(self, request, pk):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        plan = get_object_or_404(Plan, pk=pk)
        plan.delete()
        messages.success(request, "Plano excluído com sucesso!")
        return redirect("admin_panel:plan_list")


class SubscriptionListView(LoginRequiredMixin, View):
    template_name = "admin_panel/subscriptions.html"

    def get(self, request):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        subscriptions = Subscription.objects.select_related("user", "plan").order_by("-created_at")
        status_filter = request.GET.get("status", "")
        if status_filter:
            subscriptions = subscriptions.filter(status=status_filter)

        return render(
            request,
            self.template_name,
            {
                "subscriptions": subscriptions,
                "statuses": SubscriptionStatus.choices,
                "status_filter": status_filter,
            },
        )


admin_panel = AdminPanelView.as_view()
plan_list = PlanListView.as_view()
plan_create = PlanCreateView.as_view()
plan_edit = PlanEditView.as_view()
plan_delete = PlanDeleteView.as_view()
subscription_list = SubscriptionListView.as_view()
user_list = UserListView.as_view()
user_detail = UserDetailView.as_view()