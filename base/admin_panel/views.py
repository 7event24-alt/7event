from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.contrib import messages
from django import forms
from django.utils.text import slugify

from base.accounts.models import (
    Account,
    Plan,
    PlanType,
    Subscription,
    SubscriptionStatus,
    AccountType,
    User,
)
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

        users = User.objects.select_related("account", "account__plan").order_by(
            "-created_at"
        )

        search = request.GET.get("q", "")
        account_filter = request.GET.get("account", "")
        status_filter = request.GET.get("status", "")

        if search:
            users = (
                users.filter(username__icontains=search)
                | users.filter(first_name__icontains=search)
                | users.filter(last_name__icontains=search)
                | users.filter(email__icontains=search)
            )

        if account_filter:
            users = users.filter(account_id=account_filter)

        if status_filter == "active":
            users = users.filter(is_blocked=False)
        elif status_filter == "blocked":
            users = users.filter(is_blocked=True)

        accounts = Account.objects.all().order_by("name")

        context = {
            "users": users,
            "accounts": accounts,
            "search": search,
            "account_filter": account_filter,
            "status_filter": status_filter,
        }

        return render(request, self.template_name, context)


class UserDetailView(LoginRequiredMixin, View):
    template_name = "admin_panel/user_detail.html"

    def get(self, request, pk):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        user = get_object_or_404(
            User.objects.select_related("account", "account__plan"), pk=pk
        )

        jobs = Job.objects.filter(user=user).select_related("client", "account")[:10]
        clients = Client.objects.filter(account=user.account).order_by("-created_at")[
            :10
        ]
        expenses = Expense.objects.filter(user=user).select_related("job", "account")[
            :10
        ]

        total_jobs = Job.objects.filter(user=user).count()
        total_clients = Client.objects.filter(account=user.account).count()
        total_expenses = Expense.objects.filter(user=user).count()

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


class AccountCreateView(LoginRequiredMixin, View):
    template_name = "admin_panel/account_form.html"

    def get(self, request):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        from base.accounts.forms import AccountAdminForm, UserAdminCreationForm

        account_form = AccountAdminForm()
        user_form = UserAdminCreationForm()

        return render(
            request,
            self.template_name,
            {"account_form": account_form, "user_form": user_form},
        )

    def post(self, request):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        from base.accounts.forms import AccountAdminForm, UserAdminCreationForm

        account_form = AccountAdminForm(request.POST)
        user_form = UserAdminCreationForm(request.POST)

        if account_form.is_valid() and user_form.is_valid():
            account = account_form.save()

            user = user_form.save()
            user.account = account
            user.save()

            messages.success(request, f"Conta '{account.name}' criada com sucesso!")
            return redirect("admin_panel:account_detail", pk=account.pk)

        return render(
            request,
            self.template_name,
            {"account_form": account_form, "user_form": user_form},
        )


class AdminPanelView(LoginRequiredMixin, View):
    template_name = "admin_panel/home.html"

    def get(self, request):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        accounts = (
            Account.objects.select_related("plan", "subscription")
            .annotate(total_users=Count("users"))
            .order_by("-created_at")
        )

        plan_filter = request.GET.get("plan", "")
        status_filter = request.GET.get("status", "")
        search = request.GET.get("q", "")

        if plan_filter:
            accounts = accounts.filter(plan__type=plan_filter)
        if status_filter:
            accounts = accounts.filter(subscription__status=status_filter)
        if search:
            accounts = accounts.filter(name__icontains=search)

        context = {
            "accounts": accounts,
            "plan_types": PlanType.choices,
            "subscription_statuses": SubscriptionStatus.choices,
            "account_types": AccountType.choices,
            "plan_filter": plan_filter,
            "status_filter": status_filter,
            "search": search,
        }

        return render(request, self.template_name, context)


class AccountDetailView(LoginRequiredMixin, View):
    template_name = "admin_panel/company_detail.html"

    def get(self, request, pk):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        account = get_object_or_404(Account, pk=pk)
        users = account.users.all()
        total_jobs = account.jobs.count()
        total_clients = account.clients.count()
        total_expenses = account.expenses.count()

        context = {
            "account": account,
            "users": users,
            "total_jobs": total_jobs,
            "total_clients": total_clients,
            "total_expenses": total_expenses,
        }

        return render(request, self.template_name, context)


class AccountToggleActiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        account = get_object_or_404(Account, pk=pk)
        account.is_active = not account.is_active
        account.save()
        status = "ativada" if account.is_active else "desativada"
        messages.success(request, f"Conta {status} com sucesso!")
        return redirect("admin_panel:account_detail", pk=pk)


class AccountToggleBlockedView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        account = get_object_or_404(Account, pk=pk)
        account.is_blocked = not account.is_blocked
        account.save()
        status = "desbloqueada" if not account.is_blocked else "bloqueada"
        messages.success(request, f"Conta {status} com sucesso!")
        return redirect("admin_panel:account_detail", pk=pk)


class CompanyUpdateNotificationsView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Acesso restrito a superadministradores.")

        account = get_object_or_404(Account, pk=pk)
        account.notify_on_job_created = (
            request.POST.get("notify_on_job_created") == "on"
        )
        account.notify_on_job_confirmed = (
            request.POST.get("notify_on_job_confirmed") == "on"
        )
        account.notify_on_client_created = (
            request.POST.get("notify_on_client_created") == "on"
        )
        account.notify_on_service_created = (
            request.POST.get("notify_on_service_created") == "on"
        )
        account.notify_on_expense_created = (
            request.POST.get("notify_on_expense_created") == "on"
        )
        account.notify_on_quote_created = (
            request.POST.get("notify_on_quote_created") == "on"
        )
        account.save()
        messages.success(request, "Preferências de notificação atualizadas!")
        return redirect("admin_panel:account_detail", pk=pk)


company_update_notifications = CompanyUpdateNotificationsView.as_view()


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
                    "type",
                    "name",
                    "description",
                    "max_users",
                    "max_clients",
                    "max_jobs",
                    "max_expenses",
                    "max_agenda_events",
                    "price_monthly",
                    "price_quarterly",
                    "price_semester",
                    "is_active",
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
                    "type",
                    "name",
                    "description",
                    "max_users",
                    "max_clients",
                    "max_jobs",
                    "max_expenses",
                    "max_agenda_events",
                    "price_monthly",
                    "price_quarterly",
                    "price_semester",
                    "is_active",
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
                    "type",
                    "name",
                    "description",
                    "max_users",
                    "max_clients",
                    "max_jobs",
                    "max_expenses",
                    "max_agenda_events",
                    "price_monthly",
                    "price_quarterly",
                    "price_semester",
                    "is_active",
                ]

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
                    "type",
                    "name",
                    "description",
                    "max_users",
                    "max_clients",
                    "max_jobs",
                    "max_expenses",
                    "max_agenda_events",
                    "price_monthly",
                    "price_quarterly",
                    "price_semester",
                    "is_active",
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

        subscriptions = Subscription.objects.select_related("account", "plan").order_by(
            "-created_at"
        )
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
account_create = AccountCreateView.as_view()
account_detail = AccountDetailView.as_view()
account_toggle_active = AccountToggleActiveView.as_view()
account_toggle_blocked = AccountToggleBlockedView.as_view()
plan_list = PlanListView.as_view()
plan_create = PlanCreateView.as_view()
plan_edit = PlanEditView.as_view()
plan_delete = PlanDeleteView.as_view()
subscription_list = SubscriptionListView.as_view()
user_list = UserListView.as_view()
user_detail = UserDetailView.as_view()

Company = Account
company_detail = account_detail
company_toggle_active = account_toggle_active
company_toggle_blocked = account_toggle_blocked
