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
from base.services.models import Service
from base.accounts.models import Notification, NotificationType
from .models import Quote, QuoteExpense, QuoteService
from .forms import QuoteForm, QuoteExpenseForm, QuoteServiceForm


class CompanyRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
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
        services = Service.objects.filter(account=company, is_active=True)
        service_form = QuoteServiceForm(account=company)

        selected_services = []
        service_ids = request.GET.getlist("services")
        if service_ids:
            selected_services = Service.objects.filter(
                pk__in=service_ids, account=company
            )

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "services": services,
                "selected_services": selected_services,
                "service_form": service_form,
            },
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

            service_ids = request.POST.getlist("service_ids")
            for service_id in service_ids:
                try:
                    service = Service.objects.get(pk=service_id, account=company)
                    quantity = int(request.POST.get(f"quantity_{service_id}", 1))
                    custom_price = request.POST.get(f"custom_price_{service_id}")
                    QuoteService.objects.create(
                        quote=quote,
                        service=service,
                        quantity=quantity,
                        custom_price=Decimal(custom_price) if custom_price else None,
                    )
                except Service.DoesNotExist:
                    pass

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

        services = Service.objects.filter(account=company, is_active=True)
        return render(
            request,
            self.template_name,
            {"form": form, "services": services},
        )


class QuoteDetailView(CompanyRequiredMixin, View):
    template_name = "quote/detail.html"

    def get(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        expenses = quote.expenses.all()
        services = quote.services.all()
        return render(
            request,
            self.template_name,
            {"quote": quote, "expenses": expenses, "services": services},
        )


class QuoteUpdateView(CompanyRequiredMixin, View):
    template_name = "quote/form.html"

    def get(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        form = QuoteForm(instance=quote, account=request.user.account)
        services = Service.objects.filter(account=request.user.account, is_active=True)
        return render(
            request,
            self.template_name,
            {"form": form, "object": quote, "services": services},
        )

    def post(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        form = QuoteForm(request.POST, instance=quote, account=request.user.account)

        if form.is_valid():
            quote = form.save(commit=False)
            quote.labor_cost = quote.hourly_rate * quote.work_hours
            quote.save()

            existing_service_ids = set(
                quote.services.values_list("service_id", flat=True)
            )
            new_service_ids = set(int(x) for x in request.POST.getlist("service_ids"))

            for service_id in existing_service_ids - new_service_ids:
                quote.services.filter(service_id=service_id).delete()

            for service_id in new_service_ids - existing_service_ids:
                try:
                    service = Service.objects.get(
                        pk=service_id, account=request.user.account
                    )
                    quantity = int(request.POST.get(f"quantity_{service_id}", 1))
                    custom_price = request.POST.get(f"custom_price_{service_id}")
                    QuoteService.objects.create(
                        quote=quote,
                        service=service,
                        quantity=quantity,
                        custom_price=Decimal(custom_price) if custom_price else None,
                    )
                except Service.DoesNotExist:
                    pass

            for service_id in existing_service_ids & new_service_ids:
                try:
                    qs = quote.services.filter(service_id=service_id)
                    if qs.exists():
                        qs.update(
                            quantity=int(request.POST.get(f"quantity_{service_id}", 1)),
                            custom_price=Decimal(
                                request.POST.get(f"custom_price_{service_id}")
                            )
                            if request.POST.get(f"custom_price_{service_id}")
                            else None,
                        )
                except:
                    pass

            quote.save()
            messages.success(request, "Orçamento atualizado com sucesso!")
            return redirect("quote:detail", pk=quote.pk)

        services = Service.objects.filter(account=request.user.account, is_active=True)
        return render(
            request,
            self.template_name,
            {"form": form, "object": quote, "services": services},
        )


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


class QuoteAddServiceView(CompanyRequiredMixin, View):
    template_name = "quote/service_form.html"

    def get(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        services = Service.objects.filter(account=request.user.account, is_active=True)
        form = QuoteServiceForm()
        return render(
            request,
            self.template_name,
            {"form": form, "quote": quote, "services": services},
        )

    def post(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        form = QuoteServiceForm(request.POST)

        if form.is_valid():
            service = form.save(commit=False)
            service.quote = quote
            service.save()
            quote.save()
            messages.success(request, "Serviço adicionado!")
            return redirect("quote:detail", pk=quote.pk)

        services = Service.objects.filter(account=request.user.account, is_active=True)
        return render(
            request,
            self.template_name,
            {"form": form, "quote": quote, "services": services},
        )


class QuoteDeleteServiceView(CompanyRequiredMixin, View):
    def post(self, request, pk, service_pk):
        quote = get_object_or_404(Quote, pk=pk, account=request.user.account)
        service = get_object_or_404(QuoteService, pk=service_pk, quote=quote)
        service.delete()
        quote.save()
        messages.success(request, "Serviço removido!")
        return redirect("quote:detail", pk=pk)


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
        services = quote.services.all()

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
                "services": services,
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
