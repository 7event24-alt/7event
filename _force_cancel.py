import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from base.accounts.models import User

user = User.objects.filter(email="liprechaun@gmail.com").first()
if not user:
    print("Usuario nao encontrado")
    exit()

sub = getattr(user, "subscription", None)
if not sub:
    print("Sem subscription")
    exit()

print(f"stripe_subscription_id: {sub.stripe_subscription_id}")
print(f"status atual: {sub.status} / financial: {sub.financial_status}")

# Cancelar imediatamente
from base.payments.services.stripe_client import configure, cancel_immediately
configure()
result = cancel_immediately(sub.stripe_subscription_id)
print(f"Cancelado no Stripe: {result.status}")
