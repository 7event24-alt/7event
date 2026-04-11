from django.contrib import admin
from .models import Job, EventType, JobStatus, PaymentType, PaymentStatusJob


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "client",
        "account",
        "start_date",
        "status",
        "payment_status",
        "cache",
    ]
    list_filter = ["status", "payment_status", "payment_type", "event_type", "account"]
    search_fields = ["title", "client__name", "location"]
    ordering = ["-start_date"]

    fieldsets = (
        (None, {"fields": ("account", "user", "client", "title", "event_type")}),
        ("Datas", {"fields": ("start_date", "end_date", "start_time", "end_time")}),
        ("Local e Descrição", {"fields": ("location", "description")}),
        (
            "Financeiro",
            {
                "fields": (
                    "cache",
                    "payment_type",
                    "payment_date",
                    "payment_total",
                    "payment_partial_value",
                    "payment_partial_date",
                    "payment_remaining_value",
                    "payment_remaining_date",
                )
            },
        ),
        ("Status", {"fields": ("status", "payment_status")}),
    )
