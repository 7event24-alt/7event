from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View

User = get_user_model()


class AcceptInviteView(View):
    template_name = "accounts/accept_invite.html"

    def get(self, request, token):
        user = get_object_or_404(User, invite_token=token)

        if not user.invite_token:
            messages.error(request, "Este convite já foi usado ou é inválido.")
            return redirect("accounts:login")

        return render(
            request,
            self.template_name,
            {"user": user, "token": token, "invited_by": user.invited_by},
        )

    def post(self, request, token):
        user = get_object_or_404(User, invite_token=token)
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if not password1 or not password2:
            messages.error(request, "Preencha os campos de senha.")
            return render(request, self.template_name, {"user": user, "token": token})

        if password1 != password2:
            messages.error(request, "As senhas não conferem.")
            return render(request, self.template_name, {"user": user, "token": token})

        if len(password1) < 8:
            messages.error(request, "A senha deve ter pelo menos 8 caracteres.")
            return render(request, self.template_name, {"user": user, "token": token})

        user.set_password(password1)
        user.invite_token = ""
        user.is_verified = True
        user.save()

        messages.success(request, "Conta criada com sucesso! Faça login.")
        return redirect("accounts:login")


accept_invite = AcceptInviteView.as_view()
