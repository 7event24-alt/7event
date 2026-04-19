from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView, LoginView
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django import forms
from django.db import models
from django.contrib.sites.models import Site
from django.conf import settings

from .forms import RegisterForm


def get_base_url(request):
    """Obtém URL base de forma segura, sem depender do Site.objects.get_current()"""
    try:
        site = Site.objects.get_current()
        return f"https://{site.domain}"
    except Exception:
        return request.build_absolute_uri("/")[:-1]


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST.get("username"):
            context["username_value"] = self.request.POST.get("username")
        return context

    def form_invalid(self, form):
        username = self.request.POST.get("username", "")
        password = self.request.POST.get("password", "")

        if username and password:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                user = User.objects.get(
                    models.Q(username__iexact=username)
                    | models.Q(email__iexact=username)
                    | models.Q(phone__iexact=username)
                )
                if not user.is_active:
                    from django.http import HttpResponseRedirect
                    from django.urls import reverse

                    return HttpResponseRedirect(
                        reverse("accounts:account_inactive") + f"?email={user.email}"
                    )
            except User.DoesNotExist:
                pass

        if username and password:
            messages.error(
                self.request, "Usuário ou senha incorretos. Tente novamente."
            )
        elif not username:
            messages.error(self.request, "Por favor, insira seu usuário.")
        elif not password:
            messages.error(self.request, "Por favor, insira sua senha.")

        return super().form_invalid(form)

    def get_success_url(self):
        # Use Django's default logic but handle site errors gracefully
        url = super().get_success_url()
        if not url:
            from django.conf import settings

            return settings.LOGIN_REDIRECT_URL
        return url


class AccountInactiveView(View):
    template_name = "accounts/account_inactive.html"

    def get(self, request):
        email = request.GET.get("email", "")
        return render(request, self.template_name, {"email": email})


# Simple logout view that handles GET
class SimpleLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("accounts:login")


# Simple logout for sidebar (works with GET)
def custom_logout(request):
    logout(request)
    return redirect("accounts:login")


class AdminResendActivationView(View):
    """View para reenviar email de ativação a partir do admin"""

    def get(self, request, user_id):
        from django.contrib.auth.decorators import login_required
        from django.contrib.admin import site

        if not request.user.is_superuser:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Acesso restrito a administradores.")

        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)

            if user.is_active:
                from django.contrib import messages

                messages.info(request, f"O usuário {user.email} já está ativo.")
            else:
                import secrets

                user.verification_token = secrets.token_urlsafe(32)
                user.save()

                try:
                    from base.core.emails import send_verification_email

                    base_url = get_base_url(request)

                    verification_url = (
                        f"{base_url}/accounts/ativar/{user.verification_token}/"
                    )
                    send_verification_email(user, verification_url)

                    from django.contrib import messages

                    messages.success(
                        request, f"Email de ativação enviado para {user.email}!"
                    )
                except Exception as e:
                    from django.contrib import messages

                    messages.error(request, f"Erro ao enviar email: {e}")

        except User.DoesNotExist:
            from django.contrib import messages

            messages.error(request, "Usuário não encontrado.")

        return redirect("/admin/accounts/user/")


class RegistrationSuccessView(View):
    template_name = "accounts/registration_success.html"

    def get(self, request):
        email = request.GET.get("email", "")
        return render(request, self.template_name, {"email": email})


class RegisterView(View):
    template_name = "accounts/register.html"
    form_class = RegisterForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Gerar username automaticamente do email
            email = form.cleaned_data.get("email", "")
            base_username = email.split("@")[0] if email else "user"

            # Verificar se username já existe e adicionar sufixo
            from django.contrib.auth import get_user_model

            User = get_user_model()
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Definir username antes de salvar
            form.instance.username = username

            # Salvar formulário (que agora cria a empresa automaticamente)
            user = form.save()

            # Garantir que tem empresa
            if not user.account:
                from .models import Account, Plan, AccountType
                from django.utils.text import slugify
                import uuid

                company_name = (
                    f"{user.first_name} {user.last_name}".strip()
                    or user.email.split("@")[0]
                )
                base_slug = slugify(company_name)
                if not base_slug:
                    base_slug = f"company-{uuid.uuid4().hex[:8]}"

                slug = base_slug
                while Account.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                account = Account.objects.create(
                    name=company_name,
                    slug=slug,
                    account_type=AccountType.COMPANY,
                    plan=Plan.get_default(),
                    is_active=True,
                )
                user.account = account
                user.save()

            # Enviar email de verificação
            import logging

            logger = logging.getLogger(__name__)

            try:
                from base.core.emails import send_verification_email
                from django.urls import reverse

                base_url = get_base_url(request)

                verification_url = (
                    f"{base_url}/accounts/ativar/{user.verification_token}/"
                )

                email_sent = send_verification_email(user, verification_url)

                if not email_sent:
                    logger.error(
                        f"Falha ao enviar email de verificacao para {user.email}"
                    )
                    messages.warning(
                        request,
                        "Cadastro realizado, mas houve problema ao enviar email de verificação. Verifique sua caixa de spam ou solicite reenvio.",
                    )
                else:
                    logger.info(f"Email de verificacao enviado para {user.email}")

            except Exception as e:
                import traceback

                logger.error(
                    f"Erro ao enviar email de verificacao: {e}\n{traceback.format_exc()}"
                )
                messages.warning(
                    request,
                    "Cadastro realizado, mas houve problema ao enviar email de verificação. Verifique sua caixa de spam ou solicite reenvio.",
                )

            messages.success(
                request,
                "Cadastro realizado! Verifique seu email para ativar sua conta.",
            )
            return render(
                request, "accounts/registration_success.html", {"email": user.email}
            )

        return render(
            request, self.template_name, {"form": form, "form_data": request.POST}
        )


register = RegisterView.as_view()


class ActivationSuccessView(View):
    template_name = "accounts/activation_success.html"

    def get(self, request):
        return render(request, self.template_name)


class ActivateAccountView(View):
    template_name = "accounts/account_activated.html"

    def get(self, request, token=None):
        User = get_user_model()
        try:
            user = User.objects.get(verification_token=token)
            user.is_verified = True
            user.is_active = True
            user.verification_token = ""
            user.save()

            return render(request, self.template_name)

        except User.DoesNotExist:
            return render(
                request,
                "accounts/activation_error.html",
                {"success": False, "error": "Token inválido ou expirado."},
            )


class ResendActivationView(View):
    template_name = "accounts/resend_activation.html"

    def get(self, request):
        email = request.GET.get("email", "")

        # Se passou email na URL, tentar reenviar automaticamente
        if email:
            User = get_user_model()
            user = User.objects.filter(email__iexact=email).first()

            if user:
                if user.is_active:
                    messages.info(
                        request, "Esta conta já está ativa. Você pode fazer login."
                    )
                    return render(
                        request, self.template_name, {"email": email, "sent": True}
                    )

                # Reenviar email
                import secrets

                user.verification_token = secrets.token_urlsafe(32)
                user.save()

                try:
                    from base.core.emails import send_verification_email

                    base_url = get_base_url(request)

                    verification_url = (
                        f"{base_url}/accounts/ativar/{user.verification_token}/"
                    )
                    send_verification_email(user, verification_url)

                    return render(
                        request, self.template_name, {"email": email, "sent": True}
                    )
                except Exception as e:
                    messages.error(
                        request, "Erro ao enviar email. Tente novamente mais tarde."
                    )
                    print(f"Erro ao enviar email: {e}")
            else:
                messages.error(request, "Email não encontrado.")

        return render(request, self.template_name, {"email": email})

    def post(self, request):
        email = request.POST.get("email", "").strip()
        User = get_user_model()

        user = User.objects.filter(email__iexact=email).first()

        if not user:
            messages.error(request, "Email não encontrado.")
            return render(request, self.template_name, {"email": email})

        if user.is_active:
            messages.info(request, "Esta conta já está ativa. Você pode fazer login.")
            return render(request, self.template_name, {"email": email, "sent": True})

        import secrets

        user.verification_token = secrets.token_urlsafe(32)
        user.save()

        try:
            from base.core.emails import send_verification_email

            base_url = get_base_url(request)

            verification_url = f"{base_url}/accounts/ativar/{user.verification_token}/"
            send_verification_email(user, verification_url)

            messages.success(
                request,
                "Email de ativação enviado! Verifique sua caixa de entrada.",
            )
            return render(request, self.template_name, {"email": email, "sent": True})
        except Exception as e:
            messages.error(request, "Erro ao enviar email. Tente novamente mais tarde.")
            print(f"Erro ao enviar email: {e}")

        return render(request, self.template_name, {"email": email})


class ProfileView(LoginRequiredMixin, View):
    template_name = "accounts/profile.html"

    def get(self, request):
        from .forms import UserProfileForm

        form = UserProfileForm(instance=request.user)

        context = {"form": form}

        if request.user.is_superuser:
            from .models import Account, User

            context["total_accounts"] = Account.objects.count()
            context["total_users"] = User.objects.count()

        return render(request, self.template_name, context)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        from .forms import UserProfileForm

        if request.POST.get("photo_only"):
            photo = request.FILES.get("photo")
            if photo:
                old_photo = request.user.photo

                request.user.photo = photo
                request.user.updated_at = timezone.now()
                request.user.save()

                if old_photo:
                    try:
                        old_photo.delete(save=False)
                    except Exception:
                        pass
            return JsonResponse({"success": True})

        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            old_photo = form.instance.photo
            old_photo_path = request.user.photo.path if request.user.photo else None

            form.save()

            new_photo = form.instance.photo
            if old_photo and old_photo != new_photo:
                try:
                    if old_photo_path and hasattr(old_photo, "path"):
                        old_photo.delete(save=False)
                except Exception:
                    pass

            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect("accounts:profile")
        return render(request, self.template_name, {"form": form})


profile = ProfileView.as_view()


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = "/accounts/profile/"

    def form_valid(self, form):
        messages.success(self.request, "Senha alterada com sucesso!")
        return super().form_valid(form)


password_change = CustomPasswordChangeView.as_view()


def notifications(request):
    from .models import Notification

    notifications_list = Notification.objects.filter(user=request.user).order_by(
        "-created_at"
    )[:50]

    return render(
        request, "accounts/notifications.html", {"notifications": notifications_list}
    )


def notifications_api(request):
    from .models import Notification

    if not request.user.is_authenticated:
        return JsonResponse({"notifications": [], "unread_count": 0})

    notifications_list = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by("-created_at")[:20]

    data = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "action_url": n.action_url,
            "notification_type": n.notification_type,
            "is_read": n.is_read,
            "created_at": n.created_at.strftime("%d/%m/%Y %H:%M"),
            "timesince": get_timesince(n.created_at),
        }
        for n in notifications_list
    ]

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return JsonResponse({"notifications": data, "unread_count": unread_count})


def notifications_unread_count_api(request):
    from .models import Notification

    if not request.user.is_authenticated:
        return JsonResponse({"unread_count": 0})

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return JsonResponse({"unread_count": unread_count})


@csrf_exempt
def mark_as_read(request, notification_id):
    from .models import Notification

    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Notificação não encontrada"})


def get_timesince(dt):
    from django.utils.timesince import timesince

    return timesince(dt)


@csrf_exempt
@csrf_exempt
def mark_all_as_read(request):
    from .models import Notification

    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})
