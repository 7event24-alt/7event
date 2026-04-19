from django.core.cache import cache


def support_context(request):
    """Adiciona contagem de mensagens de suporte não lidas ao contexto"""
    if request.user.is_authenticated and request.user.is_superuser:
        from base.support.models import SupportMessage

        unread_count = cache.get("unread_support_count")
        if unread_count is None:
            unread_count = SupportMessage.objects.filter(is_read=False).count()
            cache.set("unread_support_count", unread_count, 300)  # 5 minutos
        return {"unread_support_count": unread_count}
    return {}


def clear_support_cache():
    """Limpa o cache de mensagens de suporte"""
    cache.delete("unread_support_count")


def user_plan_context(request):
    """Adiciona informações do plano do usuário ao contexto"""
    if request.user.is_authenticated and request.user.account:
        account = request.user.account
        plan = account.plan

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
