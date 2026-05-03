from django.contrib import admin
from .models import Job, JobStaff, EventType, JobStatus, PaymentType, PaymentStatusJob, JobStaffStatus


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "client",
        "created_by",
        "start_date",
        "status",
        "payment_status",
        "cache",
    ]
    list_filter = ["status", "payment_status", "payment_type", "event_type", "created_by"]
    search_fields = ["title", "client__name", "location"]
    ordering = ["-start_date"]

    fieldsets = (
        (None, {"fields": ("created_by", "client", "title", "event_type")}),
        ("Datas", {"fields": ("start_date", "end_date", "start_time", "end_time")}),
        ("Local e Descrição", {"fields": ("location", "description")}),
        (
            "Financeiro",
            {
                "fields": (
                    "total_budget",
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
        ("Status", {"fields": ("status", "payment_status", "approved_by", "approved_at")}),
    )


@admin.register(JobStaff)
class JobStaffAdmin(admin.ModelAdmin):
    list_display = ["job", "professional", "cache_value", "status", "created_at"]
    list_filter = ["status", "job", "professional"]
    search_fields = ["job__title", "professional__username"]
    ordering = ["-created_at"]