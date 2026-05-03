from django.core.cache import cache


def support_context(request):
    if request.user.is_authenticated and request.user.is_superuser:
        from base.support.models import SupportMessage

        unread_count = cache.get("unread_support_count")
        if unread_count is None:
            unread_count = SupportMessage.objects.filter(is_read=False).count()
            cache.set("unread_support_count", unread_count, 300)
        return {"unread_support_count": unread_count}
    return {}


def clear_support_cache():
    cache.delete("unread_support_count")


def user_plan_context(request):
    if request.user.is_authenticated:
        plan = request.user.get_plan()

        if plan is None:
            return {"user_plan": None, "user_plan_badge": "FREE"}

        plan_badge = "FREE"
        if plan.type == "professional":
            plan_badge = "PRO"
        elif plan.type == "business":
            plan_badge = "BSC"

        return {
            "user_plan": plan,
            "user_plan_badge": plan_badge,
        }
    return {}