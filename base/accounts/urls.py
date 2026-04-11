from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
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
]
