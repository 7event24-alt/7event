import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from base.accounts.models import Subscription, SubscriptionStatus, SubscriptionFinancialStatus, User, Plan

user = User.objects.filter(id=7).first()
if user:
    sub, _ = Subscription.objects.get_or_create(user=user)
    sub.status = SubscriptionStatus.ACTIVE
    sub.financial_status = SubscriptionFinancialStatus.REGULAR
    plan = Plan.objects.filter(id=4).first()
    if plan:
        sub.plan = plan
        user.plan = plan
        user.save(update_fields=["plan"])
    sub.save()
    print(f"OK - {user.email} agora eh plano {plan.name if plan else 'N/A'}")
else:
    print("usuario nao encontrado")
