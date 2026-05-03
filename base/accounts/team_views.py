from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from base.accounts.models import User
from base.core.utils import get_base_url


class TeamListView(LoginRequiredMixin, View):
    template_name = "accounts/team.html"

    def get(self, request):
        if request.user.is_superuser:
            users = User.objects.filter(is_active=True).order_by("-created_at")
        else:
            users = User.objects.filter(invited_by=request.user, is_active=True).order_by("-created_at")
        return render(request, self.template_name, {"team_members": users})


class TeamCreateView(LoginRequiredMixin, View):
    template_name = "accounts/team_form.html"

    def post(self, request):
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        role = request.POST.get("role", "")

        if not email or not first_name:
            messages.error(request, "Preencha todos os campos obrigatórios.")
            return render(request, self.template_name, {"action": "create"})

        if User.objects.filter(email=email).exists():
            messages.error(request, "Este email já está cadastrado.")
            return render(request, self.template_name, {"action": "create"})

        import uuid
        token = uuid.uuid4().hex

        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            invite_token=token,
            invited_by=request.user,
        )

        from django.template.loader import render_to_string
        from django.core.mail import send_mail

        invite_url = f"{get_base_url(request)}/accounts/accept-invite/{token}/"

        try:
            html_message = render_to_string(
                "emails/team_invite.html",
                {"user": user, "invite_url": invite_url, "invited_by": request.user},
            )
            send_mail(
                f"Você foi convidado para participar do 7event",
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