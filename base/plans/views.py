from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib import messages

from base.accounts.models import Plan, PlanType, User


class PlanListView(LoginRequiredMixin, View):
    template_name = "plans/list.html"

    def get(self, request):
        # If user already has a plan with permission, redirect to dashboard
        if request.user.account and request.user.account.plan:
            plan = request.user.account.plan
            # Check if plan has access - for now allow if they have any active plan
            if request.user.account.is_active:
                return HttpResponseRedirect(reverse("dashboard:home"))

        # Get all visible plans
        plans = Plan.objects.filter(is_visible=True).order_by("price_monthly")

        return render(
            request,
            self.template_name,
            {"plans": plans},
        )

    def post(self, request):
        """Handle plan selection - redirect to waiting or payment"""
        plan_id = request.POST.get("plan_id")

        if not plan_id:
            return HttpResponseRedirect(reverse("plans:list"))

        try:
            plan = Plan.objects.get(id=plan_id, is_visible=True)
        except Plan.DoesNotExist:
            return HttpResponseRedirect(reverse("plans:list"))

        # Store requested plan in session
        request.session["requested_plan_id"] = plan.id
        request.session["requested_plan_name"] = plan.name
        request.session["payment_link"] = plan.payment_link or ""

        # Se é plano FREE, ativar diretamente
        if plan.price_monthly == 0:
            return HttpResponseRedirect(reverse("plans:activate_free"))

        # Notify superusers about plan request
        self.notify_superuser(request.user, plan)

        # Redirect to waiting page (com link de pagamento)
        return HttpResponseRedirect(reverse("plans:waiting"))

    def notify_superuser(self, user, plan):
        """Send email to superusers notifying about plan request"""
        from django.conf import settings

        superusers = User.objects.filter(is_superuser=True)

        if not superusers:
            return

        emails = [u.email for u in superusers if u.email]

        if not emails:
            return

        subject = f"Nova solicitação de plano - {user.get_full_name() or user.email}"

        message = f"""
Olá!

Um novo usuário solicitou um plano no 7event.

Detalhes do usuário:
- Nome: {user.get_full_name() or "Não informado"}
- Email: {user.email}
- Empresa: {user.account.name if user.account else "Não informada"}

Plano solicitado: {plan.name}

Acesse o painel de administração para aprovar a solicitação.

Atenciosamente,
Equipe 7event
"""

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                emails,
                fail_silently=True,
            )
        except Exception:
            pass  # Silently fail if email fails


plan_list = PlanListView.as_view()


class ActivateFreeView(LoginRequiredMixin, View):
    """Ativar plano FREE (BASIC) para o usuário"""

    def post(self, request):
        if not request.user.account:
            messages.error(request, "Você precisa de uma conta primeiro.")
            return HttpResponseRedirect(reverse("plans:list"))

        # Buscar plano FREE (BASIC)
        free_plan = Plan.objects.filter(type=PlanType.BASIC, is_active=True).first()

        if not free_plan:
            messages.error(request, "Plano FREE não disponível.")
            return HttpResponseRedirect(reverse("plans:list"))

        # Ativar plano FREE
        account = request.user.account
        account.plan = free_plan
        account.is_active = True
        account.save()

        messages.success(request, f"Plano {free_plan.name} ativado com sucesso!")
        return HttpResponseRedirect(reverse("dashboard:home"))


class WaitingConfirmationView(LoginRequiredMixin, View):
    """Página de aguardando confirmação do pagamento"""

    template_name = "plans/waiting.html"

    def get(self, request):
        plan_name = request.session.get("requested_plan_name", "Plano")
        payment_link = request.session.get("payment_link", "")
        return render(
            request,
            self.template_name,
            {"plan_name": plan_name, "payment_link": payment_link},
        )


activate_free = ActivateFreeView.as_view()
waiting_confirmation = WaitingConfirmationView.as_view()
