from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

from .models import Expense, ExpenseCategory
from base.jobs.models import Job


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["job", "category", "value", "date", "description"]
        widgets = {
            "job": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                }
            ),
            "value": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0,00",
                    "step": "0.01",
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "rows": 2,
                    "placeholder": "Descrição",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get("class", "")
            if self.errors.get(field_name):
                field.widget.attrs["class"] = (
                    f"{current_class} border-red-500 focus:ring-red-500 focus:border-red-500".strip()
                )


class CompanyRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(request.get_full_path())

        if not request.user.account:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Você precisa estar associado a uma empresa.")
        return super().dispatch(request, *args, **kwargs)


class ExpenseListView(CompanyRequiredMixin, View):
    template_name = "expenses/list.html"

    def get(self, request):
        company = request.user.account
        user = request.user
        is_superuser = user.is_superuser

        if is_superuser:
            expenses = (
                Expense.objects.filter(account=company)
                .select_related("job", "user")
                .order_by("-date")
            )
        else:
            expenses = (
                Expense.objects.filter(account=company, user=user)
                .select_related("job", "user")
                .order_by("-date")
            )

        query = request.GET.get("q", "")
        if query:
            expenses = expenses.filter(description__icontains=query)

        category_filter = request.GET.get("category", "")
        if category_filter:
            expenses = expenses.filter(category=category_filter)

        job_filter = request.GET.get("job", "")
        if job_filter:
            expenses = expenses.filter(job_id=job_filter)

        user_filter = request.GET.get("user", "")
        if user_filter:
            expenses = expenses.filter(user_id=user_filter)

        users = []
        if is_superuser:
            users = company.users.all()

        total_value = sum(e.value for e in expenses)

        return render(
            request,
            self.template_name,
            {
                "expenses": expenses,
                "query": query,
                "category_filter": category_filter,
                "job_filter": job_filter,
                "user_filter": user_filter,
                "categories": ExpenseCategory.choices,
                "jobs": Job.objects.filter(account=company),
                "users": users,
                "is_superuser": is_superuser,
                "total_value": total_value,
            },
        )


class ExpenseCreateView(CompanyRequiredMixin, View):
    template_name = "expenses/form.html"

    def get(self, request):
        form = ExpenseForm()
        jobs = Job.objects.filter(account=request.user.account)
        return render(request, self.template_name, {"form": form, "jobs": jobs})

    def post(self, request):
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.account = request.user.account
            expense.user = request.user
            expense.save()

            # Criar notificação
            if request.user.account.notify_on_expense_created:
                from base.accounts.models import Notification, NotificationType

                Notification.objects.create(
                    user=request.user,
                    title="Nova despesa registrada",
                    message=f"Despesa de R$ {expense.value} foi registrada",
                    action_url=f"/despesas/",
                    notification_type=NotificationType.EXPENSE,
                )

            if "save_and_add" in request.POST:
                messages.success(request, "Despesa criada! Adicione outra.")
                return redirect("expenses:create")

            messages.success(request, "Despesa criada com sucesso!")
            return redirect("expenses:list")
        jobs = Job.objects.filter(account=request.user.account)
        return render(request, self.template_name, {"form": form, "jobs": jobs})


class ExpenseUpdateView(CompanyRequiredMixin, View):
    template_name = "expenses/form.html"

    def get(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, account=request.user.account)
        form = ExpenseForm(instance=expense)
        jobs = Job.objects.filter(account=request.user.account)
        return render(
            request, self.template_name, {"form": form, "object": expense, "jobs": jobs}
        )

    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, account=request.user.account)
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Despesa atualizada com sucesso!")
            return redirect("expenses:list")
        jobs = Job.objects.filter(account=request.user.account)
        return render(
            request, self.template_name, {"form": form, "object": expense, "jobs": jobs}
        )


class ExpenseDeleteView(CompanyRequiredMixin, View):
    template_name = "expenses/confirm_delete.html"

    def get(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, account=request.user.account)
        return render(request, self.template_name, {"expense": expense})

    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, account=request.user.account)
        expense.delete()
        messages.success(request, "Despesa excluída com sucesso!")
        return redirect("expenses:list")
