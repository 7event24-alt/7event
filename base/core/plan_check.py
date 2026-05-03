from django.http import HttpResponseRedirect
from django.urls import reverse


class PlanCheckMixin:
    def get_plan_limit_key(self):
        return None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        plan = request.user.get_plan()
        if not plan:
            return HttpResponseRedirect(reverse("plans:list"))

        return super().dispatch(request, *args, **kwargs)


def check_plan_limit(model_class, limit_field):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            plan = request.user.get_plan()
            if not plan:
                return HttpResponseRedirect(reverse("plans:list"))

            limit = getattr(plan, limit_field, 0)

            if limit == 0:
                return view_func(request, *args, **kwargs)

            current_count = model_class.objects.filter(created_by=request.user).count()

            if current_count >= limit:
                return HttpResponseRedirect(reverse("plans:list"))

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator