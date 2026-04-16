from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import PasswordChangeForm
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone

from .forms import RegisterForm


# Simple logout view that handles GET
class SimpleLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("accounts:login")


# Simple logout for sidebar (works with GET)
def custom_logout(request):
    logout(request)
    return redirect("accounts:login")


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

            from django.contrib.auth import get_backends

            backend = get_backends()[0]
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            # Enviar email de boas-vindas
            try:
                from base.core.emails import send_welcome_email

                send_welcome_email(user)
            except Exception as e:
                print(f"Erro ao enviar email: {e}")

            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect("dashboard:home")
        return render(request, self.template_name, {"form": form})


register = RegisterView.as_view()


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
