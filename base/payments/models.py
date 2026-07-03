from django.conf import settings
from django.db import models

from base.accounts.models import BillingPeriod, Plan


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    APPROVED = "approved", "Aprovado"
    REJECTED = "rejected", "Recusado"
    CANCELLED = "cancelled", "Cancelado"


class PaymentProvider(models.TextChoices):
    MERCADO_PAGO = "mercadopago", "Mercado Pago"


class PaymentTransaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    provider = models.CharField(
        max_length=30,
        choices=PaymentProvider.choices,
        default=PaymentProvider.MERCADO_PAGO,
    )
    billing_period = models.CharField(
        max_length=20,
        choices=BillingPeriod.choices,
        default=BillingPeriod.MONTHLY,
    )
    billing_month = models.DateField(help_text="Primeiro dia do mes da cobranca")
    external_reference = models.CharField(max_length=200, unique=True)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="BRL")

    provider_preference_id = models.CharField(max_length=100, blank=True)
    provider_payment_id = models.CharField(max_length=100, blank=True)
    checkout_url = models.URLField(blank=True)

    due_date = models.DateField()
    grace_limit_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)

    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment_transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["billing_month", "status"]),
            models.Index(fields=["provider_payment_id"]),
        ]

    def __str__(self):
        return f"{self.external_reference} ({self.status})"


class WebhookProcessingStatus(models.TextChoices):
    RECEIVED = "received", "Recebido"
    PROCESSED = "processed", "Processado"
    IGNORED = "ignored", "Ignorado"
    ERROR = "error", "Erro"


class PaymentWebhookEvent(models.Model):
    provider = models.CharField(
        max_length=30,
        choices=PaymentProvider.choices,
        default=PaymentProvider.MERCADO_PAGO,
    )
    event_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    topic = models.CharField(max_length=100, blank=True)
    resource_id = models.CharField(max_length=120, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    processing_status = models.CharField(
        max_length=20,
        choices=WebhookProcessingStatus.choices,
        default=WebhookProcessingStatus.RECEIVED,
    )
    error_message = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_webhook_events"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider} {self.event_id or self.pk}"
