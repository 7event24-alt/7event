from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.urls import reverse_lazy

from .auth_views import CustomPasswordResetView


urlpatterns = [
    path(
        "reset/",
        CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy("login")),
        name="password_reset_confirm",
    ),
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("", include("django.contrib.auth.urls")),
]
