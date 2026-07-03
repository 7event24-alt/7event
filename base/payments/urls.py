from django.urls import path

from .views import mercadopago_webhook, stripe_webhook

app_name = "payments"

urlpatterns = [
    path("webhooks/mercadopago/", mercadopago_webhook, name="webhook_mercadopago"),
    path("webhooks/stripe/", stripe_webhook, name="webhook_stripe"),
]
