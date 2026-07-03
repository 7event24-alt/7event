import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from base.accounts.models import User

user = User.objects.filter(email="liprechaun@gmail.com").first()
sub = getattr(user, "subscription", None)
if sub:
    print(f"stripe_subscription_id={sub.stripe_subscription_id!r}")
    print(f"stripe_customer_id={sub.stripe_customer_id!r}")
    print(f"plan={sub.plan}")
    print(f"status={sub.status}")
    print(f"financial={sub.financial_status}")
    print(f"cancel_at_period_end={sub.cancel_at_period_end}")
else:
    print("sem subscription")
