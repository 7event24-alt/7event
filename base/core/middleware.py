from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse

User = get_user_model()


class BlockedUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            if not request.user.is_active:
                from django.contrib.auth import logout

                logout(request)
                return redirect("accounts:login")

            if hasattr(request.user, "is_blocked") and request.user.is_blocked:
                from django.contrib.auth import logout

                logout(request)
                return redirect("accounts:login")

        return None


class AdminAccessMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith("/admin/"):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={request.path}")

            if not request.user.is_superuser:
                return redirect("dashboard:home")

        return None
