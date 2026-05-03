from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
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
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            if user.is_superuser:
                self.fields["job"].queryset = Job.objects.filter(is_active=True)
            else:
                self.fields["job"].queryset = Job.objects.filter(created_by=user, is_active=True)


class ExpenseListView(LoginRequiredMixin, View):
    template_name = "expenses/list.html"

    def get(self, request):
        user = request.user

        if user.is_superuser:
            expenses = Expense.objects.filter(is_active=True).select_related("job", "performed_by").order_by("-date")
            jobs = Job.objects.filter(is_active=True)
        else:
            expenses = Expense.objects.filter(performed_by=user, is_active=True).select_related("job").order_by("-date")
            jobs = Job.objects.filter(created_by=user, is_active=True)

        query = request.GET.get("q", "")
        if query:
            expenses = expenses.filter(description__icontains=query)

        category_filter = request.GET.get("category", "")
        if category_filter:
            expenses = expenses.filter(category=category_filter)

        job_filter = request.GET.get("job", "")
        if job_filter:
            expenses = expenses.filter(job_id=job_filter)

        total_value = sum(e.value for e in expenses)

        return render(
            request,
            self.template_name,
            {
                "expenses": expenses,
                "query": query,
                "category_filter": category_filter,
                "job_filter": job_filter,
                "categories": ExpenseCategory.choices,
                "jobs": jobs,
                "is_superuser": user.is_superuser,
                "total_value": total_value,
            },
        )


class ExpenseCreateView(LoginRequiredMixin, View):
    template_name = "expenses/form.html"

    def get(self, request):
        form = ExpenseForm(user=request.user)
        jobs = Job.objects.filter(is_active=True) if request.user.is_superuser else Job.objects.filter(created_by=request.user, is_active=True)

        preselected_job = request.GET.get("job", "")
        if preselected_job:
            form.fields["job"].initial = preselected_job
            form.fields["job"].disabled = True
            
            # Pre-fill date with job's event date
            try:
                job = Job.objects.get(pk=preselected_job, is_active=True)
                if job.start_date:
                    form.fields["date"].initial = job.start_date
            except Job.DoesNotExist:
                pass

        return render(request, self.template_name, {"form": form, "jobs": jobs, "preselected_job": preselected_job})

    def post(self, request):
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.performed_by = request.user
            expense.save()

            messages.success(request, "Despesa criada com sucesso!")
            
            # Redirect to job detail if expense is associated with a job
            if expense.job:
                return redirect("jobs:detail", pk=expense.job.pk)
            return redirect("expenses:list")
        return render(request, self.template_name, {"form": form})


class ExpenseUpdateView(LoginRequiredMixin, View):
    template_name = "expenses/form.html"

    def get(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, performed_by=request.user, is_active=True)
        form = ExpenseForm(instance=expense, user=request.user)
        return render(request, self.template_name, {"form": form, "object": expense})

    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, performed_by=request.user, is_active=True)
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Despesa atualizada com sucesso!")
            return redirect("expenses:list")
        return render(request, self.template_name, {"form": form, "object": expense})


class ExpenseDeleteView(LoginRequiredMixin, View):
    template_name = "expenses/confirm_delete.html"

    def get(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, performed_by=request.user, is_active=True)
        return render(request, self.template_name, {"expense": expense})

    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, performed_by=request.user, is_active=True)
        job = expense.job
        expense.is_active = False
        expense.save()
        messages.success(request, "Despesa excluída com sucesso!")
        
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        if job:
            return redirect("jobs:detail", pk=job.pk)
        return redirect("expenses:list")