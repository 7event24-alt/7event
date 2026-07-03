import stripe

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings

from base.accounts.models import Plan, PlanType, User
from base.payments.services.billing import (
    apply_preapproval_status,
    create_or_update_recurring_subscription,
    create_or_update_recurring_subscription_stripe,
    ensure_checkout_for_transaction,
    get_or_create_monthly_transaction,
    handle_stripe_checkout_completed,
    resume_scheduled_subscription,
    resume_scheduled_subscription_stripe,
    schedule_subscription_cancel_at_period_end,
    schedule_subscription_cancel_at_period_end_stripe,
)
from base.payments.services.mercadopago_client import MercadoPagoIntegrationError
from base.payments.services.mercadopago_client import get_preapproval
from base.support.models import SupportMessage, SupportSubject


class PlanListView(LoginRequiredMixin, View):
    template_name = "plans/list.html"

    def get(self, request):
        plans = Plan.objects.filter(is_visible=True, is_active=True).order_by("price_monthly")
        current_plan = request.user.get_plan() if request.user.is_authenticated else None
        subscription = getattr(request.user, "subscription", None)

        return render(
            request,
            self.template_name,
            {
                "plans": plans,
                "current_plan": current_plan,
                "current_plan_id": current_plan.id if current_plan else None,
                "subscription": subscription,
                "subscriptions_recurring_enabled": getattr(
                    settings,
                    "SUBSCRIPTIONS_RECURRING_ENABLED",
                    False,
                ),
            },
        )

    def post(self, request):
        """Handle plan selection - redirect to checkout"""
        plan_id = request.POST.get("plan_id")

        if not plan_id:
            return HttpResponseRedirect(reverse("plans:list"))

        try:
            plan = Plan.objects.get(id=plan_id, is_visible=True, is_active=True)
        except Plan.DoesNotExist:
            return HttpResponseRedirect(reverse("plans:list"))

        request.session["requested_plan_id"] = plan.id
        request.session["requested_plan_name"] = plan.name

        if plan.price_monthly == 0:
            return HttpResponseRedirect(reverse("plans:activate_free"))

        provider = getattr(settings, "PAYMENT_PROVIDER", "stripe")

        try:
            if provider == "stripe":
                _, _, checkout_url = create_or_update_recurring_subscription_stripe(
                    request.user, plan, request
                )
            elif getattr(settings, "SUBSCRIPTIONS_RECURRING_ENABLED", False):
                _, _, checkout_url = create_or_update_recurring_subscription(
                    request.user, plan, request
                )
            else:
                tx = get_or_create_monthly_transaction(request.user, plan)
                tx = ensure_checkout_for_transaction(tx, request, force_new=True)
                checkout_url = tx.checkout_url

            request.session["payment_link"] = checkout_url
            return HttpResponseRedirect(reverse("plans:waiting"))
        except MercadoPagoIntegrationError as exc:
            messages.error(request, str(exc))
            return HttpResponseRedirect(reverse("plans:list"))
        except ValueError as exc:
            messages.error(request, str(exc))
            return HttpResponseRedirect(reverse("plans:list"))

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
            messages.error(request, "Plano BASIC não disponível.")
            return HttpResponseRedirect(reverse("plans:list"))

        messages.success(request, f"Plano {free_plan.name} ativado com sucesso!")
        return HttpResponseRedirect(reverse("dashboard:home"))


class CancelSubscriptionView(LoginRequiredMixin, View):
    def post(self, request):
        if not getattr(settings, "SUBSCRIPTIONS_CANCEL_AT_PERIOD_END_ENABLED", True):
            messages.error(request, "Cancelamento de assinatura indisponivel no momento.")
            return HttpResponseRedirect(reverse("plans:list"))

        subscription = getattr(request.user, "subscription", None)
        if not subscription:
            messages.error(request, "Nenhuma assinatura ativa encontrada.")
            return HttpResponseRedirect(reverse("plans:list"))

        try:
            provider = getattr(settings, "PAYMENT_PROVIDER", "stripe")
            if provider == "stripe":
                schedule_subscription_cancel_at_period_end_stripe(subscription)
            else:
                schedule_subscription_cancel_at_period_end(subscription)
            messages.success(
                request,
                "Cancelamento agendado com sucesso. Seu acesso segue ativo ate o fim do ciclo pago.",
            )
        except Exception:
            messages.error(
                request,
                "Nao foi possivel agendar o cancelamento agora. Tente novamente em instantes.",
            )
        return HttpResponseRedirect(reverse("plans:list"))


class ResumeSubscriptionView(LoginRequiredMixin, View):
    def post(self, request):
        subscription = getattr(request.user, "subscription", None)
        if not subscription:
            messages.error(request, "Nenhuma assinatura encontrada para retomar.")
            return HttpResponseRedirect(reverse("plans:list"))

        try:
            provider = getattr(settings, "PAYMENT_PROVIDER", "stripe")
            if provider == "stripe":
                resume_scheduled_subscription_stripe(subscription)
            else:
                resume_scheduled_subscription(subscription)
            messages.success(
                request,
                "Assinatura retomada com sucesso. A cobranca recorrente foi mantida.",
            )
        except Exception:
            messages.error(
                request,
                "Nao foi possivel retomar a assinatura agora. Tente novamente em instantes.",
            )
        return HttpResponseRedirect(reverse("plans:list"))


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


class PaymentReturnView(LoginRequiredMixin, View):
    template_name = "plans/payment_return.html"
    flow_status = "pending"

    def get(self, request):
        preapproval_id = request.GET.get("preapproval_id") or request.GET.get("subscription_id") or ""
        if self.flow_status == "success" and preapproval_id:
            try:
                subscription = getattr(request.user, "subscription", None)
                if subscription and subscription.mp_subscription_id == preapproval_id:
                    payload = get_preapproval(preapproval_id)
                    apply_preapproval_status(subscription, payload)
            except Exception:
                pass

        session_id = request.GET.get("session_id", "")
        if self.flow_status == "success" and session_id.startswith("cs_"):
            try:
                stripe.api_key = settings.STRIPE_API_KEY
                session = stripe.checkout.Session.retrieve(session_id)
                if session.get("payment_status") == "paid" or session.get("status") == "complete":
                    handle_stripe_checkout_completed(session)
            except Exception:
                pass

        payment_id = (
            request.GET.get("payment_id")
            or request.GET.get("collection_id")
            or request.GET.get("preapproval_id")
            or request.GET.get("subscription_id")
            or ""
        )
        status = (
            request.GET.get("status")
            or request.GET.get("collection_status")
            or request.GET.get("preapproval_status")
            or ""
        )
        external_reference = request.GET.get("external_reference", "") or request.session.get(
            "requested_plan_name",
            "",
        )

        context = {
            "flow_status": self.flow_status,
            "payment_id": payment_id,
            "external_reference": external_reference,
            "status": status,
            "merchant_order_id": request.GET.get("merchant_order_id")
            or request.GET.get("preapproval_plan_id")
            or "",
        }
        return render(request, self.template_name, context)


class PaymentSuccessView(PaymentReturnView):
    flow_status = "success"


class PaymentPendingView(PaymentReturnView):
    flow_status = "pending"


class PaymentFailureView(PaymentReturnView):
    flow_status = "failure"


activate_free = ActivateFreeView.as_view()
waiting_confirmation = WaitingConfirmationView.as_view()
payment_success = PaymentSuccessView.as_view()
payment_pending = PaymentPendingView.as_view()
payment_failure = PaymentFailureView.as_view()
cancel_subscription = CancelSubscriptionView.as_view()
resume_subscription = ResumeSubscriptionView.as_view()
