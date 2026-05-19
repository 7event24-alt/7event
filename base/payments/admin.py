from django.contrib import admin

from .models import PaymentTransaction, PaymentWebhookEvent


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "external_reference",
        "user",
        "plan",
        "status",
        "amount",
        "billing_month",
        "grace_limit_date",
        "provider_payment_id",
    ]
    list_filter = ["status", "billing_month", "provider", "billing_period"]
    search_fields = ["external_reference", "user__email", "provider_payment_id"]
    readonly_fields = ["created_at", "updated_at", "raw_payload"]


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ["provider", "event_id", "topic", "resource_id", "processing_status", "created_at"]
    list_filter = ["provider", "processing_status", "topic"]
    search_fields = ["event_id", "resource_id"]
    readonly_fields = ["payload", "created_at", "processed_at"]
