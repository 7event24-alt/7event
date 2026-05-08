from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse


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


RESOURCE_CONFIG = {
    "clients": {"limit_field": "max_clients", "label": "clientes"},
    "jobs": {"limit_field": "max_jobs", "label": "trabalhos"},
    "quotes": {"limit_field": "max_quotes", "label": "orçamentos"},
    "expenses": {"limit_field": "max_expenses", "label": "despesas"},
    "personal_tasks": {"limit_field": "max_personal_tasks", "label": "tarefas pessoais"},
    "personal_agenda": {"limit_field": "max_personal_agenda_events", "label": "itens da agenda pessoal"},
}


def _default_user_count(model_class, user):
    queryset = model_class.objects.all()
    if hasattr(model_class, "created_by"):
        queryset = queryset.filter(created_by=user)
    elif hasattr(model_class, "performed_by"):
        queryset = queryset.filter(performed_by=user)
    elif hasattr(model_class, "user"):
        queryset = queryset.filter(user=user)

    if hasattr(model_class, "is_active"):
        queryset = queryset.filter(is_active=True)
    return queryset.count()


def check_resource_limit(user, resource_key, counter_fn=None):
    if user.is_superuser:
        return True, 0, 0

    plan = user.get_plan()
    if not plan:
        return False, 0, 0

    config = RESOURCE_CONFIG.get(resource_key)
    if not config:
        return True, 0, 0

    limit_field = config["limit_field"]
    limit = getattr(plan, limit_field, 0)

    # Convenção padronizada: 0 = sem limite
    if limit == 0:
        return True, 0, 0

    current = counter_fn() if counter_fn else 0
    return current < limit, current, limit


def build_plan_limit_message(resource_key, current, limit):
    config = RESOURCE_CONFIG.get(resource_key, {})
    label = config.get("label", "itens")
    return (
        f"Você atingiu o limite do seu plano para {label} "
        f"({current}/{limit}). Para criar mais, faça upgrade."
    )


def enforce_plan_limit_or_redirect(request, resource_key, counter_fn=None):
    allowed, current, limit = check_resource_limit(request.user, resource_key, counter_fn)
    if allowed:
        return None

    message = build_plan_limit_message(resource_key, current, limit)
    messages.warning(request, message)
    return HttpResponseRedirect(reverse("plans:list"))


def enforce_plan_limit_or_json(request, resource_key, counter_fn=None):
    allowed, current, limit = check_resource_limit(request.user, resource_key, counter_fn)
    if allowed:
        return None

    message = build_plan_limit_message(resource_key, current, limit)
    return JsonResponse(
        {
            "success": False,
            "code": "PLAN_LIMIT_REACHED",
            "message": message,
            "upgrade_url": reverse("plans:list"),
        },
        status=403,
    )
