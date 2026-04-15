from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.mail import send_mail

from base.accounts.models import Plan, User


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
        """Handle plan selection - redirect to payment link"""
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

        # Notify superusers about plan request
        self.notify_superuser(request.user, plan)

        # Redirect to payment link
        if plan.payment_link:
            return HttpResponseRedirect(plan.payment_link)

        return HttpResponseRedirect(reverse("plans:list"))

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
