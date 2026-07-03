from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from decimal import Decimal
from urllib.parse import urlencode

from .models import Quote, QuoteExpense, QuoteStatus
from .forms import QuoteForm, QuoteExpenseForm
from base.core.plan_check import enforce_plan_limit_or_redirect


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
        blocked = enforce_plan_limit_or_redirect(
            request,
            "quotes",
            counter_fn=lambda: Quote.objects.filter(created_by=request.user, is_active=True).count(),
        )
        if blocked:
            return blocked

        user = request.user
        form = QuoteForm(created_by=user, hide_status=True)
        return render(
            request,
            self.template_name,
            {"form": form},
        )

    def post(self, request):
        blocked = enforce_plan_limit_or_redirect(
            request,
            "quotes",
            counter_fn=lambda: Quote.objects.filter(created_by=request.user, is_active=True).count(),
        )
        if blocked:
            return blocked

        user = request.user
        post_data = request.POST.copy()
        post_data["status"] = QuoteStatus.CREATED
        form = QuoteForm(post_data, created_by=user, hide_status=True)

        if form.is_valid():
            quote = form.save(commit=False)
            quote.created_by = user
            quote.status = QuoteStatus.CREATED
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
            {
                "quote": quote,
                "expenses": expenses,
                "can_send_email": bool(quote.client and quote.client.email),
            },
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
        wants_json = request.headers.get("x-requested-with") == "XMLHttpRequest"
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

            if wants_json:
                return JsonResponse({"success": True, "expense_id": expense.pk})

            messages.success(request, "Despesa adicionada!")
            return redirect("quote:detail", pk=quote.pk)

        if wants_json:
            first_error = "Não foi possível adicionar a despesa."
            if form.errors:
                first_field = next(iter(form.errors))
                first_error = form.errors[first_field][0]
            return JsonResponse({"success": False, "error": first_error}, status=400)

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

        platform_logo_url = request.build_absolute_uri("/static/img/logo7event.png")
        company = quote.created_by
        company_logo_url = None
        company_display_name = "7event"
        if company and company.company_logo:
            company_logo_url = request.build_absolute_uri(company.company_logo.url)
        if company:
            legal_name = (company.legal_name or "").strip()
            generic_legal_names = {"conta profissional", "conta business", "conta"}
            use_legal_name = bool(legal_name) and legal_name.lower() not in generic_legal_names
            company_display_name = (
                legal_name if use_legal_name else None
                or company.get_full_name()
                or company.username
                or "7event"
            )

        html = render_to_string(
            "quote/pdf.html",
            {
                "quote": quote,
                "expenses": expenses,
                "created_by": user,
                "company": company,
                "company_logo_url": company_logo_url,
                "company_display_name": company_display_name,
                "platform_logo_url": platform_logo_url,
            },
        )

        import weasyprint
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

        messages.success(request, f"Orçamento enviado para {quote.client.email}!")
        return redirect("quote:detail", pk=pk)


class QuoteCreateJobView(LoginRequiredMixin, View):
    def get(self, request, pk):
        user = request.user
        if user.is_superuser:
            quote = get_object_or_404(Quote, pk=pk, is_active=True)
        else:
            quote = get_object_or_404(Quote, pk=pk, created_by=user, is_active=True)

        if quote.status != QuoteStatus.ACCEPTED:
            messages.error(request, "Apenas orçamentos aceitos podem gerar trabalhos.")
            return redirect("quote:detail", pk=quote.pk)

        params = {
            "quote_id": quote.pk,
            "client": quote.client_id or "",
            "title": quote.title,
            "description": "\n\n".join([x for x in [quote.description, quote.notes] if x]).strip(),
            "cache": quote.total,
        }
        return redirect(f"/app/trabalhos/novo/?{urlencode(params)}")
