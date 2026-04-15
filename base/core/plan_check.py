from django.http import HttpResponseRedirect
from django.urls import reverse


class PlanCheckMixin:
    """Mixin to verify user has an active plan before allowing create operations"""

    def get_plan_limit_key(self):
        """Override in subclasses - return the model to check"""
        return None

    def dispatch(self, request, *args, **kwargs):
        # Skip check for superusers
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Skip if no account
        if not hasattr(request.user, "account") or not request.user.account:
            return super().dispatch(request, *args, **kwargs)

        # Skip if account doesn't have a plan
        account = request.user.account
        if not account.plan:
            return HttpResponseRedirect(reverse("plans:list"))

        # Check if account is active
        if not account.is_active:
            return HttpResponseRedirect(reverse("plans:list"))

        return super().dispatch(request, *args, **kwargs)


def check_plan_limit(model_class, limit_field):
    """
    Decorator to check if user has reached their plan limit
    Usage: @check_plan_limit(Client, 'max_clients')
    """

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if not hasattr(request.user, "account") or not request.user.account:
                return HttpResponseRedirect(reverse("plans:list"))

            account = request.user.account

            if not account.plan:
                return HttpResponseRedirect(reverse("plans:list"))

            if not account.is_active:
                return HttpResponseRedirect(reverse("plans:list"))

            # Get limit from plan
            limit = getattr(account.plan, limit_field, 0)

            if limit == 0:  # Unlimited
                return view_func(request, *args, **kwargs)

            # Count current items
            current_count = model_class.objects.filter(account=account).count()

            if current_count >= limit:
                # User has reached their limit
                return HttpResponseRedirect(reverse("plans:list"))

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
