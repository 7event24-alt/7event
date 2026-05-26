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
from base.core.utils import get_base_url
from base.jobs.models import JobStaff, JobStaffStatus
from base.core.plan_check import enforce_plan_limit_or_json


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

                    verification_url = f"https://7event.com.br/app/accounts/ativar/{user.verification_token}/"
                    
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

        # Buscar ou criar termo de privacidade ativo
        from .models import PrivacyTerm
        active_term = PrivacyTerm.objects.filter(is_active=True).first()
        if not active_term:
            active_term = PrivacyTerm.objects.create(
                version='1.0',
                content='Termo de Privacidade e Uso de Dados do 7event. Ao utilizar nossa plataforma, você concorda com a coleta e uso de suas informações conforme descrito neste termo. Para mais detalhes, entre em contato conosco.',
                is_active=True
            )

        return render(request, self.template_name, {
            "form": form,
            "privacy_term": active_term,
            "terms_accepted": False
        })

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
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

            # Salvar formulário (agora inclui novos campos como full_name, cpf, etc.)
            user = form.save(commit=False)
            
            # Associar plano padrão automaticamente se não houver
            if not user.plan:
                from .models import Plan
                import logging
                logger = logging.getLogger(__name__)
                
                logger.info(f"Usuário sem plano, tentando associar plano padrão...")
                default_plan = Plan.get_default()
                logger.info(f"Plan.get_default() retornou: {default_plan}")
                
                if default_plan:
                    user.plan = default_plan
                    logger.info(f"Plano associado: {default_plan.name} (tipo: {default_plan.type})")
                else:
                    # Tenta buscar qualquer plano ativo se o FREE não existir
                    any_plan = Plan.objects.filter(is_active=True).first()
                    logger.info(f"Tentando qualquer plano ativo: {any_plan}")
                    if any_plan:
                        user.plan = any_plan
                        logger.info(f"Plano ativo associado: {any_plan.name}")
                    else:
                        # Lista todos os planos para debug
                        all_plans = Plan.objects.all()
                        logger.error(f"Nenhum plano ativo encontrado. Planos no banco: {[(p.id, p.name, p.type, p.is_active) for p in all_plans]}")
                        # Cria um plano FREE se não houver nenhum
                        user.plan = Plan.objects.create(
                            type='free',
                            name='Grátis',
                            is_active=True,
                            max_users=1,
                            max_clients=10,
                            max_jobs=10,
                            max_expenses=10,
                            max_agenda_events=10,
                            can_associate_professionals=False,
                            job_creation_limit=-1
                        )
                        logger.info(f"Plano FREE criado automaticamente")
            
            # Salvar termo aceito
            accepted_term_id = request.POST.get("accepted_term_id")
            if accepted_term_id:
                from .models import PrivacyTerm
                try:
                    term = PrivacyTerm.objects.get(id=accepted_term_id)
                    user.accepted_term = term
                except PrivacyTerm.DoesNotExist:
                    pass
            
            user.save()
            form.save_m2m()  # Salva ManyToMany (se houver)

            # Enviar email de verificação
            logger = logging.getLogger(__name__)

            try:
                from base.core.emails import send_verification_email
                from django.urls import reverse

                base_url = get_base_url(request)

                verification_url = f"https://7event.com.br/app/accounts/ativar/{user.verification_token}/"

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

            # Disparo opcional de WhatsApp via n8n (nao bloqueia cadastro)
            try:
                from base.core.n8n import send_whatsapp_by_reason

                if user.phone:
                    send_whatsapp_by_reason(
                        phone=user.phone,
                        reason="user_registered",
                        nome=(user.first_name or user.full_name or user.username or ""),
                    )
            except Exception:
                logger.exception("Falha ao disparar WhatsApp de cadastro")

            return render(
                request, "accounts/registration_success.html", {"email": user.email}
            )

        from .models import PrivacyTerm
        active_term = PrivacyTerm.objects.filter(is_active=True).first()
        terms_accepted = request.POST.get("accept_privacy") == "on"
        return render(
            request, self.template_name, {"form": form, "form_data": request.POST, "privacy_term": active_term, "terms_accepted": terms_accepted}
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

            # Disparo opcional de WhatsApp via n8n (nao bloqueia ativacao)
            try:
                from base.core.n8n import send_whatsapp_by_reason

                if user.phone:
                    send_whatsapp_by_reason(
                        phone=user.phone,
                        reason="user_activated",
                        nome=(user.first_name or user.full_name or user.username or ""),
                    )
            except Exception:
                import logging

                logging.getLogger(__name__).exception(
                    "Falha ao disparar WhatsApp de ativacao"
                )

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

                    verification_url = f"https://7event.com.br/app/accounts/ativar/{user.verification_token}/"
                    
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

            verification_url = f"https://7event.com.br/app/accounts/ativar/{user.verification_token}/"
            
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
        from .forms import PersonalInfoForm, ProfessionalInfoForm, PrivacyForm

        personal_form = PersonalInfoForm(instance=request.user)
        professional_form = ProfessionalInfoForm(instance=request.user)
        privacy_form = PrivacyForm(instance=request.user)

        context = {
            "personal_form": personal_form,
            "professional_form": professional_form,
            "privacy_form": privacy_form,
        }

        if request.user.is_superuser:
            from .models import User

            context["total_users"] = User.objects.count()

        # Processar skills para o template (converter string para lista)
        if request.user.skills:
            context["skills_list"] = [s.strip() for s in request.user.skills.split(",") if s.strip()]
        else:
            context["skills_list"] = []

        return render(request, self.template_name, context)

    def dispatch(self, request, *args, **kwargs):
        # Handle photo upload even if user is not authenticated (return JSON, not redirect)
        if request.method == 'POST' and request.POST.get("photo_only"):
            if not request.user.is_authenticated:
                return JsonResponse({"success": False, "error": "Usuário não autenticado"}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        from .forms import PersonalInfoForm, ProfessionalInfoForm, PrivacyForm

        # Handle privacy toggle
        if request.POST.get('action') == 'toggle_privacy' or request.content_type == 'application/json':
            import json
            try:
                if request.content_type == 'application/json':
                    data = json.loads(request.body)
                    show_sensitive = data.get('show_sensitive_data', False)
                else:
                    show_sensitive = request.POST.get('show_sensitive_data') == 'true'
                
                request.user.show_sensitive_data = show_sensitive
                request.user.save(update_fields=['show_sensitive_data'])
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        # Handle photo upload
        if request.POST.get("delete_photo_only"):
            try:
                if request.user.photo:
                    request.user.photo.delete(save=False)
                    request.user.photo = None
                    request.user.updated_at = timezone.now()
                    request.user.save(update_fields=["photo", "updated_at"])
                return JsonResponse({"success": True})
            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)})

        if request.POST.get("photo_only"):
            try:
                photo = request.FILES.get("photo")
                if photo:
                    old_photo_name = request.user.photo.name if request.user.photo else ""
                    
                    request.user.photo = photo
                    request.user.updated_at = timezone.now()
                    request.user.save()

                    photo_url = request.user.photo.url if (request.user.photo and request.user.photo.name) else ""
                    
                    if old_photo_name and old_photo_name != request.user.photo.name:
                        try:
                            request.user.photo.storage.delete(old_photo_name)
                        except Exception:
                            pass
                    return JsonResponse({
                        "success": True,
                        "photo_url": photo_url,
                        "version": int(timezone.now().timestamp()),
                    })
                else:
                    return JsonResponse({"success": False, "error": "Nenhuma foto enviada"})
            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)})

        # Determine which form is being submitted
        form_type = request.POST.get('form_type')

        if form_type == 'personal':
            form = PersonalInfoForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Informações pessoais atualizadas com sucesso!")
                return redirect("accounts:profile")
            else:
                # Re-render with errors
                from .forms import ProfessionalInfoForm, PrivacyForm
                professional_form = ProfessionalInfoForm(instance=request.user)
                privacy_form = PrivacyForm(instance=request.user)
                return render(request, self.template_name, {
                    "personal_form": form,
                    "professional_form": professional_form,
                    "privacy_form": privacy_form,
                    "skills_list": [s.strip() for s in (request.user.skills or "").split(",") if s.strip()]
                })

        elif form_type == 'professional':
            form = ProfessionalInfoForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Dados profissionais atualizados com sucesso!")
                return redirect("accounts:profile")
            else:
                # Re-render with errors
                from .forms import PersonalInfoForm, PrivacyForm
                personal_form = PersonalInfoForm(instance=request.user)
                privacy_form = PrivacyForm(instance=request.user)
                return render(request, self.template_name, {
                    "personal_form": personal_form,
                    "professional_form": form,
                    "privacy_form": privacy_form,
                    "skills_list": [s.strip() for s in (request.user.skills or "").split(",") if s.strip()]
                })

        elif form_type == 'notifications':
            request.user.notify_via_whatsapp = bool(request.POST.get("notify_via_whatsapp"))
            request.user.notify_via_email = bool(request.POST.get("notify_via_email"))
            request.user.save(update_fields=["notify_via_whatsapp", "notify_via_email", "updated_at"])
            messages.success(request, "Preferencias de notificacao atualizadas com sucesso!")
            return redirect("accounts:profile")

        return redirect("accounts:profile")


profile = ProfileView.as_view()


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = "/app/accounts/profile/"

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
    from django.http import JsonResponse
    from .models import Notification
    
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Not found"}, status=404)


def get_timesince(dt):
    from django.utils.timesince import timesince

    return timesince(dt)


@csrf_exempt
def mark_all_as_read(request):
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    from .models import Notification
    
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
        return HttpResponseRedirect(reverse("accounts:notifications"))
    return HttpResponseRedirect(reverse("accounts:notifications"))


def can_view_sensitive_data_of(viewer, target_user):
    """
    Verifica se o viewer pode ver dados sensíveis (CPF/RG) do target_user.
    Regras:
    1. Próprio usuário sempre pode ver
    2. Target deve ter show_sensitive_data=True
    3. Deve existir JobStaff com status CONFIRMED ou PAID entre viewer (agência) e target
    """
    if viewer == target_user:
        return True
    
    if not target_user.show_sensitive_data:
        return False
    
    from base.jobs.models import JobStaff, JobStaffStatus
    # Verificar se existe JobStaff com status CONFIRMED ou PAID
    has_confirmed_job = JobStaff.objects.filter(
        job__created_by=viewer,
        professional=target_user,
        status__in=[JobStaffStatus.CONFIRMED, JobStaffStatus.PAID]
    ).exists()
    
    return has_confirmed_job


def user_profile_detail(request, user_id=None):
    """
    Perfil Profissional com lógica de acesso restrito.
    - Agência só acessa se status no JobStaff for CONFIRMED ou PAID
    - Dados sensíveis (CPF/RG) só aparecem se can_view_sensitive_data_of retornar True
    """
    from django.shortcuts import get_object_or_404
    from .models import User
    from base.jobs.models import JobStaff, JobStaffStatus
    
    profile_user = get_object_or_404(User, id=user_id) if user_id else request.user
    
    # Verificar se o viewer tem permissão para acessar este perfil
    can_view_full_profile = False
    can_view_sensitive = False
    
    if request.user.is_authenticated:
        if request.user == profile_user:
            # Próprio usuário - acesso completo
            can_view_full_profile = True
            can_view_sensitive = True
        elif request.user.is_superuser:
            # Admin - acesso completo
            can_view_full_profile = True
            can_view_sensitive = True
        else:
            # Verificar se existe JobStaff com status CONFIRMED ou PAID
            staff_entry = JobStaff.objects.filter(
                job__created_by=request.user,
                professional=profile_user
            ).first()
            
            if staff_entry and staff_entry.status in [JobStaffStatus.CONFIRMED, JobStaffStatus.PAID]:
                can_view_full_profile = True
                can_view_sensitive = can_view_sensitive_data_of(request.user, profile_user)
            else:
                # Redirecionar com mensagem de erro
                from django.contrib import messages
                messages.error(
                    request, 
                    "Acesso disponível apenas após o aceite do profissional"
                )
                from django.http import HttpResponseRedirect
                from django.urls import reverse
                return HttpResponseRedirect(reverse("dashboard:home"))
    
    # Verificar se o viewer é o próprio usuário (para mostrar toggle de privacidade)
    is_own_profile = request.user.is_authenticated and request.user == profile_user
    
    context = {
        "profile_user": profile_user,
        "can_view_full_profile": can_view_full_profile,
        "can_view_sensitive": can_view_sensitive,
        "is_own_profile": is_own_profile,
        "skills_list": [s.strip() for s in (profile_user.skills or "").split(",") if s.strip()],
        "full_name_display": (profile_user.full_name or profile_user.get_full_name() or "").strip(),
    }
    
    return render(request, "accounts/user_profile_detail.html", context)


class PersonalTasksView(LoginRequiredMixin, View):
    template_name = "accounts/personal_tasks.html"
    
    def get(self, request):
        from .models import PersonalTask
        tasks = PersonalTask.objects.filter(user=request.user, is_completed=False)
        tasks = tasks.order_by("-date", "is_completed", "time")
        
        # Tarefas de hoje (para exibição rápida)
        from django.utils import timezone
        today = timezone.now().date()
        today_tasks = PersonalTask.objects.filter(
            user=request.user,
            date=today,
            is_completed=False
        ).order_by("time")
        
        context = {
            "tasks": tasks,
            "today_tasks": today_tasks,
            "today": today,
            "pending_count": PersonalTask.objects.filter(user=request.user, is_completed=False).count(),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        from .models import PersonalTask
        import json
        
        try:
            data = json.loads(request.body)
            action = data.get("action")
            task_id = data.get("task_id")
            
            if action == "create":
                blocked = enforce_plan_limit_or_json(
                    request,
                    "personal_tasks",
                    counter_fn=lambda: PersonalTask.objects.filter(user=request.user).count(),
                )
                if blocked:
                    return blocked

                task = PersonalTask.objects.create(
                    user=request.user,
                    title=data.get("title"),
                    date=data.get("date"),
                    time=data.get("time") or None,
                )
                return JsonResponse({"success": True, "task_id": task.id})
            
            elif action == "toggle_complete":
                task = PersonalTask.objects.get(id=task_id, user=request.user)
                task.delete()
                return JsonResponse({"success": True, "deleted": True})
            
            elif action == "delete":
                task = PersonalTask.objects.get(id=task_id, user=request.user)
                task.delete()
                return JsonResponse({"success": True})

            elif action == "update":
                task = PersonalTask.objects.get(id=task_id, user=request.user)
                task.title = data.get("title", task.title)
                task.date = data.get("date", task.date)
                task.time = data.get("time") or None
                task.save(update_fields=["title", "date", "time"])
                return JsonResponse({"success": True})
            
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
        
        return JsonResponse({"success": False})


personal_tasks = PersonalTasksView.as_view()


class PersonalAgendaView(LoginRequiredMixin, View):
    template_name = "accounts/personal_agenda.html"

    @staticmethod
    def _build_time_window(payload):
        from datetime import datetime, timedelta

        if payload.get("start_time") and payload.get("end_time"):
            return payload.get("start_time"), payload.get("end_time")

        schedule_time = payload.get("time")
        duration = payload.get("duration", "1h")

        if duration == "all_day":
            return "00:00", "23:59"

        if not schedule_time:
            return None, None

        duration_map = {
            "30m": 30,
            "1h": 60,
            "2h": 120,
            "3h": 180,
            "4h": 240,
        }
        minutes = duration_map.get(duration, 60)
        start_dt = datetime.strptime(schedule_time, "%H:%M")
        end_dt = start_dt + timedelta(minutes=minutes)
        return start_dt.strftime("%H:%M"), end_dt.strftime("%H:%M")

    def get(self, request):
        from .models import PersonalAgendaEvent, PersonalAgendaStatus

        # Regra de UX: Agenda Pessoal sempre abre em "Todos" por padrao.
        filter_status = "all"
        events = PersonalAgendaEvent.objects.filter(user=request.user)

        events = events.order_by("date", "start_time")

        context = {
            "events": events,
            "filter_status": filter_status,
            "pending_count": PersonalAgendaEvent.objects.filter(
                user=request.user, status=PersonalAgendaStatus.PENDING
            ).count(),
            "completed_count": PersonalAgendaEvent.objects.filter(
                user=request.user, status=PersonalAgendaStatus.COMPLETED
            ).count(),
            "cancelled_count": PersonalAgendaEvent.objects.filter(
                user=request.user, status=PersonalAgendaStatus.CANCELLED
            ).count(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        from .models import PersonalAgendaEvent, PersonalAgendaStatus
        import json

        try:
            data = json.loads(request.body)
            action = data.get("action")
            event_id = data.get("event_id")

            if action == "create":
                blocked = enforce_plan_limit_or_json(
                    request,
                    "personal_agenda",
                    counter_fn=lambda: PersonalAgendaEvent.objects.filter(user=request.user).count(),
                )
                if blocked:
                    return blocked

                start_time, end_time = self._build_time_window(data)
                event = PersonalAgendaEvent.objects.create(
                    user=request.user,
                    title=(data.get("title") or "").strip(),
                    date=data.get("date"),
                    start_time=start_time,
                    end_time=end_time,
                    location=(data.get("location") or "").strip(),
                    description=(data.get("description") or "").strip(),
                    recurrence=data.get("recurrence") or "none",
                    recurrence_until=data.get("recurrence_until") or None,
                )
                return JsonResponse({"success": True, "event_id": event.id})

            if action == "update":
                event = PersonalAgendaEvent.objects.get(id=event_id, user=request.user)
                start_time, end_time = self._build_time_window(data)
                event.title = (data.get("title") or event.title).strip()
                event.date = data.get("date", event.date)
                if start_time:
                    event.start_time = start_time
                if end_time:
                    event.end_time = end_time
                event.location = (data.get("location") or event.location).strip()
                event.description = (data.get("description") or event.description).strip()
                event.recurrence = data.get("recurrence", event.recurrence) or "none"
                event.recurrence_until = data.get("recurrence_until") or None
                event.save()
                return JsonResponse({"success": True})

            if action == "set_status":
                event = PersonalAgendaEvent.objects.get(id=event_id, user=request.user)
                new_status = data.get("status")
                if new_status not in {
                    PersonalAgendaStatus.PENDING,
                    PersonalAgendaStatus.COMPLETED,
                    PersonalAgendaStatus.CANCELLED,
                }:
                    return JsonResponse({"success": False, "error": "Status inválido."})
                event.status = new_status
                event.save(update_fields=["status", "updated_at"])
                return JsonResponse({"success": True})

            if action == "delete":
                event = PersonalAgendaEvent.objects.get(id=event_id, user=request.user)
                event.delete()
                return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

        return JsonResponse({"success": False, "error": "Ação inválida."})


personal_agenda = PersonalAgendaView.as_view()
