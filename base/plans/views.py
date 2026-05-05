from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib import messages

from base.accounts.models import Plan, PlanType, User
from base.support.models import SupportMessage, SupportSubject


class PlanListView(LoginRequiredMixin, View):
    template_name = "plans/list.html"

    def get(self, request):
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

        request.session["requested_plan_id"] = plan.id
        request.session["requested_plan_name"] = plan.name
        request.session["payment_link"] = plan.payment_link or ""

        if plan.price_monthly == 0:
            return HttpResponseRedirect(reverse("plans:activate_free"))

        self.notify_superuser(request.user, plan)
        self.create_upgrade_support_message(request.user, plan)

        return HttpResponseRedirect(reverse("plans:waiting"))

    def create_upgrade_support_message(self, user, plan):
        """Create support message notifying superusers about upgrade request."""
        user_name = user.get_full_name() or user.username or "Nao informado"
        current_plan = user.get_plan()
        current_plan_name = current_plan.name if current_plan else "Nao informado"
        phone = user.phone or "Nao informado"

        message = (
            "Solicitacao de upgrade de plano.\n\n"
            f"Cliente: {user_name}\n"
            f"Email: {user.email or 'Nao informado'}\n"
            f"Telefone: {phone}\n"
            f"Plano atual: {current_plan_name}\n"
            f"Plano solicitado: {plan.name}\n"
            f"ID do usuario: {user.id}\n"
        )

        SupportMessage.objects.create(
            name=user_name,
            email=user.email or "noreply@7event.com.br",
            phone=user.phone or "",
            subject=SupportSubject.PLANOS,
            message=message,
            user=user,
            is_read=False,
        )

        from base.core.context_processors import clear_support_cache

        clear_support_cache()

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
            pass


plan_list = PlanListView.as_view()


class ActivateFreeView(LoginRequiredMixin, View):
    """Ativar plano FREE para o usuário"""

    def post(self, request):
        free_plan = Plan.objects.filter(type=PlanType.FREE, is_active=True).first()

        if not free_plan:
            messages.error(request, "Plano FREE não disponível.")
            return HttpResponseRedirect(reverse("plans:list"))

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
