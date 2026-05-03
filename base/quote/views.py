from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import weasyprint

from base.clients.models import Client
from base.accounts.models import Notification, NotificationType
from base.core.emails import send_quote_email
from .models import Quote, QuoteExpense, QuoteStatus
from .forms import QuoteForm, QuoteExpenseForm


class QuoteListView(LoginRequiredMixin, View):
    template_name = "quote/list.html"

    def get(self, request):
        user = request.user
        if user.is_superuser:
            quotes = Quote.objects.filter(is_active=True).order_by("-created_at")
        else:
            quotes = Quote.objects.filter(created_by=user, is_active=True).order_by("-created_at")
        return render(request, self.template_name, {"quotes": quotes})


class QuoteCreateView(LoginRequiredMixin, View):
    template_name = "quote/form.html"

    def get(self, request):
        user = request.user
        form = QuoteForm(created_by=user)
        return render(
            request,
            self.template_name,
            {"form": form},
        )

    def post(self, request):
        user = request.user
        form = QuoteForm(request.POST, created_by=user)

        if form.is_valid():
            quote = form.save(commit=False)
            quote.created_by = user
            quote.expenses_cost = Decimal("0")
            quote.labor_cost = quote.hourly_rate * quote.work_hours
            quote.save()

            messages.success(request, "Orçamento criado com sucesso!")
            return redirect("quote:detail", pk=quote.pk)

        return render(request, self.template_name, {"form": form})


class QuoteDetailView(LoginRequiredMixin, View):
    template_name = "quote/detail.html"

    def get(self, request, pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)
        expenses = quote.expenses.all()
        return render(
            request,
            self.template_name,
            {"quote": quote, "expenses": expenses},
        )


class QuoteUpdateView(LoginRequiredMixin, View):
    template_name = "quote/form.html"

    def get(self, request, pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)
        form = QuoteForm(instance=quote, created_by=user)
        return render(
            request,
            self.template_name,
            {"form": form, "object": quote},
        )

    def post(self, request, pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)
        form = QuoteForm(request.POST, instance=quote, created_by=user)

        if form.is_valid():
            quote = form.save(commit=False)
            quote.labor_cost = quote.hourly_rate * quote.work_hours
            quote.save()

            messages.success(request, "Orçamento atualizado com sucesso!")
            return redirect("quote:detail", pk=quote.pk)

        return render(request, self.template_name, {"form": form, "object": quote})


class QuoteDeleteView(LoginRequiredMixin, View):
    template_name = "quote/confirm_delete.html"

    def get(self, request, pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)
        return render(request, self.template_name, {"quote": quote})

    def post(self, request, pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)
        quote.delete()
        messages.success(request, "Orçamento excluído com sucesso!")
        return redirect("quote:list")


class QuoteAddExpenseView(LoginRequiredMixin, View):
    template_name = "quote/expense_form.html"

    def get(self, request, pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)
        form = QuoteExpenseForm()
        return render(request, self.template_name, {"form": form, "quote": quote})

    def post(self, request, pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)
        form = QuoteExpenseForm(request.POST)

        if form.is_valid():
            expense = form.save(commit=False)
            expense.quote = quote
            expense.save()
            quote.save()
            messages.success(request, "Despesa adicionada!")
            return redirect("quote:detail", pk=quote.pk)

        return render(request, self.template_name, {"form": form, "quote": quote})


class QuoteDeleteExpenseView(LoginRequiredMixin, View):
    def post(self, request, pk, expense_pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)
        expense = get_object_or_404(QuoteExpense, pk=expense_pk, quote=quote)
        expense.delete()
        quote.save()
        messages.success(request, "Despesa removida!")
        return redirect("quote:detail", pk=pk)


class QuotePDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)
        expenses = quote.expenses.all()

        from datetime import datetime

        client_name = (
            quote.client.name.replace(" ", "_") if quote.client else "sem_cliente"
        )
        year = datetime.now().year

        logo_url = request.build_absolute_uri("/static/img/logo7event.png")

        html = render_to_string(
            "quote/pdf.html",
            {
                "quote": quote,
                "expenses": expenses,
                "created_by": user,
                "logo_url": logo_url,
            },
        )

        pdf = weasyprint.HTML(string=html).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="orcamento_{client_name}_{year}.pdf"'
        )
        return response


class QuoteSendView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)

        if not quote.client or not quote.client.email:
            messages.error(request, "Orçamento sem cliente ou email.")
            return redirect("quote:detail", pk=pk)

        quote.status = QuoteStatus.SENT
        quote.save()

        send_quote_email(quote, quote.client.email)

        messages.success(request, f"Orçamento enviado para {quote.client.email}!")
        return redirect("quote:detail", pk=pk)