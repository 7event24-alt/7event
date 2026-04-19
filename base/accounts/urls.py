from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import team_views
from . import accept_invite_views
from . import api_quick_worker

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        views.CustomLoginView.as_view(
            template_name="registration/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(
            template_name="registration/logged_out.html", next_page="/auth/login/"
        ),
        name="logout",
    ),
    # Simple logout that works
    path(
        "logout-simple/",
        views.custom_logout,
        name="logout_simple",
    ),
    # Also redirect /sair/ to login page
    path(
        "sair/",
        auth_views.LogoutView.as_view(next_page="/auth/login/"),
        name="logout_get",
    ),
    path("register/", views.register, name="register"),
    path(
        "cadastro-sucesso/",
        views.RegistrationSuccessView.as_view(),
        name="registration_success",
    ),
    path(
        "ativar/<str:token>/",
        views.ActivateAccountView.as_view(),
        name="activate_account",
    ),
    path("ativado/", views.ActivationSuccessView.as_view(), name="activation_success"),
    path("reativar/", views.ResendActivationView.as_view(), name="resend_activation"),
    path(
        "conta-inativa/", views.AccountInactiveView.as_view(), name="account_inactive"
    ),
    path(
        "admin/resend-activation/<int:user_id>/",
        views.AdminResendActivationView.as_view(),
        name="admin_resend_activation",
    ),
    path("profile/", views.profile, name="profile"),
    path("password/", views.password_change, name="password_change"),
    path("notificacoes/", views.notifications, name="notifications"),
    path("notificacoes/api/", views.notifications_api, name="notifications_api"),
    path(
        "notificacoes/api/contagem/",
        views.notifications_unread_count_api,
        name="notifications_unread_count_api",
    ),
    path(
        "notificacoes/marcar-lida/<int:notification_id>/",
        views.mark_as_read,
        name="mark_notification_read",
    ),
    path(
        "notificacoes/marcar-todas/",
        views.mark_all_as_read,
        name="mark_all_read",
    ),
    path("equipe/", team_views.team_list, name="team"),
    path("equipe/novo/", team_views.team_create, name="team_create"),
    path(
        "accept-invite/<str:token>/",
        accept_invite_views.accept_invite,
        name="accept_invite",
    ),
    path("api/quick-worker/", api_quick_worker.quick_worker, name="quick_worker"),
]
