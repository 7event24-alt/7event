from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from base.accounts.models import User


class TeamRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_account_admin:
            return HttpResponseForbidden(
                "Apenas administradores podem gerenciar equipe."
            )
        return super().dispatch(request, *args, **kwargs)


class TeamListView(TeamRequiredMixin, View):
    template_name = "accounts/team.html"

    def get(self, request):
        users = User.objects.filter(account=request.user.account).order_by(
            "-created_at"
        )
        return render(request, self.template_name, {"team_members": users})


class TeamCreateView(TeamRequiredMixin, View):
    template_name = "accounts/team_form.html"

    def get(self, request):
        return render(request, self.template_name, {"action": "create"})

    def post(self, request):
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        role = request.POST.get("role", "")

        if not email or not first_name:
            messages.error(request, "Preencha todos os campos obrigatórios.")
            return render(request, self.template_name, {"action": "create"})

        if User.objects.filter(email=email, account=request.user.account).exists():
            messages.error(request, "Este email já está cadastrado na equipe.")
            return render(request, self.template_name, {"action": "create"})

        import uuid

        token = uuid.uuid4().hex

        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            account=request.user.account,
            role=role,
            is_active=True,
            invite_token=token,
            invited_by=request.user,
        )

        from django.template.loader import render_to_string
        from django.core.mail import send_mail

        invite_url = (
            f"{request.scheme}://{request.get_host()}/accounts/accept-invite/{token}/"
        )

        try:
            html_message = render_to_string(
                "emails/team_invite.html",
                {"user": user, "invite_url": invite_url, "invited_by": request.user},
            )
            send_mail(
                f"Você foi convidado para a equipe {request.user.account.name}",
                "Você foi convidado para fazer parte da equipe.",
                "noreply@7event.com.br",
                [email],
                html_message=html_message,
            )
            messages.success(request, "Convite enviado com sucesso!")
        except Exception as e:
            messages.warning(request, f"Membro criado, mas email não enviou: {e}")

        return redirect("accounts:team")


team_list = TeamListView.as_view()
team_create = TeamCreateView.as_view()
