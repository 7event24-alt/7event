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


class CompanyRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(request.get_full_path())

        if not request.user.account:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Você precisa estar associado a uma empresa.")
        return super().dispatch(request, *args, **kwargs)


class QuoteListView(CompanyRequiredMixin, View):
    template_name = "quote/list.html"

    def get(self, request):
        company = request.user.account
        quotes = Quote.objects.filter(account=company).order_by("-created_at")
        return render(request, self.template_name, {"quotes": quotes})


class QuoteCreateView(CompanyRequiredMixin, View):
    template_name = "quote/form.html"

    def get(self, request):
        company = request.user.account
        form = QuoteForm(account=company)
        return render(
            request,
            self.template_name,
            {"form": form},
        )

    def post(self, request):
        company = request.user.account
        form = QuoteForm(request.POST, account=company)

        if form.is_valid():
            quote = form.save(commit=False)
            quote.account = company
            quote.expenses_cost = Decimal("0")
            quote.labor_cost = quote.hourly_rate * quote.work_hours
            quote.save()

            if company.notify_on_quote_created:
                Notification.objects.create(
                    user=request.user,
                    title="Novo Orçamento",
                    message=f"Orçamento #{quote.pk} criado para {quote.client.name if quote.client else 'sem cliente'}.",
                    action_url=f"/orcamentos/{quote.pk}/",
                    notification_type=NotificationType.QUOTE,
                )
            messages.success(request, "Orçamento criado com sucesso!")
            return redirect("quote:detail", pk=quote.pk)

        return render(request, self.template_name, {"form": form})


class QuoteDetailView(CompanyRequiredMixin, View):
    template_name = "quote/detail.html"

    def get(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        expenses = quote.expenses.all()
        return render(
            request,
            self.template_name,
            {"quote": quote, "expenses": expenses},
        )


class QuoteUpdateView(CompanyRequiredMixin, View):
    template_name = "quote/form.html"

    def get(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        form = QuoteForm(instance=quote, account=request.user.account)
        return render(
            request,
            self.template_name,
            {"form": form, "object": quote},
        )

    def post(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        form = QuoteForm(request.POST, instance=quote, account=request.user.account)

        if form.is_valid():
            quote = form.save(commit=False)
            quote.labor_cost = quote.hourly_rate * quote.work_hours
            quote.save()

            messages.success(request, "Orçamento atualizado com sucesso!")
            return redirect("quote:detail", pk=quote.pk)

        return render(request, self.template_name, {"form": form, "object": quote})


class QuoteDeleteView(CompanyRequiredMixin, View):
    template_name = "quote/confirm_delete.html"

    def get(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        return render(request, self.template_name, {"quote": quote})

    def post(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        quote.delete()
        messages.success(request, "Orçamento excluído com sucesso!")
        return redirect("quote:list")


class QuoteAddExpenseView(CompanyRequiredMixin, View):
    template_name = "quote/expense_form.html"

    def get(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        form = QuoteExpenseForm()
        return render(request, self.template_name, {"form": form, "quote": quote})

    def post(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        form = QuoteExpenseForm(request.POST)

        if form.is_valid():
            expense = form.save(commit=False)
            expense.quote = quote
            expense.save()
            quote.save()
            messages.success(request, "Despesa adicionada!")
            return redirect("quote:detail", pk=quote.pk)

        return render(request, self.template_name, {"form": form, "quote": quote})


class QuoteDeleteExpenseView(CompanyRequiredMixin, View):
    def post(self, request, pk, expense_pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        expense = get_object_or_404(QuoteExpense, pk=expense_pk, quote=quote)
        expense.delete()
        quote.save()
        messages.success(request, "Despesa removida!")
        return redirect("quote:detail", pk=pk)


class QuotePDFView(CompanyRequiredMixin, View):
    def get(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
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
                "company": request.user.account,
                "logo_url": logo_url,
            },
        )

        pdf = weasyprint.HTML(string=html).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="orcamento_{client_name}_{year}.pdf"'
        )
        return response


class QuoteSendView(CompanyRequiredMixin, View):
    def post(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)

        if not quote.client or not quote.client.email:
            messages.error(request, "Orçamento sem cliente ou email.")
            return redirect("quote:detail", pk=pk)

        quote.status = QuoteStatus.SENT
        quote.save()

        send_quote_email(quote, quote.client.email)

        messages.success(request, f"Orçamento enviado para {quote.client.email}!")
        return redirect("quote:detail", pk=pk)
